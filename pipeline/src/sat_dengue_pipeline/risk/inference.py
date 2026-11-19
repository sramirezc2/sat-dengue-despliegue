"""Predictores por prefijo temporal; no importa constructores de desenlaces."""

import json
from dataclasses import dataclass

import pandas as pd

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle
from sat_dengue_pipeline.domain.calendar import add_months, validate_period
from sat_dengue_pipeline.domain.canonical import PREDICTORS, build_table, predictor_matrix
from sat_dengue_pipeline.raw.build import retained_frame
from sat_dengue_pipeline.raw.panel import source_panel
from sat_dengue_pipeline.raw.producers import (
    climate_daily_normalization,
    climate_monthly_aggregation,
    epidemiology_normalization,
    geography_normalization,
)
from sat_dengue_pipeline.raw.temporal import Quarantine, parse_date, raw_temporal_projection

from .configuration import digest
from .frozen import FrozenLogistic


@dataclass(frozen=True)
class InferenceCoverage:
    """Cobertura exclusiva de lectura retrospectiva; no es un perfil de desarrollo."""

    end: str
    start: str = "2007-01"
    epi_start: str = "2007-01"
    municipalities: int = 76

    @property
    def periods(self) -> list[str]:
        """Enumerar únicamente meses anteriores o iguales al corte."""
        return pd.period_range(self.start, self.end, freq="M").astype(str).tolist()


def feature_prefix(
    bundle: ResolvedBundle, cutoff: str, *, dimension_count: int = 1122
) -> tuple[pd.DataFrame, dict]:
    """Reutilizar productores solo después de cortar las claves temporales.

    Args:
        bundle: Cinco fuentes cuya integridad validó la frontera de entrada.
        cutoff: Mes máximo observable; nunca se interpretan valores posteriores.
        dimension_count: Cardinalidad del catálogo; 76 solo en fixtures artificiales.

    Returns:
        Tabla de predictores observables y roles, sin etiquetas ni evaluabilidad.
    """
    validate_period(cutoff)
    if not "2012-01" <= cutoff <= "2025-10":
        raise ValueError("Corte de predictores no autorizado")
    files = {f.logical_name: f for f in bundle.files}
    dimension = geography_normalization(
        json.loads(files["divipola_catalog"].path.read_text(encoding="utf-8-sig")),
        json.loads(files["divipola_provenance"].path.read_text(encoding="utf-8-sig")),
        files["divipola_catalog"].sha256,
        InferenceCoverage(cutoff, municipalities=dimension_count),
    )
    dimension = dimension.loc[dimension.department_code.isin(["50", "73"])].reset_index(drop=True)
    if dimension.groupby("department_code").size().to_dict() != {"50": 29, "73": 47}:
        raise ValueError("Se requieren exactamente los 76 municipios de Meta/Tolima")
    codes = set(dimension.municipality_code)
    retained = {}
    for name, keys in raw_temporal_projection(bundle).items():
        date_col = "date" if name == "daily_climate" else "INI_SIN"
        dates = keys[date_col].map(parse_date)
        periods = dates.map(lambda d: d.isoformat()[:7] if d is not None else "")
        territory = (
            keys.mpio_cdpmp.str.strip().str.zfill(5)
            if name == "daily_climate"
            else keys.COD_DPTO_R.str.strip().str.zfill(2) + keys.COD_MUN_R.str.strip().str.zfill(3)
        )
        retained[name] = tuple(
            keys.index[periods.between("2007-01", cutoff) & territory.isin(codes)]
        )
    q = Quarantine(retained, {"inference_cutoff": cutoff})
    coverage = InferenceCoverage(cutoff)
    epi, _ = epidemiology_normalization(
        {
            n: retained_frame(bundle, q, n)
            for n in ("dengue_notifications", "severe_dengue_notifications")
        },
        dimension,
        coverage,
    )
    daily, _ = climate_daily_normalization(
        retained_frame(bundle, q, "daily_climate"), dimension, coverage
    )
    panel = source_panel((dimension, epi, climate_monthly_aggregation(daily)), coverage)
    return build_table(panel)


def prioritize(
    table: pd.DataFrame, schema: dict, origin: str, model: FrozenLogistic
) -> tuple[list[dict], str]:
    """Ordenar los elegibles con cupo fijo y conservar los 76 registros.

    Args:
        table: Prefijo de observaciones observable en T.
        schema: Roles canónicos sin desenlaces.
        origin: Origen T+2 entre noviembre de 2024 y octubre de 2025.
        model: Estado congelado cargado, sin método fit.

    Returns:
        Filas territoriales ordenadas por código y digest de los predictores en T.
    """
    if not "2024-11" <= origin <= "2025-10" or table.year_month.max() > origin:
        raise ValueError("Prefijo con futuro o calendario de publicación no autorizado")
    if not "2025-01" <= add_months(origin, 2) <= "2025-12":
        raise ValueError("Objetivo fuera de 2025")
    if schema["column_roles"]["target"] or any(
        n.startswith(("y_", "excess_target", "earlier_onset")) for n in table.columns
    ):
        raise ValueError("Inferencia no admite etiquetas o desenlaces")
    current = table.loc[table.year_month.eq(origin)].sort_values("municipality_code")
    current = current.reset_index(drop=True)
    codes = current.municipality_code.tolist()
    if (
        len(codes) != 76
        or len(set(codes)) != 76
        or (current.groupby("department_code").size().to_dict() != {"50": 29, "73": 47})
    ):
        raise ValueError("Cobertura territorial de inferencia incompleta")
    X = predictor_matrix(table, schema).loc[table.year_month.eq(origin)]
    X.index = table.loc[table.year_month.eq(origin)].municipality_code
    X = X.loc[codes].reset_index(drop=True)
    reasons = []
    for index, zone in enumerate(current.zona_canal_t):
        if pd.isna(zone):
            reason = "ORIGIN_STATE_MISSING"
        elif zone == "EXCESO":
            reason = "EXCESS_AT_ORIGIN"
        elif X.iloc[index].isna().any():
            reason = "REQUIRED_PREDICTORS_MISSING"
        elif zone not in {"EXITO", "SEGURIDAD", "ALERTA"}:
            raise ValueError("Estado en T incompatible")
        else:
            reason = None
        reasons.append(reason)
    eligible = [i for i, reason in enumerate(reasons) if reason is None]
    if len(eligible) < 8:
        raise ValueError("Menos de ocho municipios elegibles; no se publica el lote")
    scores = model.score(X.iloc[eligible].reset_index(drop=True))
    ordered = sorted(zip(eligible, scores, strict=True), key=lambda p: (-p[1], codes[p[0]]))
    ranks = {i: rank for rank, (i, _) in enumerate(ordered, 1)}
    rows = []
    for i, row in current.iterrows():
        rank = ranks.get(i)
        department = str(row.department_code)
        rows.append(
            {
                "municipality_code": str(row.municipality_code),
                "municipality_name": str(row.municipality_name),
                "department_code": department,
                "department_name": {"50": "Meta", "73": "Tolima"}[department],
                "risk_rank": rank,
                "selected_for_attention": rank is not None and rank <= 8,
                "eligibility_status": "ELIGIBLE" if rank is not None else "INELIGIBLE",
                "ineligibility_reason": reasons[i],
            }
        )
    # Solo predictores; ausencias explícitas y orden de claves estable.
    features = current[["municipality_code", "year_month"]].copy()
    for name in PREDICTORS:
        features[name] = X[name]
    records = features.astype(object).where(features.notna(), None).to_dict("records")
    return rows, digest(records)
