"""Métricas manuales, soporte único y bootstrap emparejado sin fuga."""

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from fixtures.adapter_fixture import make_registry
from fixtures.evaluation_fixture import make_evaluation
from fixtures.procedure_fixture import make_procedure, threshold_policy

from sat_dengue_pipeline.evaluation import paired
from sat_dengue_pipeline.evaluation.metrics import metric_records
from sat_dengue_pipeline.evaluation.paired import (
    EvaluationConfig,
    cluster_draws,
    evaluate,
    evaluate_procedure,
)
from sat_dengue_pipeline.experiments.procedure import fit_procedure, predict_frozen
from sat_dengue_pipeline.models.adapters import AdapterSpec


def report(tables, frozen, **kwargs):
    """Evaluar con pocas réplicas explícitas, exclusivamente datos artificiales."""
    return evaluate(
        tables,
        frozen,
        expected_digest=frozen.digest,
        config=EvaluationConfig(bootstrap_replicates=16, **kwargs),
    )


def test_hand_computed_ties_and_denominators() -> None:
    """AP/AUC 1/2; Brier 5/16; sensibilidad/FAR/volumen relativo 1/2."""
    y, p, d = pd.Series([1, 0, 1, 0]), pd.Series([0.75, 0.75, 0.25, 0.25]), pd.Series([1, 1, 0, 0])
    records = {r["metric"]: r for r in metric_records(y, p, d, probabilistic=True)}
    expected = {
        "average_precision": 0.5,
        "auroc": 0.5,
        "brier": 0.3125,
        "onset_sensitivity": 0.5,
        "false_alarm_ratio": 0.5,
        "alert_volume": 2.0,
        "alert_fraction": 0.5,
    }
    assert {name: row["value"] for name, row in records.items()} == expected
    assert records["onset_sensitivity"]["denominator"] == 2
    assert records["false_alarm_ratio"]["denominator"] == 2
    assert records["auroc"]["denominator"] == 4
    for order in ([3, 1, 0, 2], [2, 1, 3, 0]):
        actual = metric_records(
            *(obj.iloc[order].reset_index(drop=True) for obj in (y, p, d)), probabilistic=True
        )
        assert {r["metric"]: r["value"] for r in actual} == expected


@pytest.mark.parametrize("labels", [[0, 0], [1, 1], []])
def test_single_class_empty_and_zero_alerts(labels) -> None:
    """No sustituir métricas indefinidas con cero."""
    y = pd.Series(labels, dtype="Int64")
    rows = {
        r["metric"]: r
        for r in metric_records(
            y, pd.Series([0.5] * len(y)), pd.Series([0] * len(y)), probabilistic=True
        )
    }
    for name in ("average_precision", "auroc", "false_alarm_ratio"):
        assert rows[name]["value"] is None and not rows[name]["evaluable"]
    if labels:
        assert rows["false_alarm_ratio"]["status"] == "NO_ALERTS"


def test_half_credit_auroc() -> None:
    """AUROC positivo/negativo: un empate aporta medio acierto."""
    rows = metric_records(
        pd.Series([1, 1, 0, 0]), pd.Series([1.0, 0.5, 0.5, 0.0]), None, probabilistic=True
    )
    assert next(r for r in rows if r["metric"] == "auroc")["value"] == 0.875


def test_keyed_reordering_and_repeatability() -> None:
    """Cada tabla puede reordenarse independientemente sin cambiar un byte."""
    tables, frozen, _ = make_evaluation(6)
    expected = report(tables, frozen)
    changed = replace(
        tables,
        **{
            name: getattr(tables, name).sample(frac=1, random_state=i).reset_index(drop=True)
            for i, name in enumerate(
                ("keys", "labels", "probabilities", "decisions", "controls", "strata")
            )
        },
    )
    assert report(changed, frozen).canonical_json == expected.canonical_json
    assert report(tables, frozen).digest == expected.digest


def test_missing_labels_and_predictions_preserve_common_denominators() -> None:
    """Una ausencia de predicción invalida todos los métodos, sin reducir inicios."""
    tables, frozen, _ = make_evaluation()
    baseline = report(tables, frozen).payload
    probabilities = tables.probabilities.copy()
    probabilities.loc[0, "candidate_probability"] = pd.NA
    changed = report(replace(tables, probabilities=probabilities), frozen).payload
    global_rows = [r for r in changed["metrics"] if r["stratum"] == "global"]
    assert {r["support_rows"] for r in global_rows} == {len(tables.keys)}
    assert {r["missing_predictions"] for r in global_rows} == {1}
    original = next(
        r
        for r in baseline["metrics"]
        if r["stratum"] == "global"
        and r["metric"] == "onset_sensitivity"
        and r["reference"] == "candidate"
    )
    for row in global_rows:
        assert row["value"] is None
        if row["metric"] == "onset_sensitivity":
            assert row["denominator"] == original["denominator"]
    labels = tables.labels.copy()
    labels.loc[0, "onset"] = pd.NA
    missing = report(replace(tables, labels=labels), frozen).payload
    support = next(r for r in missing["strata"] if r["stratum"] == "global")
    assert support["excluded_missing_labels"] == 1 and support["evaluable_rows"] == len(labels) - 1
    assert {r["missing_labels"] for r in missing["metrics"] if r["stratum"] == "global"} == {1}


@pytest.mark.parametrize(
    "fault",
    [
        "duplicate",
        "missing",
        "foreign",
        "reserved",
        "calendar",
        "null_key",
        "stratum",
        "threshold",
        "digest",
    ],
)
def test_invalid_keyed_inputs_fail_closed(fault) -> None:
    """Rechazar ambigüedad de claves, estratos, congelación o cruces a 2025."""
    tables, frozen, _ = make_evaluation()
    labels, strata, decisions = tables.labels.copy(), tables.strata.copy(), tables.decisions.copy()
    if fault == "duplicate":
        labels = pd.concat([labels, labels.iloc[[0]]], ignore_index=True)
    elif fault == "missing":
        labels = labels.iloc[:-1]
    elif fault == "foreign":
        labels.loc[0, "municipality_code"] = "50990"
    elif fault == "reserved":
        labels.loc[0, "target_period"] = "2025-01"
    elif fault == "calendar":
        labels.loc[0, "target_period"] = "2021-06"
    elif fault == "null_key":
        labels.loc[0, "origin_period"] = None
    elif fault == "stratum":
        strata.loc[0, "department_code"] = None
    elif fault == "threshold":
        decisions.loc[0, "candidate_decision"] = 1 - decisions.loc[0, "candidate_decision"]
    with pytest.raises(ValueError):
        report(
            replace(
                tables,
                labels=labels,
                strata=strata,
                decisions=decisions,
                frozen_digest="0" * 64 if fault == "digest" else frozen.digest,
            ),
            frozen,
        )


@pytest.mark.parametrize("value", [np.inf, -np.inf, -0.1, 1.1, "bad"])
def test_invalid_probabilities_rejected(value) -> None:
    """Probabilidades fuera del contrato nunca se ocultan como ausencias."""
    tables, frozen, _ = make_evaluation()
    p = tables.probabilities.copy()
    if isinstance(value, str):
        p["candidate_probability"] = p.candidate_probability.astype(object)
    p.loc[0, "candidate_probability"] = value
    with pytest.raises(ValueError):
        report(replace(tables, probabilities=p), frozen)


def test_strata_pairing_curves_and_freeze_unchanged() -> None:
    """Departamentos particionan global; diferencias y curvas mantienen soporte."""
    tables, frozen, _ = make_evaluation()
    before = frozen.to_json()
    result = report(tables, frozen).payload
    global_support = next(r for r in result["strata"] if r["stratum"] == "global")
    departments = [r for r in result["strata"] if r["stratum"].startswith("department:")]
    assert sum(r["total_rows"] for r in departments) == global_support["total_rows"]
    assert sum(r["evaluable_rows"] for r in departments) == global_support["evaluable_rows"]
    for comparison in result["comparisons"]:
        values = {
            r["reference"]: r
            for r in result["metrics"]
            if r["metric"] == comparison["metric"] and r["stratum"] == comparison["stratum"]
        }
        left, right = values["candidate"], values[comparison["reference"]]
        assert left["support_rows"] == right["support_rows"] == comparison["support_rows"]
        assert left["paired_keys_digest"] == right["paired_keys_digest"]
        if comparison["evaluable"]:
            assert comparison["value"] == left["value"] - right["value"]
    assert all(r["diagnostic_only"] for r in result["curves"])
    assert frozen.to_json() == before
    labels = tables.labels.copy()
    labels["onset"] = 1 - labels.onset
    report(replace(tables, labels=labels), frozen)
    assert frozen.to_json() == before


def test_insufficient_clusters_and_temporal_cluster_draws() -> None:
    """No generar intervalos con Meta/Tolima; cada sorteo mantiene panel completo."""
    tables, frozen, _ = make_evaluation()
    result = report(tables, frozen).payload
    assert all(
        row["status"] == "INSUFFICIENT_CLUSTERS" and row["lower"] is None and row["upper"] is None
        for row in result["uncertainty"]
    )
    config = EvaluationConfig(bootstrap_replicates=16, min_clusters=2)
    draws = cluster_draws(tables.keys, config)
    assert draws == cluster_draws(tables.keys.sample(frac=1), config)
    assert all(len(draw) == 2 for draw in draws)
    # Cada aparición del código representa TODOS sus meses, nunca una fila aislada.
    assert len(tables.keys.loc[tables.keys.municipality_code.eq(draws[0][0])]) == 4
    assert draws != cluster_draws(tables.keys, replace(config, seed=7))


def test_paired_bootstrap_valid_and_undefined_replicates_counted() -> None:
    """Un único sorteo para referencias; réplicas inválidas no se reemplazan."""
    tables, frozen, _ = make_evaluation(6)
    result = report(tables, frozen).payload
    global_bounds = [r for r in result["uncertainty"] if r["stratum"] == "global"]
    assert len({r["draws_digest"] for r in global_bounds}) == 1
    ap = next(r for r in global_bounds if r["metric"] == "average_precision")
    assert ap["valid_replicates"] == ap["requested_replicates"] == 16
    assert ap["interval_evaluable"] and ap["descriptive_only"]
    labels = tables.labels.copy()
    codes = sorted(labels.municipality_code.unique())
    labels["onset"] = labels.municipality_code.eq(codes[0]).astype(int)
    changed = report(replace(tables, labels=labels), frozen).payload
    row = next(
        r
        for r in changed["uncertainty"]
        if r["metric"] == "average_precision" and r["stratum"] == "global"
    )
    assert 0 < row["invalid_replicates"] < 16
    assert row["valid_replicates"] + row["invalid_replicates"] == 16
    assert row["lower"] is None and row["status"] == "UNDEFINED_REPLICATES"
    assert all("municipality_code" not in r for r in changed["replicates"])


def test_actual_resamples_keep_all_months_together(monkeypatch: pytest.MonkeyPatch) -> None:
    """Espiar las réplicas realmente consumidas: multiplicidad uniforme del panel."""
    tables, frozen, _ = make_evaluation(6)
    original = paired._method_metrics
    seen = []

    def spy(frame):
        """Comprobar todas las entradas compartidas de candidato y referencias."""
        for _, group in frame.groupby("municipality_code"):
            counts = group.groupby("target_period").size()
            assert len(counts) == 4 and counts.nunique() == 1
        seen.append(len(frame))
        return original(frame)

    monkeypatch.setattr(paired, "_method_metrics", spy)
    report(tables, frozen)
    assert seen.count(24) >= 32


@pytest.mark.parametrize("fault", ["none", "digest", "origin", "target"])
def test_label_callback_runs_only_after_valid_freeze(fault: str) -> None:
    """El puente a tarea 10 verifica congelación/2025 antes de leer evaluation.y."""
    plan, batches = make_procedure()
    fitted = fit_procedure(
        batches, plan, AdapterSpec("signal_double", "1"), make_registry(), threshold_policy()
    )
    batch = batches["evaluation"]
    output = predict_frozen(fitted, batch, expected_digest=fitted.decisions.digest)
    strata = output.keys.copy()
    strata["department_code"] = strata.municipality_code.map({"50998": "50", "73998": "73"})
    calls = []

    def reader():
        """Detectar consultas antes de la compuerta."""
        calls.append(True)
        assert fault == "none", "Lectura anterior al rechazo"
        return batch.read_y()

    keys = batch.keys.copy()
    if fault in {"origin", "target"}:
        keys.loc[0, fault + "_period"] = "2025-01"
    checked = replace(batch, keys=keys, read_y=reader)
    before = fitted.decisions.to_json()
    args = dict(
        expected_digest="0" * 64 if fault == "digest" else fitted.decisions.digest,
        config=EvaluationConfig(bootstrap_replicates=4),
    )
    if fault == "none":
        evaluate_procedure(fitted, checked, strata, **args)
        assert calls == [True]
    else:
        with pytest.raises(ValueError):
            evaluate_procedure(fitted, checked, strata, **args)
        assert calls == []
    assert fitted.decisions.to_json() == before
