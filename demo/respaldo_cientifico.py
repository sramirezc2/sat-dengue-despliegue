"""Presentar agregados históricos T+2 de la receta, sin evaluar la carga del visitante."""

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
from configuracion import ROOT
from inferencia import ARTIFACT_SHA256
from sat_dengue_pipeline.risk.configuration import RECIPE_SHA

SUPPORT_PATH = ROOT / "demo/respaldo-cientifico.json"
SUPPORT_SHA256 = "6a7909a362d50d6f2da56b0f15a99d9a8d835741a4bdd151cde72aa455d63bf5"
SOURCE = "docs/evidence/reserva-2023-2024-t2/reserva.csv"
METHODS = ("Regresión logística con clima", "Canal condicionado")
INTRODUCTION = (
    "El ranking de arriba se calculó con el archivo que cargó. Para evaluar si anticipó "
    "correctamente los inicios de exceso sería necesario compararlo con los desenlaces "
    "observados dos meses después; esta demostración no consulta esos desenlaces. "
    "A continuación se muestra cómo funcionó históricamente el procedimiento de regresión "
    "logística con clima durante 2023–2024. Estas cifras respaldan la receta del modelo, "
    "pero no califican el archivo que acaba de cargar. Las posiciones representan prioridad "
    "relativa, no probabilidades de brote."
)


def _fields(value: Any, expected: set[str]) -> None:
    """Exigir un objeto cerrado; no admitir metadatos o valores desconocidos."""
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError("El esquema del respaldo científico no es válido.")


def load_support(path: Path | None = None) -> dict:
    """Validar bytes, esquema, conteos y procedencia del respaldo versionado.

    Args:
        path: Copia del JSON para pruebas; conserva el pin de contenido autorizado.

    Returns:
        Agregados históricos verificados, sin predicciones por fila.
    """
    try:
        raw = (path if path is not None else SUPPORT_PATH).read_bytes()
    except OSError:
        raise ValueError("El respaldo científico no está disponible.") from None
    if hashlib.sha256(raw).hexdigest() != SUPPORT_SHA256:
        raise ValueError("El respaldo científico difiere de la versión verificada.")
    support = json.loads(raw)
    _fields(support, {
        "schema", "recipe", "period", "horizon", "nominal_budget", "origin_months",
        "counts", "intervals", "source", "model",
    })
    _fields(support["period"], {"start", "end", "label"})
    _fields(support["source"], {"path", "sha256"})
    _fields(support["model"], {"artifact_sha256", "recipe_path", "recipe_sha256"})
    if (
        support["schema"] != "satd-demo-scientific-support-v1"
        or support["recipe"] != "log_conclima"
        or support["horizon"] != 2
        or support["nominal_budget"] != .1
        or support["origin_months"] != 23
        or support["period"] != {
            "start": "2023-01", "end": "2024-12",
            "label": "confirmación retrospectiva 2023–2024",
        }
        or support["source"]["path"] != SOURCE
        or support["model"] != {
            "artifact_sha256": ARTIFACT_SHA256,
            "recipe_path": "pipeline/conf/retroanalisis/noche/log_conclima.yml",
            "recipe_sha256": RECIPE_SHA,
        }
    ):
        raise ValueError("La identidad del respaldo científico no corresponde a la receta.")
    try:
        source_hash = hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest()
    except OSError:
        raise ValueError("La evidencia fuente del respaldo no está disponible.") from None
    if source_hash != support["source"]["sha256"]:
        raise ValueError("La evidencia fuente difiere del respaldo científico.")
    counts = support["counts"]
    _fields(counts, {
        "alerts_per_method", "evaluable_onsets", "evaluable_municipality_months",
        "model_anticipated", "channel_anticipated",
    })
    if any(type(value) is not int or value <= 0 for value in counts.values()) or not (
        max(counts["model_anticipated"], counts["channel_anticipated"])
        <= min(counts["alerts_per_method"], counts["evaluable_onsets"])
        <= max(counts["alerts_per_method"], counts["evaluable_onsets"])
        <= counts["evaluable_municipality_months"]
    ):
        raise ValueError("Los conteos del respaldo científico no se reconcilian.")
    intervals = support["intervals"]
    _fields(intervals, {
        "confidence", "resampling_unit", "replicates", "sensitivity_difference_pp",
        "false_alerts_difference_per100",
    })
    if (
        intervals["confidence"] != .95 or intervals["resampling_unit"] != "origin_month"
        or intervals["replicates"] != 2000
    ):
        raise ValueError("El método de intervalo no coincide con la evidencia.")
    difference = counts["model_anticipated"] - counts["channel_anticipated"]
    estimates = {
        "sensitivity_difference_pp": round(100 * difference / counts["evaluable_onsets"], 1),
        "false_alerts_difference_per100": round(
            -100 * difference / counts["evaluable_municipality_months"], 2
        ),
    }
    for key, expected in estimates.items():
        interval = intervals[key]
        _fields(interval, {"estimate", "low", "high"})
        if (
            any(type(v) not in {int, float} or not math.isfinite(v) for v in interval.values())
            or not interval["low"] <= interval["estimate"] <= interval["high"]
            or interval["estimate"] != expected
        ):
            raise ValueError("Los intervalos publicados no se reconcilian con los conteos.")
    return support


def descriptive_metrics(support: dict) -> dict[str, float]:
    """Derivar las cuatro métricas exclusivamente de sus numeradores y denominadores."""
    counts = support["counts"]
    hits = counts["model_anticipated"]
    alerts = counts["alerts_per_method"]
    onsets = counts["evaluable_onsets"]
    return {
        "sensitivity": hits / onsets,
        "precision": hits / alerts,
        "f1": 2 * hits / (alerts + onsets),
        "false_per_hit": (alerts - hits) / hits,
    }


def spanish(value: float, decimals: int = 1, *, signed: bool = False) -> str:
    """Formatear etiquetas visibles sin duplicar tasas redondeadas en el JSON."""
    return format(value, f"{'+' if signed else ''}.{decimals}f").replace(".", ",").replace("-", "−")


def chart_data(support: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Preparar dos comparaciones agregadas; no calcular intervalos individuales."""
    counts = support["counts"]
    sensitivity, burden = [], []
    for name, field in zip(METHODS, ("model_anticipated", "channel_anticipated"), strict=True):
        hits = counts[field]
        false = counts["alerts_per_method"] - hits
        rate = 100 * hits / counts["evaluable_onsets"]
        load = 100 * false / counts["evaluable_municipality_months"]
        sensitivity.append({
            "Método": name, "Valor": rate,
            "Etiqueta": f"{spanish(rate)} % · {hits}/{counts['evaluable_onsets']}",
        })
        burden.append({
            "Método": name, "Valor": load,
            "Etiqueta": f"{spanish(load)} · {false}/{counts['evaluable_municipality_months']}",
        })
    return pd.DataFrame(sensitivity), pd.DataFrame(burden)


def comparison_chart(
    data: pd.DataFrame, title: str, maximum: int, *, dark: bool = False,
) -> alt.LayerChart:
    """Dibujar barras desde cero, nombres de método y etiquetas numéricas explícitas."""
    base = alt.Chart(data).encode(
        x=alt.X("Valor:Q", title=title, scale=alt.Scale(domain=[0, maximum])),
        y=alt.Y("Método:N", sort=list(METHODS), title=None, axis=alt.Axis(labelLimit=300)),
    )
    bars = base.mark_bar(size=30).encode(color=alt.Color(
        "Método:N", scale=alt.Scale(domain=list(METHODS), range=["#155d4b", "#55719e"]),
        legend=None,
    ))
    labels = base.mark_text(
        align="left", dx=5, fontSize=13, color="#fafafa" if dark else "#31333f",
    ).encode(text="Etiqueta:N")
    return (bars + labels).properties(height=135).configure_view(stroke=None)
