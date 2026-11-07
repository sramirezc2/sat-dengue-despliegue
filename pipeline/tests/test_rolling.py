"""Calendario expansivo, madurez, determinismo y aislamiento de los folds."""

from dataclasses import replace

import pandas as pd
import pytest
from fixtures.experiment_fixture import DeterministicDouble, make_experiment

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import build_table
from sat_dengue_pipeline.experiments.rolling import (
    ExperimentData,
    ExperimentSpec,
    build_folds,
    calendar_audit,
    fold_inputs,
    from_prepared,
    run_rolling,
    stable_digest,
    validate_data,
)
from sat_dengue_pipeline.preparation import PREDICTOR_AVAILABILITY, prepare_horizon


@pytest.mark.parametrize("horizon", [1, 2])
def test_expanding_calendar_and_mature_disjoint_inputs(horizon: int) -> None:
    """Cada ventana aumenta y ninguna etiqueta llega en o después del consumo."""
    data, spec = make_experiment(horizon), ExperimentSpec(horizon)
    folds = build_folds(spec)
    assert len(folds) == (71 if horizon == 1 else 70)
    previous = set()
    for fold in folds:
        train, validation = fold_inputs(data, spec, fold)
        keys = set(
            train.keys[["municipality_code", "origin_period"]].itertuples(index=False, name=None)
        )
        assert previous < keys
        previous = keys
        assert train.keys.target_period.lt(fold.origin_period).all()
        assert train.keys.label_available_period.lt(fold.origin_period).all()
        assert validation.keys.origin_period.eq(fold.origin_period).all()
        assert validation.keys.target_period.eq(add_months(fold.origin_period, horizon)).all()
        assert not keys & set(
            validation.keys[["municipality_code", "origin_period"]].itertuples(
                index=False, name=None
            )
        )
        assert train.y.notna().all() and validation.y.isna().all()
    assert folds[-1].target_period == "2024-12"
    assert data.y.isna().sum() == 1 and data.X.isna().sum().sum() == 1


@pytest.mark.parametrize("horizon", [1, 2])
def test_reordering_and_future_changes_do_not_affect_prior_folds(horizon: int) -> None:
    """Resultados anteriores son idénticos pese a orden físico o cambios futuros."""
    data = make_experiment(horizon)
    spec = ExperimentSpec(horizon, first_origin="2019-01", last_target="2019-08")
    expected, audit = run_rolling(data, spec, DeterministicDouble)
    order = data.keys.sample(frac=1, random_state=71).index
    shuffled = ExperimentData(
        *(
            obj.loc[order].reset_index(drop=True)
            for obj in (data.keys, data.X, data.y, data.controls)
        )
    )
    actual, shuffled_audit = run_rolling(shuffled, spec, DeterministicDouble)
    pd.testing.assert_frame_equal(expected, actual)
    assert audit == shuffled_audit
    changed_X, changed_y = data.X.copy(), data.y.copy()
    future = data.keys.origin_period.ge("2020-01")
    changed_X.loc[future, "month_of_year"] = 999
    changed_y.loc[future] = 1
    changed = replace(data, X=changed_X, y=changed_y)
    again, _ = run_rolling(changed, spec, DeterministicDouble)
    pd.testing.assert_frame_equal(expected, again)


def test_label_availability_is_not_inferred_from_target_alone() -> None:
    """Una etiqueta retrospectiva tardía se excluye aunque su objetivo ya pasó."""
    data = make_experiment()
    keys = data.keys.copy()
    keys.loc[0, "label_available_period"] = "2019-01"
    delayed = replace(data, keys=keys)
    spec = ExperimentSpec(1, last_target="2019-03")
    first, later = build_folds(spec)
    train, _ = fold_inputs(delayed, spec, first)
    assert not (
        (train.keys.municipality_code == "50998") & (train.keys.origin_period == "2018-01")
    ).any()
    next_train, _ = fold_inputs(delayed, spec, later)
    assert len(next_train.X) > len(train.X)
    assert (
        (next_train.keys.municipality_code == "50998")
        & (next_train.keys.origin_period == "2018-01")
    ).any()


def test_factory_instances_are_new_and_inputs_not_mutated() -> None:
    """El arnés no reutiliza estado y conserva las entradas originales."""
    data = make_experiment()
    before = [obj.copy(deep=True) for obj in (data.keys, data.X, data.y, data.controls)]
    spec = ExperimentSpec(1, last_target="2019-04")
    models = []

    def factory() -> DeterministicDouble:
        """Registrar las instancias vivas de cada fold."""
        model = DeterministicDouble()
        models.append(model)
        return model

    predictions, audit = run_rolling(data, spec, factory)
    assert len(models) == len(build_folds(spec)) == len({id(model) for model in models})
    assert predictions.municipality_code.unique().tolist() == ["50998", "73998"]
    assert "y_true" not in predictions and "y_t1" not in predictions
    assert audit["digest"] == calendar_audit(spec)["digest"]
    for actual, original in zip((data.keys, data.X, data.y, data.controls), before, strict=True):
        if isinstance(actual, pd.Series):
            pd.testing.assert_series_equal(actual, original)
        else:
            pd.testing.assert_frame_equal(actual, original)
    shared = DeterministicDouble()
    with pytest.raises(ValueError, match="instancia nueva"):
        run_rolling(data, spec, lambda: shared)


@pytest.mark.parametrize(
    "fault", ["origin", "target", "available", "duplicate", "calendar", "features", "alignment"]
)
def test_bad_input_rejected_before_model_factory(fault: str) -> None:
    """Ningún ajuste puede comenzar ante claves, calendario o roles inválidos."""
    data = make_experiment()
    keys, X = data.keys.copy(), data.X.copy()
    if fault in {"origin", "target", "available"}:
        column = {
            "origin": "origin_period",
            "target": "target_period",
            "available": "label_available_period",
        }[fault]
        keys.loc[0, column] = "2025-01"
    elif fault == "duplicate":
        keys.loc[1] = keys.iloc[0]
    elif fault == "calendar":
        keys.loc[0, "target_period"] = "2018-04"
    elif fault == "features":
        X["y_t1"] = 0
    else:
        X.index = X.index + 1
    calls = []

    def factory() -> DeterministicDouble:
        """No debe alcanzarse este consumidor."""
        calls.append(True)
        return DeterministicDouble()

    with pytest.raises(ValueError):
        run_rolling(replace(data, keys=keys, X=X), ExperimentSpec(1), factory)
    assert calls == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"last_target": "2025-01"},
        {"first_origin": "2025-01"},
        {"horizon": 3},
        {"label_delay_months": -1},
        {"train_target_start": "2019-02"},
    ],
)
def test_invalid_protocol(kwargs: dict[str, object]) -> None:
    """Rechazar protocolos sin madurez o con horizonte reservado."""
    with pytest.raises(ValueError):
        ExperimentSpec(**{"horizon": 1, **kwargs})


def test_calendar_digest_and_preparation_bridge() -> None:
    """El digest no depende de filas; el enlace respeta el contrato de tarea 7."""
    from fixtures.canonical_fixture import make_panel

    spec = ExperimentSpec(2)
    first, second = calendar_audit(spec), calendar_audit(spec)
    assert first == second
    assert first["digest"] == stable_digest({k: v for k, v in first.items() if k != "digest"})
    assert calendar_audit(replace(spec, seed=7))["digest"] != first["digest"]
    table, schema = build_table(make_panel())
    origins = table.loc[
        table.year_month.between("2023-01", "2024-10"), ["municipality_code", "year_month"]
    ]
    _, _, prepared, _ = prepare_horizon(table, schema, origins, 2, PREDICTOR_AVAILABILITY)
    data = from_prepared(prepared, 2)
    validate_data(data, 2)
    pd.testing.assert_frame_equal(data.X, prepared.X)
    pd.testing.assert_series_equal(data.y, prepared.y)
