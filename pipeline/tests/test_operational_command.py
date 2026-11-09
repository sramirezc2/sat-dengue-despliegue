"""Contrato del helper operacional: procesos simulados y ninguna fuente privada."""

import os
import runpy
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("codes", [(0, 0), (7,), (0, 9), (0, -2)])
def test_order_exit_codes_and_portable_arguments(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, codes: tuple[int, ...]
) -> None:
    """Ejecutar adquisición primero y Kedro solo tras éxito, sin shell ni credenciales."""
    run = runpy.run_path(str(ROOT / "tools/build_approved_canonical.py"))["run"]
    root = tmp_path / "project with spaces" / "pipeline"
    root.mkdir(parents=True)
    calls = []
    monkeypatch.setenv("HF_TOKEN", "artificial-private-marker")

    def process(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
        """Simular el proceso sin ejecutar programas o conexiones."""
        assert isinstance(args, list)
        assert args[0] == sys.executable and kwargs["cwd"] == root
        assert not kwargs.get("shell", False)
        assert "artificial-private-marker" not in repr(args)
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, codes[len(calls) - 1])

    monkeypatch.setattr(subprocess, "run", process)
    assert run(root) == codes[-1]
    assert len(calls) == len(codes)
    assert calls[0][0][1:] == ["tools/acquire_private_raw.py"]
    if len(calls) == 2:
        args, kwargs = calls[1]
        assert args[1:6] == ["-m", "kedro", "run", "--pipelines", "canonical_build"]
        assert args[6] == "--params"
        params = dict(item.split("=", 1) for item in args[7].split(","))
        assert params["canonical.mode"] == "approved"
        assert params["canonical.tracking"] == "false"
        workspace = Path(params["canonical.workspace"])
        assert not workspace.is_absolute() and workspace.parts[:2] == ("data", "canonical-approved")
        assert "HF_TOKEN" not in kwargs["env"]
        assert os.environ["HF_TOKEN"] == "artificial-private-marker"
    assert not (root / "docs").exists()
    assert not (root / "data").exists()


def test_process_launch_error_is_sanitized(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """No divulgar rutas o mensajes arbitrarios al fallar el lanzamiento."""
    run = runpy.run_path(str(ROOT / "tools/build_approved_canonical.py"))["run"]

    def reject(*args: Any, **kwargs: Any) -> None:
        """Simular un fallo del sistema operativo."""
        raise OSError("private_marker /private/secret")

    monkeypatch.setattr(subprocess, "run", reject)
    assert run(tmp_path) == 1
    output = capsys.readouterr()
    assert "private_marker" not in output.out + output.err
    assert str(tmp_path) not in output.out + output.err
