"""Compuerta temporal previa a etiquetas; adaptación de controles de V2 916a69f."""

from dataclasses import dataclass

import pandas as pd

from .calendar import add_months, validate_period
from .canonical import KEYS


@dataclass(frozen=True)
class TemporalPolicy:
    """Límite inicial reservado para observaciones, orígenes y objetivos."""

    reserved_start: str = "2025-01"

    def __post_init__(self) -> None:
        """Validar configuración sin consultar observaciones o etiquetas."""
        validate_period(self.reserved_start)
        if self.reserved_start > "2025-01":
            raise ValueError("La configuración no puede habilitar 2025 consumido")


def validate_keys(frame: pd.DataFrame) -> None:
    """Validar exclusivamente las claves; los huecos mensuales están permitidos.

    Args:
        frame: Tabla con claves municipio-mes únicas.
    """
    if (
        frame.empty
        or frame.columns.duplicated().any()
        or not set(KEYS) <= set(frame)
        or frame[KEYS].isna().any().any()
        or frame.duplicated(KEYS).any()
    ):
        raise ValueError("Claves municipio-mes inválidas o duplicadas")
    for code, period in frame[KEYS].itertuples(index=False, name=None):
        if not isinstance(code, str) or len(code) != 5 or not code.isascii() or not code.isdigit():
            raise ValueError("Código DANE inválido")
        validate_period(period)


def guard_development(
    observations: pd.DataFrame,
    origins: pd.DataFrame,
    horizons: tuple[int, ...],
    policy: TemporalPolicy,
) -> None:
    """Rechazar periodos reservados antes de consultar valores o etiquetas.

    Args:
        observations: Historia y resultados retrospectivos, solo se leen claves.
        origins: Selección explícita de orígenes; puede incluir calendario objetivo.
        horizons: Horizontes que se prepararán juntos, únicamente 1 y 2.
        policy: Primer mes reservado, inclusive.

    Raises:
        ValueError: Ante claves inválidas, cruce reservado o calendario alterado.
    """
    if not horizons or any(type(h) is not int or h not in (1, 2) for h in horizons):
        raise ValueError("Horizonte inválido")
    validate_keys(observations)
    validate_keys(origins)
    if (
        observations.year_month.ge(policy.reserved_start).any()
        or origins.year_month.ge(policy.reserved_start).any()
    ):
        raise ValueError("Periodo reservado en observaciones u orígenes")
    targets = {h: origins.year_month.map(lambda t: add_months(t, h)) for h in horizons}
    if any(values.ge(policy.reserved_start).any() for values in targets.values()):
        raise ValueError("Objetivo reservado: el horizonte cruza el límite de desarrollo")
    for h, target in targets.items():
        name = f"target_period_t{h}"
        if name in origins and not origins[name].eq(target).fillna(False).all():
            raise ValueError("Calendario objetivo alterado")
    observed = pd.MultiIndex.from_frame(observations[KEYS])
    if not pd.MultiIndex.from_frame(origins[KEYS]).isin(observed).all():
        raise ValueError("Origen sin observación correspondiente")


def select_origins(
    observations: pd.DataFrame,
    start: str,
    end: str,
    horizon: int,
    policy: TemporalPolicy = TemporalPolicy(),
    *,
    previous_end: str | None = None,
) -> pd.DataFrame:
    """Seleccionar una ventana fija por mes objetivo, sin construir folds.

    Args:
        observations: Solo se consultan claves.
        start: Primer objetivo permitido en esta selección.
        end: Último objetivo permitido en esta selección.
        horizon: Uno o dos meses calendario.
        policy: Límite reservado.
        previous_end: Fin del rol previo; impide cruzarlo con el origen.

    Returns:
        Claves ordenadas; los objetivos y orígenes no cruzan ventanas previas.
    """
    validate_period(start)
    validate_period(end)
    validate_keys(observations)
    if type(horizon) is not int or horizon not in (1, 2):
        raise ValueError("Horizonte inválido")
    if start > end or end >= policy.reserved_start:
        raise ValueError("Ventana inválida o reservada")
    if previous_end is not None:
        validate_period(previous_end)
        if start <= previous_end:
            raise ValueError("Ventanas temporales solapadas")
    if observations.year_month.ge(policy.reserved_start).any():
        raise ValueError("Periodo reservado en observaciones")
    keys = observations[KEYS].sort_values(KEYS).reset_index(drop=True)
    target = keys.year_month.map(lambda t: add_months(t, horizon))
    mask = target.between(start, end)
    if previous_end is not None:
        mask &= keys.year_month.ge(previous_end)
    return keys.loc[mask].reset_index(drop=True)
