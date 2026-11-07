"""Contrato de adaptadores: aislamiento, esquema y probabilidades enlazadas."""

import inspect
import json
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from fixtures.adapter_fixture import SignalAdapter, make_registry
from fixtures.experiment_fixture import make_experiment

from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.experiments.rolling import ExperimentSpec, build_folds, fold_inputs
from sat_dengue_pipeline.models.adapters import (
    PREDICTION_KEYS,
    AdapterSpec,
    CheckedAdapter,
    ModelAdapter,
    ModelRegistry,
    run_candidate,
    validate_features,
    validate_predictions,
)


def test_adapters_share_harness_and_keep_labels_separate() -> None:
    """Dos familias comparten calendario/enlaces sin duplicar evaluación."""
    data, experiment = make_experiment(), ExperimentSpec(1, last_target="2019-04")
    predictions = []
    for family in ("signal_double", "constant_double"):
        spec = AdapterSpec(family, "1")
        result, audit = run_candidate(data, experiment, spec, make_registry())
        predictions.append(result)
        assert list(result) == [*PREDICTION_KEYS, "candidate", "raw_probability"]
        assert result.candidate.eq(spec.candidate).all()
        assert result.raw_probability.between(0, 1).all()
        assert len(audit["adapters"]) == len(build_folds(experiment))
        assert all(row["fitted"] and row["features"] == PREDICTORS for row in audit["adapters"])
        assert all(row["seed"] == experiment.seed for row in audit["adapters"])
        json.dumps(audit, allow_nan=False)
    pd.testing.assert_frame_equal(predictions[0][PREDICTION_KEYS], predictions[1][PREDICTION_KEYS])
    assert not predictions[0].raw_probability.equals(predictions[1].raw_probability)
    assert list(inspect.signature(ModelAdapter.predict_positive).parameters) == ["self", "X"]


def test_only_authorized_fold_reaches_fit_and_inference() -> None:
    """Los espías reciben solo filas maduras y ninguna etiqueta en inferencia."""
    data, experiment = make_experiment(2), ExperimentSpec(2, last_target="2019-05")
    fitted, inferred, instances = [], [], []

    class SpyAdapter(SignalAdapter):
        """Registrar copias de entradas por instancia."""

        def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
            """Capturar X/y antes del ajuste artificial."""
            fitted.append((X.copy(), y.copy()))
            super().fit(X, y)

        def predict_positive(self, X: pd.DataFrame) -> pd.Series:
            """Capturar exclusivamente X de inferencia."""
            inferred.append(X.copy())
            return super().predict_positive(X)

    def builder(spec: AdapterSpec) -> SpyAdapter:
        """Crear una instancia observable nueva."""
        model = SpyAdapter(spec)
        instances.append(model)
        return model

    registry = ModelRegistry()
    registry.register("spy", "1", builder)
    run_candidate(data, experiment, AdapterSpec("spy", "1"), registry)
    assert len({id(instance) for instance in instances}) == len(build_folds(experiment))
    for fold, (X, y), inference in zip(build_folds(experiment), fitted, inferred, strict=True):
        train, validation = fold_inputs(data, experiment, fold)
        pd.testing.assert_frame_equal(X, train.X)
        pd.testing.assert_series_equal(y, train.y)
        pd.testing.assert_frame_equal(inference, validation.X)


@pytest.mark.parametrize(
    "fault", ["null", "inf", "negative", "above_one", "length", "index", "string"]
)
def test_invalid_probability_rejected(fault: str) -> None:
    """Fallar antes de devolver una predicción inválida o desalineada."""
    data = make_experiment()

    class Broken(SignalAdapter):
        """Doble que emite una salida defectuosa deliberadamente."""

        def predict_positive(self, X: pd.DataFrame) -> pd.Series:
            """Inyectar un defecto en la probabilidad."""
            probability = super().predict_positive(X)
            if fault == "length":
                return probability.iloc[:-1]
            if fault == "index":
                return probability.set_axis(probability.index + 1)
            if fault == "string":
                return probability.astype(str)
            probability.iloc[0] = {
                "null": np.nan,
                "inf": np.inf,
                "negative": -0.1,
                "above_one": 1.1,
            }[fault]
            return probability

    registry = ModelRegistry()
    registry.register("broken", "1", Broken)
    with pytest.raises(ValueError, match="Probabilidades"):
        run_candidate(
            data, ExperimentSpec(1, last_target="2019-03"), AdapterSpec("broken", "1"), registry
        )


@pytest.mark.parametrize(
    "name",
    [
        "y_t1",
        "target_period_t1",
        "onset_target",
        "eligible_at_t",
        "p75_t1",
        "excess_target",
        "future_count",
        "future_available",
    ],
)
def test_future_control_or_label_not_in_X(name: str) -> None:
    """La allowlist cerrada impide equivalentes futuros y controles."""
    X = make_experiment().X.iloc[2:5].copy()
    X[name] = 0
    with pytest.raises(ValueError, match="Esquema"):
        validate_features(X)


def test_order_and_dtypes_are_frozen() -> None:
    """El contrato exige el mismo orden y tipos durante inferencia."""
    data = make_experiment()
    experiment = ExperimentSpec(1, last_target="2019-03")
    train, validation = fold_inputs(data, experiment, build_folds(experiment)[0])
    checked = CheckedAdapter(SignalAdapter(AdapterSpec("signal_double", "1")))
    with pytest.raises(ValueError, match="antes de ajustar"):
        checked.predict_positive(validation.X)
    checked.fit(train.X, train.y)
    with pytest.raises(ValueError, match="Esquema"):
        checked.predict_positive(validation.X.iloc[:, ::-1])
    changed = validation.X.copy()
    changed["month_of_year"] = changed.month_of_year.astype(float)
    with pytest.raises(ValueError, match="Tipos"):
        checked.predict_positive(changed)
    with pytest.raises(ValueError, match="reutilizar"):
        checked.fit(train.X, train.y)


@pytest.mark.parametrize("stage", ["fit_X", "fit_y", "predict_X"])
def test_mutating_adapter_rejected_without_mutating_source(stage: str) -> None:
    """Un backend defectuoso solo toca copias y se rechaza explícitamente."""
    data = make_experiment()
    X_before, y_before = data.X.copy(), data.y.copy()

    class Mutator(SignalAdapter):
        """Intentar mutar entradas del contrato."""

        def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
            """Ajustar y después alterar una entrada."""
            super().fit(X, y)
            if stage == "fit_X":
                X.iloc[0, 0] = 999
            if stage == "fit_y":
                y.iloc[0] = 1 - y.iloc[0]

        def predict_positive(self, X: pd.DataFrame) -> pd.Series:
            """Alterar X tras producir una predicción válida."""
            probability = super().predict_positive(X)
            if stage == "predict_X":
                X.iloc[0, 0] = 999
            return probability

    registry = ModelRegistry()
    registry.register("mutator", "1", Mutator)
    with pytest.raises(ValueError, match="mutó"):
        run_candidate(
            data, ExperimentSpec(1, last_target="2019-03"), AdapterSpec("mutator", "1"), registry
        )
    pd.testing.assert_frame_equal(data.X, X_before)
    pd.testing.assert_series_equal(data.y, y_before)


def test_configuration_seed_and_serialization_reproducible() -> None:
    """Misma configuración canónica y semilla producen exactamente lo mismo."""
    data, experiment = make_experiment(), ExperimentSpec(1, last_target="2019-04")
    spec = AdapterSpec("signal_double", "1", '{ "scale" : 0.7 }')
    assert spec == AdapterSpec("signal_double", "1", '{"scale":0.7}')
    first, audit = run_candidate(data, experiment, spec, make_registry())
    second, again = run_candidate(data, experiment, spec, make_registry())
    pd.testing.assert_frame_equal(first, second)
    assert json.dumps(audit, sort_keys=True) == json.dumps(again, sort_keys=True)
    changed, _ = run_candidate(
        data, replace(experiment, seed=43), replace(spec, seed=43), make_registry()
    )
    assert not first.raw_probability.equals(changed.raw_probability)


@pytest.mark.parametrize("fault", ["key", "length", "candidate", "label_column"])
def test_prediction_batch_linkage_rejected(fault: str) -> None:
    """Conservar exactamente candidato, municipio, horizonte, origen y fold."""
    spec = AdapterSpec("signal_double", "1")
    frame, _ = run_candidate(
        make_experiment(), ExperimentSpec(1, last_target="2019-03"), spec, make_registry()
    )
    keys = frame[PREDICTION_KEYS].copy()
    if fault == "key":
        frame.loc[0, "municipality_code"] = "73998"
    elif fault == "length":
        frame = frame.iloc[:-1]
    elif fault == "candidate":
        frame.loc[0, "candidate"] = "other"
    else:
        frame["y_true"] = 1
    with pytest.raises(ValueError, match="inconsistentes"):
        validate_predictions(frame, keys, spec.candidate)


def test_factory_rejects_reuse_and_failure_does_not_contaminate_next_run() -> None:
    """Un fallo aborta sin devolver salidas parciales y una corrida nueva sigue limpia."""
    data, experiment = make_experiment(), ExperimentSpec(1, last_target="2019-04")
    expected, _ = run_candidate(
        data, experiment, AdapterSpec("signal_double", "1"), make_registry()
    )
    registry = ModelRegistry()
    shared = SignalAdapter(AdapterSpec("shared", "1"))
    registry.register("shared", "1", lambda spec: shared)
    with pytest.raises(ValueError, match="previamente ajustado"):
        run_candidate(data, experiment, shared.spec, registry)
    after, _ = run_candidate(data, experiment, AdapterSpec("signal_double", "1"), make_registry())
    pd.testing.assert_frame_equal(expected, after)


def test_empty_registry_and_invalid_configuration_fail_closed() -> None:
    """No hay frameworks implícitos, configuración ejecutable ni registro silencioso."""
    with pytest.raises(ValueError, match="no registrada"):
        make_registry().create(AdapterSpec("xgboost", "1"))
    for config in ("[]", '{"bad":NaN}'):
        with pytest.raises(ValueError):
            AdapterSpec("test", "1", config)
    with pytest.raises(ValueError, match="duplicada"):
        registry = make_registry()
        registry.register("signal_double", "1", SignalAdapter)
