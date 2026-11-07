"""Tabla canónica y roles cerrados; procedencia: canonical/table.py de V2, 916a69f."""

from typing import Any

import numpy as np
import pandas as pd

from .calendar import add_months, history_periods_for_target, validate_period
from .endemic_channel import CHANNEL, compute_current_endemic_channel, percentile_type7

KEYS = ["municipality_code", "year_month"]
COUNTS = [
    "dengue_notifications_count",
    "dengue_grave_notifications_count",
    "total_notifications_count",
]
CLIMATE = [
    "rain_mm_month_sum",
    "surface_runoff_mm_month_sum",
    "total_evaporation_mm_month_sum_ecmwf",
    "solar_radiation_mj_m2_month_sum",
    "temp_mean_c_month_mean",
    "dewpoint_mean_c_month_mean",
    "soil_water_l1_month_mean",
    "wind_u_ms_month_mean",
    "wind_v_ms_month_mean",
]
LAGS = (1, 2, 3, 12)
PREDICTORS = [
    *COUNTS,
    *CLIMATE,
    *CHANNEL,
    "month_of_year",
    *(f"{name}_lag{lag}" for name in COUNTS for lag in LAGS),
    *(f"{stat}_h5_t{h}" for h in (1, 2) for stat in ("p25", "p75")),
]


def validate_source(panel: pd.DataFrame) -> None:
    """Validar el contrato municipio-mes sin imputar ceros ni reparar entradas.

    Args:
        panel: Conteos separados, clima mensual, días válidos y cobertura.

    Raises:
        ValueError: Si hay claves, conteos, cobertura o agregados inconsistentes.
    """
    required = {
        *KEYS,
        *COUNTS,
        *CLIMATE,
        "department_code",
        "in_epi_coverage",
        "epi_count_status",
        "expected_days_in_month",
        "climate_days_observed",
        *(f"{c}_valid_days" for c in CLIMATE),
    }
    if panel.empty or panel.columns.duplicated().any() or not required <= set(panel):
        raise ValueError("Esquema fuente vacío o inválido")
    if panel[KEYS].isna().any().any() or panel.duplicated(KEYS).any():
        raise ValueError("Claves municipio-mes nulas o duplicadas")
    if not all(
        isinstance(code, str) and len(code) == 5 and code.isascii() and code.isdigit()
        for code in panel.municipality_code
    ):
        raise ValueError("Código DANE inválido")
    for period in panel.year_month:
        validate_period(period)
    if not panel.department_code.eq(panel.municipality_code.str[:2]).fillna(False).all():
        raise ValueError("Departamento incoherente con municipio")
    coverage = panel.in_epi_coverage
    if not all(isinstance(value, (bool, np.bool_)) for value in coverage):
        raise ValueError("Cobertura epidemiológica inválida")
    for name in COUNTS:
        values = panel[name]
        if not pd.api.types.is_numeric_dtype(values) or pd.api.types.is_bool_dtype(values):
            raise ValueError("Conteos no numéricos")
        present = values.dropna()
        if (
            values[coverage].isna().any()
            or values[~coverage].notna().any()
            or (present < 0).any()
            or (present % 1 != 0).any()
            or not np.isfinite(present.astype(float)).all()
        ):
            raise ValueError("Conteos o cobertura inválidos; ausencia no es cero")
    if (
        not (panel[COUNTS[2]].eq(panel[COUNTS[0]] + panel[COUNTS[1]]) | ~coverage)
        .fillna(False)
        .all()
    ):
        raise ValueError("Total inconsistente con conteos separados")
    expected_status = pd.Series("outside_epi_coverage_missing", index=panel.index)
    expected_status.loc[coverage & panel[COUNTS[2]].eq(0)] = "zero_in_coverage"
    expected_status.loc[coverage & panel[COUNTS[2]].gt(0)] = "records_present"
    if not panel.epi_count_status.eq(expected_status).all():
        raise ValueError("Estado epidemiológico inconsistente")
    days = pd.Series(pd.PeriodIndex(panel.year_month, freq="M").days_in_month, index=panel.index)
    if not (panel.expected_days_in_month.eq(days) | panel.expected_days_in_month.isna()).all():
        raise ValueError("Días esperados inconsistentes con calendario")
    for name in CLIMATE:
        valid = panel[f"{name}_valid_days"]
        if not pd.api.types.is_numeric_dtype(valid) or not pd.api.types.is_numeric_dtype(
            panel[name]
        ):
            raise ValueError("Clima o días válidos no numéricos")
        complete = valid.eq(days).fillna(False)
        if (
            (valid.dropna() < 0).any()
            or (valid.dropna() % 1 != 0).any()
            or valid.gt(days).any()
            or panel.loc[~complete, name].notna().any()
            or not np.isfinite(panel[name].dropna().astype(float)).all()
        ):
            raise ValueError("Agregado climático incompatible con cobertura")


def build_table(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Preservar las columnas fuente y agregar predictores retrospectivos exactos.

    Args:
        panel: Panel fuente del contrato, sin mutación.

    Returns:
        Tabla ordenada y esquema con roles explícitos no solapados.
    """
    validate_source(panel)
    table = panel.sort_values(KEYS).reset_index(drop=True).copy()
    channel = compute_current_endemic_channel(table)
    for name in CHANNEL:
        if name in table:
            equal = table[name].eq(channel[name]) | (table[name].isna() & channel[name].isna())
            if not equal.fillna(False).all():
                raise ValueError("Canal fuente inconsistente con H5")
        table[name] = channel[name]
    derived = {
        "month_of_year",
        *(f"{name}_lag{lag}" for name in COUNTS for lag in LAGS),
        *(f"{stat}_h5_t{h}" for h in (1, 2) for stat in ("p25", "p75", "history_valid_years")),
    }
    if derived & set(panel):
        raise ValueError("Colisión de columnas derivadas")
    table["month_of_year"] = table.year_month.str[-2:].astype(int)
    for name in COUNTS:
        lookup = table.set_index(KEYS)[name].to_dict()
        for lag in LAGS:
            table[f"{name}_lag{lag}"] = pd.array(
                [
                    lookup.get((m, add_months(t, -lag)), pd.NA)
                    for m, t in table[KEYS].itertuples(index=False, name=None)
                ],
                dtype="Float64",
            )
    lookup = table.set_index(KEYS)[COUNTS[0]].to_dict()
    for horizon in (1, 2):
        histories = []
        for municipality, origin in table[KEYS].itertuples(index=False, name=None):
            periods = history_periods_for_target(add_months(origin, horizon))
            if any(period > origin for period in periods):
                raise ValueError("Historia posterior al origen")
            values = [lookup.get((municipality, p), pd.NA) for p in periods]
            histories.append([float(value) for value in values if pd.notna(value)])
        table[f"history_valid_years_h5_t{horizon}"] = [len(v) for v in histories]
        for stat, quantile in (("p25", 0.25), ("p75", 0.75)):
            table[f"{stat}_h5_t{horizon}"] = pd.array(
                [percentile_type7(v, quantile) if len(v) == 5 else pd.NA for v in histories],
                dtype="Float64",
            )
    roles = {
        "key": list(KEYS),
        "metadata": [
            n for n in ("department_code", "municipality_name", "department_name") if n in table
        ],
        "feature": list(PREDICTORS),
        "target": [n for n in ("y_t1", "y_t2") if n in table],
    }
    assigned = {n for columns in roles.values() for n in columns}
    roles["control"] = [n for n in table if n not in assigned]
    schema = {
        "schema": "canonical_model_table_v1",
        "key": KEYS,
        "column_roles": roles,
        "columns": [
            {
                "name": n,
                "dtype": str(table[n].dtype),
                "nullable": bool(table[n].isna().any()),
                "role": next(role for role, columns in roles.items() if n in columns),
                "source": "stage2" if n in panel else "derived_at_origin",
            }
            for n in table
        ],
    }
    return table, schema


def predictor_matrix(table: pd.DataFrame, schema: dict[str, Any]) -> pd.DataFrame:
    """Seleccionar exclusivamente predictores cerrados y ordenados.

    Args:
        table: Tabla canónica validada.
        schema: Roles producidos por build_table.

    Returns:
        Copia de X sin etiquetas, controles o metadatos futuros.
    """
    roles = schema["column_roles"]
    assigned = [n for columns in roles.values() for n in columns]
    if (
        list(roles) != ["key", "metadata", "feature", "target", "control"]
        or roles.get("feature") != PREDICTORS
        or roles.get("key") != KEYS
        or len(assigned) != len(set(assigned))
        or set(assigned) != set(table)
    ):
        raise ValueError("Roles canónicos alterados")
    return table.loc[:, PREDICTORS].copy()


def coverage_report(table: pd.DataFrame, schema: dict[str, Any]) -> dict[str, Any]:
    """Reportar cobertura técnica real sin filtrar cohortes ni declarar uso operativo.

    Args:
        table: Tabla canónica con ausencias preservadas.
        schema: Esquema de roles del productor.

    Returns:
        Diagnósticos equivalentes al reporte de canonical/table.py de V2.
    """
    ready = predictor_matrix(table, schema).notna().all(axis=1)
    result: dict[str, Any] = {
        "rows": len(table),
        "municipalities": int(table.municipality_code.nunique()),
        "period_start": str(table.year_month.min()),
        "period_end": str(table.year_month.max()),
        "department_codes": sorted(table.department_code.unique().tolist()),
        "national_availability": "UNVERIFIED; no national ingestion in Phase 1",
        "eligibility_rule": (
            "complete canonical predictors and observed target; "
            "technical only, no experiment admission"
        ),
        "departments": {},
        "missing_by_column": {n: int(table[n].isna().sum()) for n in table},
    }
    for code, name in (("50", "Meta"), ("73", "Tolima")):
        group = table.loc[table.department_code.eq(code)]
        result["departments"][name] = {
            "status": "AVAILABLE" if len(group) else "UNAVAILABLE",
            "rows": len(group),
            "municipalities": int(group.municipality_code.nunique()),
            "period_start": str(group.year_month.min()) if len(group) else None,
            "period_end": str(group.year_month.max()) if len(group) else None,
            "observed_zero_rows": int(group.epi_count_status.eq("zero_in_coverage").sum()),
            "missing_epi_rows": int(group[COUNTS[0]].isna().sum()),
            "complete_climate_rows": int(group[CLIMATE].notna().all(axis=1).sum()),
            "predictor_complete_rows": int(ready.loc[group.index].sum()),
            "eligible_rows_by_target": {
                target: int((ready.loc[group.index] & group[target].notna()).sum())
                for target in schema["column_roles"]["target"]
            },
        }
    return result
