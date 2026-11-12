"""Pesos cerrados, ajuste exclusivo y comparación emparejada de EXP004."""

import copy
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml
from fixtures.experiment_fixture import make_experiment
from fixtures.procedure_fixture import make_procedure, threshold_policy
from fixtures.scientific_fixture import repository

from sat_dengue_pipeline.evaluation.scientific.configuration import (
    variants,
    verify_weighting_cohorts,
)
from sat_dengue_pipeline.experiment_management import runner
from sat_dengue_pipeline.experiment_management.configuration import validate_configuration
from sat_dengue_pipeline.experiment_management.evidence import verify_execution
from sat_dengue_pipeline.experiments.procedure import fit_procedure
from sat_dengue_pipeline.experiments.rolling import ExperimentSpec, build_folds, fold_inputs
from sat_dengue_pipeline.experiments.weighting import training_weights, validate_weighting
from sat_dengue_pipeline.factory.configuration import adapter_spec
from sat_dengue_pipeline.models.adapters import ModelRegistry, run_candidate
from sat_dengue_pipeline.models.logistic import LogisticOnsetAdapter
from sat_dengue_pipeline.pipelines.retroanalisis.nodes import verificar_conjuntos
from sat_dengue_pipeline.raw.contract import sha256

ROOT = Path(__file__).resolve().parents[2]
UNIFORM = {"method": "uniform"}
RECENT = {"method": "exponential_recency", "half_life_months": 36}


def logistic_recipe() -> dict:
    """Leer la referencia climática vigente; ningún parámetro reconstruido de memoria."""
    return yaml.safe_load(
        (ROOT / "pipeline/conf/retroanalisis/noche/log_conclima.yml").read_text(encoding="utf-8")
    )


def registry() -> ModelRegistry:
    """Crear el registro mínimo del adaptador real."""
    models = ModelRegistry()
    models.register("logistic_onset", "v1", LogisticOnsetAdapter)
    return models


def test_formula_normalization_and_latest_raw_weight() -> None:
    """La vida media reduce a la mitad el peso crudo, conservando media aplicada uno."""
    keys = pd.DataFrame({"target_period": ["2018-01", "2021-01", "2024-01"]})
    weights, summary = training_weights(keys, RECENT)
    np.testing.assert_allclose(weights, np.array([0.25, 0.5, 1.0]) / (1.75 / 3))
    assert summary["raw_latest_weight"] == 1
    assert weights.is_monotonic_increasing
    assert weights.mean() == pytest.approx(1)
    assert summary["reference_target"] == "2024-01"
    assert training_weights(keys, RECENT)[1] == summary
    assert "weights" not in summary and "keys" not in summary


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {},
        {"method": "linear"},
        {"method": "uniform", "x": 1},
        {"method": "uniform", "half_life_months": 36},
        {"method": "exponential_recency"},
        {"method": "exponential_recency", "half_life_months": 0},
        {"method": "exponential_recency", "half_life_months": 12},
        {"method": "exponential_recency", "half_life_months": 36.0},
        {**RECENT, "normalize": False},
    ],
)
def test_invalid_policy_rejected(bad: object) -> None:
    """Ni claves extra ni otra vida media son opciones de EXP004."""
    with pytest.raises(ValueError):
        validate_weighting(bad)


@pytest.mark.parametrize("column", ["origin_period", "target_period", "label_available_period"])
def test_reserved_year_rejected(column: str) -> None:
    """Ningún tipo de periodo 2025 entra al cálculo de pesos."""
    keys = pd.DataFrame(
        {name: ["2024-01"] for name in ["origin_period", "target_period", "label_available_period"]}
    )
    keys[column] = "2025-01"
    with pytest.raises(ValueError, match="reservado"):
        training_weights(keys, RECENT)


def test_only_mature_fold_history_sets_reference_and_weights() -> None:
    """Un objetivo reciente con etiqueta tardía y las filas futuras no fijan la edad."""
    data = make_experiment(include_missing=False)
    spec = ExperimentSpec(1, first_origin="2019-01", last_target="2019-02")
    late = data.keys.target_period.eq("2018-12")
    keys = data.keys.copy()
    keys.loc[late, "label_available_period"] = "2019-02"
    train, _ = fold_inputs(replace(data, keys=keys), spec, build_folds(spec)[0])
    weights, summary = training_weights(train.keys, RECENT)
    assert summary["reference_target"] == "2018-11"
    assert train.keys.label_available_period.lt("2019-01").all()
    changed = data.keys.copy()
    changed.loc[changed.origin_period.ge("2020-01"), "label_available_period"] = "2024-12"
    again, _ = fold_inputs(replace(data, keys=changed), spec, build_folds(spec)[0])
    expected, _ = training_weights(again.keys, RECENT)
    assert weights.mean() == pytest.approx(expected.mean())
    assert expected.max() / expected.min() == pytest.approx(2 ** (10 / 36))


def test_uniform_equivalent_and_weighted_rolling_reproducible() -> None:
    """El arnés conserva predicciones anteriores con uniform y audita filas idénticas."""
    data = make_experiment(include_missing=False)
    config = logistic_recipe()
    spec = ExperimentSpec(1, first_origin="2019-01", last_target="2019-04", seed=config["seed"])
    adapter = adapter_spec(config)
    old, _ = run_candidate(data, spec, adapter, registry())
    uniform, ua = run_candidate(data, spec, adapter, registry(), training_weighting=UNIFORM)
    recent, ra = run_candidate(data, spec, adapter, registry(), training_weighting=RECENT)
    repeat, repeated = run_candidate(data, spec, adapter, registry(), training_weighting=RECENT)
    pd.testing.assert_frame_equal(old, uniform)
    pd.testing.assert_frame_equal(recent, repeat)
    assert ra == repeated
    for left, right in zip(ua["support"], ra["support"], strict=True):
        for key in ("training_keys_sha256", "training_labels_sha256", "prediction_keys_sha256"):
            assert left[key] == right[key]
        assert right["training_weighting"]["mean"] == pytest.approx(1)


def test_procedure_weights_only_model_and_keeps_preparation_unweighted(monkeypatch) -> None:
    """El modelo real recibe sample_weight; calibrador y selector mantienen su interfaz."""
    plan, batches = make_procedure()
    config = logistic_recipe()
    seen = []
    original = LogisticOnsetAdapter.fit

    def observe(model, X, y, *, sample_weight=None):
        """Observar sin sustituir el optimizador logístico."""
        seen.append(sample_weight)
        original(model, X, y, sample_weight=sample_weight)

    monkeypatch.setattr(LogisticOnsetAdapter, "fit", observe)
    baseline = fit_procedure(batches, plan, adapter_spec(config), registry(), threshold_policy())
    fitted = fit_procedure(
        batches,
        plan,
        adapter_spec(config),
        registry(),
        threshold_policy(),
        training_weighting=RECENT,
    )
    assert seen[0] is None and seen[1] is not None and len(seen) == 2
    expected, summary = training_weights(batches["train"].keys, RECENT)
    pd.testing.assert_series_equal(seen[1], expected)
    trace = json.loads(fitted.decisions.trace_json)
    assert trace["training_weighting"] == summary
    assert trace["input_digests"] == json.loads(baseline.decisions.trace_json)["input_digests"]
    np.testing.assert_array_equal(baseline.model.adapter._mean, fitted.model.adapter._mean)
    np.testing.assert_array_equal(baseline.model.adapter._std, fitted.model.adapter._std)


def test_cohort_gate_catches_keys_features_and_labels() -> None:
    """La comparación falla antes del ajuste si algún brazo cambia las filas o y."""
    _, batches = make_procedure()
    config = {
        "training_weighting": UNIFORM,
        "scientific_dimensions": {
            "cut": "c",
            "seed": 53,
            "population": "common",
            "reading": "primary",
        },
    }
    first = SimpleNamespace(config=config, batches={1: batches})
    second = SimpleNamespace(config=copy.deepcopy(config), batches={1: copy.copy(batches)})
    verify_weighting_cohorts({"uniform": first, "recent": second})
    y = batches["train"].read_y()
    second.batches[1]["train"] = replace(batches["train"], read_y=lambda: 1 - y)
    with pytest.raises(ValueError, match="etiquetas"):
        verify_weighting_cohorts({"uniform": first, "recent": second})
    X = batches["train"].X.copy()
    X.loc[0, "month_of_year"] = 99
    second.batches[1]["train"] = replace(batches["train"], X=X)
    with pytest.raises(ValueError, match="predictores"):
        verify_weighting_cohorts({"uniform": first, "recent": second})
    keys = batches["train"].keys.copy()
    keys.iloc[0, 0] = "50997"
    second.batches[1]["train"] = replace(batches["train"], keys=keys)
    with pytest.raises(ValueError, match="claves"):
        verify_weighting_cohorts({"uniform": first, "recent": second})


def test_csv_comparison_rejects_different_sets() -> None:
    """conjunto.csv verifica claves y etiquetas por horizonte, semilla y fold."""
    row = dict(
        horizonte=1,
        seed=53,
        fold_id="f",
        train_rows=10,
        prediction_rows=2,
        training_keys_sha256="a",
        training_labels_sha256="b",
        prediction_keys_sha256="c",
        evaluation_labels_sha256="d",
    )
    frame = pd.DataFrame([{**row, "receta": "uniform"}, {**row, "receta": "recent"}])
    verificar_conjuntos(frame, 2)
    for field in [
        "training_keys_sha256",
        "training_labels_sha256",
        "prediction_keys_sha256",
        "evaluation_labels_sha256",
        "fold_id",
    ]:
        bad = frame.copy()
        bad.loc[1, field] = "changed"
        with pytest.raises(ValueError, match="difieren"):
            verificar_conjuntos(bad, 2)


def test_logistic_scientific_e2e_records_weight_lineage_and_receipt(tmp_path, monkeypatch) -> None:
    """Ejercer el lifecycle completo con crudos artificiales, logística y ambos brazos."""
    config, entry = repository(tmp_path)
    reference = logistic_recipe()
    for key in ("predictors", "preparation", "candidate"):
        config[key] = reference[key]
    science = config["scientific_evaluation"]
    science["readings"] = ["primary", "secondary_t2"]
    science["arms"] = [
        {"id": name, "predictors": config["predictors"], "training_weighting": policy}
        for name, policy in [("uniform", UNIFORM), ("recent", RECENT)]
    ]
    validate_configuration(config)
    assert {c["training_weighting"]["method"] for _, c, _ in variants(config)} == {
        "uniform",
        "exponential_recency",
    }
    path = tmp_path / entry["configuration"]
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    regpath = tmp_path / "docs/experiments/registry.yml"
    document = yaml.safe_load(regpath.read_text(encoding="utf-8"))
    document["experiments"][0]["configuration_sha256"] = sha256(path)
    regpath.write_text(yaml.safe_dump(document), encoding="utf-8")
    monkeypatch.setattr(
        runner,
        "code_identity",
        lambda root: {"git_sha": "a" * 40, "source_sha256": "b" * 64, "dirty": False},
    )
    receipt = runner.execute(
        entry["experiment_id"], root=tmp_path, execution_id="weighted-artificial", tracking=False
    )
    folder = tmp_path / "docs/evidence/experiments" / entry["experiment_id"] / "weighted-artificial"
    assert (
        verify_execution(tmp_path, (folder / "inventory.json").relative_to(tmp_path).as_posix())
        == receipt
    )
    assert (
        receipt["training_weighting"]
        == json.loads((folder / "lineage.json").read_bytes())["training_weighting"]
    )
    assert receipt["scientific_evaluation"]["contract_status"] == "APPROVED"
    assert receipt["champion_status"] == "NOT_SELECTED"
    assert receipt["scientific_evaluation"]["scientific_conclusion"] == "NOT_APPROVED"
    assert all(
        report["raw_latest_weight"] == 1
        for horizons in receipt["training_weighting"].values()
        for report in horizons.values()
    )
    science_receipt = receipt["scientific_evaluation"]
    records = [
        record
        for name in science_receipt["records"]
        for record in json.loads((folder / name).read_bytes())["records"]
    ]
    expected_views = {("primary", 1), ("primary", 2), ("secondary_t2", 2)}
    assert {
        (row["reading"], row["horizon"]) for row in science_receipt["summary"]
    } == expected_views
    assert {row["reading"] for row in records if row["kind"] == "paired_arm_difference"} == {
        "primary",
        "secondary_t2",
    }
    for row in science_receipt["summary"]:
        primary = row["reading"] == "primary"
        assert row["B"]["required_for_verdict"] is not primary
        assert row["decision_basis"] == (
            ["UTILIDAD_PROPUESTA", "A", "C"] if primary else ["UTILIDAD_PROPUESTA", "A", "B", "C"]
        )
    secondary = [
        row for row in records if row["kind"] == "cell" and row["reading"] == "secondary_t2"
    ]
    assert secondary and all(not row["methods"]["persistence"]["degenerate"] for row in secondary)
    assert any(row["B"]["status"] == "EVALUABLE" for row in secondary)
    for row in secondary:
        comparison = row["utility_persistence_comparison"]
        assert row["B"]["required_for_verdict"] is True
        if comparison["status"] == "EVALUABLE":
            assert comparison["superior"] == (
                row["methods"]["candidate"]["TP"] > row["methods"]["persistence"]["TP"]
            )
        else:
            assert row["B"]["reason"] in {"NO_PERSISTENCE_ALERTS", "NO_ONSETS"}
            assert row["UTILIDAD_PROPUESTA"] != "CUMPLE"


def test_exp004_closed_recipe_and_reference_are_identical_except_weights() -> None:
    """La propuesta fija cinco semillas, mismas filas/roles y la única diferencia permitida."""
    config = yaml.safe_load((ROOT / "pipeline/conf/experiments/EXP004.yml").read_text())
    reference = logistic_recipe()
    for key in ("predictors", "predictor_availability", "preparation", "candidate"):
        assert config[key] == reference[key]
    effective = variants(validate_configuration(config))
    assert config["scientific_evaluation"]["readings"] == ["primary", "secondary_t2"]
    assert len(effective) == 140 and sum(len(c["horizons"]) for _, c, _ in effective) == 210
    assert all(c["horizons"] == [2] for _, c, d in effective if d["reading"] == "secondary_t2")
    assert sum(len(c["horizons"]) for _, c, d in effective if d["reading"] == "primary") == 140
    assert sum(len(c["horizons"]) for _, c, d in effective if d["reading"] == "secondary_t2") == 70
    groups = {}
    for _, variant, dimensions in effective:
        key = (dimensions["cut"], dimensions["seed"], dimensions["arm"])
        groups.setdefault(key, {})[dimensions["reading"]] = variant
    for readings in groups.values():
        assert set(readings) == {"primary", "secondary_t2"}
        for key in (
            "roles_by_horizon",
            "predictors",
            "candidate",
            "preparation",
            "calibration",
            "training_weighting",
            "data",
        ):
            assert readings["primary"][key] == readings["secondary_t2"][key]

    assert config["scientific_evaluation"]["seeds"] == [7, 13, 31, 53, 101]
    for cut in config["scientific_evaluation"]["cuts"]:
        for roles in cut["roles_by_horizon"].values():
            assert roles["train"]["start"] == "2012-03"
            assert all(v["end"] < "2025-01" for v in roles.values())
    uniform = yaml.safe_load(
        (ROOT / "pipeline/conf/retroanalisis/EXP004_uniform_history.yml").read_text()
    )
    recent = yaml.safe_load(
        (ROOT / "pipeline/conf/retroanalisis/EXP004_recent_history_36m.yml").read_text()
    )
    assert uniform.pop("training_weighting") == UNIFORM
    assert recent.pop("training_weighting") == RECENT
    assert uniform == recent == reference
    config["scientific_evaluation"]["arms"][0]["training_weighting"]["extra"] = True
    with pytest.raises(ValueError):
        validate_configuration(config)


def test_unsupported_adapter_rejected_before_training() -> None:
    """No abrir ponderación silenciosa para XGBoost ni otros adaptadores."""
    config = yaml.safe_load((ROOT / "pipeline/conf/experiments/EXP001.yml").read_text())
    config["training_weighting"] = RECENT
    with pytest.raises(ValueError, match="no soporta"):
        validate_configuration(config)


def test_two_retro_recipes_share_actual_folds_and_write_six_csvs(tmp_path, monkeypatch) -> None:
    """Ejecutar el nodo real con logística y auditar el CSV vuelto a leer desde disco."""
    from fixtures.canonical_fixture import make_panel

    import sat_dengue_pipeline.pipelines.retroanalisis.nodes as nodes
    from sat_dengue_pipeline.domain.canonical import build_table

    # Más municipios ficticios y fases distintas evitan un mes sin elegibles.
    raw = make_panel().query("municipality_code == '73998'").copy()
    panels = []
    for phase in range(17):
        part = raw.copy()
        part["municipality_code"] = f"73{900 + phase}"
        cases = (np.arange(len(part)) * 3 + phase) % 17
        part["dengue_notifications_count"] = cases.astype(float)
        part["dengue_grave_notifications_count"] = 0.0
        part["total_notifications_count"] = cases.astype(float)
        part["in_epi_coverage"] = True
        part["epi_count_status"] = np.where(cases == 0, "zero_in_coverage", "records_present")
        part["rain_mm_month_sum"] = 3.0
        part["rain_mm_month_sum_valid_days"] = part["expected_days_in_month"]
        panels.append(part)
    table, schema = build_table(pd.concat(panels, ignore_index=True))
    monkeypatch.setattr(nodes, "load_canonical", lambda artifact: (table, schema))
    params = {
        "configuraciones": [
            str(ROOT / f"pipeline/conf/retroanalisis/EXP004_{arm}.yml")
            for arm in ["uniform_history", "recent_history_36m"]
        ],
        "semillas": [7],
        "horizontes": [1, 2],
        "primer_origen": "2024-01",
        "ultimo_objetivo": "2024-06",
        "primer_entrenamiento": "2018-01",
        "cobertura_desde": "2018-01",
        "municipios_minimos": 2,
        "salida": "data/weighted-retro",
        "exclusive_output": True,
        "exigir_conjunto_igual": True,
    }
    monkeypatch.chdir(tmp_path)
    nodes.retroanalisis(object(), params)
    folder = tmp_path / params["salida"]
    assert {p.name for p in folder.iterdir()} == {
        name + ".csv"
        for name in ["resumen", "por_anio", "curva", "omitidos", "conjunto", "predicciones"]
    }
    conjunto = pd.read_csv(folder / "conjunto.csv")
    verificar_conjuntos(conjunto, 2)
    assert set(conjunto.horizonte) == {1, 2}
    assert conjunto.groupby(["horizonte", "seed", "fold_id"]).receta.nunique().eq(2).all()
    predictions = pd.read_csv(folder / "predicciones.csv")
    assert predictions.target_period.lt("2025-01").all()
    with pytest.raises(FileExistsError):
        nodes.retroanalisis(object(), params)


def test_exp004_environment_is_explicit_and_matches_recipe() -> None:
    """El comando versionado fija release/perfil/certificado sin tocar defaults globales."""
    from kedro.config import OmegaConfigLoader

    parameters = OmegaConfigLoader(str(ROOT / "pipeline/conf"), env="exp004", base_env="base")[
        "parameters"
    ]
    recipe = yaml.safe_load((ROOT / "pipeline/conf/experiments/EXP004.yml").read_text())
    assert parameters["canonical"]["mode"] == "approved"
    assert parameters["canonical"]["profile"] == "operational_full"
    assert parameters["canonical"]["manifest"] == recipe["data"]["manifest"].removeprefix(
        "pipeline/"
    )
    retro = parameters["retroanalisis"]
    assert retro["certified_data"] == recipe["data"]
    assert retro["semillas"] == recipe["scientific_evaluation"]["seeds"]
    assert retro["exclusive_output"] and retro["exigir_conjunto_igual"]
    assert retro["salida"] == "data/retroanalisis/EXP004/run1"


def test_retro_rejects_uncertified_artifact_before_training(tmp_path, monkeypatch) -> None:
    """La selección operacional no admite otro derivado aunque tenga un perfil parecido."""
    import sat_dengue_pipeline.pipelines.retroanalisis.nodes as nodes

    params = {
        "salida": "data/artificial-proof",
        "certified_data": yaml.safe_load(
            (ROOT / "pipeline/conf/experiments/EXP004.yml").read_text()
        )["data"],
    }
    monkeypatch.chdir(ROOT / "pipeline")
    with pytest.raises(ValueError, match="distinto del certificado"):
        nodes.retroanalisis(SimpleNamespace(serialized_sha256="bad", semantic_digest="bad"), params)
