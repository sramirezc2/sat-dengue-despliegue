"""Prioridad del cupo del canal con contexto artificial y sin etiquetas futuras."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from sat_dengue_pipeline.evaluation.scientific.policy import (
    cap_alerts,
    channel_decision,
    channel_score,
    freeze_policy,
)
from sat_dengue_pipeline.evaluation.scientific.reporting import (
    budget_ok,
    emission_frame,
    evaluate_cell,
)
from sat_dengue_pipeline.experiments.rolling import LINK


def context(cases: list[float], p75: list[float], horizon: int = 1) -> pd.DataFrame:
    """Crear claves y valores conocidos al cierre de T, sin desenlaces."""
    return pd.DataFrame(
        {
            "municipality_code": [f"50{i:03d}" for i in range(len(cases))],
            "origin_period": "2023-01",
            "target_period": f"2023-{1 + horizon:02d}",
            "horizon": horizon,
            "department_code": "50",
            "cases_at_origin": cases,
            "target_p75_at_origin": p75,
            "excess_at_origin": False,
        }
    )


@pytest.mark.parametrize("fraction", [0.5, 1.0, 2.0])
def test_sixty_rows_do_not_prioritize_twenty_zero_p75_rows(fraction: float) -> None:
    """Doce alertas priorizan exceso absoluto; P75=0 continúa siendo elegible."""
    frame = context([1.0] * 20 + [200.0] * 40, [0.0] * 20 + [10.0] * 40)
    eligible = channel_decision(frame, fraction)
    assert eligible.all()
    selected = cap_alerts(frame, channel_score(frame, fraction), eligible, 0.2)
    assert selected.sum() == 12
    assert frame.loc[selected, "municipality_code"].tolist() == [
        f"50{i:03d}" for i in range(20, 32)
    ]


@pytest.mark.parametrize("fraction", [0.5, 1.0, 2.0])
def test_two_hundred_cases_precede_one_case_with_zero_p75(fraction: float) -> None:
    """El canal estándar y el condicionado ordenan por su propio exceso absoluto."""
    frame = context([1.0, 200.0], [0.0, 10.0])
    np.testing.assert_allclose(channel_score(frame, fraction), [1.0, 200.0 - fraction * 10])
    decision = cap_alerts(
        frame, channel_score(frame, fraction), channel_decision(frame, fraction), 0.5
    )
    assert decision.tolist() == [False, True]


def test_quota_priority_does_not_change_channel_ranking_diagnostics() -> None:
    """AP/AUROC conservan el score previo aunque el cupo use exceso absoluto."""
    frame = context([1.0, 200.0], [0.0, 10.0]).assign(
        onset=[1, 0], excess_target=[1, 0], candidate_probability=[0.9, 0.1]
    )
    decisions = {
        "candidate": np.array([True, False]),
        "channel_C0": np.ones(2, dtype=bool),
        "persistence": np.zeros(2, dtype=bool),
    }
    cell = evaluate_cell(frame, decisions, {"status": "PENDING_RECIPE_POLICY", "budget_rate": None})
    metrics = cell["score_metrics"]["channel_C0"]
    assert metrics[0]["value"] == metrics[1]["value"] == 1.0
    assert metrics[2]["status"] == "NOT_PROBABILISTIC"


@pytest.mark.parametrize("fraction", [0.5, 1.0])
def test_channel_eligibility_and_monthly_department_quota_are_preserved(fraction: float) -> None:
    """Preservar umbral estricto, ceros, empates y cupos sin rellenar inelegibles."""
    # Dos grupos saturan el cupo y otros dos tienen una sola fila elegible.
    frames = []
    for month in ("2023-02", "2023-03"):
        for department in ("50", "73"):
            frame = context([0.0, 1.0, fraction * 10, 20.0, 20.0], [0.0, 0.0, 10.0, 10.0, 10.0])
            frame["target_period"] = month
            frame["department_code"] = department
            frame["municipality_code"] = [f"{department}{i:03d}" for i in range(5)]
            if department == "73":
                frame.loc[3:, "cases_at_origin"] = 0.0
            frames.append(frame)
    frame = pd.concat(frames, ignore_index=True)

    def selected_keys(rows: pd.DataFrame) -> set[tuple[str, str]]:
        """Seleccionar por claves para comprobar independencia del orden de filas."""
        eligible = channel_decision(rows, fraction)
        assert eligible.tolist().count(True) == 8
        selected = cap_alerts(rows, channel_score(rows, fraction), eligible, 0.4)
        counts = rows.loc[selected].groupby(["target_period", "department_code"]).size()
        assert counts.to_dict() == {
            (month, department): 2 if department == "50" else 1
            for month in ("2023-02", "2023-03")
            for department in ("50", "73")
        }
        return set(
            rows.loc[selected, ["municipality_code", "target_period"]].itertuples(
                index=False, name=None
            )
        )

    expected = {
        (municipality, month)
        for municipality in ("50003", "50004", "73001")
        for month in ("2023-02", "2023-03")
    }
    assert selected_keys(frame) == expected
    assert selected_keys(frame.sample(frac=1, random_state=7).reset_index(drop=True)) == expected
    tied = context([20.0, 20.0], [10.0, 10.0]).iloc[::-1].reset_index(drop=True)
    selected = cap_alerts(
        tied, channel_score(tied, fraction), channel_decision(tied, fraction), 0.5
    )
    assert tied.loc[selected, "municipality_code"].tolist() == ["50000"]


@pytest.mark.parametrize("horizon", [1, 2])
def test_selection_and_emission_share_fraction_priority_without_evaluation_labels(
    horizon: int,
) -> None:
    """Elegir f=0,5 en desarrollo y mantener alertas al cambiar desenlaces de evaluación."""
    selection = context([10.0, 3.0], [10.0, 0.0], horizon)
    evaluation = context([1.0, 200.0], [0.0, 10.0], horizon)

    def forbidden_read() -> None:
        """Rechazar cualquier acceso a etiquetas de evaluación al fijar la política."""
        pytest.fail("La selección no puede leer evaluation.y")

    run = SimpleNamespace(
        config={
            "horizons": [horizon],
            "scientific_evaluation": {
                "budget_rate_by_horizon": {str(horizon): 0.5},
                "channel_fraction_grid": {str(horizon): [0.5, 0.8]},
                "budget_rule": "monthly_department_floor",
                "channel_selection": "f1",
            },
        },
        scientific_contexts={(horizon, "threshold_selection"): selection},
        batches={
            horizon: {
                "threshold_selection": SimpleNamespace(
                    keys=selection[LINK], read_y=lambda: pd.Series([1, 0])
                ),
                "evaluation": SimpleNamespace(read_y=forbidden_read),
            }
        },
        fitted={
            horizon: SimpleNamespace(
                decisions=SimpleNamespace(digest="frozen-model", available_period="2022-12"),
            )
        },
        scientific_policies={},
    )
    # El contexto de evaluación ni siquiera existe al seleccionar.
    freeze_policy(run)
    policy = run.scientific_policies[horizon].copy()
    assert policy["channel_fraction"] == 0.5
    assert policy["selection_grid"] == [
        {"fraction": 0.5, "f1": 1.0, "alerts": 1},
        {"fraction": 0.8, "f1": 0.0, "alerts": 1},
    ]
    run.scientific_contexts[(horizon, "evaluation")] = evaluation
    run.fitted[horizon].model = SimpleNamespace(
        adapter=SimpleNamespace(model_sha256=lambda: "model")
    )
    run.identities = {str(horizon): {"model_json": "model"}}
    run.predictions = {
        horizon: SimpleNamespace(
            artifact_digest="frozen-model",
            keys=evaluation[LINK],
            probability=pd.Series([0.6, 0.9]),
            decision=pd.Series([True, True]),
        )
    }
    outcome = evaluation[["municipality_code", "origin_period"]].rename(
        columns={"origin_period": "year_month"}
    )
    outcome[f"y_t{horizon}"] = [0, 1]
    outcome["excess_target"] = [0, 1]
    run.scientific_outcomes = {(horizon, "evaluation"): outcome}
    _, decisions, defined = emission_frame(run, horizon)
    assert defined and decisions["channel_conditioned"].tolist() == [False, True]
    assert decisions["channel_C0"].tolist() == [True, True]  # A/B/C conserva C0 sin cupo.
    outcome[[f"y_t{horizon}", "excess_target"]] = [[1, 1], [0, 0]]
    _, changed, _ = emission_frame(run, horizon)
    for method in decisions:
        np.testing.assert_array_equal(changed[method], decisions[method])
    assert run.scientific_policies[horizon] == policy


@pytest.mark.parametrize("rate,quota", [(0.49, 1), (0.5, 2), (0.51, 2)])
def test_budget_floor_boundary_by_department_and_month(rate: float, quota: int) -> None:
    """Con cuatro filas por grupo, floor se distingue de redondeo, ceil y cupo global."""
    frame = pd.concat(
        [
            context([1.0] * 4, [0.0] * 4).assign(department_code=department, target_period=month)
            for department in ("50", "73")
            for month in ("2023-02", "2023-03")
        ],
        ignore_index=True,
    )
    selected = cap_alerts(frame, np.ones(16), np.ones(16, dtype=bool), rate)
    counts = frame.loc[selected].groupby(["department_code", "target_period"]).size()
    assert counts.to_dict() == {(d, m): quota for d in ("50", "73") for m in ("2023-02", "2023-03")}
    assert budget_ok(frame, selected, rate)
    selected[quota] = True  # Solo un grupo excede floor(tasa*4) en una alerta.
    assert not budget_ok(frame, selected, rate)
