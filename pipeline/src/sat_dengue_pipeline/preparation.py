"""Preparación sin modelos: X, y y controles separados tras la compuerta temporal."""

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .domain.canonical import KEYS, PREDICTORS, predictor_matrix
from .domain.onset import build_labels, validate_label_metadata
from .domain.temporal import TemporalPolicy, guard_development

# Disponibilidad conceptual respecto de T; no prueba latencias de un release real.
PREDICTOR_AVAILABILITY = {
    name: -int(name.rsplit("_lag", 1)[1]) if "_lag" in name else 0 for name in PREDICTORS
}


@dataclass(frozen=True)
class PreparedSet:
    """Filas utilizables con claves, X e y físicamente separados y alineados."""

    keys: pd.DataFrame
    X: pd.DataFrame
    y: pd.Series


def project_predictors(
    table: pd.DataFrame, schema: dict[str, Any], availability: dict[str, int]
) -> pd.DataFrame:
    """Aplicar roles cerrados y disponibilidad explícita relativa al origen.

    Args:
        table: Tabla canónica.
        schema: Roles no solapados del productor.
        availability: Mes relativo de disponibilidad de cada predictor.

    Returns:
        Copia de X sin objetivos, estados futuros ni controles.
    """
    if set(availability) != set(PREDICTORS) or any(
        type(offset) is not int or offset > 0 for offset in availability.values()
    ):
        raise ValueError("Disponibilidad futura o incompleta de predictores")
    return predictor_matrix(table, schema)


def _validate_existing_metadata(source: pd.DataFrame, expected: pd.DataFrame, horizon: int) -> None:
    """Comprobar metadatos recibidos únicamente para orígenes ya autorizados."""
    names = [
        f"target_period_t{horizon}",
        f"y_t{horizon}",
        f"y_evaluable_t{horizon}",
        f"y_status_t{horizon}",
    ]
    present = [name for name in names if name in source]
    if not present:
        return
    rows = source.set_index(KEYS).loc[pd.MultiIndex.from_frame(expected[KEYS])]
    rows = rows.reset_index()
    for name in present:
        equal = rows[name].eq(expected[name]) | (rows[name].isna() & expected[name].isna())
        if not equal.fillna(False).all():
            raise ValueError(f"Metadato objetivo inconsistente: {name}")
    if any(name in present for name in names[1:]) and set(present) != set(names):
        raise ValueError("Metadatos de etiqueta incompletos")
    if set(present) == set(names):
        validate_label_metadata(rows, horizon)


def prepare_horizon(
    table: pd.DataFrame,
    schema: dict[str, Any],
    origins: pd.DataFrame,
    horizon: int,
    availability: dict[str, int],
    policy: TemporalPolicy = TemporalPolicy(),
) -> tuple[pd.DataFrame, pd.DataFrame, PreparedSet, dict[str, Any]]:
    """Preparar un horizonte sin modificar elegibilidad por observaciones futuras.

    Args:
        table: Historia canónica y resultados retrospectivos hasta 2024.
        schema: Roles completos del productor.
        origins: Selección explícita de pronósticos, no toda la historia.
        horizon: T+1 o T+2.
        availability: Disponibilidad relativa de los predictores.
        policy: Compuerta previa a cualquier lectura de etiquetas.

    Returns:
        Controles, etiquetas, conjunto utilizable con X/y separados y auditoría.
        Utilizable exige elegibilidad en T, X completo y etiqueta evaluable;
        estas tres condiciones se contabilizan separadamente.
    """
    guard_development(table, origins, (horizon,), policy)
    table = table.reset_index(drop=True)
    X = project_predictors(table, schema, availability)
    zone = table.zona_canal_t
    if not zone.dropna().isin(["EXITO", "SEGURIDAD", "ALERTA", "EXCESO"]).all():
        raise ValueError("Zona del canal inválida")
    states = table[KEYS].copy()
    states["excess"] = zone.eq("EXCESO").astype("Int64").where(zone.notna(), pd.NA)
    outcome = build_labels(states, origins, horizon, policy)
    _validate_existing_metadata(table, outcome, horizon)
    _validate_existing_metadata(origins, outcome, horizon)
    selected = (
        table[KEYS]
        .join(X)
        .set_index(KEYS)
        .loc[pd.MultiIndex.from_frame(outcome[KEYS]), PREDICTORS]
        .reset_index(drop=True)
    )
    y_name = f"y_t{horizon}"
    complete = selected.notna().all(axis=1)
    usable = outcome.eligible_at_t & complete & outcome[y_name].notna()
    eligible = PreparedSet(
        keys=outcome.loc[usable, KEYS].reset_index(drop=True).copy(),
        X=selected.loc[usable].reset_index(drop=True).copy(),
        y=outcome.loc[usable, y_name].reset_index(drop=True).copy(),
    )
    controls = outcome.drop(columns=y_name).copy()
    controls["predictor_complete"] = complete
    controls["usable"] = usable
    audit = {
        "horizon": horizon,
        "reserved_start": policy.reserved_start,
        "origin_rows": len(outcome),
        "eligible_at_t_rows": int(outcome.eligible_at_t.sum()),
        "evaluable_rows": int(outcome[f"y_evaluable_t{horizon}"].sum()),
        "predictor_complete_rows": int(complete.sum()),
        "usable_rows": int(usable.sum()),
        "last_origin": str(outcome.year_month.max()),
        "last_target": str(outcome[f"target_period_t{horizon}"].max()),
        "predictor_availability": dict(availability),
        "operational_historical_availability": "UNPROVEN; retrospective consolidated data",
    }
    return controls, outcome[KEYS + [y_name]].copy(), eligible, audit
