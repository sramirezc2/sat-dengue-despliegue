"""Grano mensual, joins declarados y validación usando las autoridades de V3."""

from typing import Any

import pandas as pd

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import (
    CLIMATE,
    COUNTS,
    KEYS,
    build_table,
    predictor_matrix,
    validate_source,
)
from sat_dengue_pipeline.domain.temporal import TemporalPolicy, guard_development

from .contract import BuildConfig


def canonical_sources(
    geography: pd.DataFrame,
    epidemiology: pd.DataFrame,
    climate: pd.DataFrame,
    config: BuildConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Exigir dimensión única y fuentes mensuales únicas sin claves huérfanas."""
    if len(geography) != config.municipalities or geography.municipality_code.duplicated().any():
        raise ValueError("Cardinalidad de dimensión inválida")
    for frame in (epidemiology, climate):
        if (
            frame.duplicated(KEYS).any()
            or frame[KEYS].isna().any().any()
            or not frame.municipality_code.isin(geography.municipality_code).all()
            or not frame.year_month.isin(config.periods).all()
        ):
            raise ValueError("Grano mensual, municipio o periodo desconocido")
    return geography.copy(), epidemiology.copy(), climate.copy()


def municipality_month_grid(geography: pd.DataFrame, config: BuildConfig) -> pd.DataFrame:
    """Construir exactamente el producto cartesiano, también para 182.886 claves."""
    if len(geography) != config.municipalities or geography.municipality_code.duplicated().any():
        raise ValueError("Dimensión duplicada o incompleta")
    return (
        pd.MultiIndex.from_product(
            [sorted(geography.municipality_code), config.periods], names=KEYS
        )
        .to_frame(index=False)
        .astype("string")
    )


def canonical_panel(
    sources: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame], config: BuildConfig
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Construir el producto cartesiano y reutilizar canal/lags/roles de V3."""
    geography, epidemiology, climate = canonical_sources(*sources, config)
    grid = municipality_month_grid(geography, config)
    panel = grid.merge(geography, on="municipality_code", validate="many_to_one")
    panel = panel.merge(epidemiology, on=KEYS, how="left", validate="one_to_one")
    panel["in_epi_coverage"] = panel.year_month.ge(config.epi_start)
    for name in COUNTS:
        panel[name] = panel[name].astype("Int64")
        panel.loc[panel.in_epi_coverage, name] = panel.loc[panel.in_epi_coverage, name].fillna(0)
    panel["epi_count_status"] = pd.Series("outside_epi_coverage_missing", index=panel.index)
    panel.loc[panel.in_epi_coverage, "epi_count_status"] = "zero_in_coverage"
    panel.loc[panel[COUNTS[2]].gt(0).fillna(False), "epi_count_status"] = "records_present"
    panel["epi_count_status"] = panel.epi_count_status.astype("string")
    panel = panel.merge(climate, on=KEYS, how="left", validate="one_to_one")
    # El calendario esperado es conocido incluso si no se observó ningún día.
    panel["expected_days_in_month"] = pd.array(
        pd.PeriodIndex(panel.year_month, freq="M").days_in_month, dtype="Int64"
    )
    for name in ("climate_days_observed", *(f"{c}_valid_days" for c in CLIMATE)):
        panel[name] = panel[name].astype("Int64")
    for name in CLIMATE:
        panel[name] = panel[name].astype("Float64")
    # Solo claves antes de consultar valores del productor canónico.
    policy = TemporalPolicy(config.reserved_start)
    for h in (1, 2):
        origins = panel.loc[panel.year_month.le(add_months(config.end, -h)), KEYS]
        guard_development(panel[KEYS], origins, (h,), policy)
    return build_table(panel)


def canonical_validation(
    result: tuple[pd.DataFrame, dict], config: BuildConfig, epidemiology_audit: dict
) -> tuple[pd.DataFrame, dict]:
    """Validar esquema real, orden, nulos, cuadrícula y conservación por evento."""
    table, schema = result
    validate_source(table)
    predictor_matrix(table, schema)
    if (
        len(table) != config.municipalities * len(config.periods)
        or table.municipality_code.nunique() != config.municipalities
        or sorted(table.year_month.unique()) != config.periods
        or not table[KEYS].equals(table[KEYS].sort_values(KEYS).reset_index(drop=True))
        or schema["key"] != KEYS
        or list(table) != [column["name"] for column in schema["columns"]]
    ):
        raise ValueError("Cuadrícula, orden o esquema canónico incorrecto")
    for column in schema["columns"]:
        values = table[column["name"]]
        if str(values.dtype) != column["dtype"] or bool(values.isna().any()) != column["nullable"]:
            raise ValueError("Tipos o nulabilidad canónica alterados")
    for name, source in zip(
        COUNTS[:2], ("dengue_notifications", "severe_dengue_notifications"), strict=True
    ):
        if int(table[name].sum()) != epidemiology_audit[source]["accepted"]:
            raise ValueError("No se conservan conteos epidemiológicos")
    for h in (1, 2):
        origins = table.loc[table.year_month.le(add_months(config.end, -h)), KEYS]
        guard_development(table[KEYS], origins, (h,), TemporalPolicy(config.reserved_start))
    return table, schema
