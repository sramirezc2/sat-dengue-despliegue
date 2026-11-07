"""Regresiones de transporte; estas pruebas no simulan validación de un sistema."""

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from fixtures.legacy_publication import legacy_outputs
from fixtures.publication_fixture import write_inputs

REPO = Path(__file__).resolve().parents[2]


def test_legacy_reference_normalizes_transport_newlines(tmp_path, monkeypatch):
    """Conservar el golden LF aun si el publicador histórico escribe CRLF."""
    paths = write_inputs(tmp_path / "inputs")
    original = Path.write_text

    def crlf(path, data, *args, **kwargs):
        """Inyectar únicamente el transporte de nueva línea del escritor legado."""
        kwargs["newline"] = "\r\n"
        return original(path, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", crlf)
    outputs, _ = legacy_outputs(paths, tmp_path / "out", monkeypatch)
    assert b"\r\n" in next((tmp_path / "out").glob("*.json")).read_bytes()
    receipt = json.loads((Path(__file__).parent / "fixtures/publication_receipt.json").read_bytes())
    assert {name: hashlib.sha256(data).hexdigest() for name, data in outputs.items()} == receipt[
        "files"
    ]


def test_tracking_cli_reads_unicode_independent_of_locale(tmp_path, monkeypatch):
    """No corromper agregados/linaje UTF-8 cuando el encoding por defecto es cp1252."""
    from sat_dengue_pipeline.tracking import __main__ as cli

    report, lineage = tmp_path / "report.json", tmp_path / "lineage.json"
    report.write_bytes("informe sintético Río".encode())
    lineage.write_bytes('{"label":"Río"}'.encode())
    original = Path.read_text
    observed = []

    def cp1252(path, encoding=None, errors=None):
        """Inyectar locale solo en lectura sin encoding; no emular Windows."""
        return original(path, encoding=encoding or "cp1252", errors=errors)

    @dataclass
    class Receipt:
        """Recibo mínimo para no iniciar MLflow en esta prueba de transporte."""

        enabled: bool = False

    def record(self, data, metadata):
        """Observar las entradas antes de delegar a cualquier SDK."""
        observed.extend([data, metadata])
        return Receipt()

    monkeypatch.setattr(Path, "read_text", cp1252)
    monkeypatch.setattr(cli, "EvaluationReport", lambda text: text)
    monkeypatch.setattr(cli.LocalTracker, "record", record)
    monkeypatch.setattr(
        sys, "argv", ["tracking", "--report", str(report), "--lineage", str(lineage)]
    )
    cli.main()
    assert observed == ["informe sintético Río", {"label": "Río"}]


def test_git_autocrlf_preserves_hashed_sources(tmp_path):
    """Git real con autocrlf conserva las identidades del lock y del contrato."""
    source, clone = tmp_path / "source", tmp_path / "clone"
    source.mkdir()
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    (source / ".gitattributes").write_bytes((REPO / ".gitattributes").read_bytes())
    names = ["pipeline/uv.lock", "app/api/sat_api/contrato/schemas.py"]
    for name in names:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"first\nsecond\n")
    subprocess.run(["git", "-C", str(source), "add", "."], check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(source),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=f@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-c", "core.autocrlf=true", "clone", "-q", str(source), str(clone)],
        check=True,
        capture_output=True,
    )
    for name in names:
        assert (clone / name).read_bytes() == (source / name).read_bytes()


@pytest.mark.parametrize("kind", ["directory", "file", "dangling"])
def test_denied_symlink_privilege_preserves_guard_coverage(tmp_path, monkeypatch, kind):
    """Falta de privilegios explícita no elimina la lógica antiescape."""
    import errno

    from fixtures.links import TestLinks

    def denied(*args, **kwargs):
        """Reproducir solamente el error de capacidad, no un sistema operativo."""
        raise OSError(errno.EPERM, "fixture denied")

    monkeypatch.setattr(Path, "symlink_to", denied)
    factory = TestLinks(monkeypatch, tmp_path)
    target, link = tmp_path / "target", tmp_path / "link"
    if kind == "directory":
        target.mkdir()
    elif kind == "file":
        target.write_bytes(b"preserve")
    factory(link, target, target_is_directory=kind == "directory")
    assert link.is_symlink()
    assert (link / "child").resolve() == target / "child"
    link.unlink()
    assert not link.is_symlink()


def test_symlink_unexpected_error_is_not_hidden(tmp_path, monkeypatch):
    """Un error diferente a capacidad/privilegios sigue haciendo fallar la suite."""
    import errno

    from fixtures.links import TestLinks

    def failed(*args, **kwargs):
        """Inyectar un fallo real del dispositivo."""
        raise OSError(errno.EIO, "fixture I/O failure")

    monkeypatch.setattr(Path, "symlink_to", failed)
    with pytest.raises(OSError, match="I/O"):
        TestLinks(monkeypatch, tmp_path)(tmp_path / "link", tmp_path / "target")


@pytest.mark.parametrize(
    "attributes",
    ["tests='0'", "tests='2' skipped='1'", "tests='2' failures='1'", "tests='2' errors='1'"],
)
def test_receipt_rejects_incomplete_suite(tmp_path, attributes):
    """Un reporte vacío, fallido u omitido nunca se presenta como ejecución verde."""
    import runpy

    counts = runpy.run_path(str(REPO / "pipeline/tools/check_portability.py"))["test_counts"]
    report = tmp_path / "report.xml"
    report.write_bytes(f"<testsuites><testsuite {attributes}/></testsuites>".encode())
    with pytest.raises(ValueError, match="incompleta"):
        counts(report)


def test_receipt_counts_completed_suite(tmp_path):
    """El total procede del reporte actual, no de un número configurado."""
    import runpy

    counts = runpy.run_path(str(REPO / "pipeline/tools/check_portability.py"))["test_counts"]
    report = tmp_path / "report.xml"
    report.write_bytes(b"<testsuites><testsuite tests='7' failures='0' errors='0'/></testsuites>")
    assert counts(report) == {"tests": 7, "failures": 0, "errors": 0, "skipped": 0}
