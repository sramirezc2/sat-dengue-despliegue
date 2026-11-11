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
from sat_dengue_pipeline.domain.derived import DERIVED_COLUMNS, declared_derived
from sat_dengue_pipeline.domain.margin import (
    CLIMA_LAG_FUENTES,
    MARGIN_SOURCES,
    margin_features,
)
from sat_dengue_pipeline.domain.regional import regional_features
from sat_dengue_pipeline.experiments.rolling import (
    TRAIN_FLOOR,
    ExperimentData,
    ExperimentSpec,
    from_prepared,
)
from sat_dengue_pipeline.factory.configuration import adapter_spec
from sat_dengue_pipeline.models.adapters import ModelRegistry, run_candidate
from sat_dengue_pipeline.models.familias import ADAPTERS
from sat_dengue_pipeline.preparation import PreparedSet, prepare_horizon

KEYS = ["municipality_code", "year_month"]


def _rezago_mensual(table: pd.DataFrame, fuente: str, k: int, claves: pd.MultiIndex):
    """Valor de `fuente` k meses antes, buscado por mes calendario del municipio.

    No se usa `groupby.shift(k)`: eso toma la fila k posiciones atrás, que con un
    hueco de calendario no es el mes que se pide y produce una resta contra el mes
    equivocado sin avisar. Es el mismo arreglo que ya tiene `margin.py`.
    """
    serie = table.set_index(KEYS)[fuente]
    anterior = [
        str(pd.Period(mes, freq="M") - k) for mes in claves.get_level_values("year_month")
    ]
    buscado = pd.MultiIndex.from_arrays([claves.get_level_values("municipality_code"), anterior])
    return serie.reindex(buscado).to_numpy(dtype=float)


def bloques_derivados(
    keys: pd.DataFrame, table: pd.DataFrame, horizonte: int, preparacion: dict[str, Any]
) -> pd.DataFrame:
    """Construir **todas** las derivadas conocidas, alineadas con las filas preparadas.

    Se construyen todas, declare la receta las que declare, porque el conjunto de
    filas evaluables tiene que ser el mismo para cualquier receta: si un bloque
    se pudiera completar solo a veces y el filtro mirara únicamente los bloques
    encendidos, dos recetas entrenarían sobre filas distintas sin que
    `conjunto.csv` lo mostrara, y la diferencia entre ellas dejaría de ser
    atribuible a sus columnas.

    Args:
        keys: Claves de las filas preparadas.
        table: Panel canónico completo, ya filtrado por departamentos.
        horizonte: 1 o 2.
        preparacion: Bloque `preparation` de la receta; de aquí sale la fuente
            de casos del margen, que es una decisión declarada.

    Returns:
        Un DataFrame con las columnas de `DERIVED_COLUMNS` que el panel admite,
        en ese orden y con el índice de `keys`.
    """
    claves = pd.MultiIndex.from_frame(keys.loc[:, KEYS])
    columnas: dict[str, Any] = {}

    margen = margin_features(
        table, horizonte, preparacion.get("margin_source", MARGIN_SOURCES[0])
    ).reindex(claves)
    for columna in margen.columns:
        columnas[columna] = margen[columna].to_numpy()

    mes = keys.year_month.str[5:7].astype(int).to_numpy()
    columnas["mes_sin"] = np.sin(2 * np.pi * mes / 12)
    columnas["mes_cos"] = np.cos(2 * np.pi * mes / 12)
    columnas["depto_73"] = keys.municipality_code.str[:2].eq("73").astype(float).to_numpy()

    for nombre, fuente in CLIMA_LAG_FUENTES.items():
        for k in (1, 2):
            columnas[f"{nombre}_lag{k}"] = _rezago_mensual(table, fuente, k, claves)

    rocio = table.set_index(KEYS)["dewpoint_mean_c_month_mean"].reindex(claves)
    meta = keys.municipality_code.str[:2].eq("50").to_numpy(dtype=float)
    columnas["rocio_x_meta"] = rocio.to_numpy(dtype=float) * meta

    regional = regional_features(table).reindex(claves)
    for columna in regional.columns:
        columnas[columna] = regional[columna].to_numpy()

    return pd.DataFrame(
        {columna: columnas[columna] for columna in DERIVED_COLUMNS}, index=keys.index
    )


def conjunto_comun(
    prepared: PreparedSet, table: pd.DataFrame, horizonte: int, preparacion: dict[str, Any]
) -> tuple[PreparedSet, tuple[str, ...], dict[str, int]]:
    """Fijar el conjunto de filas común a todas las recetas y adjuntar lo declarado.

    Por qué el filtro se aplica siempre y sobre todos los bloques
    -------------------------------------------------------------

    Los bloques derivados no se pueden completar en todas las filas del panel:
    sus velocidades y rezagos necesitan meses anteriores, y `p75_canal_t` no
    existe antes de 2012 porque el canal se come los cinco años previos. En el
    release operacional eso son 152 filas —los meses 2012-01 y 2012-02 de los 76
    municipios—, todas de entrenamiento y ninguna evaluada.

    Si esas filas se descartaran solo cuando el bloque está encendido, la corrida
    con bloque y la corrida sin él entrenarían sobre conjuntos distintos y la
    diferencia entre ellas ya no sería atribuible al bloque. Por eso el filtro
    mira **todos** los bloques conocidos, no solo los que la receta declara: el
    retroanálisis fija un conjunto evaluable común y lo único que cambia entre
    recetas son las columnas que cada una pide.

    Un bloque enteramente ausente no es información y no puede vaciar la corrida:
    pasa cuando el panel no lo admite, como el regional sobre un panel con un
    solo municipio por departamento. Se excluye del filtro y se deja anotado; si
    una receta lo declara, eso sí es un error y se dice con su nombre.

    Args:
        prepared: Conjunto utilizable con las columnas canónicas.
        table: Panel canónico completo, ya filtrado por departamentos.
        horizonte: 1 o 2.
        preparacion: Bloque `preparation` de la receta.

    Returns:
        El conjunto restringido a las filas con los bloques completos —con las
        columnas declaradas al final—, sus nombres y el conteo de filas.

    Raises:
        ValueError: Si la receta declara un bloque que el panel no admite.
    """
    bloques = bloques_derivados(prepared.keys, table, horizonte, preparacion)
    derivadas = declared_derived(preparacion)
    aplicables = [columna for columna in bloques.columns if bloques[columna].notna().any()]
    ausentes = [columna for columna in derivadas if columna not in aplicables]
    if ausentes:
        raise ValueError(
            "La receta declara derivadas que el panel no admite: " + ", ".join(ausentes)
        )
    completo = bloques.loc[:, aplicables].notna().all(axis=1).to_numpy()
    cobertura = {
        "filas_preparadas": int(len(completo)),
        "filas_sin_bloque": int((~completo).sum()),
        "filas_comunes": int(completo.sum()),
        "bloques_del_filtro": len(aplicables),
        "municipios": int(prepared.keys.municipality_code.nunique()),
    }
    keys = prepared.keys.loc[completo].reset_index(drop=True)
    X = prepared.X.loc[completo].reset_index(drop=True)
    y = prepared.y.loc[completo].reset_index(drop=True)
    for columna in derivadas:
        X[columna] = bloques.loc[completo, columna].to_numpy()
    return PreparedSet(keys, X, y), derivadas, cobertura


CADENCIAS = ("mensual", "anual")


def recortar_a_la_cadencia(data: ExperimentData, origen: str, corte: str) -> ExperimentData:
    """Dejar solo el entrenamiento hasta un corte y el mes de origen que se evalúa.

    Por qué el recorte va aquí y no en el arnés
    -------------------------------------------

    El banco de la línea O reentrena una vez al año; el retroanálisis lo hace en
    cada mes de origen. Para medir esa diferencia hay que poder fijar el fin del
    entrenamiento, y el arnés lo deriva del origen de cada fold.

    Cambiarlo allá significaría agregar un campo a `ExperimentSpec`, que entra al
    digest del protocolo y por lo tanto cambia el `fold_id` de **todos** los
    experimentos existentes, incluida la certificación. Recortar las filas
    consigue exactamente lo mismo sin tocar nada: la máscara del fold sigue
    pidiendo «objetivos entre el piso y el mes anterior al origen», pero entre el
    corte y ese mes ya no queda ninguna fila. El arnés queda byte a byte igual.

    El recorte solo puede quitar filas de entrenamiento, nunca agregarlas, así
    que no abre ninguna vía de fuga que el arnés no tuviera ya cerrada.

    Args:
        data: Entradas completas del arnés.
        origen: Mes de origen que se va a evaluar; sus filas se conservan.
        corte: Último mes objetivo admitido para entrenar.

    Returns:
        Una copia con las claves, X, y y controles alineados y reindexados.
    """
    keys = data.keys
    conservar = (keys.target_period.le(corte) | keys.origin_period.eq(origen)).to_numpy()
    return ExperimentData(
        keys.loc[conservar].reset_index(drop=True),
        data.X.loc[conservar].reset_index(drop=True),
        data.y.loc[conservar].reset_index(drop=True),
        data.controls.loc[conservar].reset_index(drop=True),
        predictors=data.predictors,
        derived=data.derived,
    )


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
    cadencia: str = "mensual",
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
        cadencia: `mensual`, el reentrenamiento del arnés, o `anual`, el del
            banco de la línea O: un solo ajuste por año, con el entrenamiento
            cerrado en diciembre del año anterior.

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
    if cadencia not in CADENCIAS:
        raise ValueError(f"Cadencia no declarada: {cadencia}")
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
        # Con cadencia anual el entrenamiento se cierra en diciembre del año
        # anterior y no se mueve dentro del año, como hace el banco.
        entradas = data
        if cadencia == "anual":
            entradas = recortar_a_la_cadencia(data, origen, f"{int(origen[:4]) - 1}-12")
        try:
            frame, _ = run_candidate(entradas, experimento, spec, registry)
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
