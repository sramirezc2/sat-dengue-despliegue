"""Inicio y elegibilidad; reglas de experiments/onset.py de V2, commit 916a69f."""

import pandas as pd

from .calendar import add_months
from .canonical import KEYS
from .temporal import TemporalPolicy, guard_development


def operational_eligibility(current_excess: pd.Series) -> pd.Series:
    """Decidir elegibilidad para ambos horizontes exclusivamente con el estado T.

    Args:
        current_excess: Cero observado, uno observado o ausencia.

    Returns:
        Verdadero únicamente para no exceso observado al origen.
    """
    if not current_excess.dropna().isin([0, 1]).all():
        raise ValueError("Exceso debe ser binario o ausente")
    return current_excess.eq(0).fillna(False).astype(bool)


def build_labels(
    states: pd.DataFrame,
    origins: pd.DataFrame,
    horizon: int,
    policy: TemporalPolicy = TemporalPolicy(),
) -> pd.DataFrame:
    """Construir inicio retrospectivo sin puentear meses ni consultar 2025.

    Args:
        states: Claves y excess binario/ausente, con observaciones de resultados.
        origins: Claves de pronóstico solicitadas, distintas de la historia.
        horizon: T+1 o T+2.
        policy: Compuerta evaluada antes de acceder a excess o etiquetas.

    Returns:
        Claves, etiqueta nullable, calendario y controles de ausencia/elegibilidad.
    """
    guard_development(states, origins, (horizon,), policy)
    # Esta lectura y cualquier acceso retrospectivo ocurren después de la compuerta.
    if not states.excess.dropna().isin([0, 1]).all():
        raise ValueError("Exceso debe ser binario o ausente")
    result = origins[KEYS].sort_values(KEYS).reset_index(drop=True).copy()
    lookup = states.set_index(KEYS).excess.to_dict()
    current, previous, target, first = [], [], [], []
    for municipality, origin in result.itertuples(index=False, name=None):
        current.append(lookup[(municipality, origin)])
        previous.append(lookup.get((municipality, add_months(origin, horizon - 1)), pd.NA))
        target.append(lookup.get((municipality, add_months(origin, horizon)), pd.NA))
        first.append(lookup.get((municipality, add_months(origin, 1)), pd.NA))
    c, p, t, f = [pd.Series(v, dtype="Int64") for v in (current, previous, target, first)]
    evaluable = p.notna() & t.notna()
    y = (p.eq(0) & t.eq(1)).astype("Int64").where(evaluable, pd.NA)
    result[f"target_period_t{horizon}"] = result.year_month.map(
        lambda origin: add_months(origin, horizon)
    )
    result[f"y_t{horizon}"] = y
    result[f"y_evaluable_t{horizon}"] = evaluable
    status = pd.Series("evaluable", index=result.index)
    status.loc[p.isna() & t.notna()] = "missing_previous"
    status.loc[p.notna() & t.isna()] = "missing_target"
    status.loc[p.isna() & t.isna()] = "missing_previous_and_target"
    result[f"y_status_t{horizon}"] = status
    result["excess_previous"] = p
    result["excess_target"] = t
    result["eligible_at_t"] = operational_eligibility(c)
    result["eligibility_status"] = pd.Series(
        [
            "missing_current"
            if pd.isna(v)
            else "observed_non_excess"
            if v == 0
            else "excess_at_origin"
            for v in c
        ]
    )
    result["earlier_onset_t1"] = (operational_eligibility(c) & f.eq(1)).fillna(False)
    validate_label_metadata(result, horizon, policy)
    return result


def validate_label_metadata(
    labels: pd.DataFrame, horizon: int, policy: TemporalPolicy = TemporalPolicy()
) -> None:
    """Rechazar calendario, etiquetas y estados de evaluabilidad inconsistentes.

    Args:
        labels: Resultado de build_labels o metadatos equivalentes recibidos.
        horizon: Horizonte a comprobar.
        policy: Se comprueba antes de leer las etiquetas.
    """
    guard_development(labels, labels, (horizon,), policy)
    y = labels[f"y_t{horizon}"]
    evaluable = labels[f"y_evaluable_t{horizon}"]
    status = labels[f"y_status_t{horizon}"]
    if (
        not y.dropna().isin([0, 1]).all()
        or evaluable.isna().any()
        or not pd.api.types.is_bool_dtype(evaluable)
        or not y.notna().eq(evaluable).all()
        or status.isna().any()
        or not status.isin(
            ["evaluable", "missing_previous", "missing_target", "missing_previous_and_target"]
        ).all()
        or not status.eq("evaluable").eq(evaluable).all()
    ):
        raise ValueError("Etiqueta/evaluabilidad inconsistente; ausencia no es cero")
