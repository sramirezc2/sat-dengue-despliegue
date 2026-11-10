"""Aceptación real del grafo Kedro completo sobre cinco fuentes exclusivamente artificiales."""

import json
from pathlib import Path

import pytest
from fixtures.scientific_fixture import repository
from kedro.io import DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner

from sat_dengue_pipeline.experiment_management import runner
from sat_dengue_pipeline.experiment_management.evidence import verify_execution
from sat_dengue_pipeline.experiment_management.registry import Registry
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.models.xgboost import XGBoostOnsetAdapter
from sat_dengue_pipeline.pipelines.experiment_run.pipeline import create_pipeline
from sat_dengue_pipeline.raw.contract import sha256


def test_scientific_kedro_e2e_uses_its_certified_data_and_fitted_models(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ejecutar crudos→N=3→brazos→modelos reales→ciencia→inventario, sin mocks científicos."""
    import copy

    import yaml

    config, entry = repository(tmp_path)
    config["scientific_evaluation"]["seeds"] = [7, 13, 31, 53, 101]
    extra_cuts = []
    for year in (2022, 2023):
        roles = copy.deepcopy(config["roles_by_horizon"])
        for horizon_roles in roles.values():
            for offset, role in enumerate(
                (
                    "train",
                    "calibration_fit",
                    "calibration_selection",
                    "threshold_selection",
                    "evaluation",
                )
            ):
                target_year = year - 4 + offset
                horizon_roles[role].update(
                    start=f"{target_year}-01",
                    end=f"{target_year}-{'11' if role == 'evaluation' else '06'}",
                )
                horizon_roles[role]["support"]["months"] = 11 if role == "evaluation" else 6
        extra_cuts.append({"id": f"cut{year}", "roles_by_horizon": roles})
    config["scientific_evaluation"]["cuts"] = extra_cuts + config["scientific_evaluation"]["cuts"]
    path = tmp_path / entry["configuration"]
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    registry_path = tmp_path / "docs/experiments/registry.yml"
    registry_document = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry_document["experiments"][0]["configuration_sha256"] = sha256(path)
    registry_path.write_text(yaml.safe_dump(registry_document), encoding="utf-8")
    import subprocess

    (tmp_path / ".gitignore").write_text("pipeline/data/\npipeline/.tracking/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    begin = runner.begin_execution
    monkeypatch.setattr(
        runner,
        "begin_execution",
        lambda eid: begin(eid, root=tmp_path, execution_id="synthetic-e2e", tracking=True),
    )
    monkeypatch.setattr(
        runner,
        "code_identity",
        lambda root: {
            "git_sha": "a" * 40,
            "source_sha256": "b" * 64,
            "lock_sha256": "c" * 64,
            "versions": {"fixture": "synthetic"},
            "dirty": False,
        },
    )
    fit = XGBoostOnsetAdapter.fit
    fitted = []

    def observe_fit(model, X, y):
        """Observar el ajuste auténtico sin reemplazar el estimador o sus predicciones."""
        fit(model, X, y)
        fitted.append({"model": model.model_sha256(), "features": list(X), "rows": len(X)})

    monkeypatch.setattr(XGBoostOnsetAdapter, "fit", observe_fit)
    graph = create_pipeline()
    assert "scientific_evaluation" in {n.name for n in graph.nodes}
    result = SequentialRunner().run(
        graph, DataCatalog({"params:experiment_id": MemoryDataset(entry["experiment_id"])})
    )
    receipt = result["experiment_receipt"].load()
    reference = f"docs/evidence/experiments/{entry['experiment_id']}/synthetic-e2e/inventory.json"
    assert verify_execution(tmp_path, reference) == receipt
    assert receipt["status"] == "COMPLETED" and receipt["gate"] == "scientific_evaluation"
    assert receipt["scientific_evaluation"]["label"] == "VEREDICTO_BAJO_CONTRATO_PROPUESTO"
    folder = (tmp_path / reference).parent
    records = [
        r
        for name in receipt["scientific_evaluation"]["records"]
        for r in json.loads((folder / name).read_bytes())["records"]
    ]
    variants = [r for r in records if r["kind"] == "variant"]
    cells = [r for r in records if r["kind"] == "cell"]
    lineage = json.loads((folder / "lineage.json").read_bytes())
    canonical = lineage["canonical"]
    assert canonical["certification_status"] == "PASSED_SYNTHETIC_N3"
    assert canonical["n3_serialized_hashes"] == [canonical["serialized_sha256"]] * 3
    assert len(set(canonical["worker_pids"])) == 3
    assert {r["canonical_serialized_sha256"] for r in cells} == {canonical["serialized_sha256"]}
    assert {r["model_sha256"] for r in cells} == {r["model"] for r in fitted}
    assert len(fitted) == 180
    assert receipt["mlflow"]["enabled"]
    assert {tuple(r["features"]) for r in fitted} == {
        tuple(a["predictors"]) for a in config["scientific_evaluation"]["arms"]
    }
    assert all(r["scientific_conclusion"] == "NOT_APPROVED" for r in cells)
    assert all(
        r["UTILIDAD_PROPUESTA"] == "NO_EVALUABLE" for r in cells
    )  # Solo dos municipios: no fabricar soporte.
    for variant in variants:
        assert variant["temporal"]["evaluation_reads_after_both_predictions"]
        assert all(n == 1 for n in variant["label_reads"].values())
        assert variant["canonical"]["serialized_sha256"] == canonical["serialized_sha256"]
        for h in variant["effective_configuration"]["horizons"]:
            assert (
                variant["support"][str(h)]["evaluation"]["label_stage"]
                == "after_freeze_and_predictions"
            )
    by_variant = {(v["arm"], v["population"], v["reading"]): v for v in variants}
    for role in (
        "train",
        "calibration_fit",
        "calibration_selection",
        "threshold_selection",
        "evaluation",
    ):
        native = by_variant[("epi", "native", "primary")]["support"]["1"][role]
        common = by_variant[("epi", "common", "primary")]["support"]["1"][role]
        climate = by_variant[("climate", "common", "primary")]["support"]["1"][role]
        assert native["rows"] >= common["rows"] == climate["rows"]
    assert (
        by_variant[("epi", "native", "primary")]["support"]["1"]["train"]["rows"]
        > by_variant[("epi", "common", "primary")]["support"]["1"]["train"]["rows"]
    )
    assert any(r["kind"] == "paired_arm_difference" for r in records)
    assert any(r.get("five_seeds_check") == "REPORTED" for r in records)
    stability = [r for r in records if r["kind"] == "seed_stability"]
    assert stability and all(r["status"] == "NO_EVALUABLE" for r in stability)
    assert all(len(r["seeds"]) == 5 and r["team_approval_required"] for r in stability)
    assert Registry(tmp_path).get(entry["experiment_id"])["status"] == "RUNNING"
    from sat_dengue_pipeline.experiment_management.compare import compare

    queried = compare(tmp_path)
    assert {r["seed"] for r in queried} == {7, 13, 31, 53, 101}
    assert {r["cut"] for r in queried} == {"cut2022", "cut2023", "cut2024"}
    assert all(r["evaluation_label"] == "VEREDICTO_BAJO_CONTRATO_PROPUESTO" for r in queried)
    inventory = json.loads((folder / "inventory.json").read_bytes())
    assert all(sha256(folder / name) == digest for name, digest in inventory.items())
    assert receipt["execution_signature"] == stable_digest(lineage)


def test_scientific_pipeline_runs_with_one_kedro_cli_command(tmp_path: Path) -> None:
    """Comprobar la entrada CLI pública con tracking real y el mismo paquete instalado."""
    import os
    import shutil
    import sqlite3
    import subprocess
    import sys

    import yaml
    from fixtures.scientific_fixture import ROOT

    config, entry = repository(tmp_path)
    # Un brazo/una lectura basta para comprobar el comando; la prueba anterior compara ambos.
    config["scientific_evaluation"]["arms"] = config["scientific_evaluation"]["arms"][1:]
    config["scientific_evaluation"]["readings"] = ["primary"]
    recipe_path = tmp_path / entry["configuration"]
    recipe_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    registry_path = tmp_path / "docs/experiments/registry.yml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["experiments"][0]["configuration_sha256"] = sha256(recipe_path)
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")
    shutil.copytree(
        ROOT / "pipeline/src",
        tmp_path / "pipeline/src",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(ROOT / "pipeline/conf/base", tmp_path / "pipeline/conf/base")
    shutil.copyfile(ROOT / "pipeline/conf/logging.yml", tmp_path / "pipeline/conf/logging.yml")
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(ROOT / "pipeline" / name, tmp_path / "pipeline" / name)
    (tmp_path / ".gitignore").write_text("pipeline/data/\npipeline/.tracking/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "technical fixture",
        ],
        check=True,
    )
    env = {key: value for key, value in os.environ.items() if key != "HF_TOKEN"}
    env["PYTHONPATH"] = str(tmp_path / "pipeline/src")
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    command = [
        sys.executable,
        "-m",
        "kedro",
        "run",
        "--pipelines",
        "experiment_run",
        "--params",
        f"experiment_id={entry['experiment_id']}",
    ]
    result = subprocess.run(
        command, cwd=tmp_path / "pipeline", env=env, capture_output=True, text=True, timeout=180
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "scientific_evaluation" in result.stdout + result.stderr
    references = list(
        (tmp_path / f"docs/evidence/experiments/{entry['experiment_id']}").glob("*/inventory.json")
    )
    assert len(references) == 1
    receipt = verify_execution(tmp_path, references[0].relative_to(tmp_path).as_posix())
    assert receipt["scientific_evaluation"]["scientific_conclusion"] == "NOT_APPROVED"
    assert receipt["mlflow"]["enabled"]
    store = tmp_path / "pipeline/.tracking/experiments/tracking.sqlite"
    with sqlite3.connect(f"file:{store}?mode=ro", uri=True) as db:
        assert db.execute("SELECT COUNT(*) FROM runs WHERE status='FINISHED'").fetchone()[0] == 3
        assert db.execute("SELECT COUNT(*) FROM metrics").fetchone()[0] > 0


def test_scientific_stage_failure_preserves_terminal_and_signed_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Una predicción ajena no se evalúa: terminal BLOCKED y evidencia exclusive consultable."""
    from dataclasses import replace

    _, entry = repository(tmp_path)
    monkeypatch.setattr(
        runner,
        "code_identity",
        lambda root: {
            "git_sha": "a" * 40,
            "source_sha256": "b" * 64,
            "lock_sha256": "c" * 64,
            "versions": {},
            "dirty": False,
        },
    )
    predict = runner.engine.predict

    def corrupt_digest(run):
        """Conservar el ajuste real e introducir una identidad ajena tras la inferencia."""
        predict(run)
        run.predictions[run.config["horizons"][0]] = replace(
            run.predictions[run.config["horizons"][0]], artifact_digest="wrong-model"
        )
        return run

    monkeypatch.setattr(runner.engine, "predict", corrupt_digest)
    with pytest.raises(runner.ExecutionError, match="BLOCKED:scientific_evaluation"):
        runner.execute(
            entry["experiment_id"], root=tmp_path, execution_id="corrupt", tracking=False
        )
    receipt = verify_execution(
        tmp_path, f"docs/evidence/experiments/{entry['experiment_id']}/corrupt/inventory.json"
    )
    assert receipt["status"] == "BLOCKED" and receipt["gate"] == "scientific_evaluation"
    assert Registry(tmp_path).get(entry["experiment_id"])["status"] == "BLOCKED"
    assert receipt["scientific_evaluation"]["scientific_conclusion"] == "NOT_APPROVED"
