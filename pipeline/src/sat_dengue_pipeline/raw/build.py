"""Orquestación de I/O local; las reglas de normalización viven en funciones puras."""

import json
from pathlib import Path

import pandas as pd

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle
from sat_dengue_pipeline.domain.temporal import TemporalPolicy

from .contract import BuildConfig, raw_contract_validation
from .panel import canonical_panel, canonical_sources, canonical_validation
from .producers import (
    climate_daily_normalization,
    climate_monthly_aggregation,
    epidemiology_normalization,
    geography_normalization,
)
from .serialization import CanonicalArtifact, canonical_serialization
from .temporal import Quarantine, raw_temporal_projection, raw_temporal_quarantine


def geography(bundle: ResolvedBundle, config: BuildConfig, quarantine: Quarantine) -> pd.DataFrame:
    """Cargar JSON solo después de la compuerta de cuarentena."""
    if not quarantine.audit:
        raise ValueError("Falta cuarentena")
    files = {file.logical_name: file for file in bundle.files}
    return geography_normalization(
        json.loads(files["divipola_catalog"].path.read_text(encoding="utf-8-sig")),
        json.loads(files["divipola_provenance"].path.read_text(encoding="utf-8-sig")),
        files["divipola_catalog"].sha256,
        config,
    )


def retained_frame(bundle: ResolvedBundle, quarantine: Quarantine, name: str) -> pd.DataFrame:
    """Cargar strings por chunks y filtrar filas ANTES de interpretar valores."""
    path = next(file.path for file in bundle.files if file.logical_name == name)
    allowed = set(quarantine.retained[name])
    chunks = []
    for chunk in pd.read_csv(path, dtype=str, keep_default_na=False, chunksize=50_000):
        chunks.append(chunk.loc[chunk.index.isin(allowed)].copy())
    return pd.concat(chunks, ignore_index=True)


def epidemiology(
    bundle: ResolvedBundle, quarantine: Quarantine, dimension: pd.DataFrame, config: BuildConfig
) -> tuple[pd.DataFrame, dict]:
    """Entregar al productor únicamente registros epidemiológicos retenidos."""
    return epidemiology_normalization(
        {
            name: retained_frame(bundle, quarantine, name)
            for name in ("dengue_notifications", "severe_dengue_notifications")
        },
        dimension,
        config,
    )


def daily_climate(
    bundle: ResolvedBundle, quarantine: Quarantine, dimension: pd.DataFrame, config: BuildConfig
) -> tuple[pd.DataFrame, dict]:
    """Entregar al productor únicamente días retenidos."""
    return climate_daily_normalization(
        retained_frame(bundle, quarantine, "daily_climate"), dimension, config
    )


def build(
    bundle: ResolvedBundle, config: BuildConfig, root: Path, inventory: dict | None = None
) -> tuple[CanonicalArtifact, dict]:
    """Reconstruir sin caché canónica, fit, proveedor o reutilización de derivados."""
    verified = raw_contract_validation(bundle, config, inventory)
    projection = raw_temporal_projection(verified)
    quarantine = raw_temporal_quarantine(projection, TemporalPolicy(config.reserved_start))
    dimension = geography(verified, config, quarantine)
    epi, epi_audit = epidemiology(verified, quarantine, dimension, config)
    daily, climate_audit = daily_climate(verified, quarantine, dimension, config)
    monthly = climate_monthly_aggregation(daily)
    sources = canonical_sources(dimension, epi, monthly, config)
    result = canonical_validation(canonical_panel(sources, config), config, epi_audit)
    # Vincular la salida a los mismos bytes, incluso ante cambios externos durante la corrida.
    raw_contract_validation(bundle, config, inventory)
    artifact = canonical_serialization(result, root)
    return artifact, build_audit(result, quarantine, epi_audit, climate_audit, len(monthly))


def build_audit(
    result: tuple[pd.DataFrame, dict],
    quarantine: Quarantine,
    epi_audit: dict,
    climate_audit: dict,
    monthly_rows: int,
) -> dict:
    """Generar solo conteos/cobertura/nulos; sin filas, municipios o valores."""
    table, _ = result
    return {
        "quarantine": quarantine.audit,
        "coverage": {
            "start": str(table.year_month.min()),
            "end": str(table.year_month.max()),
            "municipalities": int(table.municipality_code.nunique()),
            "rows": len(table),
            "nulls": {name: int(table[name].isna().sum()) for name in table},
        },
        "stages": {
            "epidemiology": epi_audit,
            "climate": climate_audit,
            "monthly_climate_rows": monthly_rows,
        },
    }
