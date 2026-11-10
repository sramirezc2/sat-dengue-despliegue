"""Roles objetivo disjuntos y disponibilidad estricta antes de cualquier ajuste."""

from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from sat_dengue_pipeline.domain.calendar import add_months, validate_period
from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.domain.temporal import TemporalPolicy
from sat_dengue_pipeline.models.adapters import validate_features

from .rolling import LINK, ExperimentData, stable_digest, validate_data

ROLES = ("train", "calibration_fit", "calibration_selection", "threshold_selection", "evaluation")


@dataclass(frozen=True)
class RoleWindow:
    """Intervalo inclusivo de objetivos, nunca de posiciones de filas."""

    role: str
    start: str
    end: str


@dataclass(frozen=True)
class RoleSupport:
    """Mínimos de fábrica por clase/municipios y número exacto de meses."""

    n0: int
    n1: int
    municipalities: int
    months: int

    def __post_init__(self) -> None:
        """Rechazar soportes ambiguos antes de consultar datos."""
        if any(type(v) is not int or v < 1 for v in asdict(self).values()):
            raise ValueError("Soporte de rol inválido")


@dataclass(frozen=True)
class TemporalPlan:
    """Cinco roles ordenados, soporte mínimo y embargo adicional explícito."""

    horizon: int
    windows: tuple[RoleWindow, ...]
    embargo_months: int = 0
    min_months: int = 2
    min_class_rows: int = 1
    reserved_start: str = "2025-01"
    supports: dict[str, RoleSupport] | None = None

    def __post_init__(self) -> None:
        """Validar calendario y política antes de recibir etiquetas."""
        TemporalPolicy(self.reserved_start)
        if self.supports is not None and (
            set(self.supports) != set(ROLES)
            or any(not isinstance(v, RoleSupport) for v in self.supports.values())
        ):
            raise ValueError("Se requiere soporte para exactamente cinco roles")
        if (
            type(self.horizon) is not int
            or self.horizon not in (1, 2)
            or not isinstance(self.windows, tuple)
            or tuple(window.role for window in self.windows) != ROLES
            or type(self.embargo_months) is not int
            or self.embargo_months < 0
            or type(self.min_months) is not int
            or self.min_months < 1
            or type(self.min_class_rows) is not int
            or self.min_class_rows < 1
        ):
            raise ValueError("Plan temporal o soporte inválido")
        previous = None
        for window in self.windows:
            validate_period(window.start)
            validate_period(window.end)
            if (
                window.start > window.end
                or window.end >= self.reserved_start
                or (previous is not None and window.start <= previous)
            ):
                raise ValueError("Roles solapados, desordenados o reservados")
            previous = window.end


@dataclass(frozen=True)
class RoleBatch:
    """Entradas de un rol; las etiquetas solo se consultan mediante read_y."""

    role: str
    keys: pd.DataFrame
    X: pd.DataFrame
    controls: pd.DataFrame
    read_y: Callable[[], pd.Series]
    predictors: tuple[str, ...] = tuple(PREDICTORS)
    allow_excess_at_origin: bool = False


def split_roles(data: ExperimentData, plan: TemporalPlan) -> dict[str, RoleBatch]:
    """Separar roles por objetivo sin leer valores de y ni imputar ausencias.

    Args:
        data: Datos enlazados y separados de tarea 8.
        plan: Cinco ventanas declaradas y disjuntas.

    Returns:
        Batches con acceso diferido a etiquetas; embargo fuera de todos los roles.
    """
    validate_data(data, plan.horizon, plan.reserved_start)
    result = {}
    for window in plan.windows:
        positions = (
            pd.Series(range(len(data.keys)), index=data.keys.index)
            .loc[data.keys.target_period.between(window.start, window.end)]
            .to_numpy()
        )
        order = data.keys.iloc[positions].reset_index(drop=True).sort_values(LINK).index.to_numpy()
        positions = positions[order]

        def read_y(selected: Any = positions.copy()) -> pd.Series:
            """Leer solo las etiquetas del rol solicitado, después de su compuerta."""
            return data.y.iloc[selected].reset_index(drop=True).copy(deep=True)

        result[window.role] = RoleBatch(
            window.role,
            data.keys.iloc[positions].reset_index(drop=True).copy(),
            data.X.iloc[positions].reset_index(drop=True).copy(),
            data.controls.iloc[positions].reset_index(drop=True).copy(),
            read_y,
        )
    preflight_roles(result, plan)
    return result


def preflight_roles(batches: dict[str, RoleBatch], plan: TemporalPlan) -> dict[str, Any]:
    """Comprobar todos los roles y transiciones sin acceder a ninguna etiqueta.

    Args:
        batches: Cinco entradas distintas por objetivo, incluida evaluación.
        plan: Calendario congelado y soporte declarado.

    Returns:
        Auditoría de disponibilidad y soporte por claves, sin resultados observados.
    """
    if set(batches) != set(ROLES):
        raise ValueError("Se requieren exactamente cinco roles")
    # Todas las claves pasan antes de consultar características o callbacks y.
    for name in ROLES:
        batch = batches[name]
        dummy_y = pd.Series(pd.NA, index=batch.keys.index, dtype="Int64")
        validate_data(
            ExperimentData(batch.keys, batch.X, dummy_y, batch.controls, batch.predictors),
            plan.horizon,
            plan.reserved_start,
        )
    targets_seen: set[str] = set()
    links_seen: set[tuple[Any, ...]] = set()
    support, transitions = {}, []
    previous_available = None
    previous_role = ""
    for window in plan.windows:
        batch = batches[window.role]
        keys = batch.keys
        months = set(keys.target_period)
        expected = set(pd.period_range(window.start, window.end, freq="M").astype(str))
        links = set(keys[LINK].itertuples(index=False, name=None))
        if (
            batch.role != window.role
            or months != expected
            or len(months) < plan.min_months
            or links_seen & links
            or targets_seen & months
            or not batch.controls.eligible_at_t.all()
        ):
            raise ValueError("Soporte incompleto, roles solapados o filas no elegibles")
        if plan.supports is not None:
            requirement = plan.supports[window.role]
            if (
                len(months) != requirement.months
                or keys.municipality_code.nunique() < requirement.municipalities
            ):
                raise ValueError("Soporte de meses/municipios insuficiente antes de etiquetas")
        targets_seen |= months
        links_seen |= links
        validate_features(batch.X, predictors=batch.predictors)
        if (
            not batch.allow_excess_at_origin
            and "zona_canal_t" in batch.X
            and batch.X.zona_canal_t.eq("EXCESO").any()
        ):
            raise ValueError("Elegibilidad contradice el estado observado al origen")
        available = str(keys.label_available_period.max())
        first_origin = str(keys.origin_period.min())
        if previous_available is not None:
            embargo_end = add_months(previous_available, plan.embargo_months)
            if embargo_end >= first_origin:
                raise ValueError("Disponibilidad tardía entre roles antes del consumidor")
            transitions.append(
                {
                    "producer": previous_role,
                    "consumer": window.role,
                    "available": previous_available,
                    "embargo_end": embargo_end,
                    "first_consumer_origin": first_origin,
                }
            )
        previous_available, previous_role = available, window.role
        support[window.role] = {
            "rows": len(keys),
            "months": len(months),
            "municipalities": int(keys.municipality_code.nunique()),
            "first_origin": first_origin,
            "available": available,
            "keys_digest": stable_digest(keys.to_dict("records")),
        }
    return {"plan": asdict(plan), "support": support, "transitions": transitions}


def role_labels(batch: RoleBatch, plan: TemporalPlan) -> pd.Series:
    """Consultar etiquetas completas solo al consumir su rol autorizado.

    Args:
        batch: Rol de ajuste/selección, nunca evaluación.
        plan: Soporte mínimo por clase.

    Returns:
        Copia binaria alineada; una ausencia provoca rechazo, no cero ni descarte.
    """
    if batch.role not in ROLES[:-1]:
        raise ValueError("Evaluación no puede alimentar ajuste o selección")
    dummy = pd.Series(pd.NA, index=batch.keys.index, dtype="Int64")
    validate_data(
        ExperimentData(batch.keys, batch.X, dummy, batch.controls, batch.predictors),
        plan.horizon,
        plan.reserved_start,
    )
    y = batch.read_y()
    if (
        not isinstance(y, pd.Series)
        or not y.index.equals(batch.X.index)
        or y.isna().any()
        or not y.isin([0, 1]).all()
    ):
        raise ValueError("Etiquetas ausentes, inválidas o soporte insuficiente de ambas clases")
    counts = observed_support(batch, y)
    if not support_passes(counts, plan, batch.role):
        raise ValueError("Etiquetas: soporte por clase/municipio insuficiente")
    return y.copy(deep=True)


def observed_support(batch: RoleBatch, y: pd.Series | None = None) -> dict[str, Any]:
    """Contar solo claves, o clases cuando su lectura ya esté autorizada."""
    if y is not None and (
        not y.index.equals(batch.keys.index) or y.isna().any() or not y.isin([0, 1]).all()
    ):
        raise ValueError("Etiquetas ausentes, inválidas o desalineadas")
    return {
        "rows": len(batch.keys),
        "months": int(batch.keys.target_period.nunique()),
        "municipalities": int(batch.keys.municipality_code.nunique()),
        "n0": None if y is None else int(y.eq(0).sum()),
        "n1": None if y is None else int(y.eq(1).sum()),
    }


def support_passes(counts: dict[str, Any], plan: TemporalPlan, role: str) -> bool:
    """Comprobar mínimos de fábrica sin leer callbacks ni cambiar cohortes."""
    if plan.supports is None:
        return counts["n0"] >= plan.min_class_rows and counts["n1"] >= plan.min_class_rows
    required = plan.supports[role]
    return (
        counts["months"] == required.months
        and counts["municipalities"] >= required.municipalities
        and (counts["n0"] is None or counts["n0"] >= required.n0)
        and (counts["n1"] is None or counts["n1"] >= required.n1)
    )
