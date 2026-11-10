"""Ejecutor registrado; reutiliza ciencia de factory.engine sin alterar T16."""

import importlib.metadata
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.factory import engine, rolling_protocol
from sat_dengue_pipeline.factory.configuration import project_root
from sat_dengue_pipeline.raw.build import build
from sat_dengue_pipeline.raw.contract import sha256
from sat_dengue_pipeline.raw.serialization import load_canonical

from .certification import CertificationError, load_certified_recipe, verify_consumed
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
        from .synthetic import acceptance_bundle, scientific_acceptance_bundle

        source = (
            scientific_acceptance_bundle if config.get("schema_version") == 3 else acceptance_bundle
        )
        bundle, inventory, build_config = source(workspace / "raw")
        proof = None
    else:
        from sat_dengue_pipeline.acquisition.factory import acquire

        settings = config["data"]
        proof = load_certified_recipe(root, settings)
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
        inventory, build_config = None, proof.config
    if config.get("schema_version") == 3 and config["data"]["mode"] == "synthetic":
        from sat_dengue_pipeline.raw.reproducibility import canonical_reproducibility

        certified = canonical_reproducibility(
            bundle, build_config, workspace / "canonical", inventory
        )
        artifact, audit = certified.artifact, certified.audit
    else:
        certified = None
        artifact, audit = build(bundle, build_config, workspace / "canonical", inventory)
    canonical_lineage = (
        verify_consumed(proof, bundle, artifact, audit)
        if proof is not None
        else {
            "profile": build_config.payload(),
            "coverage": audit["coverage"],
            "certificate": None,
            "semantic_digest": artifact.semantic_digest,
            "serialized_sha256": artifact.serialized_sha256,
        }
    )
    if certified is not None:
        canonical_lineage.update(
            certification_status="PASSED_SYNTHETIC_N3",
            n3_serialized_hashes=list(certified.hashes),
            n3_semantic_digests=list(certified.semantic_digests),
            worker_pids=list(certified.worker_pids),
        )
    table, schema = load_canonical(artifact)
    # load_canonical verifica bytes, digest semántico, esquema y tipos antes del consumidor.
    return bundle, artifact, audit, table, schema, canonical_lineage


@dataclass
class RegisteredExecution:
    """Sesión única del lifecycle; Kedro pasa la referencia sin copiar conexiones/modelos."""

    root: Path
    entry: dict
    config: dict
    folder: Path
    workspace: Path
    lineage: dict
    started: str
    tracker: ExperimentTracker
    tags: dict
    parent: str | None = None
    children: list = field(default_factory=list)
    runs: dict = field(default_factory=dict)
    history_cache: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)
    scientific_records: list = field(default_factory=list)
    gate: str = "initialization"
    finalized: bool = False

    def __deepcopy__(self, memo: dict) -> "RegisteredExecution":
        """Conservar la sesión propietaria al cruzar MemoryDataset, sin duplicar SQLite."""
        return self


def begin_execution(
    experiment_id: str,
    *,
    root: Path | None = None,
    execution_id: str | None = None,
    tracking: bool = True,
) -> RegisteredExecution:
    """Reservar identidad/registro/evidencia una vez, antes de cualquier etapa científica."""
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
        folder.mkdir()
        registry.transition(experiment_id, "RUNNING")
    workspace = confined(
        root, f"pipeline/data/experiments/{execution_id}", "pipeline/data", exists=False
    )
    lineage.update(
        dataset_manifest_file_sha256=config["data"]["manifest_sha256"],
        dataset_manifest_digest=None,
        dataset_manifest_sha256=None,
        requested_canonical=config["data"].get("canonical"),
    )
    if config.get("schema_version") == 3:
        lineage["scientific_contract"] = config["scientific_evaluation"]["contract"]
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
    if config.get("schema_version") == 3:
        tags.update(
            evaluation_label="VEREDICTO_BAJO_CONTRATO_PROPUESTO",
            contract_status="PROPUESTA_PARA_APROBACION",
            contract_sha256=config["scientific_evaluation"]["contract"]["sha256"],
        )
    session = RegisteredExecution(
        root,
        entry,
        config,
        folder,
        workspace,
        lineage,
        utc_now(),
        ExperimentTracker(root / "pipeline", tracking),
        tags,
    )
    try:
        session.parent = session.tracker.start(tags)
        workspace.mkdir(parents=True)
    except BaseException as error:
        finish_execution(session, error)
    return session


STAGES = (
    "acquisition_canonical_build",
    "prepare",
    "preflight",
    "fit",
    "predict",
    "evaluate",
    "scientific_evaluation",
)


def advance(session: RegisteredExecution, *, stage: str) -> RegisteredExecution:
    """Ejecutar una etapa compartida por CLI/API y nodos Kedro, preservando cada fallo."""
    if session.finalized or stage not in STAGES:
        raise ValueError("Etapa inválida o sesión ya cerrada")
    if stage == "scientific_evaluation" and session.config.get("schema_version") != 3:
        return session
    session.gate = stage
    try:
        if stage == "acquisition_canonical_build":
            bundle, artifact, audit, table, schema, canonical = acquire_and_build(
                session.root, session.config, session.workspace
            )
            table = rolling_protocol.filtrar_poblacion(table, session.config)
            session.lineage.update(
                dataset_manifest_sha256=bundle.manifest_sha256,
                dataset_manifest_digest=bundle.manifest_sha256,
                release_id=bundle.release_id,
                raw_hashes={f.logical_name: f.sha256 for f in bundle.files},
                canonical_semantic_sha256=artifact.semantic_digest,
                canonical_serialized_sha256=artifact.serialized_sha256,
                canonical=canonical,
            )
            if session.config.get("protocol", "fixed_roles") == "rolling_origin":
                session.gate = "rolling_origin"
                session.runs["legacy"] = rolling_protocol.ejecutar(
                    table, schema, session.config, audit
                )
                configurations = []
            elif session.config.get("schema_version") == 3:
                from sat_dengue_pipeline.evaluation.scientific.configuration import variants

                configurations = [(name, config) for name, config, _ in variants(session.config)]
            else:
                configurations = [("legacy", session.config)]
            for name, config in configurations:
                session.runs[name] = engine.FactoryRun(
                    bundle,
                    config,
                    session.workspace / name,
                    session.lineage,
                    artifact=artifact,
                    table=table,
                    schema=schema,
                    audit=audit,
                    history_cache=session.history_cache,
                )
        elif stage == "scientific_evaluation":
            from sat_dengue_pipeline.evaluation.scientific.reporting import evaluate_runs

            session.scientific_records, session.results = evaluate_runs(
                session.runs, session.config
            )
        elif session.config.get("protocol", "fixed_roles") != "rolling_origin":
            function = getattr(engine, stage)
            for run in session.runs.values():
                function(run)
    except BaseException as error:
        finish_execution(session, error)
    return session


def finish_execution(
    session: RegisteredExecution, error: BaseException | None = None
) -> dict[str, Any]:
    """Cerrar MLflow e inventario con la única implementación de terminales existente."""
    if session.finalized:
        raise ValueError("Sesión ya finalizada")
    session.finalized = True
    root, entry, config = session.root, session.entry, session.config
    folder, workspace, lineage = session.folder, session.workspace, session.lineage
    relative = folder.relative_to(root).as_posix()
    started, tracker, parent = session.started, session.tracker, session.parent
    tags, children = session.tags, session.children
    experiment_id, execution_id = entry["experiment_id"], folder.name
    run = next(iter(session.runs.values()), None)
    gate = "canonical_certification" if isinstance(error, CertificationError) else session.gate
    tracking = tracker.config.enabled
    status = (
        "COMPLETED"
        if error is None
        else "KILLED"
        if isinstance(error, (KeyboardInterrupt, SystemExit))
        else "BLOCKED"
        if isinstance(error, (engine.FactoryGateError, ValueError))
        else "FAILED"
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
    results = (
        session.results
        if session.config.get("schema_version") == 3
        else (run.results if run is not None else {})
    )
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
        "schema_version": 2,
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
        "diagnostic": error.code if isinstance(error, CertificationError) else None,
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
        if config.get("schema_version") == 3:
            from .evidence import scientific_artifacts

            additions = scientific_artifacts(session.scientific_records)
            artifacts.update(additions)
            receipt["scientific_evaluation"] = {
                "label": "VEREDICTO_BAJO_CONTRATO_PROPUESTO",
                "contract": config["scientific_evaluation"]["contract"],
                "seeds": config["scientific_evaluation"]["seeds"],
                "cuts": [c["id"] for c in config["scientific_evaluation"]["cuts"]],
                "arms": [a["id"] for a in config["scientific_evaluation"]["arms"]],
                "records": sorted(additions),
                "summary": [
                    {
                        key: record[key]
                        for key in (
                            "arm",
                            "population",
                            "reading",
                            "horizon",
                            "territory",
                            "status",
                            "B",
                            "decision_basis",
                        )
                    }
                    for fragment in additions.values()
                    for record in fragment["records"]
                    if record["kind"] == "seed_stability"
                ],
                "pending_scientific_limits": [
                    "team_approval",
                    "finalist_E2E_N3",
                    "independent_confirmatory_cohort",
                ],
                "scientific_conclusion": "NOT_APPROVED",
            }
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
        diagnostic = f":{error.code}" if isinstance(error, CertificationError) else ""
        raise ExecutionError(f"{status}:{gate}{diagnostic}; execution_id={execution_id}") from None
    # RUNNING significa resultados disponibles pendientes de conclusiones humanas.
    return receipt


def execute(
    experiment_id: str,
    *,
    root: Path | None = None,
    execution_id: str | None = None,
    tracking: bool = True,
) -> dict[str, Any]:
    """Usar exactamente las etapas del grafo Kedro, sin otro orquestador científico.

    Args:
        experiment_id: Identidad registrada y aprobada, nunca reutilizada.
        root: Raíz del repositorio; opcional para aceptación aislada.
        execution_id: Identidad exclusiva; no permite sobrescritura.
        tracking: Habilitar el backend MLflow local existente.

    Returns:
        Recibo terminal con conclusiones humanas todavía pendientes.
    """
    session = begin_execution(
        experiment_id, root=root, execution_id=execution_id, tracking=tracking
    )
    for stage in STAGES:
        advance(session, stage=stage)
    return finish_execution(session)


def kedro_execute(experiment_id: str) -> dict:
    """Nodo delgado: toda la ejecución falla con código no cero si no se completa."""
    return execute(experiment_id)
