"""Calendario mensual exacto; procedencia: V2 consolidation.py, commit 916a69f."""

import re

import pandas as pd


def validate_period(period: str) -> None:
    """Exigir un periodo mensual canónico sin coerciones.

    Args:
        period: Clave mensual AAAA-MM.

    Raises:
        ValueError: Si el periodo es inválido.
    """
    if not isinstance(period, str) or not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", period):
        raise ValueError("Periodo mensual inválido")
    if int(period[:4]) == 0:
        raise ValueError("Periodo mensual inválido")


def add_months(year_month: str, offset: int) -> str:
    """Sumar meses de calendario, sin depender de posiciones de filas.

    Args:
        year_month: Periodo AAAA-MM.
        offset: Desplazamiento entero en meses.

    Returns:
        Periodo desplazado.
    """
    validate_period(year_month)
    if type(offset) is not int:
        raise ValueError("El desplazamiento debe ser entero")
    return str(pd.Period(year_month, freq="M") + offset)


def history_periods_for_target(target_period: str, history_years: int = 5) -> list[str]:
    """Enumerar el mismo mes en los años inmediatamente anteriores al objetivo.

    Args:
        target_period: Mes de referencia o mes objetivo.
        history_years: Cantidad exacta de años, sin sustituir huecos por años antiguos.

    Returns:
        Periodos históricos ordenados cronológicamente.
    """
    validate_period(target_period)
    if type(history_years) is not int or history_years <= 0:
        raise ValueError("Ventana histórica inválida")
    year = int(target_period[:4])
    return [f"{y:04d}-{target_period[-2:]}" for y in range(year - history_years, year)]
