"""Retroanálisis de ventana expansiva sobre el panel canónico con el arnés existente.

Reutiliza sin modificarlos prepare_horizon, from_prepared, run_candidate y el adaptador
XGBoost de la fábrica. Cada mes de origen se ejecuta como un fold propio del arnés; los meses
sin soporte de entrenamiento o predicción se registran y se omiten en vez de abortar la corrida.
La receta (predictores, preparación, candidato y semilla) se toma de una configuración de
experimento existente, para comparar el mismo modelo que correría la fábrica.

Las probabilidades no se calibran: la comparación ordena dentro de cada mes de origen y cada
mes es un único fold, así que una calibración monótona no cambia ese orden.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.experiments.rolling import ExperimentSpec, from_prepared
from sat_dengue_pipeline.factory.configuration import adapter_spec
from sat_dengue_pipeline.models.adapters import ModelRegistry, run_candidate
from sat_dengue_pipeline.models.familias import ADAPTERS
from sat_dengue_pipeline.preparation import prepare_horizon

KEYS = ["municipality_code", "year_month"]


def predicciones_rolling(
    table: pd.DataFrame,
    schema: dict[str, Any],
    config: dict[str, Any],
    horizonte: int,
    primer_origen: str = "2019-01",
    ultimo_objetivo: str = "2024-12",
) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    """Producir predicciones fuera de muestra reentrenando en cada mes de origen.

    Args:
        table: Panel canónico hasta 2024.
        schema: Esquema del productor canónico.
        config: Configuración de experimento con predictores, preparación, candidato y semilla.
        horizonte: 1 o 2.
        primer_origen: Primer mes de origen evaluado.
        ultimo_objetivo: Último mes objetivo; no puede alcanzar 2025.

    Returns:
        Predicciones del arnés concatenadas y la lista de meses omitidos con su motivo.
    """
    demora = config["label_delay_months"]
    # La etiqueta debe estar disponible antes del periodo reservado, no solo el objetivo.
    disponible = table.year_month.map(lambda t: add_months(t, horizonte + demora))
    origins = table.loc[disponible.le(ultimo_objetivo), KEYS].reset_index(drop=True)
    _, _, prepared, _ = prepare_horizon(
        table, schema, origins, horizonte, config["predictor_availability"]
    )
    data = from_prepared(prepared, horizonte, label_delay_months=demora)
    spec = adapter_spec(config)
    registry = ModelRegistry()
    if (spec.family, spec.version) not in ADAPTERS:
        raise ValueError(f"Familia no soportada: {spec.family} {spec.version}")
    registry.register(spec.family, spec.version, ADAPTERS[(spec.family, spec.version)])
    partes, omitidos = [], []
    origen = primer_origen
    while add_months(origen, horizonte + demora) <= ultimo_objetivo:
        experimento = ExperimentSpec(
            horizon=horizonte,
            seed=config["seed"],
            first_origin=origen,
            last_target=add_months(origen, horizonte),
            label_delay_months=demora,
        )
        try:
            frame, _ = run_candidate(data, experimento, spec, registry)
            partes.append(frame)
        except ValueError as error:
            omitidos.append({"origin_period": origen, "motivo": str(error)})
        origen = add_months(origen, 1)
    columnas = ["municipality_code", "origin_period", "target_period", "horizon", "fold_id",
                "candidate", "raw_probability"]
    preds = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=columnas)
    return preds, omitidos
