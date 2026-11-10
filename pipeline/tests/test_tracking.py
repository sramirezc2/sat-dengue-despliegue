"""MLflow real local: ciclo de vida, privacidad y neutralidad científica."""

import ast
import builtins
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

import pytest
from fixtures.evaluation_fixture import make_evaluation

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle, ResolvedFile
from sat_dengue_pipeline.evaluation.paired import EvaluationConfig, EvaluationReport, evaluate
from sat_dengue_pipeline.experiments.rolling import ExperimentSpec, calendar_audit
from sat_dengue_pipeline.models.adapters import AdapterSpec
from sat_dengue_pipeline.tracking.local import TAGS, LocalTracker, TrackingConfig
from sat_dengue_pipeline.tracking.privacy import (
    LINEAGE_FIELDS,
    canonical_bytes,
    collect_lineage,
)


@pytest.fixture
def inputs(tmp_path: Path) -> tuple[Path, EvaluationReport, dict[str, Any]]:
    """Crear repositorio temporal y linaje verídico de una cohorte artificial."""
    repo = tmp_path / "workspace"
    (repo / "pipeline").mkdir(parents=True)
    (repo / ".gitignore").write_text(".tracking/\n", encoding="utf-8")
    (repo / "pipeline/uv.lock").write_bytes((Path(__file__).parents[1] / "uv.lock").read_bytes())
    subprocess.run(["git", "init", "-q", "-b", "feature/pipeline-e2e", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "synthetic fixture",
        ],
        check=True,
    )
    tables, frozen, _ = make_evaluation()
    report = evaluate(
        tables,
        frozen,
        expected_digest=frozen.digest,
        config=EvaluationConfig(bootstrap_replicates=4),
    )
    source = tmp_path / "panel.txt"
    source.write_bytes(b"artificial engineering fixture")
    bundle = ResolvedBundle(
        "synthetic-v1",
        "a" * 64,
        "2018-01-01",
        "2024-12-31",
        (
            ResolvedFile(
                "panel",
                source,
                source.stat().st_size,
                hashlib.sha256(source.read_bytes()).hexdigest(),
            ),
        ),
    )
    lineage = collect_lineage(
        repo,
        bundle,
        provider="local",
        spec=AdapterSpec("signal_double", "1"),
        protocol_digest=calendar_audit(ExperimentSpec(1))["digest"],
        report=report,
    )
    return repo, report, lineage


def test_real_local_run_recoverable_metadata_and_privacy(inputs, monkeypatch) -> None:
    """SQL y repositorio SDK reales bajo guard global de red/DNS, sin servidor."""
    repo, report, lineage = inputs
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "https://tracking.invalid")
    monkeypatch.setenv("MLFLOW_TRACKING_TOKEN", "never-log-fixture")
    before = report.canonical_json
    tracker = LocalTracker(repo, TrackingConfig(enabled=True))
    receipt = tracker.record(report, lineage)
    assert receipt.status == "FINISHED" and receipt.tracking_enabled
    assert receipt.parent_run_id is None and len(receipt.run_id) == 32
    run = tracker.get_run(receipt.run_id)
    assert run.info.status == "FINISHED" and run.info.user_id == ""
    assert run.info.artifact_uri.startswith("satdlocal:/")
    assert set(run.data.params) == LINEAGE_FIELDS
    assert set(run.data.tags) <= TAGS
    assert (
        json.loads(run.data.params["git_sha"])
        == subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    )
    assert json.loads(run.data.params["git_dirty"]) is False
    for name in (
        "release_id",
        "manifest_sha256",
        "input_hashes",
        "provider",
        "coverage_start",
        "coverage_end",
        "lock_sha256",
        "dependencies",
        "bootstrap",
    ):
        assert json.loads(run.data.params[name]) == lineage[name]
    recovered = LocalTracker(repo, TrackingConfig(enabled=True))
    assert recovered.get_run(receipt.run_id).info.status == "FINISHED"
    files = recovered.artifacts(receipt.run_id)
    assert set(files) == {
        "metrics.json",
        "comparisons.json",
        "strata.json",
        "curves.json",
        "uncertainty.json",
        "configuration.json",
        "lineage.json",
    }
    recorded = json.loads(files["lineage.json"])
    assert recorded["run_id"] == receipt.run_id
    for name in ("metrics", "comparisons", "strata", "curves", "uncertainty"):
        assert files[name + ".json"] == canonical_bytes(report.payload[name])
    assert report.canonical_json == before
    dump = "\n".join(sqlite3.connect(tracker.root / "tracking.sqlite").iterdump())
    all_bytes = b"".join(files.values()) + dump.encode()
    for forbidden in (
        str(repo),
        "/Users/",
        "municipality_code",
        "y_true",
        "fixture@example.invalid",
        "Fixture",
        "tracking.invalid",
        "never-log-fixture",
    ):
        assert forbidden.encode() not in all_bytes
    assert re.search(rb"(?<![A-Za-z0-9])(?:50991|73991)(?![A-Za-z0-9])", all_bytes) is None
    assert os.environ["MLFLOW_DISABLE_TELEMETRY"] == "true"
    assert subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"]) == b""


def test_disabled_does_not_import_sdk_or_create_store(
    inputs, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tracking apagado conserva resultados sin dependencias SDK en ejecución."""
    repo, report, lineage = inputs
    original = builtins.__import__

    def guard(name: str, *args: Any, **kwargs: Any) -> Any:
        """Detectar cualquier import innecesario del SDK."""
        assert name.split(".")[0] != "mlflow"
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guard)
    before = report.digest
    receipt = LocalTracker(repo).record(report, lineage)
    assert receipt.status == "DISABLED" and receipt.run_id is None
    assert not (repo / ".tracking").exists() and report.digest == before


def test_enabled_disabled_identical_scientific_artifacts_and_new_ids(inputs) -> None:
    """Observabilidad no altera bytes/orden/semillas y cada repetición crea otro ID."""
    repo, report, lineage = inputs
    before = report.canonical_json
    off = LocalTracker(repo).record(report, lineage)
    tracker = LocalTracker(repo, TrackingConfig(enabled=True))
    first, second = tracker.record(report, lineage), tracker.record(report, lineage)
    assert first.run_id != second.run_id
    assert first.artifact_digest == second.artifact_digest == off.artifact_digest
    for name in (
        "metrics.json",
        "comparisons.json",
        "strata.json",
        "curves.json",
        "uncertainty.json",
    ):
        assert tracker.artifacts(first.run_id)[name] == tracker.artifacts(second.run_id)[name]
    assert report.canonical_json == before


def test_dirty_and_portable_multiple_stores(inputs) -> None:
    """No ocultar dirty; dos rutas relativas tienen backends independientes."""
    repo, report, lineage = inputs
    (repo / "untracked.txt").write_text("artificial", encoding="utf-8")
    source = repo.parent / "panel.txt"
    bundle = ResolvedBundle(
        "synthetic-v1",
        "a" * 64,
        "2018-01-01",
        "2024-12-31",
        (
            ResolvedFile(
                "panel",
                source,
                source.stat().st_size,
                hashlib.sha256(source.read_bytes()).hexdigest(),
            ),
        ),
    )
    lineage = collect_lineage(
        repo,
        bundle,
        provider="local",
        spec=AdapterSpec("signal_double", "1"),
        protocol_digest=lineage["protocol_digest"],
        report=report,
    )
    receipts = []
    for name in ("first", "second"):
        tracker = LocalTracker(repo, TrackingConfig(True, ".tracking/" + name))
        receipt = tracker.record(report, lineage)
        assert json.loads(tracker.get_run(receipt.run_id).data.params["git_dirty"]) is True
        assert tracker.root.is_relative_to(repo)
        receipts.append(receipt)
    assert receipts[0].run_id != receipts[1].run_id


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt])
def test_failure_lifecycle_propagates_without_complete_artifacts(
    inputs, monkeypatch, failure
) -> None:
    """RUNNING se cierra FAILED/KILLED, propagando el fallo sin mutar ciencia."""
    repo, report, lineage = inputs
    tracker = LocalTracker(repo, TrackingConfig(enabled=True))
    seen = []

    def broken(run_id, artifacts):
        """Fallar después de iniciar la corrida pero antes de aprobar artefactos."""
        seen.append(run_id)
        assert tracker.get_run(run_id).info.status == "RUNNING"
        raise failure("injected tracking failure")

    monkeypatch.setattr(tracker, "_publish", broken)
    before = report.canonical_json
    with pytest.raises(failure):
        tracker.record(report, lineage)
    assert tracker.get_run(seen[0]).info.status == (
        "FAILED" if failure is RuntimeError else "KILLED"
    )
    assert not tracker._artifact_dir(seen[0]).exists()
    assert report.canonical_json == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("token", "private"),
        ("release_id", "hf_sensitive_token"),
        ("release_id", "/Users/private/source"),
        ("release_id", "C:\\private\\source"),
        ("candidate_config", {"api_key": "private"}),
        ("candidate_config", {"input_path": "private"}),
        ("candidate_config", {"municipality_code": "50991"}),
        ("provider", "https://example.invalid"),
    ],
)
def test_rejects_secret_path_unknown_or_individual_metadata(inputs, field, value) -> None:
    """La validación ocurre antes de crear store o corrida."""
    repo, report, lineage = inputs
    with pytest.raises(ValueError):
        LocalTracker(repo, TrackingConfig(enabled=True)).record(report, {**lineage, field: value})
    assert not (repo / ".tracking").exists()


@pytest.mark.parametrize("section", ["metrics", "strata", "curves", "uncertainty", "replicates"])
def test_rejects_unknown_aggregate_fields(inputs, section) -> None:
    """Ninguna tabla agregada puede esconder filas/códigos o columnas nuevas."""
    repo, report, lineage = inputs
    payload = report.payload
    if not payload[section]:
        payload[section] = [{"municipality_code": "50991"}]
    else:
        payload[section][0]["municipality_code"] = "50991"
    altered = EvaluationReport(json.dumps(payload))
    with pytest.raises(ValueError):
        LocalTracker(repo, TrackingConfig(enabled=True)).record(altered, lineage)
    assert not (repo / ".tracking").exists()


@pytest.mark.parametrize(
    "store",
    ["/tmp/private", "../escape", "http://example.invalid", ".tracking/../escape", "s3://bucket"],
)
def test_rejects_nonlocal_store(store: str) -> None:
    """No se aceptan URI, HOME implícito o rutas fuera del namespace ignorado."""
    with pytest.raises(ValueError):
        TrackingConfig(True, store)


def test_symlink_escape_and_unignored_store_rejected(inputs, symlink_factory) -> None:
    """El SDK nunca recibe una ruta que escape por symlink o no esté ignorada."""
    repo, report, lineage = inputs
    symlink_factory(repo / ".tracking", repo.parent, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinks"):
        LocalTracker(repo, TrackingConfig(enabled=True)).record(report, lineage)
    (repo / ".tracking").unlink()
    (repo / ".gitignore").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="ignorado"):
        LocalTracker(repo, TrackingConfig(enabled=True)).record(report, lineage)


@pytest.mark.parametrize("component", ["tracking.sqlite", "artifacts", "staging"])
def test_store_components_cannot_escape_by_symlink(inputs, component: str, symlink_factory) -> None:
    """Rechazar enlaces internos antes de importar o escribir el backend."""
    repo, report, lineage = inputs
    root = repo / ".tracking/local"
    root.mkdir(parents=True)
    symlink_factory(root / component, repo.parent, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinks"):
        LocalTracker(repo, TrackingConfig(enabled=True)).record(report, lineage)


def test_scientific_modules_do_not_import_mlflow() -> None:
    """Solo el adaptador de tracking puede depender del SDK, nunca ciencia."""
    root = Path(__file__).parents[1] / "src/sat_dengue_pipeline"
    for folder in ("evaluation", "experiments", "models", "domain"):
        for path in (root / folder).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                imports = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                )
                assert all(name.split(".")[0] != "mlflow" for name in imports), path
    assert "provider" not in ResolvedBundle.__dataclass_fields__


def test_failure_after_artifact_move_removes_incomplete_publication(inputs, monkeypatch) -> None:
    """Incluso un fallo posterior al rename elimina artefactos de la corrida fallida."""
    repo, report, lineage = inputs
    tracker = LocalTracker(repo, TrackingConfig(enabled=True))
    original, seen = tracker._publish, []

    def fail_after_move(run_id, artifacts):
        """Inyectar fallo tras materializar los agregados locales."""
        original(run_id, artifacts)
        seen.append(run_id)
        raise RuntimeError("injected after move")

    monkeypatch.setattr(tracker, "_publish", fail_after_move)
    with pytest.raises(RuntimeError, match="injected"):
        tracker.record(report, lineage)
    assert tracker.get_run(seen[0]).info.status == "FAILED"
    assert not tracker._artifact_dir(seen[0]).exists()


def test_artifact_integrity_rejects_tampering(inputs) -> None:
    """El inventario verifica bytes, no solo nombres o tamaños."""
    repo, report, lineage = inputs
    tracker = LocalTracker(repo, TrackingConfig(enabled=True))
    receipt = tracker.record(report, lineage)
    (tracker._artifact_dir(receipt.run_id) / "metrics.json").write_bytes(b"[]")
    with pytest.raises(ValueError, match="Inventario"):
        tracker.artifacts(receipt.run_id)


def test_cli_disabled_is_explicit_and_does_not_create_storage(inputs, monkeypatch, capsys) -> None:
    """El comando opera solo sobre agregados preexistentes y es opt-in."""
    import sys

    from sat_dengue_pipeline.tracking.__main__ import main

    repo, report, lineage = inputs
    report_path, lineage_path = repo / "report.json", repo / "lineage.json"
    report_path.write_text(report.canonical_json, encoding="utf-8")
    lineage_path.write_text(json.dumps(lineage), encoding="utf-8")
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        sys, "argv", ["tracking", "--report", "report.json", "--lineage", "lineage.json"]
    )
    main()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "DISABLED" and not (repo / ".tracking").exists()


def test_store_can_move_without_rewriting_private_paths(inputs) -> None:
    """Las URI lógicas conservan acceso real tras mover el workspace local."""
    import shutil

    repo, report, lineage = inputs
    tracker = LocalTracker(repo, TrackingConfig(enabled=True))
    receipt = tracker.record(report, lineage)
    expected = tracker.artifacts(receipt.run_id)
    tracker.close()
    moved = repo.parent / "moved-workspace"
    shutil.copytree(repo, moved)
    recovered = LocalTracker(moved, TrackingConfig(enabled=True))
    assert recovered.get_run(receipt.run_id).info.status == "FINISHED"
    assert recovered.artifacts(receipt.run_id) == expected
