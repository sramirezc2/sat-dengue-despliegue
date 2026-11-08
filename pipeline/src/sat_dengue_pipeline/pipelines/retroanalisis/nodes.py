"""Nodo del retroanálisis: predicciones por origen y validación contra el canal."""

from pathlib import Path

import pandas as pd
import yaml

from sat_dengue_pipeline.evaluation.retroanalisis import predicciones_rolling
from sat_dengue_pipeline.evaluation.validacion_anual import validar_candidato
from sat_dengue_pipeline.raw.serialization import load_canonical


def retroanalisis(artifact, params: dict) -> tuple[pd.DataFrame, ...]:
    """Ejecutar la ventana expansiva por horizonte y compararla con las líneas base del canal.

    Args:
        artifact: Artefacto canónico producido por canonical_build.
        params: configuracion (ruta a un YAML de experimento), horizontes, primer_origen,
            ultimo_objetivo y salida (carpeta bajo data/, ignorada por Git).

    Returns:
        Tupla (resumen, por_anio, curva, omitidos), cada una con columna horizonte.
    """
    table, schema = load_canonical(artifact)
    config = yaml.safe_load(Path(params["configuracion"]).read_text(encoding="utf-8"))
    salidas: dict[str, list[pd.DataFrame]] = {"resumen": [], "anio": [], "curva": [], "omit": []}
    for h in params["horizontes"]:
        preds, omitidos = predicciones_rolling(
            table, schema, config, int(h), params["primer_origen"], params["ultimo_objetivo"]
        )
        salidas["omit"].append(pd.DataFrame(omitidos).assign(horizonte=h))
        if preds.empty or preds.fold_id.nunique() < 2:
            continue
        candidato = str(preds.candidate.iloc[0])
        resumen, anio, curva = validar_candidato(
            table, preds, {"candidato": candidato, "horizonte": int(h)}
        )
        salidas["resumen"].append(resumen.assign(horizonte=h, candidato=candidato))
        salidas["anio"].append(anio.assign(horizonte=h))
        salidas["curva"].append(curva.assign(horizonte=h))
    tablas = tuple(
        pd.concat(v, ignore_index=True) if v else pd.DataFrame() for v in salidas.values()
    )
    destino = Path(params["salida"])
    if destino.parts[:1] != ("data",):
        raise ValueError("La salida del retroanálisis debe quedar bajo data/")
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in zip(("resumen", "por_anio", "curva", "omitidos"), tablas):
        tabla.to_csv(destino / f"{nombre}.csv", index=False)
    return tablas
