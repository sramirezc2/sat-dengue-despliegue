"""Etapas de publicación Kedro; recibos exclusivos fuera de evidencia histórica."""

import re
import uuid
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest, ResolvedBundle, ResolvedFile
from sat_dengue_pipeline.acquisition.factory import acquire
from sat_dengue_pipeline.acquisition.raw_manifest import OPERATIONAL_MANIFEST, validate_raw_manifest
from sat_dengue_pipeline.canonical_cache import preflight_cache
from sat_dengue_pipeline.models.logistic import canonical_json
from sat_dengue_pipeline.pipelines.deployment_publication.contract import decode_json
from sat_dengue_pipeline.pipelines.deployment_publication.io import (
    promote,
    stage_package,
    validate_staging,
)
from sat_dengue_pipeline.raw.contract import BuildConfig, raw_contract_validation

from .configuration import ROOT, lineage, local_path, recipe, sha
from .frozen import FrozenLogistic, load_artifact, materialize, save_artifact
from .inference import feature_prefix, prioritize
from .publication import build_package, document, load_schema


@dataclass
class Context:
    """Contexto operacional local; no se serializan rutas ni credenciales."""

    settings: dict
    artifact_dir: Path
    run_dir: Path
    provenance: dict
    frozen: FrozenLogistic | None = None
    receipt: dict = field(default_factory=lambda: {"status": "RUNNING", "stages": []})

    def record(self) -> None:
        """Actualizar solo el recibo de esta reserva operacional exclusiva."""
        from sat_dengue_pipeline.raw.serialization import atomic_write

        atomic_write(self.run_dir / "receipt.json", canonical_json(self.receipt))


def audited(name: str) -> Callable:
    """Registrar fallos sanitizados sin esconder intentos ni escribir historia."""

    def decorate(function: Callable) -> Callable:
        @wraps(function)
        def run(context: Context, *args: Any) -> Any:
            try:
                result = function(context, *args)
                context.receipt["stages"].append(name)
                context.record()
                return result
            except Exception as error:
                context.receipt.update(
                    status="FAILED", failed_stage=name, error_type=type(error).__name__
                )
                context.record()
                raise

        return run

    return decorate


def preflight(settings: dict) -> Context:
    """Verificar identidad y artefacto antes de adquirir o interpretar fuentes."""
    required = {
        "mode",
        "source",
        "artifact_directory",
        "artifact_sha256",
        "certificate",
        "certificate_sha256",
        "edition",
    }
    if (
        not required <= set(settings) <= required | {"run_directory", "approval_record"}
        or settings["mode"] not in {"materialize", "frozen"}
        or (
            settings["source"] not in {"approved", "synthetic"}
            or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", settings["edition"])
        )
    ):
        raise ValueError("Configuración de prioridades incompatible")
    recipe()
    artifact = local_path(settings["artifact_directory"])
    run_dir = local_path(settings.get("run_directory") or "data/risk-2025/runs/" + uuid.uuid4().hex)
    run_dir.mkdir(parents=True, exist_ok=False)
    context = Context(settings, artifact, run_dir, lineage())
    context.receipt["execution_id"] = run_dir.name
    context.record()
    try:
        if (
            settings["mode"] == "frozen"
            and not settings["artifact_sha256"]
            and settings.get("approval_record")
        ):
            from sat_dengue_pipeline.canonical_cache import reject_cache_symlinks

            pointer = local_path(settings["approval_record"])
            reject_cache_symlinks(pointer)
            approved = decode_json(pointer.read_bytes())
            if set(approved) != {
                "artifact_directory",
                "artifact_sha256",
                "certificate",
                "certificate_sha256",
            }:
                raise ValueError("Registro de activación incompatible")
            settings = {**settings, **approved}
            context.settings = settings
            context.artifact_dir = artifact = local_path(settings["artifact_directory"])
        if settings["source"] == "approved":
            manifest = ReleaseManifest.from_json(
                (ROOT / "pipeline" / OPERATIONAL_MANIFEST).read_text()
            )
            validate_raw_manifest(manifest)
            raw_digest = manifest.manifest_sha256
        else:
            from .synthetic import write_sources

            bundle, inventory = write_sources(run_dir / "raw")
            context.receipt["synthetic_inventory"] = inventory
            raw_digest = bundle.manifest_sha256
        context.provenance["raw_manifest_sha256"] = raw_digest
        if settings["mode"] == "materialize":
            if artifact.exists() or settings["artifact_sha256"] or settings["certificate_sha256"]:
                raise ValueError("Materialización exige destino nuevo y no una identidad previa")
        else:
            if not re.fullmatch(r"[0-9a-f]{64}", settings["artifact_sha256"]):
                raise ValueError("Publicación ordinaria exige SHA-256 aprobado del artefacto")
            context.frozen = load_artifact(
                artifact, settings["artifact_sha256"], context.provenance
            )
            certificate = local_path(settings["certificate"])
            from sat_dengue_pipeline.canonical_cache import reject_cache_symlinks

            reject_cache_symlinks(certificate)
            raw = certificate.read_bytes()
            if sha(raw) != settings["certificate_sha256"]:
                raise ValueError("Certificado no aprobado")
            proof = decode_json(raw)
            if set(proof) != {"status", "artifact_sha256", "package_sha256", "runs"} or (
                proof["status"] != "CERTIFIED_N3"
                or len(proof["runs"]) != 3
                or len({r["execution_id"] for r in proof["runs"]}) != 3
                or proof["artifact_sha256"] != settings["artifact_sha256"]
                or any(
                    r["artifact_sha256"] != proof["artifact_sha256"]
                    or r["package_sha256"] != proof["package_sha256"]
                    for r in proof["runs"]
                )
            ):
                raise ValueError("Certificación aislada incompleta o divergente")
            context.receipt["certified_package_sha256"] = proof["package_sha256"]
        context.record()
        return context
    except Exception as error:
        context.receipt.update(
            status="FAILED", failed_stage="preflight", error_type=type(error).__name__
        )
        context.record()
        raise


@audited("raw_integrity")
def sources(context: Context) -> ResolvedBundle:
    """Resolver cinco fuentes del worktree; adquirir únicamente si faltan."""
    if context.settings["source"] == "synthetic":
        from sat_dengue_pipeline.raw.fixture import fixture_inventory

        bundle, inventory = fixture_inventory(context.run_dir / "raw")
        config = BuildConfig(
            profile="synthetic", start="2007-01", epi_start="2007-01", municipalities=76
        )
        raw_contract_validation(bundle, config, inventory)
        return bundle
    manifest = ReleaseManifest.from_json((ROOT / "pipeline" / OPERATIONAL_MANIFEST).read_text())
    cache = local_path(f"data/01_raw/inbox/{manifest.release_id}/{manifest.manifest_sha256}")
    names = {f.relative_path for f in manifest.files}
    preflight_cache(cache, names, manifest=OPERATIONAL_MANIFEST, allow_missing=True)
    if not cache.exists() or any(not (cache / n).exists() for n in names):
        bundle, result = acquire(
            {
                "acquisition": {
                    "manifest": OPERATIONAL_MANIFEST,
                    "cache": "data/01_raw/inbox",
                    "require_private": True,
                }
            },
            ROOT / "pipeline",
        )
        if bundle is None:
            raise ValueError("Adquisición fallida: " + result["error_type"])
    preflight_cache(cache, names, manifest=OPERATIONAL_MANIFEST)
    bundle = ResolvedBundle(
        manifest.release_id,
        manifest.manifest_sha256,
        manifest.coverage_start,
        manifest.coverage_end,
        tuple(
            ResolvedFile(f.logical_name, cache / f.relative_path, f.size_bytes, f.sha256)
            for f in manifest.files
        ),
        manifest.release_kind,
    )
    raw_contract_validation(bundle, BuildConfig.operational_full())
    return bundle


@audited("frozen_model")
def frozen_model(context: Context, bundle: ResolvedBundle) -> FrozenLogistic:
    """Materializar una sola vez o usar exclusivamente el artefacto verificado."""
    if context.frozen is not None:
        return context.frozen
    if context.settings["mode"] != "materialize":
        raise ValueError("Modo congelado sin artefacto verificado; no hay fallback de ajuste")
    table, schema = feature_prefix(
        bundle, "2024-10", dimension_count=76 if context.settings["source"] == "synthetic" else 1122
    )
    model = materialize(table, schema, context.provenance)
    save_artifact(model, context.artifact_dir)
    return load_artifact(context.artifact_dir, model.artifact_sha256, context.provenance)


@audited("monthly_priorities")
def monthly(context: Context, bundle: ResolvedBundle, model: FrozenLogistic) -> list[dict]:
    """Construir doce prefijos independientes, sin estado futuro compartido."""
    from sat_dengue_pipeline.domain.calendar import add_months

    docs = []
    for m in range(1, 13):
        target = f"2025-{m:02d}"
        origin = add_months(target, -2)
        table, schema = feature_prefix(
            bundle,
            origin,
            dimension_count=(76 if context.settings["source"] == "synthetic" else 1122),
        )
        rows, feature_sha = prioritize(table, schema, origin, model)
        docs.append(
            document(
                rows,
                feature_sha,
                target,
                model,
                bundle.release_id,
                (
                    "SYNTHETIC"
                    if context.settings["source"] == "synthetic"
                    else "CONSOLIDATED_RETROSPECTIVE"
                ),
            )
        )
    # Detectar cambios concurrentes de los bytes después de construir predictores.
    for f in bundle.files:
        from sat_dengue_pipeline.raw.contract import sha256

        if f.path.stat().st_size != f.size_bytes or sha256(f.path) != f.sha256:
            raise ValueError("Fuentes alteradas durante la ejecución")
    return docs


@audited("package_validation")
def package(context: Context, documents: list[dict]) -> Any:
    """Validar todo el lote antes de tocar la frontera publicada."""
    result = build_package(documents)
    package_sha = sha(result.manifest)
    if context.settings["mode"] == "frozen" and (
        package_sha != context.receipt["certified_package_sha256"]
    ):
        raise ValueError("Publicación distinta de la certificación aprobada")
    context.receipt.update(
        artifact_sha256=documents[0]["trace"]["artifact_sha256"], package_sha256=package_sha
    )
    return result


@audited("publication")
def publish(context: Context, result: Any) -> dict:
    """Materialización no promueve; publicación ordinaria exige certificado N=3."""
    if context.settings["mode"] == "materialize":
        context.receipt["status"] = "MATERIALIZED_NOT_PUBLISHED"
        context.record()
        return context.receipt
    destination = local_path(
        "datos/resultados/risk-ranking/" + context.settings["edition"], published=True
    )
    if context.settings["source"] == "synthetic":
        destination = context.run_dir / "results"
    schema = load_schema()
    committed = promote(
        validate_staging(stage_package(result, destination, schema), schema), schema
    )
    context.receipt.update(status="COMMITTED", publication_manifest_sha256=sha(result.manifest))
    context.record()
    return committed
