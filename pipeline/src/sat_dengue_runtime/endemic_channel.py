"""Canal contemporáneo H5; reglas adoptadas de V2 consolidation.py, 916a69f."""

from math import isfinite

import pandas as pd

from .calendar import history_periods_for_target

CHANNEL = ["p25_canal_t", "p50_canal_t", "p75_canal_t", "zona_canal_t"]


def percentile_type7(values: list[float], q: float) -> float:
    """Calcular el percentil Hyndman–Fan tipo 7 mediante interpolación lineal.

    Args:
        values: Observaciones finitas de la ventana histórica.
        q: Cuantil entre cero y uno, inclusive.

    Returns:
        Percentil interpolado sin redondeo.
    """
    if not values or not isfinite(q) or not 0 <= q <= 1:
        raise ValueError("Percentil o ventana inválidos")
    ordered = sorted(float(value) for value in values)
    if not all(isfinite(value) for value in ordered):
        raise ValueError("Historia no finita")
    rank = (len(ordered) - 1) * q
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (rank - lower) * (ordered[upper] - ordered[lower])


def classify_endemic_zone(current_count: float, p25: float, p50: float, p75: float) -> str:
    """Clasificar el conteo actual conservando las desigualdades de V2.

    Args:
        current_count: Conteo observado del mes T.
        p25: Percentil 25 histórico.
        p50: Percentil 50 histórico.
        p75: Percentil 75 histórico.

    Returns:
        EXITO, SEGURIDAD, ALERTA o EXCESO.
    """
    if current_count < p25:
        return "EXITO"
    if current_count <= p50:
        return "SEGURIDAD"
    if current_count <= p75:
        return "ALERTA"
    return "EXCESO"


def compute_current_endemic_channel(panel: pd.DataFrame) -> pd.DataFrame:
    """Agregar el canal contemporáneo solo con cinco años históricos completos.

    Args:
        panel: Panel con claves y conteos ya validados por el productor canónico.

    Returns:
        Copia ordenada con umbrales nulos si falta el conteo actual o la historia.
    """
    table = panel.sort_values(["municipality_code", "year_month"]).reset_index(drop=True).copy()
    lookup = table.set_index(["municipality_code", "year_month"])[
        "dengue_notifications_count"
    ].to_dict()
    values: list[tuple[float | None, float | None, float | None, str | None]] = []
    for municipality, period in table[["municipality_code", "year_month"]].itertuples(
        index=False, name=None
    ):
        history = [lookup.get((municipality, p), pd.NA) for p in history_periods_for_target(period)]
        current = lookup[(municipality, period)]
        if pd.isna(current) or any(pd.isna(value) for value in history):
            values.append((None, None, None, None))
        else:
            quantiles = [percentile_type7(history, q) for q in (0.25, 0.5, 0.75)]
            values.append((*quantiles, classify_endemic_zone(current, *quantiles)))
    for i, column in enumerate(CHANNEL):
        dtype = "string" if column == "zona_canal_t" else "float64"
        table[column] = pd.array([row[i] for row in values], dtype=dtype)
    return table
