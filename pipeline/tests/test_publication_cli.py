"""Compatibilidad de argumentos/códigos y equivalencia del wrapper sobre datos artificiales."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fixtures.legacy_publication import legacy_outputs
from fixtures.publication_fixture import GENERATED, PROCEDURE, write_inputs

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/construir_resultados.py"


def command(paths: dict, output: Path | None) -> list[str]:
    """Construir la interfaz existente más fecha fija, sin leer defaults reales."""
    args = [
        sys.executable,
        str(SCRIPT),
        "--procedimiento",
        PROCEDURE,
        "--version-datos",
        "synthetic-v1",
        "--generado",
        GENERATED,
    ]
    if output is not None:
        args += ["--salida", str(output)]
    for name, path in paths.items():
        args += [f"--{name}", str(path)]
    return args


@pytest.mark.parametrize("retro", [True, False])
@pytest.mark.parametrize("candidate", ["auto", "xgboost"])
def test_wrapper_exact_legacy_bytes(tmp_path, monkeypatch, retro, candidate):
    """Conservar JSON, nombres y mensajes esenciales en las cuatro combinaciones."""
    paths = write_inputs(tmp_path / "inputs")
    if not retro:
        paths["retroanalisis"] = tmp_path / "absent.json"
    legacy_paths = {**paths, "candidato": Path(candidate)}
    expected, _ = legacy_outputs(legacy_paths, tmp_path / "legacy", monkeypatch)
    output = tmp_path / "new"
    result = subprocess.run(
        command(legacy_paths, output), capture_output=True, text=True, cwd=tmp_path
    )
    assert result.returncode == 0, result.stderr
    assert {p.name: p.read_bytes() for p in output.glob("*.json")} == expected
    assert "2 archivo(s) escritos" in result.stdout
    assert "umbral T+1: 0.800000" in result.stdout
    assert "umbral T+2: 0.800000" in result.stdout
    manifest = json.loads((output / ".publication/manifest.json").read_bytes())
    assert manifest["selection"]["forced"] == (candidate != "auto")
    assert manifest["candidate"] == ("lightgbm" if candidate == "auto" else candidate)
    if candidate != "auto":
        assert "Candidato forzado por bandera: xgboost" in result.stdout
        assert "AVISO: anula el criterio" in result.stdout
    elif not retro:
        assert "Retroanalisis: ausente" in result.stdout


def test_cli_defaults_use_callers_cwd_without_touching_published_files(tmp_path):
    """Los defaults históricos siguen siendo datos/resultados y retro opcional relativos al cwd."""
    paths = write_inputs(tmp_path / "inputs")
    paths.pop("retroanalisis")
    result = subprocess.run(command(paths, None), cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert len(list((tmp_path / "datos/resultados").glob("*.json"))) == 2
    assert "Retroanalisis: ausente" in result.stdout


def test_cli_forced_reason_is_auditable(tmp_path):
    """La justificación explícita queda en el manifiesto sin cambiar el JSON de producto."""
    paths = write_inputs(tmp_path / "inputs")
    out = tmp_path / "out"
    result = subprocess.run(
        command(paths, out) + ["--candidato", "xgboost", "--justificacion", "synthetic audit"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    selection = json.loads((out / ".publication/manifest.json").read_bytes())["selection"]
    assert selection == {"requested": "xgboost", "forced": True, "reason": "synthetic audit"}


@pytest.mark.parametrize(
    "args,code,fragment",
    [
        ([], 2, "required"),
        (["--help"], 0, "--predicciones"),
    ],
)
def test_cli_parse_codes(args, code, fragment, tmp_path):
    """Argparse conserva éxito de ayuda y código 2 para argumentos incompletos."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == code
    assert fragment in result.stdout + result.stderr


@pytest.mark.parametrize("content", ["{}", "[]", "invalid"])
def test_cli_invalid_retro_preserves_failure_code(tmp_path, content):
    """Un retroanálisis inválido falla sin convertirlo silenciosamente en ausencia."""
    paths = write_inputs(tmp_path / "inputs")
    paths["retroanalisis"].write_text(content, encoding="utf-8")
    out = tmp_path / "out"
    result = subprocess.run(command(paths, out), cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    assert "ERROR:" in result.stderr
    assert not out.exists()


def test_cli_default_clock_is_utc_at_command_boundary(tmp_path):
    """Solo el comando resuelve la hora predeterminada, con zona UTC explícita."""
    from datetime import datetime, timezone

    paths, out = write_inputs(tmp_path / "inputs"), tmp_path / "out"
    args = command(paths, out)
    index = args.index("--generado")
    del args[index : index + 2]
    before = datetime.now(timezone.utc).replace(microsecond=0)
    result = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    generated = datetime.fromisoformat(
        json.loads((out / ".publication/manifest.json").read_bytes())["generated_at"]
    )
    assert before <= generated <= datetime.now(timezone.utc)
    assert generated.utcoffset().total_seconds() == 0


def test_cli_unknown_candidate_error_code_and_message(tmp_path):
    """El error observable de candidato ausente sigue siendo código 1 y ERROR específico."""
    paths = write_inputs(tmp_path / "inputs")
    out = tmp_path / "out"
    result = subprocess.run(
        command(paths, out) + ["--candidato", "absent"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "ERROR: el archivo de predicciones no contiene el candidato 'absent'" in result.stderr
    assert not out.exists()
