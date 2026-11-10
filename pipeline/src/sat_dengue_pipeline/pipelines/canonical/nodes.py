"""Adaptadores Kedro delgados; las reglas pertenecen al dominio puro."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest, ResolvedBundle, ResolvedFile
from sat_dengue_pipeline.acquisition.raw_manifest import (
    OPERATIONAL_MANIFEST,
    OPERATIONAL_PROFILE,
    RAW_MANIFESTS,
    validate_raw_manifest,
)
from sat_dengue_pipeline.canonical_cache import acquire_command, preflight_cache
from sat_dengue_pipeline.domain.temporal import TemporalPolicy
from sat_dengue_pipeline.raw import build as io
from sat_dengue_pipeline.raw.contract import BuildConfig, raw_contract_validation
from sat_dengue_pipeline.raw.fixture import fixture_config, synthetic_bundle
from sat_dengue_pipeline.raw.panel import canonical_panel, canonical_sources, canonical_validation
from sat_dengue_pipeline.raw.producers import climate_monthly_aggregation
from sat_dengue_pipeline.raw.reproducibility import CertifiedCanonical, canonical_reproducibility
from sat_dengue_pipeline.raw.serialization import CanonicalArtifact, canonical_serialization
from sat_dengue_pipeline.raw.temporal import Quarantine, raw_temporal_quarantine


@dataclass(frozen=True)
class BuildInput:
    """Contexto operacional; las funciones de dominio no lo reciben."""

    bundle: ResolvedBundle
    config: BuildConfig
    inventory: dict | None
    workspace: Path
    tracking: bool
    manifest: str = OPERATIONAL_MANIFEST


def build_input(parameters: dict) -> BuildInput:
    """Elegir fixture o caché aprobada verificada; nunca descargar desde ciencia."""
    required = {"mode", "workspace", "tracking"}
    if not required <= set(parameters) <= required | {"manifest", "profile"} or (
        parameters["mode"] not in {"synthetic", "approved"}
    ):
        raise ValueError("Modo canónico desconocido")
    workspace = Path(parameters["workspace"])
    if (
        workspace.is_absolute()
        or not workspace.resolve().is_relative_to(Path("data").resolve())
        or type(parameters["tracking"]) is not bool
    ):
        raise ValueError("Workspace relativo bajo data/ requerido")
    if parameters["mode"] == "synthetic":
        if "profile" in parameters:
            raise ValueError("El fixture no admite un perfil real")
        bundle, inventory = synthetic_bundle(workspace / "raw")
        return BuildInput(bundle, fixture_config(), inventory, workspace, parameters["tracking"])
    profile = parameters.get("profile", OPERATIONAL_PROFILE)
    if profile not in {"approved", "operational_full"}:
        raise ValueError("Perfil canónico desconocido")
    config = BuildConfig.operational_full() if profile == "operational_full" else BuildConfig()
    manifest_path = parameters.get("manifest", OPERATIONAL_MANIFEST)
    if manifest_path not in RAW_MANIFESTS:
        raise ValueError("Manifiesto operacional no aprobado")
    manifest = ReleaseManifest.from_json(Path(manifest_path).read_text(encoding="utf-8"))
    validate_raw_manifest(manifest)
    cache = Path("data/01_raw/inbox") / manifest.release_id / manifest.manifest_sha256
    preflight_cache(cache, {file.relative_path for file in manifest.files}, manifest=manifest_path)
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
    return BuildInput(bundle, config, None, workspace, parameters["tracking"], manifest_path)


def validate_input(source: BuildInput) -> ResolvedBundle:
    """Validar crudos antes de proyectar claves."""
    try:
        return raw_contract_validation(source.bundle, source.config, source.inventory)
    except (ValueError, OSError):
        if source.config.profile == "synthetic":
            raise
        raise ValueError(
            f"Caché corrupta o contrato crudo inválido. Ejecute: {acquire_command(source.manifest)}"
        ) from None


def quarantine(keys: dict[str, pd.DataFrame], source: BuildInput) -> Quarantine:
    """Aplicar la autoridad temporal existente."""
    return raw_temporal_quarantine(keys, TemporalPolicy(source.config.reserved_start))


def geography(bundle: ResolvedBundle, q: Quarantine, source: BuildInput) -> pd.DataFrame:
    """Cargar JSON únicamente tras cuarentena."""
    return io.geography(bundle, source.config, q)


def epidemiology(
    bundle: ResolvedBundle, q: Quarantine, geo: pd.DataFrame, source: BuildInput
) -> tuple[pd.DataFrame, dict]:
    """Entregar al productor solo filas retenidas."""
    return io.epidemiology(bundle, q, geo, source.config)


def daily(
    bundle: ResolvedBundle,
    q: Quarantine,
    geo: pd.DataFrame,
    source: BuildInput,
    _epidemiology: tuple[pd.DataFrame, dict],
) -> tuple[pd.DataFrame, dict]:
    """Entregar días retenidos tras completar la etapa epidemiológica."""
    return io.daily_climate(bundle, q, geo, source.config)


def monthly(result: tuple[pd.DataFrame, dict]) -> pd.DataFrame:
    """Delegar al agregador puro."""
    return climate_monthly_aggregation(result[0])


def sources(
    geo: pd.DataFrame, epi: tuple[pd.DataFrame, dict], climate: pd.DataFrame, source: BuildInput
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validar contratos mensuales antes de unir."""
    return canonical_sources(geo, epi[0], climate, source.config)


def panel(inputs: tuple, source: BuildInput) -> tuple:
    """Reutilizar el productor canónico del dominio."""
    return canonical_panel(inputs, source.config)


def validate(result: tuple, source: BuildInput, epi: tuple) -> tuple:
    """Verificar esquema y conservación."""
    return canonical_validation(result, source.config, epi[1])


def serialize(result: tuple, source: BuildInput) -> CanonicalArtifact:
    """Escribir salida provisional, todavía no certificada para entrenar."""
    raw_contract_validation(source.bundle, source.config, source.inventory)
    return canonical_serialization(result, source.workspace / "provisional")


def audit(result: tuple, q: Quarantine, epi: tuple, climate: tuple, months: pd.DataFrame) -> dict:
    """Resumir etapas sin pasar filas al observador."""
    return io.build_audit(result, q, epi[1], climate[1], len(months))


def certify(source: BuildInput) -> CertifiedCanonical:
    """Reconstruir N=3 desde cero, sin salida provisional compartida."""
    return canonical_reproducibility(
        source.bundle, source.config, source.workspace, source.inventory
    )


def observe(
    source: BuildInput, artifact: CanonicalArtifact, audit: dict, hashes: tuple[str, ...] = ()
) -> object:
    """Conectar el observador existente después del cálculo."""
    from sat_dengue_pipeline.tracking.canonical import collect_canonical_tracking
    from sat_dengue_pipeline.tracking.local import LocalTracker, TrackingConfig

    workspace = Path.cwd()
    payload = collect_canonical_tracking(
        workspace.parent, source.bundle, source.config, artifact, audit, hashes
    )
    tracker = LocalTracker(
        workspace, TrackingConfig(enabled=source.tracking, experiment_name="satd-canonical")
    )
    try:
        return tracker.record_canonical(payload)
    finally:
        tracker.close()


def observe_certificate(source: BuildInput, certificate: CertifiedCanonical) -> object:
    """Observar únicamente huellas y agregados del gate."""
    return observe(source, certificate.artifact, certificate.audit, certificate.hashes)
