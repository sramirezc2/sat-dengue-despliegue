"""Estados artificiales de episodio, persistencia y ausencia; ninguna fila real."""

import pandas as pd


def make_states() -> pd.DataFrame:
    """Construir siete meses, con inicio en febrero/mayo y junio desconocido.

    Returns:
        Estados binarios/ausentes de un municipio ficticio, hasta junio de 2024.
    """
    return pd.DataFrame(
        {
            "municipality_code": ["50998"] * 7,
            "year_month": pd.period_range("2023-12", "2024-06", freq="M").astype(str),
            "excess": pd.array([0, 0, 1, 1, 0, 1, pd.NA], dtype="Int64"),
        }
    )
