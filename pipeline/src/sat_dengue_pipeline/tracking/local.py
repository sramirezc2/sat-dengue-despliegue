"""Backend local explícito: SQLite MLflow y repositorio SDK sin registro global."""

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sat_dengue_pipeline.evaluation.paired import EvaluationReport
from sat_dengue_pipeline.experiments.rolling import stable_digest

from .privacy import LINEAGE_FIELDS, aggregate_artifacts, canonical_bytes, validate_lineage

LOGICAL_ROOT = "satdlocal:/artifacts"
TAGS = {"mlflow.runName", "scientific_digest", "artifact_digest", "tracking_schema", "failure_kind"}
ARTIFACTS = {
    "metrics.json",
    "comparisons.json",
    "strata.json",
    "curves.json",
    "uncertainty.json",
    "configuration.json",
    "lineage.json",
    "inventory.json",
    "canonical_build.json",
}


@dataclass(frozen=True)
class TrackingConfig:
    """Tracking explícito y desactivado por defecto; ruta relativa bajo .tracking."""

    enabled: bool = False
    store: str = ".tracking/local"
    experiment_name: str = "satd-evaluation"

    def __post_init__(self) -> None:
        """Rechazar URI remota, rutas absolutas, escapes y nombres privados."""
        if (
            type(self.enabled) is not bool
            or re.fullmatch(r"\.tracking/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", self.store) is None
            or ".." in Path(self.store).parts
            or re.fullmatch(r"satd-[a-z0-9_-]{1,48}", self.experiment_name) is None
        ):
            raise ValueError("Configuración local relativa inválida")


@dataclass(frozen=True)
class TrackingReceipt:
    """Recibo separado de ciencia y sin URI o ruta privada."""

    experiment_name: str
    run_id: str | None
    parent_run_id: str | None
    status: str
    tracking_enabled: bool
    artifact_digest: str


class LocalTracker:
    """Una instancia, un backend explícito; sin API fluida ni autologging."""

    def __init__(self, workspace: Path, config: TrackingConfig = TrackingConfig()) -> None:
        """Recibir ubicación operacional sin guardarla en metadatos.

        Args:
            workspace: Directorio explícito del subproyecto, nunca HOME implícito.
            config: Opt-in y ruta relativa ignorada por Git.
        """
        self.workspace = workspace.resolve()
        self.config = config
        self.root = self.workspace / config.store
        self.store: Any = None
        self.experiment_id: str | None = None

    def _open(self) -> None:
        """Abrir backend únicamente al habilitar tracking, tras validar privacidad."""
        current = self.workspace
        for part in Path(self.config.store).parts:
            current = current / part
            if current.is_symlink():
                raise ValueError("El store no admite symlinks")
        if any(
            (self.root / name).is_symlink() for name in ("tracking.sqlite", "staging", "artifacts")
        ):
            raise ValueError("Los componentes del store no admiten symlinks")
        if (
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.workspace),
                    "check-ignore",
                    "-q",
                    "--",
                    self.config.store + "/tracking.sqlite",
                ]
            ).returncode
            != 0
        ):
            raise ValueError("El store debe estar ignorado por Git")
        # Opt-outs documentados del SDK antes de importarlo; no se usan para ciencia.
        os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
        os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
        try:
            from mlflow.store.tracking.sqlalchemy_store import SqlAlchemyStore
        except ModuleNotFoundError as exc:
            raise RuntimeError("Instalar tracking con uv sync --locked --group tracking") from exc

        self.root.mkdir(parents=True, exist_ok=True)
        self.store = SqlAlchemyStore(
            "sqlite:///" + str(self.root / "tracking.sqlite"), LOGICAL_ROOT
        )
        experiment = self.store.get_experiment_by_name(self.config.experiment_name)
        self.experiment_id = (
            experiment.experiment_id
            if experiment
            else self.store.create_experiment(
                self.config.experiment_name, artifact_location=LOGICAL_ROOT
            )
        )
        if self.store.get_experiment(self.experiment_id).artifact_location != LOGICAL_ROOT:
            raise ValueError("Identidad del repositorio local alterada")

    def _artifact_dir(self, run_id: str) -> Path:
        """Resolver solo identificadores reales dentro del store configurado."""
        if re.fullmatch(r"[0-9a-f]{32}", run_id) is None:
            raise ValueError("run_id inválido")
        current = self.root
        for part in ("artifacts", run_id, "artifacts"):
            current = current / part
            if current.is_symlink():
                raise ValueError("El repositorio no admite symlinks")
        return current

    def _publish(self, run_id: str, artifacts: dict[str, Any]) -> None:
        """Publicar artefactos pequeños mediante el repositorio oficial SDK."""
        from mlflow.store.artifact.local_artifact_repo import LocalArtifactRepository

        staging = self.root / "staging"
        staging.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=staging) as temp:
            source, destination = Path(temp) / "source", Path(temp) / "artifacts"
            source.mkdir()
            repository = LocalArtifactRepository(str(destination))
            for name, value in artifacts.items():
                data = canonical_bytes(value)
                if len(data) > 512_000 or name not in ARTIFACTS:
                    raise ValueError("Artefacto desconocido o pesado")
                path = source / name
                path.write_bytes(data)
                repository.log_artifact(str(path))
            final = self._artifact_dir(run_id)
            final.parent.mkdir(parents=True, exist_ok=True)
            destination.rename(final)

    def record(self, report: EvaluationReport, lineage: dict[str, Any]) -> TrackingReceipt:
        """Observar resultados ya calculados sin modificarlos ni decidir políticas.

        Args:
            report: Agregados inmutables de tarea 11.
            lineage: Metadatos cerrados capturados por orquestación.

        Returns:
            Recibo independiente; deshabilitado no crea almacenamiento ni importa SDK.
        """
        artifacts = aggregate_artifacts(report)
        validate_lineage(lineage, report)
        assert set(lineage) == LINEAGE_FIELDS
        metrics = [
            (row["metric"], row["value"])
            for row in report.payload["metrics"]
            if row["stratum"] == "global"
            and row["reference"] == "candidate"
            and row["evaluable"]
        ]
        return self._record(artifacts, lineage, report.digest, metrics)

    def record_canonical(self, payload: dict[str, Any]) -> TrackingReceipt:
        """Observar construcción/certificación con la misma persistencia local opt-in."""
        from .canonical import validate_canonical_tracking

        validate_canonical_tracking(payload)
        lineage = {name: payload[name] for name in (
            "raw_manifest_digest", "builder_git_sha", "builder_config_digest", "lock_digest",
            "canonical_semantic_digest", "certification",
        )}
        return self._record(
            {"canonical_build.json": payload}, lineage, payload["canonical_semantic_digest"], []
        )

    def _record(
        self, artifacts: dict[str, Any], lineage: dict[str, Any], scientific_digest: str,
        metric_values: list[tuple[str, float]],
    ) -> TrackingReceipt:
        """Persistir agregados previamente validados con un único lifecycle compartido."""
        digest = stable_digest(
            {
                name: hashlib.sha256(canonical_bytes(value)).hexdigest()
                for name, value in artifacts.items()
            }
        )
        if not self.config.enabled:
            return TrackingReceipt(
                self.config.experiment_name, None, None, "DISABLED", False, digest
            )
        self._open()
        from mlflow.entities import Metric, Param, RunStatus, RunTag

        tags = {
            "mlflow.runName": self.config.experiment_name,
            "scientific_digest": scientific_digest,
            "artifact_digest": digest,
            "tracking_schema": "local-aggregates-v1",
        }
        assert set(tags) <= TAGS
        run = self.store.create_run(
            self.experiment_id,
            user_id="",
            start_time=int(time.time() * 1000),
            tags=[RunTag(k, v) for k, v in tags.items()],
            run_name=self.config.experiment_name,
        )
        run_id = run.info.run_id
        try:
            if run.info.artifact_uri != LOGICAL_ROOT + "/" + run_id + "/artifacts":
                raise ValueError("MLflow generó una URI no portable")
            params = [Param(key, canonical_bytes(value).decode()) for key, value in lineage.items()]
            metrics = [
                Metric(name, value, int(time.time() * 1000), 0)
                for name, value in metric_values
            ]
            self.store.log_batch(run_id, metrics=metrics, params=params, tags=[])
            artifacts["lineage.json"] = {**lineage, "run_id": run_id}
            inventory = {
                name: hashlib.sha256(canonical_bytes(value)).hexdigest()
                for name, value in artifacts.items()
            }
            artifacts["inventory.json"] = inventory
            self._publish(run_id, artifacts)
            self.store.update_run_info(
                run_id,
                run_status=RunStatus.FINISHED,
                end_time=int(time.time() * 1000),
                run_name=None,
            )
        except BaseException as exc:
            try:
                final = self._artifact_dir(run_id)
            except ValueError:
                final = None  # No seguir un enlace alterado durante la operación.
            if final is not None and final.exists():
                shutil.rmtree(final)
            status = (
                RunStatus.KILLED
                if isinstance(exc, (KeyboardInterrupt, SystemExit))
                else RunStatus.FAILED
            )
            self.store.update_run_info(
                run_id, run_status=status, end_time=int(time.time() * 1000), run_name=None
            )
            raise
        return TrackingReceipt(self.config.experiment_name, run_id, None, "FINISHED", True, digest)

    def get_run(self, run_id: str) -> Any:
        """Recuperar la entidad real MLflow por ID, sin singleton o servidor.

        Args:
            run_id: Identidad generada por MLflow.

        Returns:
            Run de MLflow con estado/params/tags persistidos.
        """
        if self.store is None:
            if not self.config.enabled:
                raise ValueError("Tracking desactivado")
            self._open()
        self._artifact_dir(run_id)
        return self.store.get_run(run_id)

    def close(self) -> None:
        """Liberar conexiones locales sin borrar datos o cambiar resultados científicos."""
        if self.store is not None:
            self.store.engine.dispose()
            self.store = None
            self.experiment_id = None

    def artifacts(self, run_id: str) -> dict[str, bytes]:
        """Recuperar artefactos mediante ubicación explícita y verificar inventario.

        Args:
            run_id: Corrida real terminada.

        Returns:
            Artefactos verificados; no se usa un resolver global para URI lógicas.
        """
        import json

        if self.get_run(run_id).info.status != "FINISHED":
            raise ValueError("La corrida no está completa")
        folder = self._artifact_dir(run_id)
        if any(
            path.is_symlink()
            or not path.is_file()
            or path.name not in ARTIFACTS
            or path.stat().st_size > 512_000
            for path in folder.iterdir()
        ):
            raise ValueError("Artefacto desconocido, pesado o symlink")
        values = {path.name: path.read_bytes() for path in folder.iterdir()}
        inventory = json.loads(values.pop("inventory.json"))
        if set(values) != set(inventory) or any(
            hashlib.sha256(data).hexdigest() != inventory[name] for name, data in values.items()
        ):
            raise ValueError("Inventario de artefactos alterado")
        return values
