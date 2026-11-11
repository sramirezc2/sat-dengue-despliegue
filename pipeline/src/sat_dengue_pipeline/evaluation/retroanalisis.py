"""Retroanálisis de ventana expansiva sobre el panel canónico con el arnés existente.

Reutiliza sin modificarlos prepare_horizon, run_candidate y los adaptadores de la fábrica.
Cada mes de origen se ejecuta como un fold propio del arnés; los meses sin soporte de
entrenamiento o predicción se registran y se omiten en vez de abortar la corrida.
La receta (predictores, preparación, candidato y semilla) se toma de una configuración de
experimento existente, para comparar el mismo modelo que correría la fábrica.

Si la receta declara `preparation.variables_g`, el bloque de margen se adjunta aquí, después
de la preparación canónica y antes del arnés, igual que hace la fábrica en su `_deferred_batch`.
Las seis columnas no entran a la tabla canónica: son derivadas deterministas de columnas que ya
están en ella, y agregarlas allá cambiaría el digest del artefacto.

Las probabilidades no se calibran: la comparación ordena dentro de cada mes de origen y cada
mes es un único fold, así que una calibración monótona no cambia ese orden.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import numpy as np
import pandas as pd

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.margin import (
    CLIMA_LAG_COLUMNS,
    CLIMA_LAG_FUENTES,
    DEPTO_COLUMNS,
    MARGIN_COLUMNS,
    MARGIN_SOURCES,
    MES_COLUMNS,
    ROCIO_META_COLUMNS,
    margin_features,
)
from sat_dengue_pipeline.experiments.rolling import TRAIN_FLOOR, ExperimentSpec, from_prepared
from sat_dengue_pipeline.factory.configuration import adapter_spec
from sat_dengue_pipeline.models.adapters import ModelRegistry, run_candidate
from sat_dengue_pipeline.models.familias import ADAPTERS
from sat_dengue_pipeline.preparation import PreparedSet, prepare_horizon

KEYS = ["municipality_code", "year_month"]


def conjunto_comun(
    prepared: PreparedSet, table: pd.DataFrame, horizonte: int, preparacion: dict[str, Any]
) -> tuple[PreparedSet, tuple[str, ...], dict[str, int]]:
    """Fijar el conjunto de filas común a todas las recetas y adjuntar G si se declara.

    Por qué el filtro se aplica siempre, aun sin G
    ----------------------------------------------

    El bloque de margen no se puede completar en todas las filas del panel: la
    velocidad y la aceleración necesitan el mes anterior, y `p75_canal_t` no
    existe antes de 2012 porque el canal se come los cinco años previos. En el
    release operacional eso son 152 filas —los meses 2012-01 y 2012-02 de los
    76 municipios—, todas de entrenamiento y ninguna evaluada.

    Si esas filas se descartaran solo cuando G está encendida, la corrida con G
    y la corrida sin G entrenarían sobre conjuntos distintos y la diferencia
    entre ellas ya no sería atribuible al bloque. Por eso el filtro se aplica
    **siempre**: el retroanálisis fija un conjunto evaluable común, y lo único
    que cambia entre recetas son las columnas que cada una declara.

    El bloque se calcula sobre la historia completa del municipio, no sobre las
    filas seleccionadas, porque las velocidades necesitan el mes inmediatamente
    anterior aunque ese mes no sea un origen evaluable.

    Args:
        prepared: Conjunto utilizable con las columnas canónicas.
        table: Panel canónico completo, ya filtrado por departamentos.
        horizonte: 1 o 2.
        preparacion: Bloque `preparation` de la receta.

    Returns:
        El conjunto restringido a las filas con bloque completo —con las seis
        columnas al final si la receta las declara—, los nombres declarados y
        el conteo de filas antes y después del filtro.
    """
    bloque = margin_features(table, horizonte, preparacion.get("margin_source", MARGIN_SOURCES[0]))
    alineado = bloque.reindex(pd.MultiIndex.from_frame(prepared.keys.loc[:, KEYS]))
    completo = alineado.notna().all(axis=1).to_numpy()
    cobertura = {
        "filas_preparadas": int(len(completo)),
        "filas_sin_bloque": int((~completo).sum()),
        "filas_comunes": int(completo.sum()),
    }
    keys = prepared.keys.loc[completo].reset_index(drop=True)
    X = prepared.X.loc[completo].reset_index(drop=True)
    y = prepared.y.loc[completo].reset_index(drop=True)
    derivadas: tuple[str, ...] = ()
    if preparacion.get("variables_g"):
        for column in MARGIN_COLUMNS:
            X[column] = alineado.loc[completo, column].to_numpy()
        derivadas += tuple(MARGIN_COLUMNS)
    if preparacion.get("variables_mes"):
        mes = keys.year_month.str[5:7].astype(int).to_numpy()
        X["mes_sin"] = np.sin(2 * np.pi * mes / 12)
        X["mes_cos"] = np.cos(2 * np.pi * mes / 12)
        derivadas += tuple(MES_COLUMNS)
    if preparacion.get("variable_depto"):
        X["depto_73"] = keys.municipality_code.str[:2].eq("73").astype(float).to_numpy()
        derivadas += tuple(DEPTO_COLUMNS)
    if preparacion.get("clima_rezagos"):
        orden = table.sort_values(KEYS)
        idx = pd.MultiIndex.from_frame(keys.loc[:, KEYS])
        for nombre, fuente in CLIMA_LAG_FUENTES.items():
            serie = orden.set_index(KEYS)[fuente]
            for k in (1, 2):
                rezago = serie.groupby(level=0).shift(k)
                X[f"{nombre}_lag{k}"] = rezago.reindex(idx).to_numpy(dtype=float)
        derivadas += tuple(CLIMA_LAG_COLUMNS)
    if preparacion.get("rocio_meta"):
        rocio = table.set_index(KEYS)["dewpoint_mean_c_month_mean"]
        idx = pd.MultiIndex.from_frame(keys.loc[:, KEYS])
        meta = keys.municipality_code.str[:2].eq("50").to_numpy(dtype=float)
        X["rocio_x_meta"] = rocio.reindex(idx).to_numpy(dtype=float) * meta
        derivadas += tuple(ROCIO_META_COLUMNS)
    return PreparedSet(keys, X, y), derivadas, cobertura


def predicciones_rolling(
    table: pd.DataFrame,
    schema: dict[str, Any],
    config: dict[str, Any],
    horizonte: int,
    primer_origen: str = "2019-01",
    ultimo_objetivo: str = "2024-12",
    primer_entrenamiento: str = TRAIN_FLOOR,
    ventana_anios: int | None = None,
    excluir_anios: list | None = None,
    entrenar_departamentos: list | None = None,
) -> tuple[pd.DataFrame, list[dict[str, str]], dict[str, int]]:
    """Producir predicciones fuera de muestra reentrenando en cada mes de origen.

    Args:
        table: Panel canónico hasta 2024.
        schema: Esquema del productor canónico.
        config: Configuración de experimento con predictores, preparación, candidato y semilla.
        horizonte: 1 o 2.
        primer_origen: Primer mes de origen evaluado.
        primer_entrenamiento: Primer mes objetivo utilizable para entrenar. Antes
            estaba quemado en 2018-01, heredado del release histórico; con el
            release operacional la historia llega a 2007 y el piso es 2012-01.
        ultimo_objetivo: Último mes objetivo; no puede alcanzar 2025.
        ventana_anios: Si se declara, cada origen entrena solo con los últimos años
            indicados (sin bajar del piso); si no, la ventana es expansiva.
        excluir_anios: Años objetivo que no entran al entrenamiento (siguen
            evaluándose).
        entrenar_departamentos: Si se declara, solo esos departamentos entran al
            entrenamiento; los demás se predicen sin haber entrenado con ellos.

    Returns:
        Predicciones del arnés, la lista de meses omitidos con su motivo y el
        conteo de filas del conjunto común (ver `conjunto_comun`).
    """
    demora = config["label_delay_months"]
    # La etiqueta debe estar disponible antes del periodo reservado, no solo el objetivo.
    disponible = table.year_month.map(lambda t: add_months(t, horizonte + demora))
    origins = table.loc[disponible.le(ultimo_objetivo), KEYS].reset_index(drop=True)
    _, _, prepared, _ = prepare_horizon(
        table, schema, origins, horizonte, config["predictor_availability"]
    )
    prepared, derivadas, cobertura = conjunto_comun(
        prepared, table, horizonte, config["preparation"]
    )
    data = from_prepared(prepared, horizonte, label_delay_months=demora, derived=derivadas)
    if excluir_anios:
        # Sin etiqueta no hay entrenamiento: esas filas siguen evaluándose, porque la
        # evaluación toma las etiquetas del panel y no de data.y.
        anio = data.keys.target_period.str[:4]
        y = data.y.astype("Int64").mask(anio.isin([str(a) for a in excluir_anios]))
        data = dataclasses.replace(data, y=y)
    if entrenar_departamentos:
        fuera = ~data.keys.municipality_code.str[:2].isin([str(d) for d in entrenar_departamentos])
        data = dataclasses.replace(data, y=data.y.astype("Int64").mask(fuera.to_numpy()))
    spec = adapter_spec(config)
    registry = ModelRegistry()
    if (spec.family, spec.version) not in ADAPTERS:
        raise ValueError(f"Familia no soportada: {spec.family} {spec.version}")
    registry.register(spec.family, spec.version, ADAPTERS[(spec.family, spec.version)])
    partes, omitidos = [], []
    origen = primer_origen
    while add_months(origen, horizonte + demora) <= ultimo_objetivo:
        inicio = primer_entrenamiento
        if ventana_anios:
            # Ventana móvil: solo los últimos `ventana_anios` años antes del origen.
            inicio = max(primer_entrenamiento, add_months(origen, -12 * int(ventana_anios)))
        experimento = ExperimentSpec(
            horizon=horizonte,
            seed=config["seed"],
            train_target_start=inicio,
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
    columnas = [
        "municipality_code",
        "origin_period",
        "target_period",
        "horizon",
        "fold_id",
        "candidate",
        "raw_probability",
    ]
    preds = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=columnas)
    return preds, omitidos, cobertura
