"""Centinelas antífuga para calibración, umbral y referencias de inicio."""

import json
from dataclasses import FrozenInstanceError, replace
from typing import Any

import numpy as np
import pandas as pd
import pytest
from fixtures.adapter_fixture import SignalAdapter, make_registry
from fixtures.procedure_fixture import make_procedure, threshold_policy

from sat_dengue_pipeline.experiments import procedure
from sat_dengue_pipeline.experiments.decisions import (
    ThresholdPolicy,
    apply_sigmoid,
    choose_representation,
    fit_sigmoid,
    select_threshold,
)
from sat_dengue_pipeline.experiments.procedure import (
    FrozenDecisions,
    fit_procedure,
    predict_frozen,
)
from sat_dengue_pipeline.experiments.roles import ROLES, preflight_roles, role_labels
from sat_dengue_pipeline.models.adapters import AdapterSpec, ModelRegistry


@pytest.mark.parametrize("horizon", [1, 2])
def test_evaluation_y_never_read_during_fit_calibration_threshold_or_prediction(
    horizon: int,
) -> None:
    """Un callback bomba demuestra ausencia de lectura, no solo un resultado vacío."""
    plan, batches = make_procedure(horizon)
    reads = dict.fromkeys(ROLES, 0)
    wrapped = {}
    for name, batch in batches.items():

        def reader(role: str = name, original: Any = batch.read_y) -> pd.Series:
            """Fallar si evaluación alcanza cualquier etapa de ajuste o selección."""
            reads[role] += 1
            assert role != "evaluation", "evaluation.y fue leído"
            return original()

        wrapped[name] = replace(batch, read_y=reader)
    fitted = fit_procedure(
        wrapped, plan, AdapterSpec("signal_double", "1"), make_registry(), threshold_policy()
    )
    assert reads == {**dict.fromkeys(ROLES[:-1], 1), "evaluation": 0}
    prediction = predict_frozen(
        fitted, wrapped["evaluation"], expected_digest=fitted.decisions.digest
    )
    assert reads["evaluation"] == 0
    pd.testing.assert_frame_equal(
        prediction.keys.iloc[:, :4], batches["evaluation"].keys.iloc[:, :4]
    )
    assert prediction.decision.isin([0, 1]).all()
    assert (
        len(prediction.probability)
        == len(prediction.prevalence_probability)
        == len(prediction.persistence_decision)
    )


def test_each_fit_and_selection_receives_only_its_own_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Espiar modelo/sigmoide/selección: una sola llamada por etapa y rol exacto."""
    plan, batches = make_procedure()
    expected = {name: batch.read_y() for name, batch in batches.items() if name != "evaluation"}
    calls = {"model_fit": 0, "calibrator_fit": 0, "choice": 0, "threshold": 0}

    class SpyAdapter(SignalAdapter):
        """Registrar el único ajuste del modelo candidato."""

        def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
            """No permitir entradas de calibración o evaluación en fit."""
            calls["model_fit"] += 1
            pd.testing.assert_frame_equal(X, batches["train"].X)
            pd.testing.assert_series_equal(y, expected["train"])
            super().fit(X, y)

    original_fit, original_choice, original_threshold = (
        procedure.fit_sigmoid,
        procedure.choose_representation,
        procedure.select_threshold,
    )

    def sigmoid(probability: pd.Series, y: pd.Series, seed: int) -> tuple[float, float]:
        """Solo calibration_fit puede ajustar coeficientes."""
        calls["calibrator_fit"] += 1
        assert calls["model_fit"] == 1 and calls["threshold"] == 0
        pd.testing.assert_series_equal(y, expected["calibration_fit"])
        return original_fit(probability, y, seed)

    def choose(raw: pd.Series, calibrated: pd.Series, y: pd.Series) -> Any:
        """Solo calibration_selection decide la representación."""
        calls["choice"] += 1
        pd.testing.assert_series_equal(y, expected["calibration_selection"])
        return original_choice(raw, calibrated, y)

    def threshold(probability: pd.Series, y: pd.Series, policy: ThresholdPolicy) -> Any:
        """Threshold_selection no llama a ningún ajuste nuevamente."""
        calls["threshold"] += 1
        assert calls["model_fit"] == calls["calibrator_fit"] == calls["choice"] == 1
        pd.testing.assert_series_equal(y, expected["threshold_selection"])
        return original_threshold(probability, y, policy)

    monkeypatch.setattr(procedure, "fit_sigmoid", sigmoid)
    monkeypatch.setattr(procedure, "choose_representation", choose)
    monkeypatch.setattr(procedure, "select_threshold", threshold)
    registry = ModelRegistry()
    registry.register("spy", "1", SpyAdapter)
    fitted = fit_procedure(batches, plan, AdapterSpec("spy", "1"), registry, threshold_policy())
    predict_frozen(fitted, batches["evaluation"], expected_digest=fitted.decisions.digest)
    assert calls == dict.fromkeys(calls, 1)


def test_evaluation_labels_and_future_values_cannot_change_frozen_decisions() -> None:
    """Cambios futuros dejan idénticos modelo, calibrador, selección y digest."""
    plan, batches = make_procedure()
    spec = AdapterSpec("signal_double", "1")
    fitted = fit_procedure(batches, plan, spec, make_registry(), threshold_policy())
    changed = dict(batches)
    X = batches["evaluation"].X.copy()
    X["rain_mm_month_sum"] += 1000
    changed["evaluation"] = replace(
        batches["evaluation"], X=X, read_y=lambda: 1 - batches["evaluation"].read_y()
    )
    again = fit_procedure(changed, plan, spec, make_registry(), threshold_policy())
    assert fitted.decisions.to_json() == again.decisions.to_json()
    assert fitted.model.adapter.mean == again.model.adapter.mean
    # Las etiquetas de selección de umbral tampoco pueden reajustar etapas previas.
    changed["threshold_selection"] = replace(
        batches["threshold_selection"], read_y=lambda: 1 - batches["threshold_selection"].read_y()
    )
    altered = fit_procedure(changed, plan, spec, make_registry(), threshold_policy())
    assert fitted.decisions.coefficient == altered.decisions.coefficient
    assert fitted.decisions.intercept == altered.decisions.intercept
    assert fitted.decisions.representation == altered.decisions.representation
    assert fitted.decisions.train_prevalence == altered.decisions.train_prevalence


@pytest.mark.parametrize(
    "fault",
    [
        "origin_2025",
        "target_2025",
        "label_available_2025",
        "late",
        "overlap",
        "ineligible",
        "current_excess",
    ],
)
def test_preflight_rejects_before_any_label_reader_or_fit(fault: str) -> None:
    """2025 y transiciones inválidas se rechazan antes de cualquier consumidor."""
    plan, batches = make_procedure(2)
    batch = batches["evaluation"]
    keys, controls, X = batch.keys.copy(), batch.controls.copy(), batch.X.copy()
    if fault.endswith("2025"):
        name = {
            "origin_2025": "origin_period",
            "target_2025": "target_period",
            "label_available_2025": "label_available_period",
        }[fault]
        keys.loc[0, name] = "2025-01"
    elif fault == "late":
        batch = batches["threshold_selection"]
        keys, controls, X = batch.keys.copy(), batch.controls.copy(), batch.X.copy()
        keys["label_available_period"] = "2021-01"
    elif fault == "overlap":
        keys = batches["threshold_selection"].keys.copy()
        controls = batches["threshold_selection"].controls.copy()
        X = batches["threshold_selection"].X.copy()
    elif fault == "ineligible":
        controls.loc[0, "eligible_at_t"] = False
    else:
        X.loc[0, "zona_canal_t"] = "EXCESO"
    batches[batch.role] = replace(batch, keys=keys, controls=controls, X=X)
    calls = []

    def forbidden() -> pd.Series:
        """Cualquier lectura de etiquetas antes del rechazo sería fuga."""
        calls.append("labels")
        pytest.fail("Etiqueta consultada antes del rechazo")

    batches = {name: replace(value, read_y=forbidden) for name, value in batches.items()}
    registry = ModelRegistry()

    def builder(spec: AdapterSpec) -> SignalAdapter:
        """No puede crearse un modelo antes de validar todo el calendario."""
        calls.append("fit")
        pytest.fail("Se inició un consumidor antes del rechazo")

    registry.register("spy", "1", builder)
    with pytest.raises(ValueError):
        fit_procedure(batches, plan, AdapterSpec("spy", "1"), registry, threshold_policy())
    assert calls == []


@pytest.mark.parametrize("role", ROLES[:-1])
def test_missing_or_single_class_labels_rejected_without_coercion(role: str) -> None:
    """Ningún rol puede convertir desconocido en cero ni omitir soporte exigido."""
    plan, batches = make_procedure()
    for fault in ("missing", "single_class"):
        y = batches[role].read_y()
        if fault == "missing":
            y.iloc[0] = pd.NA
        else:
            y[:] = 0
        changed = {**batches, role: replace(batches[role], read_y=lambda values=y: values)}
        with pytest.raises(ValueError, match="Etiquetas"):
            fit_procedure(
                changed,
                plan,
                AdapterSpec("signal_double", "1"),
                make_registry(),
                threshold_policy(),
            )


def test_roles_are_disjoint_ordered_and_embargo_is_not_training() -> None:
    """Validar por objetivos y disponibilidad real, no por origen solamente."""
    plan, batches = make_procedure(2)
    audit = preflight_roles(batches, plan)
    target_sets = [set(batches[role].keys.target_period) for role in ROLES]
    for left, right in zip(target_sets, target_sets[1:]):
        assert max(left) < min(right) and not left & right
    assert all(row["embargo_end"] < row["first_consumer_origin"] for row in audit["transitions"])
    assert "2019-01" not in set().union(*target_sets)
    with pytest.raises(ValueError, match="Disponibilidad"):
        preflight_roles(batches, replace(plan, embargo_months=3))
    windows = list(plan.windows)
    windows[2] = replace(windows[2], start=windows[1].end)
    with pytest.raises(ValueError, match="solapados"):
        replace(plan, windows=tuple(windows))
    with pytest.raises(ValueError, match="Soporte"):
        preflight_roles(batches, replace(plan, min_months=7))


def test_direct_label_reader_cannot_bypass_reserved_boundary() -> None:
    """La función directa vuelve a comprobar claves antes de invocar el callback."""
    plan, batches = make_procedure()
    batch = batches["train"]
    keys = batch.keys.copy()
    keys.loc[0, "target_period"] = "2025-01"
    calls = []

    def forbidden() -> pd.Series:
        """Detectar lectura de etiqueta reservada incluso fuera de fit_procedure."""
        calls.append(True)
        pytest.fail("Etiqueta reservada leída")

    with pytest.raises(ValueError, match="reservado"):
        role_labels(replace(batch, keys=keys, read_y=forbidden), plan)
    assert calls == []


def test_prevalence_train_only_and_persistence_share_all_keys() -> None:
    """Referencias no ven etiquetas futuras y no reducen la cohorte del candidato."""
    plan, batches = make_procedure()
    train_prevalence = float(batches["train"].read_y().mean())
    fitted = fit_procedure(
        batches, plan, AdapterSpec("signal_double", "1"), make_registry(), threshold_policy()
    )
    # Evaluación puede tener ausencia real de etiqueta: no se consulta ni se imputa.
    unavailable = batches["evaluation"].read_y()
    unavailable.iloc[0] = pd.NA
    evaluation = replace(batches["evaluation"], read_y=lambda: unavailable)
    result = predict_frozen(fitted, evaluation, expected_digest=fitted.decisions.digest)
    assert result.prevalence_probability.eq(train_prevalence).all()
    assert result.persistence_decision.eq(0).all()
    assert len(result.keys) == len(evaluation.keys) == len(unavailable)
    evaluable = unavailable.notna()
    for values in (
        result.raw_probability,
        result.probability,
        result.decision,
        result.prevalence_probability,
        result.persistence_decision,
    ):
        assert values.index.equals(result.keys.index)
        assert len(values.loc[evaluable]) == int(evaluable.sum())
    assert pd.isna(unavailable.iloc[0])


def test_grid_tie_rules_and_unavailable_denominator() -> None:
    """Grilla explícita: empates prefieren menos FP y después mayor umbral."""
    probability = pd.Series([0.8, 0.8, 0.1, 0.1])
    y = pd.Series([1, 1, 0, 0], dtype="Int64")
    policy = ThresholdPolicy((0.0, 0.5, 0.7, 0.9, 1.0), max_false_alarm_ratio=1.0)
    selected, grid = select_threshold(probability, y, policy)
    assert selected == 0.7
    assert grid[-1]["emitted_alerts"] == 0 and grid[-1]["false_alarm_ratio"] is None
    assert select_threshold(probability, y, policy) == (selected, grid)
    with pytest.raises(ValueError, match="factible"):
        select_threshold(
            pd.Series([0.5, 0.5]),
            pd.Series([0, 1]),
            ThresholdPolicy((0.0, 1.0), max_false_alarm_ratio=0.0),
        )


@pytest.mark.parametrize("grid", [(0.0, 0.5, 0.5, 1.0), (0.0, np.nan, 1.0), (1.0, 0.0), (0.2, 0.8)])
def test_invalid_threshold_policy(grid: tuple[float, ...]) -> None:
    """No se repara o reemplaza silenciosamente una política de umbral."""
    with pytest.raises(ValueError, match="Cuadrícula"):
        ThresholdPolicy(grid, max_false_alarm_ratio=1.0)


def test_calibration_choice_and_parameter_application() -> None:
    """Conservar original en empate y aplicar parámetros sin refit."""
    raw = pd.Series([0.9, 0.9, 0.9, 0.9])
    y = pd.Series([0, 1, 0, 1])
    assert choose_representation(raw, raw.copy(), y)[0] == "original"
    assert choose_representation(raw, pd.Series([0.5] * 4), y)[0] == "sigmoid"
    coefficient, intercept = fit_sigmoid(raw, y, 42)
    probability = apply_sigmoid(raw, coefficient, intercept)
    assert probability.between(0, 1).all()
    pd.testing.assert_series_equal(probability, apply_sigmoid(raw, coefficient, intercept))
    assert apply_sigmoid(pd.Series([0.0, 1.0]), 1e308, -1e308).between(0, 1).all()


def test_artifacts_are_frozen_serializable_repeatable_and_not_overridable() -> None:
    """Digest idéntico y aplicación repetida sin volver a ajustar o consultar y."""
    plan, batches = make_procedure()
    X_before = {name: batch.X.copy(deep=True) for name, batch in batches.items()}
    keys_before = {name: batch.keys.copy(deep=True) for name, batch in batches.items()}
    fitted = fit_procedure(
        batches, plan, AdapterSpec("signal_double", "1"), make_registry(), threshold_policy()
    )
    frozen = fitted.decisions
    restored = FrozenDecisions.from_json(frozen.to_json())
    assert restored == frozen and restored.digest == frozen.digest
    again = fit_procedure(
        batches, plan, AdapterSpec("signal_double", "1"), make_registry(), threshold_policy()
    )
    assert again.decisions.to_json() == frozen.to_json()
    first = predict_frozen(fitted, batches["evaluation"], expected_digest=frozen.digest)
    second = predict_frozen(
        replace(fitted, decisions=restored), batches["evaluation"], expected_digest=frozen.digest
    )
    for name in (
        "keys",
        "raw_probability",
        "probability",
        "decision",
        "prevalence_probability",
        "persistence_decision",
    ):
        left, right = getattr(first, name), getattr(second, name)
        if isinstance(left, pd.DataFrame):
            pd.testing.assert_frame_equal(left, right)
        else:
            pd.testing.assert_series_equal(left, right)
    with pytest.raises(FrozenInstanceError):
        frozen.threshold = 0.5
    with pytest.raises(ValueError, match="alterada"):
        replace(frozen, threshold=0.51)
    with pytest.raises(ValueError, match="override"):
        predict_frozen(fitted, batches["evaluation"], expected_digest="0" * 64)
    tampered = json.loads(frozen.to_json())
    tampered["payload"]["threshold"] = 0.51
    with pytest.raises(ValueError, match="Recibo"):
        FrozenDecisions.from_json(json.dumps(tampered))
    for name in ROLES:
        pd.testing.assert_frame_equal(batches[name].X, X_before[name])
        pd.testing.assert_frame_equal(batches[name].keys, keys_before[name])
