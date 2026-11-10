"""Métricas con empates agrupados y denominadores explícitos sobre soporte común."""

from typing import Any

import numpy as np
import pandas as pd

from sat_dengue_pipeline.experiments.rolling import stable_digest

DEFINITIONS = {
    "schema": "paired-onset-metrics-v1",
    "average_precision": "non_interpolated_distinct_score_groups; two_classes_required",
    "auroc": "positive_negative_rank_pairs; ties_half_credit; two_classes_required",
    "brier": "mean_squared_probability_error; persistence_not_probabilistic",
    "onset_sensitivity": "true_alerts/all_known_onsets; missing_predictions_keep_denominator",
    "false_alarm_ratio": "false_alerts/emitted_alerts; zero_alerts_undefined",
    "alert_volume": "emitted_alerts",
    "alert_fraction": "emitted_alerts/common_evaluable_population",
    "support": (
        "known_labels_and_explicit_context; missing_prediction_union_invalidates_all_methods"
    ),
}
METRICS = tuple(name for name in DEFINITIONS if name not in {"schema", "support"})
DEFINITIONS_DIGEST = stable_digest(DEFINITIONS)
DIRECTIONS = {
    name: (
        "lower"
        if name in {"brier", "false_alarm_ratio"}
        else "higher"
        if name in {"average_precision", "auroc", "onset_sensitivity"}
        else "descriptive"
    )
    for name in METRICS
}


def numeric(values: pd.Series, *, binary: bool = False) -> pd.Series:
    """Validar valores conocidos, preservando ausencias sin coerción a cero.

    Args:
        values: Probabilidades o etiquetas numéricas/ausentes.
        binary: Exigir cero o uno para valores presentes.

    Returns:
        Copia nullable, con valores no finitos/fuera de dominio rechazados.
    """
    present = values.dropna()
    if not present.empty and not pd.api.types.is_numeric_dtype(values):
        raise ValueError("Valores no numéricos")
    result = values.astype("Float64")
    if not np.isfinite(result.dropna().to_numpy(dtype=float)).all():
        raise ValueError("Valores no finitos")
    if not result.dropna().between(0, 1).all() or (binary and not present.isin([0, 1]).all()):
        raise ValueError("Valores fuera de dominio")
    return result


def metric_records(
    y: pd.Series,
    score: pd.Series,
    decision: pd.Series | None,
    *,
    probabilistic: bool,
    missing_predictions: int = 0,
    missing_labels: int = 0,
) -> list[dict[str, Any]]:
    """Calcular métricas sin eliminar filas distintas por método.

    Args:
        y: Etiquetas conocidas del soporte común, sin X o controles.
        score: Probabilidad o score determinista documentado.
        decision: Alertas binarias; None significa política no declarada.
        probabilistic: Brier solo aplica a probabilidades.
        missing_predictions: Unión de ausencias de todos los métodos del soporte.
        missing_labels: Ausencias excluidas y contadas en la cohorte declarada.

    Returns:
        Siete registros con denominadores y estados explícitos.
    """
    if not y.index.equals(score.index) or (
        decision is not None and not y.index.equals(decision.index)
    ):
        raise ValueError("Entradas desalineadas")
    y, score = numeric(y, binary=True), numeric(score)
    if y.isna().any():
        raise ValueError("El soporte común debe tener etiquetas conocidas")
    if decision is not None:
        decision = numeric(decision, binary=True)
    n, positives = len(y), int(y.eq(1).sum())
    negatives = n - positives
    missing = max(
        missing_predictions,
        int(score.isna().sum()),
        int(decision.isna().sum()) if decision is not None else 0,
    )
    values: dict[str, tuple[float | None, float | None, int | None, str]] = {}
    for name in METRICS:
        denominator = positives if name == "onset_sensitivity" else n
        values[name] = (
            None,
            None,
            denominator,
            "EMPTY_SUPPORT" if not n else "MISSING_PREDICTIONS",
        )
    if n and not missing:
        labels, scores = y.to_numpy(dtype=int), score.to_numpy(dtype=float)
        if positives and negatives:
            order = np.argsort(-scores, kind="stable")
            ordered, ranked = labels[order], scores[order]
            ends = np.r_[np.flatnonzero(np.diff(ranked) != 0), n - 1]
            tp = np.cumsum(ordered)[ends]
            ap = float(np.sum(np.diff(np.r_[0, tp]) / positives * tp / (ends + 1)))
            order = np.argsort(scores, kind="stable")
            grouped = pd.DataFrame({"s": scores[order], "y": labels[order]}).groupby("s").y
            counts = grouped.agg(["sum", "count"])
            pos = counts["sum"].to_numpy()
            neg = counts["count"].to_numpy() - pos
            credit = float(np.sum(pos * (np.cumsum(neg) - neg + 0.5 * neg)))
            values["average_precision"] = (ap, positives, n, "OK")
            values["auroc"] = (
                credit / (positives * negatives),
                credit,
                positives * negatives,
                "OK",
            )
        else:
            for name in ("average_precision", "auroc"):
                values[name] = (None, None, n, "SINGLE_CLASS")
        error = float(np.sum((scores - labels) ** 2))
        values["brier"] = (error / n, error, n, "OK")
        if decision is not None:
            alerts = decision.eq(1)
            emitted, detected = int(alerts.sum()), int((alerts & y.eq(1)).sum())
            false = int((alerts & y.eq(0)).sum())
            values["onset_sensitivity"] = (
                detected / positives if positives else None,
                detected,
                positives,
                "OK" if positives else "NO_ONSETS",
            )
            values["false_alarm_ratio"] = (
                false / emitted if emitted else None,
                false,
                emitted,
                "OK" if emitted else "NO_ALERTS",
            )
            values["alert_volume"] = (float(emitted), emitted, n, "OK")
            values["alert_fraction"] = (emitted / n, emitted, n, "OK")
    if not probabilistic:
        values["brier"] = (None, None, n, "NOT_PROBABILISTIC")
    if decision is None:
        for name in ("onset_sensitivity", "false_alarm_ratio", "alert_volume", "alert_fraction"):
            values[name] = (
                None,
                None,
                positives if name == "onset_sensitivity" else n,
                "NO_DECISION_POLICY",
            )
    return [
        dict(
            metric=name,
            value=value,
            evaluable=value is not None,
            status=status,
            numerator=numerator,
            denominator=denominator,
            support_rows=n,
            positive_rows=positives,
            negative_rows=negatives,
            missing_labels=missing_labels,
            missing_predictions=missing,
        )
        for name, (value, numerator, denominator, status) in values.items()
    ]
