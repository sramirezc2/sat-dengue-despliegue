"""Ejecutor registrado; reutiliza ciencia de factory.engine sin alterar T16."""

import importlib.metadata
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.factory import engine
from sat_dengue_pipeline.factory.configuration import project_root
from sat_dengue_pipeline.raw.build import build
from sat_dengue_pipeline.raw.contract import BuildConfig, sha256
from sat_dengue_pipeline.raw.serialization import load_canonical

from .configuration import load_configuration
from .evidence import publish
from .registry import Registry, confined, identifier, registry_lock
from .tracking import ExperimentTracker


class ExecutionError(RuntimeError):
    """Ejecución terminal no exitosa; detalle público limitado al recibo agregado."""


def utc_now() -> str:
    """Registrar UTC inequívoco fuera de las identidades deterministas."""
    return datetime.now(timezone.utc).isoformat()


def code_identity(root: Path) -> dict:
    """Capturar código/dirty/lock/versiones sin incluir diffs, rutas privadas o entorno."""

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()

    return {
        "git_sha": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "source_sha256": stable_digest(
            {
                p.relative_to(root).as_posix(): sha256(p)
                for p in sorted((root / "pipeline/src").rglob("*"))
                if p.is_file() and p.suffix in {".py", ".json"}
            }
        ),
        "lock_sha256": sha256(root / "pipeline/uv.lock"),
        "versions": {
            n: importlib.metadata.version(n)
            for n in ("numpy", "pandas", "scikit-learn", "scipy", "xgboost", "kedro")
        },
    }


def acquire_and_build(root: Path, config: dict, workspace: Path) -> tuple:
    """Adquirir release fijado y reconstruir, sin aceptar tablas derivadas externas."""
    if config["data"]["mode"] == "synthetic":
        from .synthetic import acceptance_bundle

        bundle, inventory, build_config = acceptance_bundle(workspace / "raw")
    else:
        from sat_dengue_pipeline.acquisition.factory import acquire

        settings = config["data"]
        bundle, receipt = acquire(
            {
                "acquisition": {
                    "manifest": settings["manifest"].removeprefix("pipeline/"),
                    "cache": "data/01_raw/experiments",
                    "require_private": settings["require_private"],
                }
            },
            root / "pipeline",
        )
        if bundle is None:
            raise ExecutionError("acquisition_failed")
        inventory, build_config = None, BuildConfig()
    artifact, audit = build(bundle, build_config, workspace / "canonical", inventory)
    table, schema = load_canonical(artifact)
    # load_canonical verifica bytes, digest semántico, esquema y tipos antes del consumidor.
    return bundle, artifact, audit, table, schema


def execute(
    experiment_id: str,
    *,
    root: Path | None = None,
    execution_id: str | None = None,
    tracking: bool = True,
) -> dict[str, Any]:
    """Ejecutar una receta aprobada y persistir terminales aun ante error o interrupción.

    Args:
        experiment_id: Identidad registrada y aprobada.
        root: Raíz del repositorio; por defecto el subproyecto instalado.
        execution_id: Identidad opcional para recuperación/pruebas; nunca sobrescribible.
        tracking: Habilitar MLflow local explícito.

    Returns:
        Recibo terminal completado; fallos propagan ExecutionError o interrupción.
    """
    root = root or project_root().parent
    execution_id = identifier(execution_id or uuid.uuid4().hex)
    lineage = code_identity(root)
    with registry_lock(root):
        registry = Registry(root)
        entry = registry.get(experiment_id, approved=True)
        config = load_configuration(root, entry)
        registry.assert_identity(entry)
        relative = f"docs/evidence/experiments/{experiment_id}/{execution_id}"
        folder = confined(root, relative, "docs/evidence/experiments", exists=False)
        folder.parent.mkdir(parents=True, exist_ok=True)
        folder.mkdir()  # Reserva exclusiva antes de cambiar estado o crear MLflow.
        registry.transition(experiment_id, "RUNNING")
    workspace = confined(
        root, f"pipeline/data/experiments/{execution_id}", "pipeline/data", exists=False
    )
    started = utc_now()
    lineage["dataset_manifest_sha256"] = config["data"]["manifest_sha256"]
    run = None
    error: BaseException | None = None
    status = "FAILED"
    gate = "initialization"
    tracker = ExperimentTracker(root / "pipeline", tracking)
    parent = None
    tags = {
        k: str(entry[k])
        for k in (
            "experiment_id",
            "hypothesis_id",
            "protocol_sha256",
            "configuration_sha256",
            "experiment_type",
        )
    }
    tags.update(execution_id=execution_id, code_sha256=lineage["source_sha256"], evidence=relative)
    children = []
    try:
        parent = tracker.start(tags)
        workspace.mkdir(parents=True)
        gate = "acquisition_canonical_build"
        bundle, artifact, audit, table, schema = acquire_and_build(root, config, workspace)
        lineage.update(
            dataset_manifest_sha256=bundle.manifest_sha256,
            release_id=bundle.release_id,
            raw_hashes={f.logical_name: f.sha256 for f in bundle.files},
            canonical_semantic_sha256=artifact.semantic_digest,
            canonical_serialized_sha256=artifact.serialized_sha256,
        )
        run = engine.FactoryRun(
            bundle,
            config,
            workspace,
            lineage,
            artifact=artifact,
            table=table,
            schema=schema,
            audit=audit,
        )
        for function in (
            engine.prepare,
            engine.preflight,
            engine.fit,
            engine.predict,
            engine.evaluate,
        ):
            gate = function.__name__
            function(run)
        status = "COMPLETED"
    except BaseException as exc:
        error = exc
        status = (
            "KILLED"
            if isinstance(exc, (KeyboardInterrupt, SystemExit))
            else ("BLOCKED" if isinstance(exc, (engine.FactoryGateError, ValueError)) else "FAILED")
        )
    signature_fields = {
        "experiment_id": experiment_id,
        "protocol_sha256": entry["protocol_sha256"],
        "configuration_sha256": entry["configuration_sha256"],
        **lineage,
    }
    signature = stable_digest(signature_fields)
    tags.update(
        dataset_sha256=str(lineage["dataset_manifest_sha256"]), execution_signature=signature
    )
    results = run.results if run is not None else {}
    try:
        if status == "COMPLETED" and len(results) > 1:
            for h, result in sorted(results.items()):
                child_tags = {**tags, "horizon": h, "candidate": config["candidate"]["family"]}
                child = tracker.start(child_tags, parent)
                children.append(child)
                tracker.finish(child, status, child_tags, result["metrics"])
        parent_metrics = {
            h + "." + ref: records
            for h, result in results.items()
            for ref, records in result["metrics"].items()
        }
        tracker.finish(parent, status, tags, parent_metrics)
    except BaseException as exc:
        error = exc
        status = "KILLED" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "FAILED"
        gate = "tracking"
        # Las corridas creadas deben terminar incluso si el logging falló.
        for run_id in [*children, parent]:
            if run_id is not None:
                from mlflow.entities import RunStatus

                tracker.store.update_run_info(
                    run_id, RunStatus.KILLED if status == "KILLED" else RunStatus.FAILED, None, None
                )
    receipt = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "execution_id": execution_id,
        "experiment_type": entry["experiment_type"],
        "execution_signature": signature,
        "protocol_sha256": entry["protocol_sha256"],
        "configuration_sha256": entry["configuration_sha256"],
        "status": status,
        "started_utc": started,
        "finished_utc": utc_now(),
        "horizons": config["horizons"],
        "candidate": config["candidate"]["family"],
        "seed": config["seed"],
        "gate": gate,
        "error_type": type(error).__name__ if error else None,
        "mlflow": {"enabled": tracking, "parent_run_id": parent, "children": children},
        "champion_status": "NOT_SELECTED",
        "operational_authorization": False,
    }
    artifacts = {
        "receipt.json": receipt,
        "configuration.json": config,
        "lineage.json": signature_fields,
        "metrics.json": results,
        "validation.json": {
            "status": status,
            "support": run.support if run else {},
            "temporal": run.temporal if run else {},
            "canonical_audit": run.audit if run else {},
            "artifact_sha256": run.identities if run else {},
            "label_reads": run.label_reads if run else {},
        },
    }
    try:
        publish(folder, artifacts)
    except BaseException as exc:
        failed = "KILLED" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "FAILED"
        try:
            for run_id in [*children, parent]:
                if run_id is not None:
                    from mlflow.entities import RunStatus

                    tracker.store.update_run_info(
                        run_id,
                        RunStatus.KILLED if failed == "KILLED" else RunStatus.FAILED,
                        None,
                        None,
                    )
            with registry_lock(root):
                Registry(root).transition(experiment_id, "BLOCKED", "BLOCKED")
            from .evidence import exclusive_json

            workspace.mkdir(parents=True, exist_ok=True)
            exclusive_json(
                workspace / "evidence-failure.json",
                {
                    **receipt,
                    "status": failed,
                    "gate": "evidence_publish",
                    "error_type": type(exc).__name__,
                    "incomplete_evidence": relative,
                },
            )
        finally:
            tracker.close()
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise ExecutionError(f"{failed}:evidence_publish; execution_id={execution_id}") from None
    tracker.close()
    if error:
        with registry_lock(root):
            Registry(root).transition(experiment_id, "BLOCKED", "BLOCKED")
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise error
        raise ExecutionError(f"{status}:{gate}; execution_id={execution_id}") from None
    # RUNNING significa resultados disponibles pendientes de conclusiones humanas.
    return receipt


def kedro_execute(experiment_id: str) -> dict:
    """Nodo delgado: toda la ejecución falla con código no cero si no se completa."""
    return execute(experiment_id)
