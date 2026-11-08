"""Fábrica S53 con datos artificiales: receta, soportes, deferencia y N=3 exacta."""

import copy
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from fixtures.experiment_fixture import make_experiment

from sat_dengue_pipeline.domain.canonical import KEYS, PREDICTORS, ROLE_ORDER
from sat_dengue_pipeline.experiments.roles import ROLES, RoleSupport
from sat_dengue_pipeline.factory import engine, execution
from sat_dengue_pipeline.factory.configuration import (
    adapter_spec,
    validate_configuration,
)
from sat_dengue_pipeline.models.xgboost import XGBoostOnsetAdapter


@pytest.fixture
def config():
    """Leer la configuración aprobada, sin adquirir datos ni abrir el caché real."""
    path = Path(__file__).parents[1] / "conf/base/parameters_experiment.yml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["factory_experiment"]


def test_document_configuration_and_recipe_are_identical(config):
    """Ningún parámetro difiere del bloque normativo aprobado o cae a defaults."""
    assert validate_configuration(config) == config
    from kedro.config import OmegaConfigLoader

    root = Path(__file__).parents[1]
    loaded = OmegaConfigLoader(str(root / "conf"), base_env="base", default_run_env="base")[
        "parameters"
    ]["factory_experiment"]
    assert loaded == config
    assert config["seed"] == 53 and config["horizons"] == [1, 2]
    assert config["predictors"] == PREDICTORS and len(PREDICTORS) == 33
    assert config["threshold"]["grid"] == [k / 200 for k in range(201)]
    assert config["threshold"]["max_false_alarm_ratio_by_horizon"] == {"1": 0.8, "2": 0.8}
    assert not config["preparation"]["variables_g"]
    assert not config["preparation"]["channel_budget"]
    for field in (
        "early_stopping",
        "hyperparameter_search",
        "class_balancing",
        "refit",
        "seed_selection",
    ):
        assert config["candidate"][field] is False
    changed = copy.deepcopy(config)
    changed["seed"] = 42
    with pytest.raises(ValueError, match="especificación"):
        validate_configuration(changed)


def test_fixed_zone_encoding_exact_order_and_float32(config):
    """Cuatro bits de zona en posición fija, sin aprender vocabulario o reordenar X."""
    model = XGBoostOnsetAdapter(adapter_spec(config))
    X = make_experiment(include_missing=False).X.iloc[:4].copy()
    X["zona_canal_t"] = ["EXITO", "SEGURIDAD", "ALERTA", "EXCESO"]
    before = X.copy(deep=True)
    matrix = model.matrix(X)
    index = PREDICTORS.index("zona_canal_t")
    np.testing.assert_array_equal(matrix[:, index : index + 4], np.eye(4, dtype=np.float32))
    assert matrix.shape == (4, 36) and matrix.dtype == np.float32
    pd.testing.assert_frame_equal(X, before)


@pytest.mark.parametrize("fault", ["null", "extra", "missing", "order", "unknown_zone"])
def test_adapter_rejects_bad_schema_before_fit(config, fault):
    """Rechazar entradas distintas de los 33 predictores canónicos completos."""
    data = make_experiment(include_missing=False)
    X = data.X.copy()
    if fault == "null":
        X.loc[0, "rain_mm_month_sum"] = np.nan
    elif fault == "extra":
        X["G"] = 1
    elif fault == "missing":
        X = X.drop(columns="month_of_year")
    elif fault == "order":
        X = X[list(X)[::-1]]
    else:
        X.loc[0, "zona_canal_t"] = "UNKNOWN"
    model = XGBoostOnsetAdapter(adapter_spec(config))
    with pytest.raises(ValueError):
        model.fit(X, data.y)
    assert model.fit_calls == 0


def test_native_model_complete_json_stable_and_no_refit(config, monkeypatch):
    """JSON incluye 80 árboles y parámetros; dos ajustes S53 coinciden exactamente."""
    import xgboost as xgb

    calls = []
    original = xgb.train

    def checked_train(**kwargs):
        """No permitir eval_set, callbacks, early stopping o parámetros no declarados."""
        assert set(kwargs) == {"params", "dtrain", "num_boost_round"}
        assert kwargs["params"] == config["candidate"]["parameters"]
        calls.append(True)
        return original(**kwargs)

    monkeypatch.setattr(xgb, "train", checked_train)
    data = make_experiment(include_missing=False)
    first = XGBoostOnsetAdapter(adapter_spec(config))
    second = XGBoostOnsetAdapter(adapter_spec(config))
    for model in (first, second):
        model.fit(data.X, data.y)
    assert first is not second and first.model_json() == second.model_json()
    assert first.model_sha256() == second.model_sha256()
    payload = json.loads(first.model_json())
    assert len(payload["model"]["learner"]["gradient_booster"]["model"]["trees"]) == 80
    assert payload["native_configuration"]["learner"]["generic_param"]["seed"] == "53"
    before = first.model_sha256()
    first.predict_positive(data.X)
    assert first.model_sha256() == before
    with pytest.raises(ValueError, match="Refit"):
        first.fit(data.X, data.y)
    assert len(calls) == 2
    changed = copy.deepcopy(config)
    changed["candidate"]["parameters"].pop("eta")
    with pytest.raises(ValueError, match="faltantes"):
        XGBoostOnsetAdapter(adapter_spec(changed))


@pytest.fixture
def prepared_run(config, tmp_path, monkeypatch):
    """Construir únicamente claves y features artificiales; instrumentar creación de y."""
    rows = []
    for code in ("50998", "73998"):
        for month in pd.period_range("2017-01", "2024-12", freq="M"):
            feature = {name: float(month.month) for name in PREDICTORS}
            feature["zona_canal_t"] = "SEGURIDAD"
            rows.append({"municipality_code": code, "year_month": str(month), **feature})
    table = pd.DataFrame(rows, columns=KEYS + PREDICTORS)
    schema = {"column_roles": {role: [] for role in ROLE_ORDER}}
    schema["column_roles"].update(key=KEYS, feature=PREDICTORS)
    created = []

    def deferred_labels(history, schema, origins, horizon, availability, policy):
        """No leer fuentes reales ni construir etiquetas de un rol antes de su callback."""
        created.append((horizon, str(origins.year_month.min())))
        labels = origins.copy()
        labels[f"y_t{horizon}"] = (
            origins.year_month.str[-2:].astype(int).mod(3).eq(0).astype("Int64")
        )
        return None, labels, None, None

    monkeypatch.setattr(engine, "prepare_horizon", deferred_labels)
    run = engine.FactoryRun(None, config, tmp_path, {}, table=table, schema=schema)
    return run, created


def _small_test_support(run):
    """Reducir solo el plan artificial del test, sin cambiar la configuración productiva."""
    for h in (1, 2):
        plan = run.plans[h]
        run.plans[h] = replace(
            plan,
            supports={role: RoleSupport(1, 1, 2, plan.supports[role].months) for role in ROLES},
        )


def test_evaluation_labels_created_only_after_both_predictions(prepared_run):
    """Espiar la construcción de y, no solamente un lector de y ya construido."""
    run, created = prepared_run
    engine.prepare(run)
    assert created == [] and run.label_reads == {}
    _small_test_support(run)
    with pytest.raises(engine.FactoryGateError, match="before_predictions"):
        run.batches[1]["evaluation"].read_y()
    engine.preflight(run)
    assert len(created) == 8 and all(":evaluation" not in k for k in run.label_reads)
    engine.fit(run)
    assert len(created) == 8
    assert run.fitted[1].model.adapter is not run.fitted[2].model.adapter
    engine.predict(run)
    assert len(created) == 8
    engine.evaluate(run)
    assert len(created) == 10
    assert all(run.label_reads[f"{h}:evaluation"] == 1 for h in (1, 2))
    assert all(run.fitted[h].model.adapter.fit_calls == 1 for h in (1, 2))


def test_inner_kedro_graph_preserves_state_and_loads_receipt(prepared_run, monkeypatch):
    """Ejecutar los siete nodos con fixture y cargar el dataset final de Kedro 1.7."""
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue_pipeline.pipelines.factory_validation.pipeline import create_run_pipeline

    run, created = prepared_run
    original_prepare = engine.prepare

    def prepare_small(context):
        """Usar exclusivamente soportes pequeños artificiales de esta prueba."""
        original_prepare(context)
        _small_test_support(context)
        return context

    monkeypatch.setattr(engine, "reconstruct", lambda context: context)
    monkeypatch.setattr(engine, "prepare", prepare_small)
    monkeypatch.setattr(engine, "receipt", lambda context: {"status": "PASSED"})
    graph = create_run_pipeline()
    datasets = {name: MemoryDataset(copy_mode="assign") for name in graph.datasets()}
    datasets["factory_context"] = MemoryDataset(run, copy_mode="assign")
    outputs = SequentialRunner().run(graph, DataCatalog(datasets))
    assert outputs["factory_receipt"].load() == {"status": "PASSED"}
    assert len(created) == 10 and len(run.results) == 2


def test_all_producer_support_validated_before_any_model(prepared_run):
    """Un fallo en T+2 deja ambos horizontes sin modelos, con conteos completos."""
    run, _ = prepared_run
    engine.prepare(run)
    _small_test_support(run)
    run.plans[2].supports["calibration_selection"] = RoleSupport(9999, 9999, 2, 6)
    with pytest.raises(engine.FactoryGateError, match="T2:calibration_selection"):
        engine.preflight(run)
    assert run.fitted == {} and len(run.support) == 2
    assert run.support["1"]["evaluation"]["n1"] is None


@pytest.mark.parametrize("fault", ["target_2025", "availability_2025", "embargo"])
def test_factory_temporal_fault_before_any_label_construction(prepared_run, fault):
    """Reutilizar guards por objetivo, disponibilidad y dependencia consumidora."""
    run, created = prepared_run
    run.config = copy.deepcopy(run.config)
    if fault == "target_2025":
        run.config["roles_by_horizon"]["2"]["evaluation"]["end"] = "2025-01"
    elif fault == "availability_2025":
        run.config["label_delay_months"] = 25
    else:
        run.config["embargo_months"] = 3
    with pytest.raises(ValueError):
        engine.prepare(run)
        _small_test_support(run)
        engine.preflight(run)
    assert created == [] and run.fitted == {}


def test_evaluation_support_failure_is_after_prediction_and_has_no_retry(prepared_run):
    """Fallo posterior no realimenta fit ni vuelve a leer etiquetas o seleccionar."""
    run, _ = prepared_run
    engine.prepare(run)
    _small_test_support(run)
    engine.preflight(run)
    engine.fit(run)
    engine.predict(run)
    run.plans[2].supports["evaluation"] = RoleSupport(9999, 9999, 2, 11)
    with pytest.raises(engine.FactoryGateError, match="evaluation_support_failed"):
        engine.evaluate(run)
    assert all(run.fitted[h].model.adapter.fit_calls == 1 for h in (1, 2))
    assert run.results == {} and run.label_reads["2:evaluation"] == 1


@pytest.mark.parametrize("fault", ["gate", "divergence"])
def test_n3_stops_without_third_or_fourth_attempt(config, monkeypatch, tmp_path, fault):
    """Un fallo o divergencia produce NOT_EXECUTED, nunca se oculta con otro intento."""
    calls = []

    def isolated(bundle, cfg, directory):
        calls.append(directory)
        assert list(directory.iterdir()) == []
        n = len(calls)
        if fault == "gate":
            return {"status": "FAILED", "gate": "producer_support"}
        return {
            "status": "PASSED",
            "identity": {"hash": str(n)},
            "identity_sha256": str(n),
            "operation": {"pid": n},
        }

    monkeypatch.setattr(execution, "project_root", lambda: tmp_path)
    monkeypatch.setattr(execution, "isolated_run", isolated)
    result = execution.reproduce({"configuration": config, "bundle": object(), "acquisition": {}})
    assert result["status"] == "BLOCKED"
    assert len(calls) == (1 if fault == "gate" else 2)
    assert result["records"][-1]["status"] == "NOT_EXECUTED"


def test_immutable_writer_cannot_replace_evidence(tmp_path):
    """Abrir exclusivamente sin truncar ningún recibo existente."""
    path = tmp_path / "run-1.json"
    execution._exclusive_json(path, {"status": "PASSED"})
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        execution._exclusive_json(path, {"status": "FAILED"})
    assert path.read_bytes() == before
