"""Regresiones científicas con aritmética independiente, cohortes y fronteras observables."""

import copy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from fixtures.scientific_fixture import recipe

from sat_dengue_pipeline.domain.onset import build_labels
from sat_dengue_pipeline.evaluation.scientific import reporting
from sat_dengue_pipeline.evaluation.scientific.configuration import variants
from sat_dengue_pipeline.evaluation.scientific.policy import (
    cap_alerts,
    channel_decision,
    origin_context,
)
from sat_dengue_pipeline.evaluation.scientific.reporting import evaluate_cell, summaries
from sat_dengue_pipeline.evaluation.scientific.statistics import (
    historical_abc,
    method_counts,
    paired_intervals,
    utility_verdict,
)
from sat_dengue_pipeline.experiment_management.configuration import validate_configuration
from sat_dengue_pipeline.experiments.rolling import stable_digest


def observations() -> pd.DataFrame:
    """Ochenta observaciones, cuarenta inicios y cuatro meses para cálculos manuales."""
    return pd.DataFrame(
        {
            "municipality_code": [f"50{i:03d}" for i in range(20)] * 4,
            "origin_period": np.repeat(["2022-12", "2023-01", "2023-02", "2023-03"], 20),
            "target_period": np.repeat(["2023-01", "2023-02", "2023-03", "2023-04"], 20),
            "horizon": 1,
            "department_code": "50",
            "onset": [0, 1] * 40,
            "excess_target": [0, 1] * 40,
            "candidate_probability": [0.1, 0.9] * 40,
            "cases_at_origin": [1.0] * 80,
            "target_p75_at_origin": [1.0] * 80,
            "excess_at_origin": False,
        }
    )


@pytest.mark.parametrize(
    "fault",
    [
        "unknown",
        "duplicate_seed",
        "duplicate_cut",
        "overlap",
        "future",
        "predictor",
        "rate",
        "extra_reading",
        "union",
    ],
)
def test_scientific_recipe_fails_before_acquisition(fault: str) -> None:
    """Rechazar recetas ambiguas antes de crear evidencia o estimadores."""
    config = recipe()
    science = config["scientific_evaluation"]
    if fault == "unknown":
        science["auto_approve"] = True
    elif fault == "duplicate_seed":
        science["seeds"] = [53, 53]
    elif fault == "duplicate_cut":
        science["cuts"] *= 2
    elif fault == "overlap":
        second = copy.deepcopy(science["cuts"][0])
        second["id"] = "other"
        science["cuts"].append(second)
    elif fault == "future":
        science["cuts"][0]["roles_by_horizon"]["2"]["evaluation"]["end"] = "2025-01"
    elif fault == "predictor":
        science["arms"][0]["predictors"] = ["y_t2"]
    elif fault == "rate":
        science["budget_rate_by_horizon"]["2"] = 1.1
    elif fault == "extra_reading":
        science["readings"] = ["previous_target_non_excess"]
    else:
        science["arms"] = science["arms"][:1]
    with pytest.raises(ValueError):
        validate_configuration(config)


def test_recipe_derives_declared_features_and_every_seed_without_selection() -> None:
    """La semilla modifica la identidad efectiva, no el calendario ni las variables elegidas."""
    config = recipe()
    config["scientific_evaluation"]["seeds"] = [7, 13, 31, 53, 101]
    validate_configuration(config)
    generated = variants(config)
    assert len(generated) == 40
    assert {c["seed"] for _, c, _ in generated} == {7, 13, 31, 53, 101}
    for _, effective, dimensions in generated:
        assert effective["candidate"]["parameters"]["seed"] == dimensions["seed"]
        assert len(effective["preparation"]["matrix_columns"]) == len(effective["predictors"])
        assert effective["roles_by_horizon"] == config["roles_by_horizon"]


def test_t2_event_and_gate_are_distinct_and_future_does_not_change_emission() -> None:
    """0→1→1 no es inicio T+2; 1→0→1 sí lo es, con compuerta primaria cerrada en T."""
    keys = pd.DataFrame(
        {"municipality_code": ["50998"] * 3, "year_month": ["2023-01", "2023-02", "2023-03"]}
    )
    origins = keys.iloc[:1]
    labels = build_labels(keys.assign(excess=pd.array([0, 1, 1], dtype="Int64")), origins, 2)
    assert labels.y_t2.tolist() == [0] and labels.eligible_at_t.tolist() == [True]
    labels = build_labels(keys.assign(excess=pd.array([1, 0, 1], dtype="Int64")), origins, 2)
    assert labels.y_t2.tolist() == [1] and labels.eligible_at_t.tolist() == [False]
    table = keys.assign(
        dengue_notifications_count=2.0,
        total_notifications_count=9999.0,
        p75_h5_t2=1.0,
        zona_canal_t=["SEGURIDAD", "EXCESO", "EXCESO"],
        department_code="50",
    )
    requested = pd.DataFrame(
        {
            "municipality_code": ["50998"],
            "origin_period": ["2023-01"],
            "target_period": ["2023-03"],
            "horizon": [2],
        }
    )
    before = origin_context(table, requested, 2)
    assert before.cases_at_origin.tolist() == [2.0]  # El P75 H5 corresponde al evento 210.
    table.loc[1:, ["zona_canal_t", "dengue_notifications_count"]] = ["SEGURIDAD", 999.0]
    after = origin_context(table, requested, 2)
    pd.testing.assert_frame_equal(before, after)
    assert channel_decision(before, 1).tolist() == [True]


def test_abc_preserves_historical_far_and_B_is_not_burden() -> None:
    """Comprobar a mano TP, alertas, dos eventos de falsas y margen absoluto de cinco puntos."""
    frame = observations()
    model = np.array([False, True] * 40)
    channel = np.array([True, True, False, False] * 20)
    methods = {
        "candidate": method_counts(frame, model),
        "channel_C0": method_counts(frame, channel),
        "persistence": method_counts(frame, np.zeros(80, dtype=bool)),
    }
    abc = historical_abc(methods)
    assert abc["conditions"] == {
        "A_superar_canal": True,
        "B_superar_persistencia": True,
        "C_margen_FAR_exceso": True,
    }
    assert methods["candidate"]["TP"] == 40 and methods["channel_C0"]["TP"] == 20
    assert methods["candidate"]["denominators"]["carga_FA_inicio_100mm"] == 80
    assert methods["candidate"]["denominators"]["FAR_exceso"] == 40
    # Una continuación es correcta para exceso y falsa para inicio.
    frame.loc[0, "excess_target"] = 1
    all_alerts = method_counts(frame, np.ones(80, dtype=bool))
    assert all_alerts["FP_exceso"] == 39 and all_alerts["FP_inicio"] == 40
    assert all_alerts["carga_FA_inicio_100mm"] == 50
    assert methods["persistence"]["FAR_exceso"] is None
    undefined = historical_abc({**methods, "channel_C0": methods["persistence"]})
    assert undefined["status"] == "ABC_HISTORICA_NO_EVALUABLE"


def test_zero_onsets_and_zero_alerts_never_pass_by_coercion() -> None:
    """No convertir cocientes indefinidos en éxitos académicos o métricas de seguridad cero."""
    frame = observations().assign(onset=0, excess_target=0)
    counts = method_counts(frame, np.zeros(len(frame), dtype=bool))
    assert counts["onset_sensitivity"] is None and counts["FAR_inicio"] is None
    assert historical_abc({m: counts for m in ["candidate", "channel_C0", "persistence"]})[
        "conditions"
    ] == {"A_superar_canal": None, "B_superar_persistencia": None, "C_margen_FAR_exceso": None}


def test_budget_is_monthly_territorial_and_ties_are_deterministic() -> None:
    """El cupo no depende de y, del orden de filas ni del rendimiento observado."""
    frame = observations()
    selected = cap_alerts(frame, np.ones(80), np.ones(80, dtype=bool), 0.15)
    assert selected.sum() == 12  # Tres de veinte por cada mes.
    assert all(frame.loc[selected].groupby("target_period").size() == 3)
    frame["onset"] = 1 - frame.onset
    np.testing.assert_array_equal(
        cap_alerts(frame, np.ones(80), np.ones(80, dtype=bool), 0.15), selected
    )
    shuffled = frame.sample(frac=1, random_state=1)
    other = cap_alerts(shuffled.reset_index(drop=True), np.ones(80), np.ones(80, dtype=bool), 0.15)
    assert set(
        map(tuple, shuffled.loc[other, ["municipality_code", "target_period"]].values)
    ) == set(map(tuple, frame.loc[selected, ["municipality_code", "target_period"]].values))


def test_paired_intervals_preserve_identical_methods_and_undefined_replicates() -> None:
    """Diferencias de métodos iguales son cero en cada réplica compartida, no solo en media."""
    frame = observations()
    decision = np.array([0, 1] * 40, dtype=bool)
    result = paired_intervals(frame, {"candidate": decision, "channel_conditioned": decision})
    for ci in result["intervals"].values():
        assert ci["lower"] == ci["upper"] == 0.0
        assert ci["valid_replicates"] == 2000
    frame.loc[frame.target_period.ne("2023-01"), "onset"] = 0
    result = paired_intervals(frame, {"candidate": decision, "channel_conditioned": decision})
    ci = result["intervals"]["delta_sensitivity_pp"]
    assert ci["invalid_replicates"] > 0 and ci["lower"] is None
    assert ci["valid_replicates"] + ci["invalid_replicates"] == 2000


def test_utility_uses_both_paired_bounds_and_remains_distinct_from_abc() -> None:
    """Una puntual favorable sin precisión suficiente no se convierte en CUMPLE."""
    frame = observations()
    candidate = np.array([0, 1] * 40, dtype=bool)
    channel = np.array([0, 1, 0, 0] * 20, dtype=bool)
    decisions = {
        "candidate": candidate,
        "channel_conditioned": channel,
        "channel_C0": channel,
        "persistence": np.zeros(80, dtype=bool),
    }
    methods = {m: method_counts(frame, d) for m, d in decisions.items()}
    interval = paired_intervals(frame, decisions)
    assert utility_verdict(methods, interval) == "CUMPLE"
    interval["intervals"]["delta_sensitivity_pp"]["lower"] = 9.9
    assert utility_verdict(methods, interval) == "PRECISION_INSUFICIENTE"
    assert utility_verdict(methods, interval, budget_respected=False) == "NO_CUMPLE_POR_EFECTO"
    assert utility_verdict(methods, interval, missing_predictions=1) == "INVALIDO"
    assert utility_verdict(methods, interval, policy_defined=False) == "NO_EVALUABLE"
    methods["candidate"]["I"] = 29
    assert utility_verdict(methods, interval) == "NO_EVALUABLE"


@pytest.mark.parametrize(
    "k,small,votes,status",
    [
        (4, 0, 3, "CUMPLE"),
        (4, 1, 2, "CUMPLE"),
        (2, 0, 2, "INSUFFICIENT_CUTS"),
        (4, 0, 2, "NO_CUMPLE"),
        (7, 0, 4, "CUMPLE"),
    ],
)
def test_cut_consistency_excludes_only_predeclared_small_support(
    k: int, small: int, votes: int, status: str
) -> None:
    """Reproducir 3/4 y 2/3 sin sumar semillas como si fueran cortes independientes."""
    records = []
    for cut in range(k):
        records.append(
            {
                "kind": "cell",
                "year": "all",
                "cut": str(cut),
                "arm": "epi",
                "population": "native",
                "reading": "primary",
                "horizon": 1,
                "territory": "primary_meta_tolima",
                "seed": 53,
                "policy_status": "FROZEN",
                "support_status": "INSUFFICIENT_30_ONSETS" if cut >= k - small else "SUFFICIENT",
                "UTILIDAD_PROPUESTA": "CUMPLE" if cut < votes else "NO_CUMPLE_POR_EFECTO",
                "ABC_HISTORICA": {"status": "ABC_HISTORICA_CUMPLE"},
                "methods": {
                    "candidate": {"TP": 31},
                    "channel_C0": {"TP": 30},
                    "channel_conditioned": {"TP": 30},
                },
                "paired_keys_digest": "a",
            }
        )
    result = summaries(
        records,
        {
            "seeds": [53],
            "cuts": [{"id": str(cut)} for cut in range(k)],
            "consistency_rule": "strict_majority_min_three",
            "consistency_vote": "both_rules_cumple",
        },
    )
    assert result[0]["status"] == status
    assert result[0]["usable_cuts"] == k - small
    assert result[1]["five_seeds_check"] == "NOT_VERIFIED"
    assert result[1]["status"] == "NO_EVALUABLE"
    for r in records:
        r["UTILIDAD_PROPUESTA"] = "INVALIDO"
    assert (
        summaries(
            records,
            {
                "seeds": [53],
                "cuts": [{"id": str(cut)} for cut in range(k)],
                "consistency_rule": "strict_majority_min_three",
                "consistency_vote": "both_rules_cumple",
            },
        )[0]["status"]
        == "INVALIDO"
    )


def test_pending_policy_stops_only_utility_and_missing_labels_keep_original_budget() -> None:
    """A/B/C puede calcularse mientras falta una decisión del presupuesto/canal propuesto."""
    frame = observations()
    frame.loc[0, "onset"] = None
    decisions = {
        "candidate": np.ones(80, dtype=bool),
        "channel_C0": np.ones(80, dtype=bool),
        "persistence": np.zeros(80, dtype=bool),
    }
    cell = evaluate_cell(frame, decisions, {"status": "PENDING_RECIPE_POLICY", "budget_rate": None})
    assert cell["prediction_rows"] == 80 and cell["methods"]["candidate"]["N"] == 79
    assert cell["missing_labels"] == 1
    assert (
        cell["UTILIDAD_PROPUESTA"] == "NO_EVALUABLE"
        and cell["ABC_HISTORICA"]["conditions"]["A_superar_canal"] is False
    )


def test_negative_control_that_meets_invalidates_the_policy() -> None:
    """Un control perfecto construido como contraejemplo no debe aprobar una política inválida."""
    frame = observations()
    perfect = frame.onset.eq(1).to_numpy()
    weak = np.array([0, 1, 0, 0] * 20, dtype=bool)
    decisions = {
        "candidate": weak,
        "channel_C0": weak,
        "channel_conditioned": weak,
        "persistence": np.zeros(80, dtype=bool),
        "random_ranking": perfect,
        "alert_everything": np.ones(80, dtype=bool),
        "inflated_channel": np.ones(80, dtype=bool),
    }
    cell = evaluate_cell(frame, decisions, {"status": "FROZEN", "budget_rate": 1.0})
    assert cell["negative_controls"]["random_ranking"] == "CUMPLE"
    assert cell["UTILIDAD_PROPUESTA"] == "INVALIDO"
    assert cell["scientific_conclusion"] == "NOT_APPROVED"


@pytest.mark.parametrize("cause", ["negative_control", "missing_prediction", "support_only"])
def test_insufficient_producer_support_preserves_invalid_cell_cuts_and_five_seeds(
    monkeypatch: pytest.MonkeyPatch, cause: str
) -> None:
    """Un corte inválido no desaparece tras tres votos favorables de cada una de cinco semillas."""
    import copy

    frame = observations()
    perfect = frame.onset.eq(1).to_numpy()
    weak = np.array([0, 1, 0, 0] * 20, dtype=bool)
    decisions = {
        "candidate": perfect,
        "channel_C0": weak,
        "channel_conditioned": weak,
        "persistence": np.zeros(80, dtype=bool),
        "random_ranking": weak,
        "alert_everything": np.ones(80, dtype=bool),
        "inflated_channel": weak,
    }
    affected_frame, affected_decisions = frame.copy(), copy.deepcopy(decisions)
    if cause == "negative_control":
        affected_decisions["random_ranking"] = perfect
    elif cause == "missing_prediction":
        affected_frame.loc[7, "candidate_probability"] = np.nan
    policy = {"status": "FROZEN", "budget_rate": 1.0, "sha256": "a" * 64}
    seeds = [7, 13, 31, 53, 101]
    runs = {}
    for seed in seeds:
        for cut in range(4):
            dimensions = dict(
                arm="epi", population="native", reading="primary", seed=seed, cut=str(cut)
            )
            runs[f"{seed}.{cut}"] = SimpleNamespace(
                artifact=SimpleNamespace(serialized_sha256="b" * 64, semantic_digest="c" * 64),
                config={"horizons": [1], "scientific_dimensions": dimensions},
                lineage={"canonical": {}},
                identities={"1": {"model_json": "d" * 64}},
                support={"1": {"evaluation": {"passed": not (seed == 53 and cut == 3)}}},
                temporal={},
                label_reads={},
                scientific_policies={1: policy},
            )

    def artificial_emission(run, horizon):
        """Sustituir solo procedencia de modelos: métricas y agregación usan funciones reales."""
        dims = run.config["scientific_dimensions"]
        if dims["seed"] == 53 and dims["cut"] == "3":
            return affected_frame, affected_decisions, True
        return frame, decisions, True

    monkeypatch.setattr(reporting, "verify_artifact", lambda artifact: None)
    monkeypatch.setattr(reporting, "emission_frame", artificial_emission)
    monkeypatch.setattr(
        reporting, "cells", lambda frame: [("primary_meta_tolima", "all", np.ones(80, dtype=bool))]
    )
    records, _ = reporting.evaluate_runs(
        runs,
        {
            "horizons": [1],
            "scientific_evaluation": {
                "seeds": seeds,
                "cuts": [{"id": str(cut)} for cut in range(4)],
                "consistency_rule": "strict_majority_min_three",
                "consistency_vote": "both_rules_cumple",
            },
        },
    )
    cell = next(r for r in records if r["kind"] == "cell" and r["seed"] == 53 and r["cut"] == "3")
    assert cell["support_status"] == "INSUFFICIENT_DECLARED_ROLE_SUPPORT"
    assert not cell["producer_support_passed"]
    expected = "NO_EVALUABLE" if cause == "support_only" else "INVALIDO"
    assert cell["UTILIDAD_PROPUESTA"] == expected
    if cause == "negative_control":
        assert cell["negative_controls"]["random_ranking"] == "CUMPLE"
    elif cause == "missing_prediction":
        assert cell["missing_predictions"] == 1 and cell["ABC_HISTORICA"]["status"] == "INVALIDO"
    consistency = next(r for r in records if r["kind"] == "consistency" and r["seed"] == 53)
    assert consistency["usable_cuts"] == consistency["votes"] == 3
    assert consistency["status"] == ("CUMPLE" if cause == "support_only" else "INVALIDO")
    combined = next(r for r in records if r["kind"] == "seed_stability")
    assert len(combined["seeds"]) == 5
    assert combined["status"] == (
        "CUMPLE_BAJO_CONTRATO_PROPUESTO" if cause == "support_only" else "INVALIDO"
    )
    assert all(s["consistency"] == "CUMPLE" for s in combined["seeds"] if s["seed"] != 53)


def test_scientific_fragment_hash_and_presence_are_required(tmp_path: Path) -> None:
    """No aceptar agregados alterados ni quitar del inventario una evidencia enlazada."""
    import json

    from sat_dengue_pipeline.experiment_management.evidence import (
        publish,
        scientific_artifacts,
        verify_execution,
    )

    folder = tmp_path / "docs/evidence/experiments/SYNTHSCIENCE/check"
    folder.mkdir(parents=True)
    lineage = {
        "experiment_id": "SYNTHSCIENCE",
        "protocol_sha256": "a" * 64,
        "configuration_sha256": "b" * 64,
        "scientific_contract": {"sha256": "c" * 64},
    }
    extra = scientific_artifacts([{"kind": "cell", "label": "VEREDICTO_BAJO_CONTRATO_PROPUESTO"}])
    receipt = {
        "status": "COMPLETED",
        "experiment_id": "SYNTHSCIENCE",
        "execution_id": "check",
        "protocol_sha256": "a" * 64,
        "configuration_sha256": "b" * 64,
        "execution_signature": stable_digest(lineage),
        "scientific_evaluation": {
            "contract": lineage["scientific_contract"],
            "records": list(extra),
        },
    }
    publish(
        folder,
        {
            "receipt.json": receipt,
            "lineage.json": lineage,
            "configuration.json": {},
            "metrics.json": {},
            "validation.json": {},
            **extra,
        },
    )
    reference = "docs/evidence/experiments/SYNTHSCIENCE/check/inventory.json"
    assert verify_execution(tmp_path, reference) == receipt
    chunk = folder / next(iter(extra))
    original = chunk.read_bytes()
    chunk.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="alterado"):
        verify_execution(tmp_path, reference)
    chunk.unlink()
    inventory = json.loads((folder / "inventory.json").read_bytes())
    inventory.pop(next(iter(extra)))
    (folder / "inventory.json").write_text(json.dumps(inventory), encoding="utf-8")
    with pytest.raises(ValueError, match="Inventario científico"):
        verify_execution(tmp_path, reference)


def test_small_differences_report_all_five_seeds_without_sufficient_cuts() -> None:
    """Conservar diferencias y signos sin inventar soporte a partir de cinco semillas."""
    rows = []
    for seed, delta in zip([7, 13, 31, 53, 101], [-2, -1, 0, 1, 2], strict=True):
        rows.append(
            {
                "kind": "cell",
                "year": "all",
                "cut": "one",
                "arm": "epi",
                "population": "common",
                "reading": "primary",
                "horizon": 2,
                "territory": "primary_meta_tolima",
                "seed": seed,
                "policy_status": "FROZEN",
                "support_status": "SUFFICIENT",
                "UTILIDAD_PROPUESTA": "PRECISION_INSUFICIENTE",
                "ABC_HISTORICA": {"status": "ABC_HISTORICA_NO_CUMPLE"},
                "methods": {
                    "candidate": {"TP": 31 + delta},
                    "channel_C0": {"TP": 31},
                    "channel_conditioned": {"TP": 31},
                },
                "paired_keys_digest": "identical-support",
            }
        )
    result = summaries(
        rows,
        {
            "seeds": [7, 13, 31, 53, 101],
            "cuts": [{"id": "one"}],
            "consistency_rule": "strict_majority_min_three",
            "consistency_vote": "both_rules_cumple",
        },
    )
    stability = result[-1]
    assert stability["five_seeds_check"] == "REPORTED"
    assert stability["status"] == "NO_EVALUABLE"
    distribution = stability["distributions"][0]
    assert distribution["mean"] == 0 and distribution["positive"] == distribution["negative"] == 2
    assert (
        distribution["ties"] == 1
        and distribution["one_or_two_onset_check"] == "REPORTED_FIVE_SEEDS"
    )


def test_missing_comparator_prediction_is_rejected_without_dropping_rows() -> None:
    """No convertir una decisión ausente en alerta verdadera mediante astype(bool)."""
    predictions = np.ones(80)
    predictions[7] = np.nan
    with pytest.raises(ValueError, match="Predicciones ausentes"):
        method_counts(observations(), predictions)


def test_all_comparators_keep_ranking_metrics_and_do_not_claim_probabilities() -> None:
    """AP/AUROC de referencias constantes son 0,5; Brier de una regla no probabilística es NA."""
    frame = observations()
    decisions = {
        "candidate": frame.onset.eq(1).to_numpy(),
        "channel_C0": np.ones(80, dtype=bool),
        "persistence": np.zeros(80, dtype=bool),
    }
    cell = evaluate_cell(frame, decisions, {"status": "PENDING_RECIPE_POLICY", "budget_rate": None})
    metrics = cell["score_metrics"]
    assert metrics["candidate"][0]["value"] == metrics["candidate"][1]["value"] == 1.0
    for name in ("channel_C0", "persistence"):
        assert metrics[name][0]["value"] == metrics[name][1]["value"] == 0.5
        assert metrics[name][2]["value"] is None
        assert metrics[name][2]["status"] == "NOT_PROBABILISTIC"


def test_tracking_logs_more_than_one_thousand_metrics_with_tags(tmp_path: Path) -> None:
    """El límite de lote combina métricas y tags; no se pierden valores al dividirlos."""
    import sqlite3
    import subprocess

    from sat_dengue_pipeline.experiment_management.tracking import ExperimentTracker

    (tmp_path / "pipeline").mkdir()
    (tmp_path / ".gitignore").write_text("pipeline/.tracking/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    tracker = ExperimentTracker(tmp_path / "pipeline", True)
    tags = {"execution_id": "large-technical-batch", "contract_status": "PROPUESTA_PARA_APROBACION"}
    run_id = tracker.start(tags)
    metrics = {"technical": [{"metric": f"value_{i}", "value": float(i)} for i in range(1200)]}
    tracker.finish(run_id, "COMPLETED", tags, metrics)
    tracker.close()
    store = tmp_path / "pipeline/.tracking/experiments/tracking.sqlite"
    with sqlite3.connect(f"file:{store}?mode=ro", uri=True) as db:
        assert db.execute(
            "SELECT count(*),sum(value) FROM metrics WHERE run_uuid=?", (run_id,)
        ).fetchone() == (1200, sum(range(1200)))
        assert (
            db.execute("SELECT status FROM runs WHERE run_uuid=?", (run_id,)).fetchone()[0]
            == "FINISHED"
        )


def test_stricter_declared_role_support_is_not_overridden_by_thirty_onsets() -> None:
    """Cuarenta inicios no satisfacen una receta que predeclaró cien, aunque superen treinta."""
    from types import SimpleNamespace

    from sat_dengue_pipeline.evaluation.scientific.reporting import read_outcomes
    from sat_dengue_pipeline.experiments.roles import RoleSupport

    frame = observations()
    counts = {"rows": 80, "municipalities": 20, "months": 4, "n0": None, "n1": None}
    run = SimpleNamespace(
        config={"horizons": [1]},
        prediction_complete={1: True},
        temporal={},
        support={"1": {"evaluation": counts}},
        plans={
            1: SimpleNamespace(
                supports={"evaluation": RoleSupport(n0=1, n1=100, municipalities=20, months=4)}
            )
        },
        batches={1: {"evaluation": SimpleNamespace(read_y=lambda: frame.onset)}},
    )
    read_outcomes(run)
    assert counts["n1"] == 40 and counts["passed"] is False
    assert counts["label_stage"] == "after_freeze_and_predictions"
