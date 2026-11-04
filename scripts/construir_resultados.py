"""Construye los resultados publicados del tablero desde las corridas del repositorio cientifico.

Entradas, todas producidas por los pipelines de Kedro de SAT-Dengue-V2:

  panel.csv        etapa de datos: casos observados y canal endemico por municipio y mes
  predictions.csv  etapa de evaluacion: probabilidad calibrada y decision por municipio,
                   mes de referencia, horizonte y candidato
  comparison.csv   etapa de evaluacion: desempeno agregado del bloque evaluado

Salida: un archivo por departamento y periodo en el directorio de resultados, con el
nombre `resultado_<departamento>_<AAAA-MM>.json` que espera el servicio.

El umbral de decision no viene explicito en las corridas. Se recupera del propio
archivo de predicciones como la probabilidad mas baja que si emitio alerta, lo que
reproduce exactamente la frontera que aplico el pipeline. El script falla si las
dos clases no quedan separadas, porque entonces el umbral seria una invencion.

Uso:

    python scripts/construir_resultados.py \\
        --panel RUTA/panel.csv \\
        --predicciones RUTA/predictions.csv \\
        --comparacion RUTA/comparison.csv \\
        --candidato xgboost \\
        --salida datos/resultados
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEPARTAMENTOS = {"73": "Tolima", "50": "Meta"}

ESPACIO_IDS = uuid.UUID("6f1b0f2e-9a7a-4a1a-9a9f-3f5a1b2c3d4e")

ZONAS_VALIDAS = {"EXITO", "SEGURIDAD", "ALERTA", "EXCESO"}

MOTIVO_POR_ESTADO = {
    "insufficient_history": ("INSUFFICIENT_HISTORY", "Historia insuficiente para el canal."),
    "target_outside_panel": ("NOT_CALCULATED", "El mes objetivo esta fuera del panel."),
}

MOTIVO_SIN_PREDICCION = ("NOT_CALCULATED", "El procedimiento no produjo resultado para este mes.")

MINUSCULAS = {"de", "del", "la", "las", "los", "y", "el", "san", "santa"}
MOTIVO_SIN_FILA = ("MISSING_DATA", "No hay datos del municipio para este mes.")


@dataclass(frozen=True, slots=True)
class Umbral:
    valor: float
    margen: float


def _numero(texto: str | None) -> float | None:
    if texto is None or texto == "":
        return None
    return float(texto)


def _entero(texto: str | None) -> int | None:
    valor = _numero(texto)
    return None if valor is None else int(round(valor))


def _mes_siguiente(periodo: str, saltos: int) -> str:
    anio, mes = (int(p) for p in periodo.split("-"))
    total = (anio * 12 + mes - 1) + saltos
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _nombre_propio(texto: str) -> str:
    """El panel trae los nombres en mayusculas; el tablero los muestra legibles."""
    palabras = texto.strip().lower().split()
    return " ".join(
        palabra if indice and palabra in MINUSCULAS and palabra not in {"san", "santa"}
        else palabra.capitalize()
        for indice, palabra in enumerate(palabras)
    )


def _id(*partes: str) -> str:
    return str(uuid.uuid5(ESPACIO_IDS, "|".join(partes)))


def leer_panel(ruta: Path) -> dict[tuple[str, str], dict[str, str]]:
    with ruta.open(encoding="utf-8") as fh:
        return {(f["municipality_code"], f["year_month"]): f for f in csv.DictReader(fh)}


def leer_predicciones(
    ruta: Path, candidato: str
) -> tuple[dict[tuple[str, str, str], dict[str, str]], dict[str, Umbral]]:
    """Indexar las predicciones del candidato y recuperar su umbral por horizonte."""
    indice: dict[tuple[str, str, str], dict[str, str]] = {}
    clases: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"0": [], "1": []})

    with ruta.open(encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            if fila["candidate"] != candidato:
                continue
            probabilidad = _numero(fila["prediction_probability"])
            if probabilidad is None:
                continue
            indice[(fila["municipality_code"], fila["year_month"], fila["horizon"])] = fila
            clases[fila["horizon"]][fila["prediction_label"]].append(probabilidad)

    if not indice:
        sys.exit(f"ERROR: el archivo de predicciones no contiene el candidato {candidato!r}")

    umbrales: dict[str, Umbral] = {}
    for horizonte, grupos in clases.items():
        if not grupos["1"]:
            sys.exit(f"ERROR: el candidato {candidato!r} no emitio ninguna alerta en T+{horizonte}")
        maximo_sin_alerta = max(grupos["0"], default=0.0)
        minimo_con_alerta = min(grupos["1"])
        if maximo_sin_alerta >= minimo_con_alerta:
            sys.exit(
                f"ERROR: en T+{horizonte} las decisiones no separan las probabilidades "
                f"({maximo_sin_alerta} >= {minimo_con_alerta}); el umbral no es recuperable"
            )
        umbrales[horizonte] = Umbral(minimo_con_alerta, minimo_con_alerta - maximo_sin_alerta)
    return indice, umbrales


def leer_comparacion(ruta: Path, candidato: str) -> dict[str, dict[str, str]]:
    with ruta.open(encoding="utf-8") as fh:
        return {f["horizon"]: f for f in csv.DictReader(fh) if f["candidate"] == candidato}


# Nombres para humanos. "persistence" es la linea base declarada en la politica
# de decision: alertar donde el exceso ya esta ocurriendo. Se llama regla simple
# porque eso es lo que es, y porque "persistencia" no le dice nada a nadie fuera
# del equipo.
ETIQUETAS_CANDIDATO = {
    "persistence": "Regla simple",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "gam": "GAM",
}


def leer_todos_los_candidatos(ruta: Path, publicado: str) -> list[dict[str, object]]:
    """Desempeno de cada candidato evaluado, para poder compararlos en pantalla.

    El tablero declaraba que el modelo no esta aprobado y no mostraba contra que
    se lo habia medido. Sin la linea base, "25 % de los inicios" no se puede
    juzgar: hay que saber que la regla simple detecta cero a un mes y treinta a
    dos meses. Todo sale de la misma corrida registrada.
    """
    with ruta.open(encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    salida: list[dict[str, object]] = []
    for f in filas:
        cand = f["candidate"]
        salida.append(
            {
                "horizon": f"T{f['horizon']}",
                "candidate": cand,
                "label": ETIQUETAS_CANDIDATO.get(cand, cand),
                "role": (
                    "BASELINE"
                    if cand == "persistence"
                    else "PUBLISHED" if cand == publicado else "OTHER"
                ),
                "onsets_detected": _entero(f.get("detected_onsets")),
                "actual_onsets": _entero(f.get("real_onsets")),
                "alerts_emitted": _entero(f.get("emitted_alerts")),
                "false_alerts": _entero(f.get("false_alerts")),
                "false_alert_ratio": _numero(f.get("false_alarm_ratio")),
                "onset_sensitivity": _numero(f.get("onset_sensitivity")),
                "auroc": _numero(f.get("auroc")),
                "average_precision": _numero(f.get("average_precision")),
                "brier": _numero(f.get("brier")),
            }
        )
    salida.sort(key=lambda r: (r["horizon"], -(r["onsets_detected"] or 0)))
    return salida


def serie_del_canal(
    panel: dict[tuple[str, str], dict[str, str]], municipio: str, referencia: str
) -> list[dict[str, object]]:
    """Los doce meses del ano de referencia, para la grafica del canal.

    Los casos de los meses posteriores al de referencia se omiten: en el mes T
    nadie los conoce todavia y publicarlos seria fuga. Los percentiles si se
    conservan porque se calculan con la historia previa.
    """
    anio = referencia.split("-")[0]
    serie = []
    for mes in range(1, 13):
        periodo = f"{anio}-{mes:02d}"
        fila = panel.get((municipio, periodo))
        observados = _entero(fila["total_notifications_count"]) if fila else None
        serie.append(
            {
                "period": periodo,
                "cases": observados if periodo <= referencia else None,
                "p25": _numero(fila["p25_canal_t"]) if fila else None,
                "median": _numero(fila["p50_canal_t"]) if fila else None,
                "p75": _numero(fila["p75_canal_t"]) if fila else None,
            }
        )
    return serie


def construir_resultado(
    *,
    horizonte: str,
    municipio: str,
    periodo: str,
    fila_panel: dict[str, str] | None,
    prediccion: dict[str, str] | None,
    umbral: Umbral,
    candidato: str,
    procedimiento: str,
    version_modelo: str,
) -> dict[str, object]:
    objetivo = _mes_siguiente(periodo, int(horizonte))
    base: dict[str, object] = {"horizon": f"T{horizonte}", "target_period": objetivo}

    if prediccion is not None:
        probabilidad = float(prediccion["prediction_probability"])
        return {
            **base,
            "result_id": _id(procedimiento, municipio, periodo, horizonte),
            "probability": round(probabilidad, 6),
            "threshold": round(umbral.valor, 6),
            "alert_status": "ALERT" if probabilidad >= umbral.valor else "NO_ALERT",
            "availability_status": "AVAILABLE",
            "availability_reason": None,
            "model_family": candidato,
            "model_role": "PROVISIONAL_CANDIDATE",
            "model_version": version_modelo,
            "procedure_id": procedimiento,
        }

    if fila_panel is None:
        estado, motivo = MOTIVO_SIN_FILA
    else:
        estado, motivo = MOTIVO_POR_ESTADO.get(
            fila_panel.get(f"y_status_t{horizonte}", ""), MOTIVO_SIN_PREDICCION
        )
    return {
        **base,
        "result_id": None,
        "probability": None,
        "threshold": None,
        "alert_status": "UNAVAILABLE",
        "availability_status": estado,
        "availability_reason": motivo,
        "model_family": None,
        "model_role": None,
        "model_version": None,
        "procedure_id": None,
    }


def construir_documento(
    *,
    departamento: str,
    periodo: str,
    panel: dict[tuple[str, str], dict[str, str]],
    predicciones: dict[tuple[str, str, str], dict[str, str]],
    umbrales: dict[str, Umbral],
    comparacion: dict[str, dict[str, str]],
    candidatos: list[dict[str, object]],
    candidato: str,
    procedimiento: str,
    version_modelo: str,
    version_datos: str,
    generado: str,
) -> dict[str, object]:
    municipios_del_depto = sorted(
        {codigo for codigo, _ in panel if codigo.startswith(departamento)}
    )
    municipios = []
    for codigo in municipios_del_depto:
        fila = panel.get((codigo, periodo))
        nombre = _nombre_propio(fila["municipality_name"]) if fila else codigo
        zona = (fila or {}).get("zona_canal_t", "")
        municipios.append(
            {
                "municipality_code": codigo,
                "municipality_name": nombre,
                "cases_t": _entero(fila["total_notifications_count"]) if fila else None,
                "endemic_zone_t": zona if zona in ZONAS_VALIDAS else "UNAVAILABLE",
                "p25": _numero(fila["p25_canal_t"]) if fila else None,
                "median": _numero(fila["p50_canal_t"]) if fila else None,
                "p75": _numero(fila["p75_canal_t"]) if fila else None,
                "endemic_channel_series": serie_del_canal(panel, codigo, periodo),
                "results": [
                    construir_resultado(
                        horizonte=h,
                        municipio=codigo,
                        periodo=periodo,
                        fila_panel=fila,
                        prediccion=predicciones.get((codigo, periodo, h)),
                        umbral=umbrales[h],
                        candidato=candidato,
                        procedimiento=procedimiento,
                        version_modelo=version_modelo,
                    )
                    for h in ("1", "2")
                ],
            }
        )

    registros = []
    for horizonte, fila in sorted(comparacion.items()):
        registros.append(
            {
                "horizon": f"T{horizonte}",
                "procedure_id": procedimiento,
                "evaluation_period_start": "2025-01",
                "evaluation_period_end": "2025-12",
                "evaluation_geography": "Tolima y Meta, 76 municipios",
                "auroc": _numero(fila.get("auroc")),
                "average_precision": _numero(fila.get("average_precision")),
                "brier": _numero(fila.get("brier")),
                "false_alerts": _entero(fila.get("false_alerts")),
                "alerts_emitted": _entero(fila.get("emitted_alerts")),
                "false_alert_ratio": _numero(fila.get("false_alarm_ratio")),
                "onsets_detected": _entero(fila.get("detected_onsets")),
                "actual_onsets": _entero(fila.get("real_onsets")),
                "onset_sensitivity": _numero(fila.get("onset_sensitivity")),
            }
        )

    return {
        "metadata": {
            "result_set_id": _id(procedimiento, departamento, periodo),
            "reference_period": periodo,
            "generated_at": generado,
            "data_updated_at": generado,
            "data_version": version_datos,
        },
        "governance": {
            "governance_gate": "G5",
            "governance_status": "NOT_APPROVED",
            "champion_status": "NOT_SELECTED",
            "limitation": (
                "Resultados reales de un candidato provisional sobre el bloque de "
                "evaluacion congelado de 2025. El champion no esta seleccionado y "
                "estas alertas no estan autorizadas para decisiones operativas."
            ),
        },
        "department": {
            "department_code": departamento,
            "department_name": DEPARTAMENTOS[departamento],
            "requested_period": periodo,
        },
        "municipalities": municipios,
        "evaluation_context": {
            "demonstrative_values": False,
            "evaluation_records": registros,
            "comparison": candidatos,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--predicciones", type=Path, required=True)
    parser.add_argument("--comparacion", type=Path, required=True)
    parser.add_argument("--candidato", default="xgboost")
    parser.add_argument("--procedimiento", required=True, help="Identificador de la corrida")
    parser.add_argument("--version-modelo", default=None)
    parser.add_argument("--version-datos", required=True)
    parser.add_argument("--salida", type=Path, default=Path("datos/resultados"))
    args = parser.parse_args()

    panel = leer_panel(args.panel)
    predicciones, umbrales = leer_predicciones(args.predicciones, args.candidato)
    comparacion = leer_comparacion(args.comparacion, args.candidato)
    candidatos = leer_todos_los_candidatos(args.comparacion, args.candidato)
    generado = datetime.now(timezone.utc).isoformat(timespec="seconds")
    version_modelo = args.version_modelo or f"{args.candidato}-{args.procedimiento[:12]}"

    horizontes_por_periodo: dict[str, set[str]] = defaultdict(set)
    for _, periodo, horizonte in predicciones:
        horizontes_por_periodo[periodo].add(horizonte)
    periodos = sorted(p for p, hs in horizontes_por_periodo.items() if hs == {"1", "2"})
    descartados = sorted(set(horizontes_por_periodo) - set(periodos))
    if descartados:
        print(f"  meses omitidos por tener un solo horizonte: {', '.join(descartados)}")
    args.salida.mkdir(parents=True, exist_ok=True)

    print(f"Candidato {args.candidato}")
    for horizonte, umbral in sorted(umbrales.items()):
        print(f"  umbral T+{horizonte}: {umbral.valor:.6f} (margen {umbral.margen:.2e})")

    escritos = 0
    for departamento in DEPARTAMENTOS:
        for periodo in periodos:
            documento = construir_documento(
                departamento=departamento,
                periodo=periodo,
                panel=panel,
                predicciones=predicciones,
                umbrales=umbrales,
                comparacion=comparacion,
                candidatos=candidatos,
                candidato=args.candidato,
                procedimiento=args.procedimiento,
                version_modelo=version_modelo,
                version_datos=args.version_datos,
                generado=generado,
            )
            destino = args.salida / f"resultado_{departamento}_{periodo}.json"
            destino.write_text(
                json.dumps(documento, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            escritos += 1
    print(f"{escritos} archivo(s) escritos en {args.salida}")


if __name__ == "__main__":
    main()
