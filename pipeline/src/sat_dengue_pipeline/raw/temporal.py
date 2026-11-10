"""Proyección de claves y cuarentena previa a cualquier productor de valores."""

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache

import pandas as pd

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle
from sat_dengue_pipeline.domain.temporal import TemporalPolicy
from sat_dengue_pipeline.experiments.rolling import stable_digest

PROJECTION = {
    "dengue_notifications": ["COD_DPTO_R", "COD_MUN_R", "INI_SIN"],
    "severe_dengue_notifications": ["COD_DPTO_R", "COD_MUN_R", "INI_SIN"],
    "daily_climate": ["mpio_cdpmp", "date"],
}


@lru_cache(maxsize=16_384)
def parse_date(value: str) -> date | None:
    """Interpretar ISO o día/mes/año, incluido el midnight localizado aprobado."""
    value = value.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[ T]00:00:00)?", value):
            return date.fromisoformat(value[:10])
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}(?: 00:00:00)?", value):
            return datetime.strptime(value[:10], "%d/%m/%Y").date()
        localized = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4}) 12:00:00 a\.[ \u00a0]m\.", value)
        if localized:
            day, month, year = map(int, localized.groups())
            return date(year, month, day)
    except ValueError:
        pass
    return None


def raw_temporal_projection(bundle: ResolvedBundle) -> dict[str, pd.DataFrame]:
    """Leer exclusivamente columnas territoriales y temporales, sin eventos o clima."""
    return {
        file.logical_name: pd.read_csv(
            file.path, usecols=PROJECTION[file.logical_name], dtype=str, keep_default_na=False
        ).loc[:, PROJECTION[file.logical_name]]
        for file in bundle.files
        if file.logical_name in PROJECTION
    }


@dataclass(frozen=True)
class Quarantine:
    """Índices transitorios permitidos y auditoría agregada sin filas publicables."""

    retained: dict[str, tuple[int, ...]]
    audit: dict[str, dict]


def raw_temporal_quarantine(
    projection: dict[str, pd.DataFrame], policy: TemporalPolicy
) -> Quarantine:
    """Excluir reserva e inválidos antes de cargar valores para normalización.

    Args:
        projection: Únicamente claves sin normalizar.
        policy: Autoridad temporal de V3.

    Returns:
        Selectores internos y conteos/digests; nunca filas en la auditoría.
    """
    retained, audit = {}, {}
    reserved_start = date.fromisoformat(policy.reserved_start + "-01")
    for name, keys in projection.items():
        date_column = "date" if name == "daily_climate" else "INI_SIN"
        dates = keys[date_column].map(parse_date)
        invalid = dates.isna()
        if len(keys) and invalid.all():
            raise ValueError("Fuente sin ninguna fecha interpretable; no se pueden inferir ceros")
        reserved = dates.map(lambda d: d is not None and d >= reserved_start)
        retained[name] = tuple(keys.index[~invalid & ~reserved])
        excluded = keys.loc[invalid | reserved].astype(str).values.tolist()
        # Orden multiconjunto: no depende del orden de archivo y conserva duplicados.
        excluded.sort(key=lambda row: json.dumps(row, ensure_ascii=False))
        audit[name] = {
            "input": len(keys),
            "retained": len(retained[name]),
            "reserved": int(reserved.sum()),
            "invalid_date": int(invalid.sum()),
            "digest": stable_digest(excluded),
        }
        assert audit[name]["input"] == sum(
            audit[name][key] for key in ("retained", "reserved", "invalid_date")
        )
    return Quarantine(retained, audit)
