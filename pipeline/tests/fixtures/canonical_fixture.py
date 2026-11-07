"""Muestra artificial de ingeniería; ningún registro procede de datos científicos."""

import json
from typing import Any

import numpy as np
import pandas as pd

CLIMATE_NAMES = [
    "rain_mm_month_sum",
    "surface_runoff_mm_month_sum",
    "total_evaporation_mm_month_sum_ecmwf",
    "solar_radiation_mj_m2_month_sum",
    "temp_mean_c_month_mean",
    "dewpoint_mean_c_month_mean",
    "soil_water_l1_month_mean",
    "wind_u_ms_month_mean",
    "wind_v_ms_month_mean",
]
COUNT_NAMES = [
    "dengue_notifications_count",
    "dengue_grave_notifications_count",
    "total_notifications_count",
]


def make_panel() -> pd.DataFrame:
    """Generar dos municipios ficticios, ceros, ausencias y un hueco de calendario.

    Returns:
        Panel pequeño 2018–2024, sin usar datos externos ni productores V3.
    """
    rows = []
    for code in ("50998", "73998"):
        for i, period in enumerate(pd.period_range("2018-01", "2024-12", freq="M")):
            if code == "50998" and str(period) == "2022-02":
                continue
            covered = str(period) != "2018-01"
            dengue = float((i * 3) % 17) if covered else np.nan
            grave = float(i % 3) if covered else np.nan
            total = dengue + grave
            row = {
                "municipality_code": code,
                "department_code": code[:2],
                "municipality_name": "Municipio ficticio " + code,
                "department_name": "Meta" if code[:2] == "50" else "Tolima",
                "year_month": str(period),
                COUNT_NAMES[0]: dengue,
                COUNT_NAMES[1]: grave,
                COUNT_NAMES[2]: total,
                "in_epi_coverage": covered,
                "epi_count_status": (
                    "outside_epi_coverage_missing"
                    if not covered
                    else "zero_in_coverage"
                    if total == 0
                    else "records_present"
                ),
                "expected_days_in_month": period.days_in_month,
                "climate_days_observed": period.days_in_month,
            }
            for name in CLIMATE_NAMES:
                incomplete = str(period) == "2023-04" and name == CLIMATE_NAMES[0]
                row[name] = np.nan if incomplete else -2.0 if "evaporation" in name else 3.0
                row[f"{name}_valid_days"] = 2 if incomplete else period.days_in_month
            rows.append(row)
    return pd.DataFrame(rows)


def frame_payload(frame: pd.DataFrame) -> dict[str, Any]:
    """Serializar valores, tipos, nulos y orden sin tolerancias numéricas.

    Args:
        frame: Tabla generada por cualquiera de las dos implementaciones.

    Returns:
        Representación JSON determinista con escalares nativos.
    """

    def scalar(value: Any) -> Any:
        """Convertir solo escalares NumPy y ausencias para JSON estándar."""
        if pd.isna(value):
            return None
        return value.item() if isinstance(value, np.generic) else value

    return {
        "columns": list(frame.columns),
        "dtypes": [str(dtype) for dtype in frame.dtypes],
        "rows": [[scalar(v) for v in row] for row in frame.itertuples(index=False, name=None)],
    }


def canonical_bytes(payload: Any) -> bytes:
    """Codificar JSON canónico sin NaN ni redondeos explícitos.

    Args:
        payload: Estructura de valores primitivos serializables.

    Returns:
        JSON UTF-8 con orden de claves y separadores estables.
    """
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()
