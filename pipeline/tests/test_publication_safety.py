"""Gates, contrato y rollback con fallos reales de filesystem inyectados sobre fixtures."""

import ast
import hashlib
import json
import subprocess
import sys
import uuid
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from fixtures.publication_fixture import GENERATED, PROCEDURE, publication_rows

from sat_dengue_pipeline.pipelines.deployment_publication import domain as d
from sat_dengue_pipeline.pipelines.deployment_publication import io
from sat_dengue_pipeline.pipelines.deployment_publication.contract import validate_document
from sat_dengue_pipeline.pipelines.deployment_publication.errors import (
    PublicationContractError,
    PublicationError,
    PublicationInputError,
    PublicationTransactionError,
)
from sat_dengue_pipeline.pipelines.deployment_publication.io import (
    load_schema,
    promote,
    stage_package,
    validate_staging,
)
from sat_dengue_pipeline.pipelines.deployment_publication.package import (
    PublicationConfig,
    PublicationFile,
    build_package,
    encode_json,
)


@pytest.fixture
def package():
    """Construir dos documentos artificiales, sin publicaciones del repositorio."""
    return build_package(
        *publication_rows(), PublicationConfig(PROCEDURE, "synthetic-v1", GENERATED)
    )


def snapshot(root):
    """Observar únicamente un directorio temporal propiedad de la prueba."""
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def alter_file(package, content=None, name=None):
    """Recalcular hashes para que las pruebas inválidas alcancen el gate contractual."""
    first, *rest = package.files
    files = tuple(
        sorted(
            (
                PublicationFile(
                    name or first.name, content if content is not None else first.content
                ),
                *rest,
            ),
            key=lambda f: f.name,
        )
    )
    manifest = json.loads(package.manifest)
    manifest["files"] = [
        {
            "name": f.name,
            "size_bytes": len(f.content),
            "sha256": hashlib.sha256(f.content).hexdigest(),
        }
        for f in files
    ]
    return replace(package, files=files, manifest=encode_json(manifest))


def publish(package, out):
    """Ejecutar los gates productivos sin sustituir la promoción real."""
    schema = load_schema()
    return promote(validate_staging(stage_package(package, out, schema), schema), schema)


def test_states_names_channel_uuids_and_governance(package):
    """Preservar reglas visibles, nombres propios y casos del canal en ambos departamentos."""
    assert package.audit["thresholds"] == {
        h: {"value": 0.8, "margin": 0.7000000000000001} for h in ("1", "2")
    }
    assert package.audit["omitted_periods"] == ["2024-03"]
    for file in package.files:
        doc = json.loads(file.content)
        dept = doc["department"]["department_code"]
        assert doc["department"]["department_name"] == {"50": "Meta", "73": "Tolima"}[dept]
        towns = doc["municipalities"]
        assert [t["municipality_code"] for t in towns] == sorted(
            t["municipality_code"] for t in towns
        )
        assert towns[0]["municipality_name"] == "San Juan de la Sierra"
        assert towns[1]["municipality_name"] == "Ficticio del Río"
        assert towns[0]["cases_t"] == 20  # Nunca total_notifications_count=999.
        assert [t["results"][0]["availability_status"] for t in towns[:6]] == [
            "AVAILABLE",
            "AVAILABLE",
            "MISSING_DATA",
            "INSUFFICIENT_HISTORY",
            "NOT_CALCULATED",
            "NOT_CALCULATED",
        ]
        assert towns[0]["results"][0]["alert_status"] == "NO_ALERT"
        assert towns[1]["results"][0]["alert_status"] == "ALERT"
        assert towns[2]["municipality_name"] == dept + "002"
        result = towns[0]["results"][0]
        assert result["result_id"] == str(
            uuid.uuid5(d.ESPACIO_IDS, f"{PROCEDURE}|{dept}000|2024-02|1")
        )
        assert result["model_role"] == "PROVISIONAL_CANDIDATE"
        assert doc["governance"]["governance_status"] == "NOT_APPROVED"
        assert doc["governance"]["champion_status"] == "NOT_SELECTED"
        point = towns[0]["endemic_channel_series"][2]
        assert point["period"] == "2024-03" and point["cases"] is None and point["p75"] == 15
        refs = [
            r
            for r in doc["evaluation_context"]["comparison"]
            if r["source"] == "computed_from_panel"
        ]
        assert [r["actual_onsets"] for r in refs] == [2, 2]
        assert all(r["candidate"] == "endemic_channel" for r in refs)


def test_ineligible_contract_without_inventing_legacy_eligibility(package):
    """Aceptar INELIGIBLE contractual y preservar el fallback legado caracterizado."""
    file = package.files[0]
    doc = json.loads(file.content)
    doc["municipalities"][4]["results"][0]["availability_status"] = "INELIGIBLE"
    validate_document(doc, load_schema(), file.name)


@pytest.mark.parametrize(
    "failure", ["absent", "reference_only", "no_t1", "no_alerts", "nonseparable"]
)
def test_candidate_and_threshold_errors(failure):
    """Nunca fabricar un candidato o umbral cuando las entradas no lo permiten."""
    panel, predictions, comparison, retro = publication_rows()
    config = PublicationConfig(PROCEDURE, "synthetic-v1", GENERATED)
    if failure == "absent":
        config = replace(config, candidato="unknown")
    elif failure == "reference_only":
        comparison = [r for r in comparison if r["result"] == "reference"]
    elif failure == "no_t1":
        comparison = [r for r in comparison if r["horizon"] == "2"]
    else:
        for row in predictions:
            if row["candidate"] == "lightgbm":
                row["prediction_label"] = (
                    "0"
                    if failure == "no_alerts"
                    else ("1" if row["prediction_probability"] == "0.1" else "0")
                )
    with pytest.raises(PublicationError, match="ERROR:"):
        build_package(panel, predictions, comparison, retro, config)


@pytest.mark.parametrize("value", ["-0.1", "1.1", "nan", "inf", "not-a-number"])
def test_invalid_probability_rejected(value):
    """Rechazar probabilidades inválidas antes de serializar o publicar."""
    panel, predictions, comparison, retro = publication_rows()
    predictions[0]["prediction_probability"] = value
    with pytest.raises(PublicationInputError):
        build_package(
            panel, predictions, comparison, retro, PublicationConfig(PROCEDURE, "v1", GENERATED)
        )


@pytest.mark.parametrize("index", [0, 1, 2])
def test_duplicate_input_keys_rejected(index):
    """No resolver claves repetidas mediante el orden físico de las filas."""
    rows = list(publication_rows())
    rows[index].append(deepcopy(rows[index][0]))
    with pytest.raises(PublicationInputError, match="duplicadas"):
        build_package(*rows, PublicationConfig(PROCEDURE, "v1", GENERATED))


def test_ids_do_not_depend_on_generation_time(package):
    """El UUID depende del procedimiento y claves, conservando el espacio histórico."""
    other = build_package(
        *publication_rows(),
        PublicationConfig(PROCEDURE, "synthetic-v1", "2024-07-02T12:00:00+00:00"),
    )
    for first, second in zip(package.files, other.files, strict=True):
        a, b = json.loads(first.content), json.loads(second.content)
        assert a["metadata"]["result_set_id"] == b["metadata"]["result_set_id"]
        assert [t["results"] for t in a["municipalities"]] == [
            t["results"] for t in b["municipalities"]
        ]


def test_all_single_horizon_periods_omitted():
    """Sin meses completos se conserva la salida de cero resultados del legado."""
    panel, predictions, comparison, retro = publication_rows()
    predictions = [r for r in predictions if r["horizon"] == "1"]
    result = build_package(
        panel, predictions, comparison, retro, PublicationConfig(PROCEDURE, "v1", GENERATED)
    )
    assert result.files == ()


def test_partial_staging_failure_preserves_previous(package, tmp_path, monkeypatch):
    """Una escritura parcial nunca se expone bajo el destino publicado."""
    out = tmp_path / "out"
    publish(package, out)
    before, write, calls = snapshot(out), io._write_file, []

    def fail(path, data):
        """Fallar al escribir el segundo archivo dentro del staging privado."""
        calls.append(path)
        if len(calls) == 2:
            path.write_bytes(b"partial")
            raise OSError("injected")
        write(path, data)

    monkeypatch.setattr(io, "_write_file", fail)
    with pytest.raises(OSError):
        stage_package(package, out, load_schema())
    assert snapshot(out) == before
    assert not list(tmp_path.glob(".satd-publication-*"))


@pytest.mark.parametrize("position", [1, 2, 3])
@pytest.mark.parametrize("after_replace", [False, True])
def test_rollback_even_after_effective_rename(
    package, tmp_path, monkeypatch, position, after_replace
):
    """Restaurar bytes previos aun tras un rename efectivo y un error de confirmación."""
    out, schema = tmp_path / "out", load_schema()
    publish(package, out)
    before = snapshot(out)
    newer = build_package(
        *publication_rows(),
        PublicationConfig(PROCEDURE, "synthetic-v1", "2024-07-02T12:00:00+00:00"),
    )
    gate = validate_staging(stage_package(newer, out, schema), schema)
    original, calls = io._replace, []

    def fail(source, destination):
        """Fallar una sola promoción manteniendo filesystem real para rollback."""
        calls.append(destination)
        if len(calls) == position and not after_replace:
            raise OSError("injected")
        original(source, destination)
        if len(calls) == position and after_replace:
            raise OSError("injected after rename")

    monkeypatch.setattr(io, "_replace", fail)
    with pytest.raises(PublicationTransactionError, match="anterior conservada"):
        promote(gate, schema)
    assert snapshot(out) == before
    assert not gate.stage.root.exists()
    assert not list(tmp_path.glob("*.lock"))


def test_rollback_removes_only_new_files(package, tmp_path, monkeypatch):
    """Conservar archivos ajenos y eliminar únicamente los creados por la transacción."""
    out, schema = tmp_path / "out", load_schema()
    out.mkdir()
    (out / "notes.txt").write_text("preserve", encoding="utf-8")
    before, original, calls = snapshot(out), io._replace, []
    gate = validate_staging(stage_package(package, out, schema), schema)

    def fail(source, destination):
        """Cancelar en la segunda promoción."""
        calls.append(destination)
        if len(calls) == 2:
            raise OSError("injected")
        original(source, destination)

    monkeypatch.setattr(io, "_replace", fail)
    with pytest.raises(PublicationTransactionError):
        promote(gate, schema)
    assert snapshot(out) == before


@pytest.mark.parametrize(
    "name",
    [
        "../escape.json",
        "/absolute.json",
        "features.json",
        "resultado_99_2024-02.json",
        "resultado_50_2024-13.json",
    ],
)
def test_invalid_name_before_staging(package, tmp_path, name):
    """Rechazar escapes, nombres ajenos al contrato y periodos inválidos."""
    with pytest.raises(PublicationContractError):
        stage_package(alter_file(package, name=name), tmp_path / "out", load_schema())
    assert not (tmp_path / "out").exists()
    assert not list(tmp_path.glob(".satd-publication-*"))


def test_duplicate_output_names(package, tmp_path):
    """Un nombre repetido no puede sobrescribir otra entrada del conjunto."""
    with pytest.raises(PublicationContractError):
        stage_package(replace(package, files=package.files * 2), tmp_path / "out", load_schema())


@pytest.mark.parametrize("data", [b"invalid", b"[]", b'{"x":NaN}', b'{"x":1,"x":2}', b"\xff"])
def test_invalid_json_preserves_previous(package, tmp_path, data):
    """Hashes recalculados no permiten publicar JSON inválido, ambiguo o no finito."""
    out = tmp_path / "out"
    publish(package, out)
    before = snapshot(out)
    with pytest.raises(PublicationContractError):
        stage_package(alter_file(package, content=data), out, load_schema())
    assert snapshot(out) == before


@pytest.mark.parametrize("where", ["destination", "ancestor", "result", "metadata", "stage"])
def test_symlinks_never_followed(package, tmp_path, where, symlink_factory):
    """Un symlink no puede dirigir lecturas/escrituras fuera de la frontera."""
    actual, out = tmp_path / "actual", tmp_path / "out"
    actual.mkdir()
    (actual / "sentinel").write_text("preserve", encoding="utf-8")
    before = snapshot(actual)
    if where == "destination":
        symlink_factory(out, actual, target_is_directory=True)
    elif where == "ancestor":
        symlink_factory(tmp_path / "linked", actual, target_is_directory=True)
        out = tmp_path / "linked/out"
    elif where in {"result", "metadata"}:
        out.mkdir()
        symlink_factory(
            out / (package.files[0].name if where == "result" else ".publication"),
            actual / "sentinel" if where == "result" else actual,
            target_is_directory=where == "metadata",
        )
    else:
        stage = stage_package(package, out, load_schema())
        path = stage.root / "new" / package.files[0].name
        path.unlink()
        symlink_factory(path, actual / "sentinel")
        with pytest.raises(PublicationTransactionError):
            validate_staging(stage, load_schema())
        assert not stage.root.exists()
        assert snapshot(actual) == before
        return
    with pytest.raises(PublicationTransactionError):
        stage_package(package, out, load_schema())
    assert snapshot(actual) == before


@pytest.mark.parametrize("mutation", ["extra_file", "corrupt", "manifest"])
def test_staging_revalidated_before_promotion(package, tmp_path, mutation):
    """Un paquete alterado entre construcción y validación se elimina sin publicar."""
    out, schema = tmp_path / "out", load_schema()
    stage = stage_package(package, out, schema)
    if mutation == "extra_file":
        (stage.root / "new/extra.json").write_text("{}", encoding="utf-8")
    elif mutation == "corrupt":
        (stage.root / "new" / package.files[0].name).write_bytes(b"partial")
    else:
        (stage.root / "new/.publication/manifest.json").write_bytes(b"{}")
    with pytest.raises(PublicationTransactionError):
        validate_staging(stage, schema)
    assert not out.exists() and not stage.root.exists()


def test_actual_api_schema_in_external_process(package):
    """Pydantic valida los bytes y el snapshot sin imports de app en producción."""
    repo = Path(__file__).resolve().parents[2]
    code = """
import json,runpy,sys
from pathlib import Path
model=runpy.run_path(str(Path(sys.argv[1])/'app/api/sat_api/contrato/schemas.py'))['DashboardResponse']
payload=json.load(sys.stdin)
assert model.model_json_schema()==payload['schema']
for document in payload['documents']: model.model_validate_json(document)
print('API schema and generated documents valid')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(repo)],
        input=json.dumps(
            {
                "schema": load_schema(),
                "documents": [file.content.decode() for file in package.files],
            }
        ),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "mutation",
    [
        "extra_field",
        "champion",
        "decision",
        "future_cases",
        "duplicate_code",
        "uuid",
        "status",
        "target",
    ],
)
def test_valid_json_with_invalid_contract_never_promoted(package, tmp_path, mutation):
    """Una estructura JSON válida no omite los invariantes ejecutables del producto."""
    out = tmp_path / "out"
    publish(package, out)
    before = snapshot(out)
    doc = json.loads(package.files[0].content)
    town = doc["municipalities"][0]
    if mutation == "extra_field":
        doc["metadata"]["extra"] = "unexpected"
    elif mutation == "champion":
        doc["governance"]["champion_status"] = "SELECTED"
    elif mutation == "decision":
        town["results"][0]["probability"] = 0.9
    elif mutation == "future_cases":
        town["endemic_channel_series"][2]["cases"] = 20
    elif mutation == "duplicate_code":
        doc["municipalities"][1]["municipality_code"] = town["municipality_code"]
    elif mutation == "uuid":
        doc["metadata"]["result_set_id"] = "invalid"
    elif mutation == "status":
        town["results"][0]["availability_status"] = "PROBABLE"
    else:
        town["results"][0]["target_period"] = "2024-05"
    with pytest.raises(PublicationContractError):
        stage_package(alter_file(package, content=encode_json(doc)), out, load_schema())
    assert snapshot(out) == before


def test_tamper_after_gate_is_rejected_at_promotion(package, tmp_path):
    """Revalidar el disco incluso después de emitir la compuerta de validación."""
    schema, out = load_schema(), tmp_path / "out"
    publish(package, out)
    before = snapshot(out)
    gate = validate_staging(stage_package(package, out, schema), schema)
    (gate.stage.root / "new" / package.files[0].name).write_bytes(b"tampered")
    with pytest.raises(PublicationTransactionError):
        promote(gate, schema)
    assert snapshot(out) == before
    assert not gate.stage.root.exists()


def test_input_symlink_rejected(tmp_path, symlink_factory):
    """Las entradas locales tampoco pueden resolver symlinks silenciosamente."""
    actual = tmp_path / "source.csv"
    actual.write_text("fake,header\n1,2\n", encoding="utf-8")
    link = tmp_path / "linked.csv"
    symlink_factory(link, actual)
    with pytest.raises(PublicationTransactionError):
        io.read_csv(link)


@pytest.mark.parametrize(
    "value",
    [
        "2024-07-01 12:00:00+00:00",
        "2024-07-01T12:00:00",
        "2024-07-01T12:00:00+01:00",
        "2024-07-01T12:00:00+00:00\n",
        "2024-13-01T12:00:00Z",
        "2024-07-01T12:00:00.123456789123456789Z",
    ],
)
def test_injected_timestamp_is_strict_utc_rfc3339(value):
    """Impedir fechas que el contrato Zod rechazaría aunque Python las interprete."""
    with pytest.raises(PublicationInputError):
        PublicationConfig(PROCEDURE, "synthetic-v1", value)


def test_production_import_boundaries_and_domain_purity():
    """El dominio no consulta archivos, reloj, red, proveedores ni consumidores."""
    repo = Path(__file__).resolve().parents[2]
    root = repo / "pipeline/src/sat_dengue_pipeline/pipelines/deployment_publication"
    for path in root.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [n.name for n in node.names]
                if isinstance(node, ast.Import)
                else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            )
            assert not any(
                n.split(".")[0] in {"app", "sat_api", "huggingface_hub", "boto3"} for n in names
            )
            if path.name in {"domain.py", "package.py", "contract.py"} and isinstance(
                node, ast.Call
            ):
                assert not (isinstance(node.func, ast.Name) and node.func.id in {"open", "exit"})
                assert not (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"now", "utcnow", "getenv", "read_text", "read_bytes"}
                )
    assert not any(
        isinstance(node, ast.FunctionDef)
        for node in ast.walk(
            ast.parse((repo / "scripts/construir_resultados.py").read_text(encoding="utf-8"))
        )
    )
