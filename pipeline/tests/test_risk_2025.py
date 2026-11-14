"""Centinelas focalizados de prioridades; ningún dato ni modelo científico real."""

import ast
import copy
import json
import runpy
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import KEYS, PREDICTORS
from sat_dengue_pipeline.models.logistic import LogisticOnsetAdapter, canonical_json
from sat_dengue_pipeline.pipelines.deployment_publication import io
from sat_dengue_pipeline.pipelines.deployment_publication.package import PublicationPackage
from sat_dengue_pipeline.risk.configuration import ROOT, digest, local_path, sha
from sat_dengue_pipeline.risk.frozen import (
    decode_artifact,
    load_artifact,
    materialize,
    save_artifact,
)
from sat_dengue_pipeline.risk.inference import feature_prefix, prioritize
from sat_dengue_pipeline.risk.publication import (
    build_package,
    load_schema,
    validate_document,
    validate_package,
)


@pytest.fixture
def training() -> tuple:
    """Tabla artificial mínima con etiquetas maduras solo hasta septiembre de 2024."""
    rows = []
    for d, n in (("50", 29), ("73", 47)):
        for i in range(n):
            code = f"{d}{900 + i:03d}"
            for month in ("2024-07", "2024-08", "2024-09", "2024-10"):
                row = {p: float(i + 1) for p in PREDICTORS}
                row.update(
                    municipality_code=code,
                    year_month=month,
                    department_code=d,
                    municipality_name="FICTICIO " + code,
                    zona_canal_t="SEGURIDAD",
                )
                if month == "2024-09" and i < 10:
                    row["zona_canal_t"] = "EXCESO"
                rows.append(row)
    table = pd.DataFrame(rows).sort_values(KEYS).reset_index(drop=True)
    for name in PREDICTORS:
        table[name] = table[name].astype("string" if name == "zona_canal_t" else "Float64")
    for name in [*KEYS, "department_code", "municipality_name"]:
        table[name] = table[name].astype("string")
    schema = {
        "column_roles": {
            "key": KEYS,
            "metadata": ["department_code", "municipality_name"],
            "feature": PREDICTORS,
            "target": [],
            "control": [],
        }
    }
    provenance = {
        "code_sha": "a" * 40,
        "lock_sha256": "b" * 64,
        "code_tree_sha256": "c" * 64,
        "raw_manifest_sha256": "d" * 64,
    }
    return table, schema, provenance


@pytest.fixture
def frozen(training) -> object:
    """Materializar solo un modelo artificial pequeño, sin entrenamiento real."""
    return materialize(*training)


def current(training, origin="2024-11") -> tuple:
    """Construir una entrada observable artificial sin desenlaces."""
    table, schema, _ = training
    table = table.loc[table.year_month.eq("2024-07")].copy()
    table["year_month"] = origin
    return table, schema


def fixture_document() -> dict:
    """Leer la misma fuente pública artificial de los tres consumidores."""
    return json.loads((ROOT / "contracts/fixtures/risk-ranking.json").read_bytes())


def fixture_package() -> object:
    """Crear los doce meses sintéticos para probar únicamente la transacción."""
    docs = []
    for month in range(1, 13):
        d = fixture_document()
        d["target_period"] = f"2025-{month:02d}"
        d["reference_period"] = d["data_cutoff"] = add_months(d["target_period"], -2)
        docs.append(d)
    return build_package(docs)


def test_fit_once_reload_exactly_and_no_fit_during_scoring(training, monkeypatch, tmp_path):
    """La materialización ajusta una vez y la carga conserva el estado efectivo."""
    calls = []
    original = LogisticOnsetAdapter.fit

    def spy(self, X, y):
        """Contar ajustes efectivos."""
        calls.append(1)
        return original(self, X, y)

    monkeypatch.setattr(LogisticOnsetAdapter, "fit", spy)
    model = materialize(*training)
    assert len(calls) == 1
    save_artifact(model, tmp_path / "artifact")

    def forbidden(*args, **kwargs):
        """Fallar si carga o scoring intentan aprender."""
        pytest.fail("fit prohibido después del freeze")

    monkeypatch.setattr(LogisticOnsetAdapter, "fit", forbidden)
    loaded = load_artifact(tmp_path / "artifact", model.artifact_sha256, training[2])
    X = training[0].loc[training[0].year_month.eq("2024-07"), PREDICTORS].reset_index(drop=True)
    assert loaded.payload == model.payload
    assert np.array_equal(loaded.score(X), model.score(X))
    assert loaded.payload["last_training_available"] < "2024-11"
    bad = copy.deepcopy(model.payload)
    bad["procedure"]["train_end"] = "2025-01"
    raw = canonical_json(bad)
    with pytest.raises(ValueError):
        decode_artifact(raw, sha(raw), training[2])


@pytest.mark.parametrize("period", ["2024-11", "2025-01", "2025-10"])
def test_learning_rejects_future_before_any_fit(training, monkeypatch, period):
    """Las observaciones posteriores al corte no llegan a etiquetas ni al ajuste."""
    table, schema, provenance = training
    future = table.iloc[:1].copy()
    future["year_month"] = period

    def forbidden(*args, **kwargs):
        """Detectar lectores que jamás deben ejecutarse."""
        pytest.fail("Se accedió a un consumidor aprendido")

    monkeypatch.setattr(LogisticOnsetAdapter, "fit", forbidden)
    import sat_dengue_pipeline.preparation as preparation

    monkeypatch.setattr(preparation, "build_labels", forbidden)
    with pytest.raises(ValueError, match="corte"):
        materialize(pd.concat([table, future]), schema, provenance)


def test_ranking_is_global_deterministic_and_ties_use_code(training, frozen):
    """Empates y permutaciones no reasignan las ocho plazas globales."""
    table, schema = current(training)
    for name in PREDICTORS:
        if name != "zona_canal_t":
            table[name] = 1.0
            table[name] = table[name].astype("Float64")
    first, feature_hash = prioritize(table, schema, "2024-11", frozen)
    shuffled, second_hash = prioritize(
        table.sample(frac=1, random_state=7), schema, "2024-11", frozen
    )
    assert first == shuffled and feature_hash == second_hash
    assert [r["municipality_code"] for r in first if r["selected_for_attention"]] == [
        f"50{i}" for i in range(900, 908)
    ]
    filtered = [r for r in first if r["department_code"] == "73"]
    assert min(r["risk_rank"] for r in filtered) == 30
    assert sum(r["selected_for_attention"] for r in filtered) == 0


def test_less_than_eight_and_labels_and_future_fail(training, frozen):
    """No completar cupo con ineligibles ni consumir desenlaces o futuro."""
    table, schema = current(training)
    table.loc[7:, "zona_canal_t"] = "EXCESO"
    with pytest.raises(ValueError, match="ocho"):
        prioritize(table, schema, "2024-11", frozen)
    table, schema = current(training)
    table["y_true"] = 0
    with pytest.raises(ValueError, match="etiquetas"):
        prioritize(table, schema, "2024-11", frozen)
    table, schema = current(training, "2025-11")
    with pytest.raises(ValueError):
        prioritize(table, schema, "2025-11", frozen)


@pytest.mark.parametrize("target,origin", [("2025-01", "2024-11"), ("2025-12", "2025-10")])
def test_calendar(target, origin):
    """Los extremos de 2025 nunca generan objetivos de 2026."""
    d = fixture_document()
    d.update(target_period=target, reference_period=origin, data_cutoff=origin)
    validate_document(d, load_schema())
    d["reference_period"] = "2025-12"
    with pytest.raises(ValueError):
        validate_document(d, load_schema())


@pytest.mark.parametrize("field", ["probability", "threshold", "y_true", "TP", "false_alerts"])
def test_contract_forbids_observed_outcomes_and_probabilities(field):
    """Los consumidores no admiten resultados observados ni campos probabilísticos."""
    d = fixture_document()
    d["municipalities"][0][field] = 0
    with pytest.raises(Exception):
        validate_document(d, load_schema())


@pytest.mark.parametrize("kind", ["calendar", "rank", "selection", "department", "version"])
def test_contract_rejects_same_cross_field_fixtures_as_api_and_zod(kind):
    """Los tres consumidores rechazan las mismas relaciones incompatibles."""
    d = fixture_document()
    if kind == "calendar":
        d["reference_period"] = "2025-12"
    if kind == "rank":
        d["municipalities"][0]["risk_rank"] = 2
    if kind == "selection":
        d["municipalities"][0]["selected_for_attention"] = False
    if kind == "department":
        d["municipalities"][0]["department_code"] = "73"
    if kind == "version":
        d["schema_version"] = "wrong"
    with pytest.raises(Exception):
        validate_document(d, load_schema())


@pytest.mark.parametrize("value,valid", [(1.0, True), ("1", False), (True, False), (1.5, False)])
def test_json_numeric_integer_parity(value, valid):
    """JSON Schema y JavaScript no distinguen 1 de 1.0, sí bool y string."""
    d = fixture_document()
    d["municipalities"][0]["risk_rank"] = value
    if valid:
        validate_document(d, load_schema())
    else:
        with pytest.raises(Exception):
            validate_document(d, load_schema())


def test_package_is_complete_and_staging_tamper_preserves_previous(tmp_path):
    """Paquetes incompletos, sabotaje y ediciones distintas fallan sin promover."""
    package = fixture_package()
    schema = load_schema()
    with pytest.raises(ValueError):
        validate_package(PublicationPackage(package.files[:-1], package.manifest, {}), schema)
    altered = json.loads(package.manifest)
    altered["files"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256"):
        validate_package(PublicationPackage(package.files, canonical_json(altered), {}), schema)
    destination = tmp_path / "results"
    stage = io.stage_package(package, destination, schema)
    file = stage.root / "new" / package.files[0].name
    file.write_bytes(file.read_bytes() + b" ")
    with pytest.raises(Exception):
        io.validate_staging(stage, schema)
    assert not destination.exists()
    io.promote(io.validate_staging(io.stage_package(package, destination, schema), schema), schema)
    before = {
        p.relative_to(destination): p.read_bytes() for p in destination.rglob("*") if p.is_file()
    }
    docs = [json.loads(f.content) for f in package.files]
    for d in docs:
        d["data_version"] = "different"
    different = build_package(docs)
    with pytest.raises(Exception):
        io.promote(
            io.validate_staging(io.stage_package(different, destination, schema), schema), schema
        )
    assert before == {
        p.relative_to(destination): p.read_bytes() for p in destination.rglob("*") if p.is_file()
    }


def test_promote_failure_rolls_back(tmp_path, monkeypatch):
    """Un fallo tras el primer rename elimina solo los archivos nuevos del intento."""
    package = fixture_package()
    schema = load_schema()
    previous = tmp_path / "previous-edition"
    io.promote(io.validate_staging(io.stage_package(package, previous, schema), schema), schema)
    protected = {
        p.relative_to(previous): p.read_bytes() for p in previous.rglob("*") if p.is_file()
    }
    destination = tmp_path / "new-edition"
    original = io._replace
    calls = []

    def fail(source, target):
        """Sabotear la segunda promoción."""
        calls.append(target)
        if len(calls) == 2:
            raise OSError("controlled failure")
        original(source, target)

    monkeypatch.setattr(io, "_replace", fail)
    with pytest.raises(Exception):
        io.promote(
            io.validate_staging(io.stage_package(package, destination, schema), schema), schema
        )
    assert not destination.exists()
    assert protected == {
        p.relative_to(previous): p.read_bytes() for p in previous.rglob("*") if p.is_file()
    }


def test_publication_paths_cannot_escape_worktree():
    """No usar rutas o enlaces al entorno de EXP006."""
    with pytest.raises(ValueError):
        local_path("../../sat-dengue-despliegue/pipeline/data/model")
    with pytest.raises(ValueError):
        local_path("../app/api/forbidden")


def test_inference_does_not_import_outcome_builders():
    """La proyección independiente no importa constructores de desenlaces."""
    tree = ast.parse((ROOT / "pipeline/src/sat_dengue_pipeline/risk/inference.py").read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any(n and n.endswith(("preparation", "onset", "paired")) for n in imports)
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import sat_dengue_pipeline.risk.inference; "
                "assert not any(m.startswith('sat_dengue_pipeline') and "
                "m.endswith(('preparation', 'onset', 'paired')) for m in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
    )


def test_activation_uses_certified_pins_and_never_repeats_implicitly(tmp_path, monkeypatch):
    """Probar el comando de activación con un certificado falso, sin ejecutar N=3."""
    main = runpy.run_path(str(ROOT / "pipeline/tools/certify_risk_2025.py"))["main"]
    pins = {
        "artifact_directory": "data/model",
        "artifact_sha256": "a" * 64,
        "certificate": "data/certification.json",
        "certificate_sha256": "b" * 64,
    }
    calls = []

    def fake_certify(**kwargs):
        """No ejecutar procesos, fuentes o ajustes."""
        calls.append(kwargs)
        return pins

    monkeypatch.setitem(main.__globals__, "certify", fake_certify)
    monkeypatch.setitem(main.__globals__, "local_path", lambda p: tmp_path / "approved.json")
    monkeypatch.setattr(sys, "argv", ["certify_risk_2025.py", "--activate"])
    main()
    assert json.loads((tmp_path / "approved.json").read_bytes()) == pins
    with pytest.raises(SystemExit):
        main()
    assert calls == [{"synthetic": False}]
    monkeypatch.setattr(sys, "argv", ["certify_risk_2025.py", "--activate", "--synthetic"])
    with pytest.raises(SystemExit):
        main()
    assert len(calls) == 1


def test_frozen_preflight_fails_before_acquisition_or_fit(tmp_path, monkeypatch):
    """Un artefacto ausente no activa descargas ni entrenamiento alternativo."""
    from sat_dengue_pipeline.risk import nodes

    def forbidden(*args, **kwargs):
        """Ninguna recuperación implícita está autorizada."""
        pytest.fail("Adquisición o fit durante preflight congelado")

    monkeypatch.setattr(nodes, "local_path", lambda p: tmp_path / p)
    monkeypatch.setattr(nodes, "acquire", forbidden)
    monkeypatch.setattr(LogisticOnsetAdapter, "fit", forbidden)
    settings = {
        "mode": "frozen",
        "source": "approved",
        "artifact_directory": "missing",
        "artifact_sha256": "a" * 64,
        "certificate": "missing-certificate.json",
        "certificate_sha256": "b" * 64,
        "edition": "artificial",
    }
    with pytest.raises(FileNotFoundError):
        nodes.preflight(settings)
    receipt = next(tmp_path.glob("data/risk-2025/runs/*/receipt.json"))
    assert json.loads(receipt.read_bytes())["failed_stage"] == "preflight"


def test_frozen_node_cannot_fall_back_to_training(training, tmp_path, monkeypatch):
    """El nodo también falla cerrado si se lo invoca sin el preflight."""
    from sat_dengue_pipeline.risk import nodes

    def forbidden(*args, **kwargs):
        """No interpretar fuentes ni aprender en una carga congelada incompleta."""
        pytest.fail("Fallback de entrenamiento")

    context = nodes.Context({"mode": "frozen"}, tmp_path / "missing", tmp_path, training[2])
    monkeypatch.setattr(nodes, "feature_prefix", forbidden)
    monkeypatch.setattr(nodes, "materialize", forbidden)
    with pytest.raises(ValueError, match="fallback"):
        nodes.frozen_model(context, None)


def test_frozen_tamper_and_native_parameters_are_rejected(training, frozen, tmp_path):
    """Modelo, manifiesto, biblioteca y preparación tienen identidad explícita."""
    save_artifact(frozen, tmp_path / "artifact")
    (tmp_path / "artifact/model.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="SHA-256"):
        load_artifact(tmp_path / "artifact", frozen.artifact_sha256, training[2])
    payload = copy.deepcopy(frozen.payload)
    payload["state"]["native_configuration"]["params"]["C"] = 9
    payload["effective_state_sha256"] = digest(payload["state"])
    raw = canonical_json(payload)
    with pytest.raises(ValueError, match="parámetros"):
        decode_artifact(raw, sha(raw), training[2])


def test_frozen_accepts_only_descendant_with_identical_scientific_lineage(
    training, frozen, monkeypatch
):
    """Permitir cierres documentales sin alterar la procedencia del modelo."""
    from types import SimpleNamespace

    from sat_dengue_pipeline.risk import frozen as module

    current_provenance = {**training[2], "code_sha": "b" * 40}
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0))
    raw = canonical_json(frozen.payload)
    loaded = decode_artifact(raw, sha(raw), current_provenance)
    assert loaded.payload["provenance"] == training[2]
    for key in ("lock_sha256", "code_tree_sha256", "raw_manifest_sha256"):
        with pytest.raises(ValueError, match="Identidad"):
            decode_artifact(raw, sha(raw), {**current_provenance, key: "e" * 64})
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1))
    with pytest.raises(ValueError, match="ancestro"):
        decode_artifact(raw, sha(raw), current_provenance)


def test_publication_does_not_fit(training, frozen, tmp_path, monkeypatch):
    """El recorrido posterior al freeze no aprende ni consulta etiquetas."""
    import sat_dengue_pipeline.preparation as preparation
    from sat_dengue_pipeline.risk import nodes

    def forbidden(*args, **kwargs):
        """Detener llamadas de aprendizaje o desenlaces en publicación."""
        pytest.fail("fit o etiquetas durante publicación")

    monkeypatch.setattr(LogisticOnsetAdapter, "fit", forbidden)
    monkeypatch.setattr(preparation, "build_labels", forbidden)
    table, schema = current(training)
    rows, _ = prioritize(table, schema, "2024-11", frozen)
    assert sum(r["selected_for_attention"] for r in rows) == 8
    context = nodes.Context(
        {"mode": "frozen", "source": "synthetic", "edition": "test"},
        tmp_path / "model",
        tmp_path,
        training[2],
    )
    result = fixture_package()
    context.receipt["certified_package_sha256"] = sha(result.manifest)
    validated = nodes.package(context, [json.loads(f.content) for f in result.files])
    nodes.publish(context, validated)
    assert context.receipt["status"] == "COMMITTED"


def test_kedro_catalog_keeps_receipt_state_between_nodes(training, tmp_path):
    """El catálogo configurado no pierde mutaciones por copias profundas."""
    import yaml
    from kedro.io import DataCatalog, MemoryDataset

    from sat_dengue_pipeline.risk.nodes import Context

    config = yaml.safe_load((ROOT / "pipeline/conf/base/catalog_risk_2025.yml").read_text())
    assert config["risk_context"] == {"type": "MemoryDataset", "copy_mode": "assign"}
    catalog = DataCatalog(
        {"risk_context": MemoryDataset(copy_mode=config["risk_context"]["copy_mode"])}
    )
    context = Context({}, tmp_path / "model", tmp_path, training[2])
    catalog.save("risk_context", context)
    catalog.load("risk_context").receipt["artifact_sha256"] = "a" * 64
    assert catalog.load("risk_context").receipt["artifact_sha256"] == "a" * 64


@pytest.mark.intensive
def test_five_sources_future_invariance(tmp_path, monkeypatch):
    """Aceptación diferida: ni valores futuros maliciosos llegan al productor."""
    from sat_dengue_pipeline.raw.fixture import fixture_inventory
    from sat_dengue_pipeline.risk.synthetic import write_sources

    bundle, _ = write_sources(tmp_path / "raw")
    train, train_schema = feature_prefix(bundle, "2024-10", dimension_count=76)
    model = materialize(
        train,
        train_schema,
        {
            "code_sha": "a" * 40,
            "code_tree_sha256": "b" * 64,
            "lock_sha256": "c" * 64,
            "raw_manifest_sha256": "d" * 64,
        },
    )
    first, schema = feature_prefix(bundle, "2024-11", dimension_count=76)
    climate = tmp_path / "raw/google_earth_engine.csv"
    with climate.open("a") as stream:
        stream.write("2025-12-01,2025,12,335,50,,900,50900,,MUST_NOT_PARSE\n")
    second, _ = feature_prefix(
        fixture_inventory(tmp_path / "raw")[0], "2024-11", dimension_count=76
    )
    pd.testing.assert_frame_equal(first, second)
    assert prioritize(first, schema, "2024-11", model) == prioritize(
        second, schema, "2024-11", model
    )
    assert schema["column_roles"]["target"] == []
