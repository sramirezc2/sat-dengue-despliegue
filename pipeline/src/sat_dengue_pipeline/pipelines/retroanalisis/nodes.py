"""Nodo del retroanálisis: predicciones por origen y validación contra el canal.

Por qué este nodo verifica el panel antes de medir
--------------------------------------------------

El pipeline `retroanalisis` arranca con los parámetros por defecto de
`conf/base/parameters.yml`, donde `canonical.mode` es `synthetic`: dos municipios
ficticios (50998 y 73998) y 84 meses desde 2018-01. Con ese panel ningún fold
tiene soporte —los percentiles del canal se comen los cinco años anteriores— así
que los 163 orígenes se omiten uno por uno, el nodo escribía tres CSV vacíos y
Kedro reportaba «Pipeline execution completed successfully in 6.3 sec».

Una medición que no midió nada no puede reportar éxito. Las dos guardas de abajo
—`verificar_panel` antes de empezar y el corte por horizonte sin folds— existen
para que ese caso falle diciendo qué pasó, en vez de dejar un resumen vacío que
alguien pueda leer como resultado.
"""

from pathlib import Path

import pandas as pd
import yaml

from sat_dengue_pipeline.evaluation.retroanalisis import predicciones_rolling
from sat_dengue_pipeline.evaluation.validacion_anual import validar_candidato
from sat_dengue_pipeline.experiments.rolling import TRAIN_FLOOR
from sat_dengue_pipeline.raw.serialization import load_canonical


def verificar_panel(table: pd.DataFrame, params: dict, piso: str) -> None:
    """Rechazar un panel que no puede sostener la medición declarada.

    La receta declara qué panel espera —desde cuándo y con cuántos municipios—
    y aquí se compara contra el panel que llegó. No se infiere el modo del
    artefacto canónico: el esquema serializado no lo lleva, así que la
    exigencia se escribe en `parameters_retroanalisis.yml` y se verifica.

    Args:
        table: Panel canónico ya filtrado por departamentos.
        params: Parámetros del retroanálisis; exige `cobertura_desde` y
            `municipios_minimos`.
        piso: Primer mes objetivo utilizable para entrenar.

    Raises:
        ValueError: Si el panel está vacío, empieza después de lo exigido o
            trae menos municipios de los declarados.
    """
    if table.empty:
        raise ValueError(
            "Panel vacío tras filtrar departamentos: no hay nada que medir. "
            "Revise retroanalisis.departamentos contra el panel canónico."
        )
    exigida = str(params["cobertura_desde"])
    minimos = int(params["municipios_minimos"])
    cobertura = str(table.year_month.min())
    municipios = int(table.municipality_code.nunique())
    sintetico = (
        " El modo canónico por defecto es sintético y no sirve para medir: "
        "corra con canonical.mode=approved."
    )
    if cobertura > exigida or cobertura > piso:
        raise ValueError(
            f"El panel empieza en {cobertura}; la receta exige {exigida} y "
            f"el entrenamiento arranca en {piso}." + sintetico
        )
    if municipios < minimos:
        raise ValueError(
            f"El panel trae {municipios} municipios y la receta exige al menos "
            f"{minimos}." + sintetico
        )


def retroanalisis(artifact, params: dict) -> tuple[pd.DataFrame, ...]:
    """Ejecutar la ventana expansiva por horizonte y compararla con las líneas base del canal.

    Varias recetas en una sola corrida comparten panel, folds y filas, así que
    sus filas del resumen son comparables entre sí: la columna `receta` dice de
    cuál viene cada una.

    Args:
        artifact: Artefacto canónico producido por canonical_build.
        params: configuraciones (lista de YAML de receta; también se acepta
            configuracion con una sola ruta), horizontes, primer_origen,
            ultimo_objetivo, primer_entrenamiento, cobertura_desde,
            municipios_minimos, salida (carpeta bajo data/, ignorada por Git) y,
            opcional, departamentos (códigos DANE; el panel canónico es nacional).

    Returns:
        Tupla (resumen, por_anio, curva, omitidos), cada una con las columnas
        horizonte y receta. En `salida` queda además conjunto.csv, con las
        filas preparadas, descartadas y comunes por receta y horizonte.

    Raises:
        ValueError: Si la salida cae fuera de data/, si el panel no sostiene la
            medición o si algún horizonte se queda sin folds evaluables.
    """
    destino = Path(params["salida"])
    if destino.parts[:1] != ("data",):
        raise ValueError("La salida del retroanálisis debe quedar bajo data/")
    table, schema = load_canonical(artifact)
    # Con `entrenamiento_nacional` el modelo entrena con todo el país y se evalúa
    # solo en los departamentos declarados: las predicciones y las líneas base se
    # restringen a ellos, así que las filas evaluadas son las mismas.
    nacional = table if params.get("entrenamiento_nacional") else None
    departamentos = params.get("departamentos")
    if departamentos:
        codigos = [str(c) for c in departamentos]
        table = table[table.department_code.isin(codigos)].reset_index(drop=True)
    piso = str(params.get("primer_entrenamiento", TRAIN_FLOOR))
    verificar_panel(table, params, piso)
    recetas = params.get("configuraciones") or params["configuracion"]
    recetas = [recetas] if isinstance(recetas, str) else list(recetas)
    salidas: dict[str, list[pd.DataFrame]] = {
        "resumen": [],
        "anio": [],
        "curva": [],
        "omit": [],
        "conjunto": [],
        "predicciones": [],
    }
    for ruta in recetas:
        receta = Path(ruta).stem
        config = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))
        for h in params["horizontes"]:
            preds, omitidos, cobertura = predicciones_rolling(
                table if nacional is None else nacional,
                schema,
                config,
                int(h),
                params["primer_origen"],
                params["ultimo_objetivo"],
                piso,
                params.get("ventana_anios"),
            )
            etiquetas = {"horizonte": h, "receta": receta}
            if nacional is not None:
                evaluados = set(table.municipality_code)
                preds = preds[preds.municipality_code.isin(evaluados)].reset_index(drop=True)
            salidas["omit"].append(pd.DataFrame(omitidos).assign(**etiquetas))
            salidas["conjunto"].append(pd.DataFrame([{**cobertura, **etiquetas}]))
            if preds.empty or preds.fold_id.nunique() < 2:
                # El diagnóstico se escribe igual; lo que no se escribe es un resumen vacío.
                destino.mkdir(parents=True, exist_ok=True)
                pd.concat(salidas["omit"], ignore_index=True).to_csv(
                    destino / "omitidos.csv", index=False
                )
                motivo = omitidos[0]["motivo"] if omitidos else "sin orígenes evaluables"
                raise ValueError(
                    f"Retroanálisis sin folds en T+{h} con la receta {receta} "
                    f"({len(omitidos)} orígenes omitidos); primer motivo: {motivo}. "
                    f"El diagnóstico quedó en {destino / 'omitidos.csv'}."
                )
            candidato = str(preds.candidate.iloc[0])
            salidas["predicciones"].append(preds.assign(receta=receta))
            resumen, anio, curva = validar_candidato(
                table, preds, {"candidato": candidato, "horizonte": int(h)}
            )
            salidas["resumen"].append(resumen.assign(**etiquetas, candidato=candidato))
            salidas["anio"].append(anio.assign(**etiquetas))
            salidas["curva"].append(curva.assign(**etiquetas))
    tablas = tuple(
        pd.concat(v, ignore_index=True) if v else pd.DataFrame() for v in salidas.values()
    )
    destino.mkdir(parents=True, exist_ok=True)
    nombres = ("resumen", "por_anio", "curva", "omitidos", "conjunto", "predicciones")
    for nombre, tabla in zip(nombres, tablas):
        tabla.to_csv(destino / f"{nombre}.csv", index=False)
    # El quinto CSV es auditoría del conjunto común y el sexto guarda el puntaje de
    # cada fila (para ensambles y lecturas posteriores); el nodo entrega los cuatro
    # que el pipeline declara.
    return tablas[:4]
