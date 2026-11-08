"""Regresiones de transporte Git para archivos cuya identidad depende de bytes."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_autocrlf_preserves_identity_files(tmp_path: Path) -> None:
    """Simular un checkout Windows sobre bytes artificiales, sin leer datos reales.

    Args:
        tmp_path: Repositorio temporal completamente aislado.
    """
    if not shutil.which("git"):
        pytest.fail("Git es necesario para comprobar la integridad del checkout")
    files = (
        "pipeline/conf/base/parameters_experiment.yml",
        "docs/experiments/protocols/fixture.md",
        "docs/evidence/task16/fixture.json",
        "docs/decisions/task16-experiment-specification.md",
        "datos/resultados/fixture.json",
    )
    content = b"first\nsecond\n"
    (tmp_path / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
    for name in (*files, "control.txt"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def git(*args: str) -> None:
        """Ejecutar Git con configuración explícita y comprobar el resultado."""
        subprocess.run(
            ["git", "-c", "core.autocrlf=true", "-c", "core.safecrlf=false", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

    git("init", "--quiet")
    git("add", ".")
    git("checkout-index", "--all", "--prefix=export/")
    for name in files:
        assert (tmp_path / "export" / name).read_bytes() == content, name
    assert (tmp_path / "export/control.txt").read_bytes() == b"first\r\nsecond\r\n"


def test_source_identity_uses_posix_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """Conservar la identidad del código con representación relativa Windows.

    Args:
        monkeypatch: Cambio controlado de separadores sin emular el sistema.
    """
    from pathlib import PureWindowsPath

    from sat_dengue_pipeline.experiment_management.runner import code_identity

    before = code_identity(ROOT)["source_sha256"]
    original = Path.relative_to

    def windows_relative(path: Path, *args, **kwargs):
        """Representar únicamente las rutas relativas mediante PureWindowsPath."""
        return PureWindowsPath(*original(path, *args, **kwargs).parts)

    monkeypatch.setattr(Path, "relative_to", windows_relative)
    assert code_identity(ROOT)["source_sha256"] == before
