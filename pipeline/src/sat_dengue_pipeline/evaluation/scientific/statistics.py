"""Métricas, A/B/C e intervalos realmente emparejados por mes objetivo."""

from typing import Any

import numpy as np
import pandas as pd

from sat_dengue_pipeline.evaluation.metrics import metric_records
from sat_dengue_pipeline.experiments.rolling import stable_digest


def ratio(numerator: int | float, denominator: int | float) -> float | None:
    """Preservar denominadores nulos como ausencia, nunca como cero favorable."""
    return float(numerator / denominator) if denominator else None


def method_counts(frame: pd.DataFrame, decision: np.ndarray) -> dict[str, Any]:
    """Medir inicios y excesos sobre las mismas filas evaluables de un método."""
    y = frame.onset.to_numpy(dtype=int)
    excess = frame.excess_target.to_numpy(dtype=int)
    supplied = np.asarray(decision)
    if supplied.ndim != 1 or not np.isin(supplied, [0, 1]).all():
        raise ValueError("Predicciones ausentes o no binarias: soporte común inválido")
    decision = supplied.astype(bool)
    if len(decision) != len(y):
        raise ValueError("Decisiones desalineadas")
    n, i = len(frame), int(y.sum())
    tp, alerts = int((decision & (y == 1)).sum()), int(decision.sum())
    false_onset = alerts - tp
    false_excess = int((decision & (excess == 0)).sum())
    return {
        "N": n,
        "I": i,
        "TP": tp,
        "L": alerts,
        "FP_inicio": false_onset,
        "FP_exceso": false_excess,
        "onset_sensitivity": ratio(tp, i),
        "FAR_inicio": ratio(false_onset, alerts),
        "FAR_exceso": ratio(false_excess, alerts),
        "carga_FA_inicio_100mm": ratio(100 * false_onset, n),
        "false_alerts_per_detected_onset": ratio(false_onset, tp),
        "alert_fraction": ratio(alerts, n),
        "denominators": {
            "onset_sensitivity": i,
            "FAR_inicio": alerts,
            "FAR_exceso": alerts,
            "carga_FA_inicio_100mm": n,
            "false_alerts_per_detected_onset": tp,
            "alert_fraction": n,
        },
    }


def persistence_comparison(
    methods: dict[str, dict[str, Any]], candidate: str = "candidate"
) -> dict[str, Any]:
    """Distinguir una comparación informativa de la persistencia degenerada por cohorte."""
    model, persistence = methods[candidate], methods["persistence"]
    reason = (
        "DEGENERATE_PRIMARY_COHORT"
        if persistence.get("degenerate", False)
        else "NO_PERSISTENCE_ALERTS"
        if persistence["L"] == 0
        else "NO_ONSETS"
        if not model["I"]
        else None
    )
    return {
        "status": "NO_EVALUABLE" if reason else "EVALUABLE",
        "reason": reason,
        "superior": None if reason else model["TP"] > persistence["TP"],
        "required_for_verdict": not persistence.get("degenerate", False),
    }


def historical_abc(methods: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Aplicar A/B/C histórica con C0, C1 y FAR de exceso; sin reutilizar la carga como B."""
    candidate, channel, persistence = (
        methods[k] for k in ("candidate", "channel_C0", "persistence")
    )
    if len({(m["N"], m["I"]) for m in (candidate, channel, persistence)}) != 1:
        raise ValueError("A/B/C sobre soportes distintos")
    enough = candidate["I"] > 0
    comparison = persistence_comparison(methods)
    conditions = {
        "A_superar_canal": candidate["TP"] > channel["TP"] if enough else None,
        "B_superar_persistencia": comparison["superior"],
        "C_margen_FAR_exceso": (
            candidate["FAR_exceso"] - channel["FAR_exceso"] <= 0.05 + 1e-12
            if candidate["FAR_exceso"] is not None and channel["FAR_exceso"] is not None
            else None
        ),
    }
    status = (
        "ABC_HISTORICA_NO_CUMPLE"
        if False in conditions.values()
        else "ABC_HISTORICA_NO_EVALUABLE"
        if None in conditions.values()
        else "ABC_HISTORICA_CUMPLE"
    )
    return {
        "status": status,
        "conditions": conditions,
        "persistence_comparison": comparison,
        "margin_FAR_exceso": 0.05,
        "support_sufficient": candidate["I"] >= 30,
        "descriptive_only": True,
    }


def paired_intervals(
    frame: pd.DataFrame,
    decisions: dict[str, np.ndarray],
    *,
    candidate: str = "candidate",
    reference: str = "channel_conditioned",
    replicates: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    """Remuestrear meses completos con el mismo calendario para ambos métodos.

    Args:
        frame: Soporte común, con etiquetas ya liberadas después de predecir.
        decisions: Decisiones por método, ninguna política se reajusta al remuestrear.
        candidate: Método izquierdo de la diferencia.
        reference: Método derecho, sobre exactamente las mismas observaciones.
        replicates: 2.000 en el contrato propuesto; parámetro para comprobaciones analíticas.
        seed: Semilla de bootstrap, distinta de las semillas de entrenamiento.

    Returns:
        Intervalos de diferencias y número de réplicas indefinidas; sin ocultarlas.
    """
    months = sorted(frame.target_period.unique())
    names = [candidate, reference]
    counts = np.zeros((len(months), 2, 5), dtype=float)
    for j, month in enumerate(months):
        mask = frame.target_period.eq(month).to_numpy()
        for k, name in enumerate(names):
            values = method_counts(frame.loc[mask], decisions[name][mask])
            counts[j, k] = [values[n] for n in ("N", "I", "TP", "L", "FP_exceso")]
    rng = np.random.default_rng(seed)
    draws = (
        rng.integers(0, len(months), size=(replicates, len(months)))
        if months
        else np.empty((0, 0), dtype=int)
    )
    sampled = counts[draws].sum(axis=1) if months else np.empty((0, 2, 5))
    with np.errstate(divide="ignore", invalid="ignore"):
        sensitivity = 100 * sampled[:, :, 2] / sampled[:, :, 1]
        burden = 100 * (sampled[:, :, 3] - sampled[:, :, 2]) / sampled[:, :, 0]
        far = sampled[:, :, 4] / sampled[:, :, 3]
    result = {}
    for name, values in (
        ("delta_sensitivity_pp", sensitivity),
        ("delta_carga_FA_inicio_100mm", burden),
        ("delta_FAR_exceso", far),
    ):
        differences = values[:, 0] - values[:, 1]
        finite = np.isfinite(differences)
        valid = int(finite.sum())
        evaluable = len(months) >= 2 and valid == replicates
        bounds = (
            np.quantile(differences, [0.025, 0.975], method="linear").tolist()
            if evaluable
            else [None, None]
        )
        result[name] = {
            "lower": bounds[0],
            "upper": bounds[1],
            "valid_replicates": valid,
            "invalid_replicates": replicates - valid,
            "requested_replicates": replicates,
            "status": "OK_UNDER_PROPOSED_CONTRACT"
            if evaluable
            else "UNDEFINED_OR_INSUFFICIENT_BLOCKS",
        }
    return {
        "candidate": candidate,
        "reference": reference,
        "method": "paired_target_month_bootstrap",
        "seed": seed,
        "level": 0.95,
        "target_months": len(months),
        "draws_digest": stable_digest({"months": months, "draws": draws.tolist()}),
        "intervals": result,
        "contract_status": "PROPUESTA_PARA_APROBACION",
    }


def utility_verdict(
    methods: dict[str, dict[str, Any]],
    interval: dict[str, Any],
    *,
    candidate: str = "candidate",
    policy_defined: bool = True,
    budget_respected: bool = True,
    missing_predictions: int = 0,
) -> str:
    """Devolver solo el veredicto bajo contrato propuesto, separado de A/B/C."""
    model, channel = (methods[n] for n in (candidate, "channel_conditioned"))
    if missing_predictions:
        return "INVALIDO"
    if not policy_defined or model["I"] < 30 or not model["N"]:
        return "NO_EVALUABLE"
    comparison = persistence_comparison(methods, candidate)
    if comparison["status"] == "NO_EVALUABLE" and comparison["required_for_verdict"]:
        return "NO_EVALUABLE"
    gain = 100 * (model["onset_sensitivity"] - channel["onset_sensitivity"])
    burden = model["carga_FA_inicio_100mm"] - channel["carga_FA_inicio_100mm"]
    if (
        gain < 10 - 1e-12
        or burden > 5 + 1e-12
        or (comparison["status"] == "EVALUABLE" and not comparison["superior"])
        or not budget_respected
    ):
        return "NO_CUMPLE_POR_EFECTO"
    limits = interval["intervals"]
    low = limits["delta_sensitivity_pp"]["lower"]
    high = limits["delta_carga_FA_inicio_100mm"]["upper"]
    return (
        "CUMPLE"
        if low is not None and high is not None and low >= 10 and high <= 5
        else "PRECISION_INSUFICIENTE"
    )


def probability_metrics(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Reutilizar AP/AUROC/Brier existentes sobre las mismas etiquetas de inicio."""
    return metric_records(
        frame.onset.reset_index(drop=True).astype("Int64"),
        frame.candidate_probability.reset_index(drop=True).astype(float),
        None,
        probabilistic=True,
    )[:3]
