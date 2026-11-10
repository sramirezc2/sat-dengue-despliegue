"""Nodos sin proveedores ni modelos para preparación temporal independiente."""

from typing import Any

import pandas as pd

from sat_dengue_pipeline.domain.temporal import TemporalPolicy, guard_development
from sat_dengue_pipeline.preparation import prepare_horizon


def check_temporal_gate(
    table: pd.DataFrame, origins: pd.DataFrame, reserved_start: str
) -> pd.DataFrame:
    """Validar ambos horizontes antes de liberar orígenes a los nodos posteriores.

    Args:
        table: Tabla canónica; solo se consultan claves.
        origins: Selección de orígenes.
        reserved_start: Primer mes reservado.

    Returns:
        Copia de orígenes autorizados.
    """
    guard_development(table, origins, (1, 2), TemporalPolicy(reserved_start))
    return origins.copy(deep=True)


def prepare_onset(
    table: pd.DataFrame,
    schema: dict[str, Any],
    checked_origins: pd.DataFrame,
    availability: dict[str, int],
    reserved_start: str,
) -> dict[str, Any]:
    """Producir etiquetas, controles, auditoría y conjuntos separados por horizonte.

    Args:
        table: Tabla canónica, con historia y resultados permitidos.
        schema: Roles del productor.
        checked_origins: Orígenes liberados por la compuerta previa.
        availability: Disponibilidad explícita de predictores al origen.
        reserved_start: Primer mes reservado.

    Returns:
        Seis salidas para datasets en memoria; ninguna persistencia o modelo.
    """
    policy = TemporalPolicy(reserved_start)
    # Repetir la compuerta protege también la invocación directa del nodo.
    guard_development(table, checked_origins, (1, 2), policy)
    controls, audits = {}, {}
    output: dict[str, Any] = {}
    for horizon in (1, 2):
        control, labels, eligible, audit = prepare_horizon(
            table, schema, checked_origins, horizon, availability, policy
        )
        controls[f"t{horizon}"] = control
        audits[f"t{horizon}"] = audit
        output[f"labels_t{horizon}"] = labels
        output[f"eligible_t{horizon}"] = eligible
    return {**output, "controls": controls, "audit": audits}
