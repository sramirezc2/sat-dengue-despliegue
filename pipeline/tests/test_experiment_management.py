"""Aceptación T17: historia, aprobación, aislamiento, terminales y MLflow sin datos reales."""

import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from sat_dengue_pipeline.experiment_management import runner
from sat_dengue_pipeline.experiment_management.compare import compare
from sat_dengue_pipeline.experiment_management.configuration import (
    load_configuration,
    validate_configuration,
)
from sat_dengue_pipeline.experiment_management.evidence import exclusive_json, verify_execution
from sat_dengue_pipeline.experiment_management.registry import (
    Registry,
    confined,
    read_yaml,
    registry_lock,
)
from sat_dengue_pipeline.experiment_management.tracking import ExperimentTracker
from sat_dengue_pipeline.raw.contract import sha256


@pytest.fixture
def repository(tmp_path, monkeypatch):
    """Copiar solo recetas técnicas; no abrir publicaciones, crudos privados ni T16."""
    source = Path(__file__).parents[2]
    for name in ("EXP001", "EXP002"):
        shutil.copytree(
            source / "docs/experiments" / name,
            tmp_path / "docs/experiments" / name,
            ignore=shutil.ignore_patterns("CONCLUSIONS.md"),
        )
        path = tmp_path / f"pipeline/conf/experiments/{name}.yml"
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / f"pipeline/conf/experiments/{name}.yml", path)
    document = read_yaml(source / "docs/experiments/registry.yml")
    for entry in document["experiments"]:
        entry.update(status="APPROVED", scientific_result="NOT_APPLICABLE")
    (tmp_path / "docs/experiments/registry.yml").write_text(yaml.safe_dump(document))
    (tmp_path / ".gitignore").write_text("pipeline/data/\npipeline/.tracking/\n")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.setattr(
        runner,
        "code_identity",
        lambda root: {
            "git_sha": "a" * 40,
            "dirty": False,
            "source_sha256": "b" * 64,
            "lock_sha256": "c" * 64,
            "versions": {"fixture": "1"},
        },
    )
    return tmp_path


def save_registry(root, document):
    """Simular modificaciones versionadas explícitas para atacar validadores."""
    (root / "docs/experiments/registry.yml").write_text(yaml.safe_dump(document))


def change_config(root, eid, mutate):
    """Cambiar fixture y su hash declarado; el validador semántico aún debe rechazarlo."""
    registry = Registry(root)
    entry = registry.get(eid)
    path = root / entry["configuration"]
    config = read_yaml(path)
    mutate(config)
    path.write_text(yaml.safe_dump(config))
    registry.entries[eid]["configuration_sha256"] = sha256(path)
    save_registry(root, registry.document)


def receipt(root, eid, execution="acceptance"):
    """Leer solo el recibo público de una ejecución de prueba."""
    return verify_execution(root, f"docs/evidence/experiments/{eid}/{execution}/inventory.json")


def test_two_real_synthetic_factories_coexist_and_compare(repository):
    """Ejecutar fuente→canónico→roles→modelos→calibración→evaluación en dos recetas."""
    root = repository
    first = runner.execute("EXP001", root=root, execution_id="acceptance", tracking=False)
    before = (root / "docs/evidence/experiments/EXP001/acceptance/inventory.json").read_bytes()
    second = runner.execute("EXP002", root=root, execution_id="other", tracking=False)
    assert first["status"] == second["status"] == "COMPLETED"
    assert first["execution_signature"] != second["execution_signature"]
    assert (
        root / "docs/evidence/experiments/EXP001/acceptance/inventory.json"
    ).read_bytes() == before
    rows = compare(root)
    assert {r["experiment_id"] for r in rows} == {"EXP001", "EXP002"}
    assert {r["horizon"] for r in compare(root, horizon=2)} == {2}
    assert compare(root, status="BLOCKED") == []
    assert compare(root, candidate="not-implemented") == []
    assert all(r["scientific_result"] == "NOT_APPLICABLE" for r in rows)
    for eid, execution in (("EXP001", "acceptance"), ("EXP002", "other")):
        folder = root / f"docs/evidence/experiments/{eid}/{execution}"
        validation = json.loads((folder / "validation.json").read_bytes())
        assert validation["canonical_audit"]["coverage"]["end"] == "2024-12"
        assert sum(v["reserved"] for v in validation["canonical_audit"]["quarantine"].values()) == 3
        assert validation["temporal"]["all_producer_support_before_any_fit"]
        assert validation["temporal"]["evaluation_reads_after_both_predictions"]
        metrics = json.loads((folder / "metrics.json").read_bytes())
        assert all(value["fit_calls"] == 1 for value in metrics.values())
        assert all(validation["label_reads"][f"{h}:evaluation"] == 1 for h in metrics)
        assert Registry(root).get(eid)["status"] == "RUNNING"
    with pytest.raises(ValueError, match="APPROVED"):
        runner.execute("EXP001", root=root, execution_id="acceptance", tracking=False)
    assert receipt(root, "EXP001") == first


@pytest.mark.parametrize("fault", ["unknown", "duplicate", "absolute", "escape", "hash", "slug"])
def test_registry_rejects_invalid_entries(repository, fault):
    """Rechazar identidad ambigua, campos abiertos y rutas/hash sin autorización."""
    document = Registry(repository).document
    entry = document["experiments"][0]
    if fault == "unknown":
        entry["import"] = "arbitrary.module"
    elif fault == "duplicate":
        document["experiments"].append(copy.deepcopy(entry))
    elif fault == "absolute":
        entry["protocol"] = "/etc/passwd"
    elif fault == "escape":
        entry["configuration"] = "pipeline/conf/experiments/../base/parameters.yml"
    elif fault == "hash":
        entry["protocol_sha256"] = "0" * 64
    else:
        document["experiments"][1]["experiment_slug"] = entry["experiment_slug"]
    save_registry(repository, document)
    with pytest.raises(ValueError):
        Registry(repository)
    assert not (repository / "docs/evidence").exists()


@pytest.mark.parametrize("location", ["file", "parent", "output"])
def test_symlinks_rejected_at_file_parent_and_output(repository, symlink_factory, location):
    """No seguir enlaces en lectura ni al reservar evidencia."""
    if location == "output":
        path = repository / "docs/evidence/experiments/EXP001"
        path.parent.mkdir(parents=True)
        original = repository / "outside"
        original.mkdir()
        symlink_factory(path, original, target_is_directory=True)
        with pytest.raises(ValueError, match="Symlink"):
            runner.execute("EXP001", root=repository, tracking=False)
        assert list(original.iterdir()) == []
    else:
        path = repository / (
            "docs/experiments/EXP001/SPECIFICATION.md"
            if location == "file"
            else "pipeline/conf/experiments"
        )
        original = repository / "saved"
        path.rename(original)
        symlink_factory(path, original, target_is_directory=location == "parent")
        with pytest.raises(ValueError, match="Symlink"):
            Registry(repository)


def test_yaml_duplicate_fields_are_rejected(repository):
    """No permitir que el parser sustituya una aprobación o receta silenciosamente."""
    path = repository / "docs/experiments/registry.yml"
    with path.open("a") as stream:
        stream.write("\nschema_version: 1\n")
    with pytest.raises(ValueError, match="duplicada"):
        read_yaml(path)


@pytest.mark.parametrize(
    "fault",
    [
        "family",
        "2025",
        "unknown",
        "predictors",
        "roles",
        "seed",
        "preparation",
        "threshold",
        "availability",
        "calibration",
    ],
)
def test_configuration_fails_closed_even_with_new_hash(repository, fault):
    """Hashes válidos no autorizan familias, transformaciones o políticas no implementadas."""
    config = read_yaml(repository / "pipeline/conf/experiments/EXP001.yml")
    if fault == "family":
        config["candidate"]["family"] = "lightgbm"
    elif fault == "2025":
        config["reserved_start"] = "2026-01"
    elif fault == "unknown":
        config["candidate"]["import"] = "os.system"
    elif fault == "predictors":
        config["predictors"].append("G")
    elif fault == "roles":
        config["roles_by_horizon"]["1"]["evaluation"]["end"] = "2025-01"
    elif fault == "seed":
        config["seed"] = True
    elif fault == "preparation":
        config["preparation"]["variables_g"] = True
    elif fault == "threshold":
        config["threshold"]["objective"] = "automatic_champion"
    elif fault == "availability":
        config["predictor_availability"]["month_of_year"] = 1
    else:
        config["calibration"]["tie"] = "sigmoid"
    with pytest.raises(ValueError):
        validate_configuration(config)


@pytest.mark.parametrize("status", ["PROPOSED", "RUNNING", "BLOCKED", "COMPLETED"])
def test_only_approved_can_execute(repository, status):
    """La compuerta precede adquisición, MLflow y reserva de evidencia."""
    document = Registry(repository).document
    document["experiments"][0]["status"] = status
    save_registry(repository, document)
    with pytest.raises(ValueError):
        runner.execute("EXP001", root=repository, tracking=False)
    assert not (repository / "docs/evidence").exists()


@pytest.mark.parametrize(
    "exception,terminal",
    [(RuntimeError, "FAILED"), (ValueError, "BLOCKED"), (KeyboardInterrupt, "KILLED")],
)
def test_failures_and_interrupts_leave_receipts(repository, monkeypatch, exception, terminal):
    """No registrar mensajes privados de proveedores ni aparentar éxito tras excepciones."""

    def broken(*args):
        raise exception("private-path-and-token-do-not-log")

    monkeypatch.setattr(runner, "acquire_and_build", broken)
    expected = KeyboardInterrupt if exception is KeyboardInterrupt else runner.ExecutionError
    with pytest.raises(expected):
        runner.execute("EXP001", root=repository, execution_id="broken", tracking=False)
    record = receipt(repository, "EXP001", "broken")
    assert record["status"] == terminal
    assert Registry(repository).get("EXP001")["status"] == "BLOCKED"
    assert "private-path-and-token" not in json.dumps(compare(repository))
    assert {r["value"] for r in compare(repository)} == {None}


def test_append_only_and_stale_lock_fail_closed(repository):
    """No truncar evidencia ni adquirir dos veces el lock del registro."""
    path = repository / "receipt.json"
    exclusive_json(path, {"status": "FAILED"})
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        exclusive_json(path, {"status": "COMPLETED"})
    assert path.read_bytes() == before
    with registry_lock(repository):
        with pytest.raises(FileExistsError):
            with registry_lock(repository):
                pass
    with pytest.raises(ValueError):
        confined(
            repository,
            "docs/evidence/experiments/../task16",
            "docs/evidence/experiments",
            exists=False,
        )


def test_legal_transitions_and_conclusions_required(repository):
    """PROPOSED→APPROVED→RUNNING; COMPLETED requiere evidencia y aprendizaje completo."""
    registry = Registry(repository)
    with pytest.raises(ValueError, match="Transición"):
        registry.transition("EXP001", "COMPLETED")
    registry.entries["EXP001"]["status"] = "PROPOSED"
    registry.transition("EXP001", "APPROVED")
    registry.transition("EXP001", "RUNNING")
    with pytest.raises(ValueError):
        registry.transition("EXP001", "COMPLETED", "NEGATIVE")
    registry.transition("EXP001", "BLOCKED", "BLOCKED")
    with pytest.raises(ValueError):
        registry.transition("EXP001", "APPROVED")


def test_identity_cannot_be_reused_with_new_recipe(repository, monkeypatch):
    """Cambiar protocolo y recalcular el hash no borra la identidad histórica."""

    def broken(*args):
        raise RuntimeError("controlled")

    monkeypatch.setattr(runner, "acquire_and_build", broken)
    with pytest.raises(runner.ExecutionError):
        runner.execute("EXP001", root=repository, execution_id="history", tracking=False)
    path = repository / "docs/experiments/EXP001/SPECIFICATION.md"
    path.write_text(path.read_text() + "\nChanged protocol\n")
    document = read_yaml(repository / "docs/experiments/registry.yml")
    document["experiments"][0].update(protocol_sha256=sha256(path), status="APPROVED")
    save_registry(repository, document)
    with pytest.raises(ValueError, match="otra receta"):
        runner.execute("EXP001", root=repository, tracking=False)
    assert receipt(repository, "EXP001", "history")["status"] == "FAILED"


def test_real_local_mlflow_hierarchy_and_metrics(repository):
    """SQLite real: padre e hijos para T+1/T+2, referencias Git y métricas agregadas."""
    record = runner.execute("EXP001", root=repository, execution_id="tracking", tracking=True)
    tracker = ExperimentTracker(repository / "pipeline", True)
    try:
        parent = tracker.get_run(record["mlflow"]["parent_run_id"])
        assert parent.info.status == "FINISHED"
        assert parent.data.tags["status"] == "COMPLETED"
        assert parent.data.tags["execution_signature"] == record["execution_signature"]
        assert parent.data.metrics
        assert len(record["mlflow"]["children"]) == 2
        for child_id in record["mlflow"]["children"]:
            child = tracker.get_run(child_id)
            assert child.info.status == "FINISHED"
            assert child.data.tags["mlflow.parentRunId"] == parent.info.run_id
            assert child.data.metrics
    finally:
        tracker.close()


def test_tracking_failure_is_terminal_and_does_not_hide_success(repository, monkeypatch):
    """Un fallo del store deja el padre FAILED y recibo público sin mensaje privado."""

    def failed_finish(self, *args, **kwargs):
        raise RuntimeError("controlled logging failure")

    monkeypatch.setattr(ExperimentTracker, "finish", failed_finish)
    with pytest.raises(runner.ExecutionError):
        runner.execute("EXP002", root=repository, execution_id="tracking-failed", tracking=True)
    record = receipt(repository, "EXP002", "tracking-failed")
    assert record["status"] == "FAILED" and record["gate"] == "tracking"
    tracker = ExperimentTracker(repository / "pipeline", True)
    try:
        assert tracker.get_run(record["mlflow"]["parent_run_id"]).info.status == "FAILED"
    finally:
        tracker.close()


def test_completed_negative_result_requires_conclusions_and_verified_evidence(repository):
    """Aceptar aprendizaje negativo solo tras secciones completas y evidencia íntegra."""
    from sat_dengue_pipeline.experiment_management.registry import CONCLUSION_SECTIONS

    runner.execute("EXP002", root=repository, execution_id="reviewed", tracking=False)
    registry = Registry(repository)
    path = repository / registry.get("EXP002")["conclusions"]
    reference = "docs/evidence/experiments/EXP002/reviewed/inventory.json"
    path.write_text(
        "# EXP002 NEGATIVE\n\n"
        + "\n\n".join(
            "## "
            + section
            + "\nConclusión técnica explícita, sin aprobación científica. "
            + reference
            for section in CONCLUSION_SECTIONS
        )
    )
    registry.transition("EXP002", "COMPLETED", "NEGATIVE")
    assert Registry(repository).get("EXP002")["scientific_result"] == "NEGATIVE"
    assert {r["scientific_result"] for r in compare(repository)} == {"NEGATIVE"}
    metrics = repository / "docs/evidence/experiments/EXP002/reviewed/metrics.json"
    metrics.write_text("{}")
    with pytest.raises(ValueError, match="alterado"):
        Registry(repository)


def test_signature_stable_across_execution_ids_and_no_overwrite(repository):
    """Dos checkouts de la misma aprobación conservan firma, con execution_id distinto."""
    other = repository / "another-checkout"
    shutil.copytree(repository / "docs", other / "docs")
    shutil.copytree(repository / "pipeline", other / "pipeline")
    first = runner.execute("EXP002", root=repository, execution_id="first", tracking=False)
    second = runner.execute("EXP002", root=other, execution_id="second", tracking=False)
    assert first["execution_signature"] == second["execution_signature"]
    assert first["execution_id"] != second["execution_id"]
    assert receipt(repository, "EXP002", "first") == first


def test_repeated_execution_id_cannot_destroy_prior_receipt(repository, monkeypatch):
    """Aun restaurando APPROVED, mkdir exclusivo conserva la corrida anterior."""

    def broken(*args):
        raise RuntimeError("controlled")

    monkeypatch.setattr(runner, "acquire_and_build", broken)
    original = Registry(repository).document
    with pytest.raises(runner.ExecutionError):
        runner.execute("EXP002", root=repository, execution_id="fixed", tracking=False)
    before = receipt(repository, "EXP002", "fixed")
    save_registry(repository, original)
    with pytest.raises(FileExistsError):
        runner.execute("EXP002", root=repository, execution_id="fixed", tracking=False)
    assert receipt(repository, "EXP002", "fixed") == before


def test_evidence_write_failure_marks_parent_failed_and_blocks_registry(repository, monkeypatch):
    """Paquete incompleto no se compara como éxito; recuperación local conserva el fallo."""

    def broken_publish(*args):
        raise OSError("controlled evidence disk error")

    monkeypatch.setattr(runner, "publish", broken_publish)
    with pytest.raises(runner.ExecutionError, match="evidence_publish"):
        runner.execute("EXP002", root=repository, execution_id="disk", tracking=True)
    recovery = json.loads(
        (repository / "pipeline/data/experiments/disk/evidence-failure.json").read_bytes()
    )
    assert recovery["status"] == "FAILED"
    assert Registry(repository).get("EXP002")["status"] == "BLOCKED"
    tracker = ExperimentTracker(repository / "pipeline", True)
    try:
        assert tracker.get_run(recovery["mlflow"]["parent_run_id"]).info.status == "FAILED"
    finally:
        tracker.close()
    with pytest.raises(ValueError):
        compare(repository)


def test_one_horizon_one_model_and_no_redundant_child(repository):
    """T+1 por sí solo también usa el arnés compartido sin asumir que existe T+2."""

    def single(config):
        config["horizons"] = [1]
        config["roles_by_horizon"] = {"1": config["roles_by_horizon"]["2"]}
        config["threshold"]["max_false_alarm_ratio_by_horizon"] = {"1": 1.0}

    change_config(repository, "EXP002", single)
    result = runner.execute("EXP002", root=repository, execution_id="one", tracking=True)
    assert result["horizons"] == [1] and result["mlflow"]["children"] == []
    assert {row["horizon"] for row in compare(repository)} == {1}


def test_cli_registration_and_explicit_approval(repository, monkeypatch, capsys):
    """El comando público registra propuestas y exige una transición separada para aprobar."""
    import sys

    from sat_dengue_pipeline.experiment_management.__main__ import main

    entry = Registry(repository).get("EXP002")
    entry.update(
        experiment_id="EXP003",
        experiment_slug="new-fixture",
        hypothesis_id="EXP003-H0",
        status="PROPOSED",
        scientific_result="PENDING",
        protocol="docs/experiments/EXP003/SPECIFICATION.md",
        configuration="pipeline/conf/experiments/EXP003.yml",
        conclusions="docs/experiments/EXP003/CONCLUSIONS.md",
    )
    protocol = repository / entry["protocol"]
    protocol.parent.mkdir()
    protocol.write_text("# EXP003 fixture protocol frozen for CLI test\n")
    config = repository / entry["configuration"]
    shutil.copyfile(repository / "pipeline/conf/experiments/EXP002.yml", config)
    entry.update(protocol_sha256=sha256(protocol), configuration_sha256=sha256(config))
    registration = protocol.parent / "registration.yml"
    registration.write_text(yaml.safe_dump(entry))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "experiments",
            "--root",
            str(repository),
            "register",
            "--entry",
            "docs/experiments/EXP003/registration.yml",
        ],
    )
    main()
    assert json.loads(capsys.readouterr().out)["status"] == "OK"
    assert Registry(repository).get("EXP003")["status"] == "PROPOSED"
    with pytest.raises(ValueError):
        main()
    monkeypatch.setattr(
        sys, "argv", ["experiments", "--root", str(repository), "transition", "EXP003", "APPROVED"]
    )
    main()
    assert Registry(repository).get("EXP003", approved=True)["status"] == "APPROVED"


def test_comparison_reads_only_registry_and_aggregate_evidence(repository, monkeypatch):
    """Comparar sin abrir protocolo/configuración, datos, modelos o conclusiones."""
    runner.execute("EXP002", root=repository, execution_id="offline", tracking=False)
    original = Path.read_text

    def limited_read(path, *args, **kwargs):
        if path.name != "registry.yml":
            raise AssertionError("Comparison opened an external document")
        return original(path, *args, **kwargs)

    original_bytes = Path.read_bytes

    def limited_bytes(path):
        if path.name != "registry.yml" and not path.is_relative_to(repository / "docs/evidence"):
            raise AssertionError("Comparison opened an external document")
        return original_bytes(path)

    monkeypatch.setattr(Path, "read_text", limited_read)
    monkeypatch.setattr(Path, "read_bytes", limited_bytes)
    assert compare(repository, horizon=2)


@pytest.mark.parametrize("document", ["configuration", "protocol"])
def test_document_changed_after_registry_read_is_rejected(repository, document):
    """Rechazar bytes alterados entre resolver el registro y materializar la receta."""
    entry = Registry(repository).get("EXP001")
    path = repository / entry[document]
    if document == "configuration":
        config = read_yaml(path)
        config["threshold"]["grid"] = [0.0, 0.5, 1.0]
        path.write_text(yaml.safe_dump(config))
    else:
        path.write_text(path.read_text() + "\nProtocol changed after registry lookup.\n")
    with pytest.raises(ValueError, match="alterad"):
        load_configuration(repository, entry)
