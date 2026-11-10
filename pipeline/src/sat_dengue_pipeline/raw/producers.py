"""Productores puros: dimensión, eventos de residencia y clima diario/mensual."""

import calendar
import math
import re
from collections import Counter

import pandas as pd

from sat_dengue_pipeline.domain.canonical import CLIMATE, COUNTS, KEYS

from .contract import BuildConfig
from .temporal import parse_date

CLIMATE_INPUT = [
    "rain_mm_day",
    "surface_runoff_mm_day",
    "total_evaporation_mm_day_ecmwf",
    "solar_radiation_mj_m2_day",
    "temp_mean_c",
    "dewpoint_mean_c",
    "soil_water_l1_mean",
    "wind_u_mean_ms",
    "wind_v_mean_ms",
]
REJECTIONS = {"invalid_residence", "unknown_municipality", "outside_period", "wrong_event"}


def _code(value: str, width: int) -> str | None:
    """Normalizar únicamente códigos enteros ASCII de ancho acotado."""
    value = value.strip()
    return value.zfill(width) if re.fullmatch(rf"[0-9]{{1,{width}}}", value) else None


def geography_normalization(
    catalog: dict, provenance: dict, catalog_sha: str, config: BuildConfig
) -> pd.DataFrame:
    """Interpretar el JSON aprobado y verificar la vinculación de procedencia."""
    try:
        if provenance["files"]["Divipola-municipios.md"]["sha256"] != catalog_sha:
            raise ValueError("Procedencia DIVIPOLA no coincide")
        if not isinstance(provenance["authority"], str) or not provenance["authority"]:
            raise ValueError("Autoridad DIVIPOLA ausente")
        rows = catalog["resultado"]
        if int(catalog["conteo"]) != config.municipalities or len(rows) != config.municipalities:
            raise ValueError("Cardinalidad DIVIPOLA incorrecta")
        records = []
        for row in rows:
            code = _code(str(row["CODIGO_DPTO_MPIO"]), 5)
            department = _code(str(row["CODIGO_DEPARTAMENTO"]), 2)
            municipal = _code(str(row["CODIGO_MUNICIPIO"]), 3)
            name = row["NOMBRE_MUNICIPIO"]
            if (
                code is None
                or department is None
                or municipal is None
                or (code != department + municipal or not isinstance(name, str) or not name.strip())
            ):
                raise ValueError("Clave DIVIPOLA incoherente")
            records.append([code, department, name])
        table = pd.DataFrame(records, columns=[*KEYS[:1], "department_code", "municipality_name"])
        if table.municipality_code.duplicated().any():
            raise ValueError("Municipio DIVIPOLA duplicado")
        return table.astype("string").sort_values(KEYS[:1]).reset_index(drop=True)
    except (KeyError, TypeError, AttributeError):
        raise ValueError("Esquema JSON/procedencia DIVIPOLA inválido") from None


def epidemiology_normalization(
    frames: dict[str, pd.DataFrame], geography: pd.DataFrame, config: BuildConfig
) -> tuple[pd.DataFrame, dict]:
    """Contar cada registro aceptado, sin deduplicación ni fecha de notificación.

    Args:
        frames: Solo filas retenidas por cuarentena.
        geography: Dimensión única.
        config: Cobertura mensual explícita.

    Returns:
        Conteos mensuales separados y conciliación agregada por fuente/causa.
    """
    known = set(geography.municipality_code)
    counts: dict[tuple[str, str], list[int]] = {}
    audit = {}
    for index, (name, event) in enumerate(
        (("dengue_notifications", "210"), ("severe_dengue_notifications", "220"))
    ):
        frame = frames[name]
        rejected: Counter = Counter({reason: 0 for reason in sorted(REJECTIONS)})
        accepted = 0
        for values in frame.itertuples(index=False, name=None):
            row = dict(zip(frame.columns, values, strict=True))
            department, municipality = _code(row["COD_DPTO_R"], 2), _code(row["COD_MUN_R"], 3)
            onset = parse_date(row["INI_SIN"])
            if onset is None:
                raise ValueError("La cuarentena debe rechazar INI_SIN ausente o inválida")
            period = onset.isoformat()[:7]
            code = department + municipality if department and municipality else None
            if row["COD_EVE"].strip() != event:
                reason = "wrong_event"
            elif code is None:
                reason = "invalid_residence"
            elif code not in known:
                reason = "unknown_municipality"
            elif not config.epi_start <= period <= config.end:
                reason = "outside_period"
            else:
                reason = None
            if reason:
                rejected[reason] += 1
            else:
                counts.setdefault((code, period), [0, 0])[index] += 1
                accepted += 1
        audit[name] = {"input": len(frame), "accepted": accepted, "rejected": dict(rejected)}
        assert accepted + sum(rejected.values()) == len(frame)
    records = [[*key, *value, sum(value)] for key, value in sorted(counts.items())]
    monthly = pd.DataFrame(records, columns=[*KEYS, *COUNTS])
    for key in KEYS:
        monthly[key] = monthly[key].astype("string")
    for name in COUNTS:
        monthly[name] = monthly[name].astype("Int64")
    return monthly, audit


def climate_daily_normalization(
    frame: pd.DataFrame, geography: pd.DataFrame, config: BuildConfig
) -> tuple[pd.DataFrame, dict]:
    """Validar fechas redundantes, claves y valores después de cuarentena."""
    records, outside = [], 0
    known = set(geography.municipality_code)
    for values in frame.itertuples(index=False, name=None):
        row = dict(zip(frame.columns, values, strict=True))
        day = parse_date(row["date"])
        if day is None:
            raise ValueError("Fecha climática fuera del contrato de cuarentena")
        period = day.isoformat()[:7]
        code = _code(row["mpio_cdpmp"], 5)
        if (
            code not in known
            or _code(row["dpto_ccdgo"], 2) != code[:2]
            or _code(row["mpio_ccdgo"], 3) != code[2:]
        ):
            raise ValueError("Municipio climático desconocido o incoherente")
        if (row["year"], row["month"], row["day_of_year"]) != (
            str(day.year),
            str(day.month),
            str(day.timetuple().tm_yday),
        ):
            raise ValueError("Calendario diario climático incoherente")
        if not config.start <= period <= config.end:
            outside += 1
            continue
        values = []
        for name in CLIMATE_INPUT:
            value = row[name].strip()
            number = float(value) if value else None
            if number is not None and not math.isfinite(number):
                raise ValueError("Clima no finito")
            values.append(number)
        records.append([code, period, day.isoformat(), *values])
    daily = pd.DataFrame(records, columns=[*KEYS, "date", *CLIMATE_INPUT])
    if daily.duplicated(["municipality_code", "date"]).any():
        raise ValueError("Día municipal duplicado; no se puede inflar cobertura")
    for name in (*KEYS, "date"):
        daily[name] = daily[name].astype("string")
    for name in CLIMATE_INPUT:
        daily[name] = daily[name].astype("Float64")
    return daily.sort_values([*KEYS, "date"]).reset_index(drop=True), {
        "input": len(frame),
        "accepted": len(daily),
        "outside_period": outside,
    }


def climate_monthly_aggregation(daily: pd.DataFrame) -> pd.DataFrame:
    """Agregar en orden de fecha, con nulos si falta un solo día por variable."""
    records = []
    for (code, period), group in daily.groupby(KEYS, sort=True):
        expected = calendar.monthrange(int(period[:4]), int(period[-2:]))[1]
        group = group.sort_values("date")
        values, days = [], []
        for i, name in enumerate(CLIMATE_INPUT):
            observed = group[name].dropna().tolist()
            days.append(len(observed))
            total = math.fsum(observed) if len(observed) == expected else None
            values.append(total / expected if i >= 4 and total is not None else total)
        records.append([code, period, expected, len(group), *values, *days])
    table = pd.DataFrame(
        records,
        columns=[
            *KEYS,
            "expected_days_in_month",
            "climate_days_observed",
            *CLIMATE,
            *(f"{name}_valid_days" for name in CLIMATE),
        ],
    )
    for key in KEYS:
        table[key] = table[key].astype("string")
    for name in table.columns[2:]:
        table[name] = table[name].astype("Float64" if name in CLIMATE else "Int64")
    return table
