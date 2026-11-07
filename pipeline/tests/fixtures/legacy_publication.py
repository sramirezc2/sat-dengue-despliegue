"""Referencia inmutable V3: solo código del publicador al iniciar tarea 14."""

import hashlib
import subprocess
import sys
import types
from datetime import datetime
from pathlib import Path

from .publication_fixture import GENERATED, PROCEDURE

COMMIT = "32b6d06"
BLOB_PATH = "scripts/construir_resultados.py"


def legacy_module() -> types.ModuleType:
    """Cargar el blob histórico local, sin acceder a V2 ni datos del repositorio."""
    repo = Path(__file__).resolve().parents[3]
    source = subprocess.check_output(["git", "-C", str(repo), "show", f"{COMMIT}:{BLOB_PATH}"])
    module = types.ModuleType("satd_legacy_publication_fixture")
    sys.modules[module.__name__] = module
    exec(compile(source, BLOB_PATH, "exec"), module.__dict__)
    return module


def legacy_outputs(paths: dict[str, Path], destination: Path, monkeypatch) -> tuple[dict, str]:
    """Ejecutar el CLI legado con reloj UTC fijo y entradas explícitas artificiales."""
    module = legacy_module()

    class FixedClock:
        """Reloj inyectado solo en la referencia de prueba."""

        @staticmethod
        def now(tz):
            """Devolver la fecha UTC congelada."""
            return datetime.fromisoformat(GENERATED)

    monkeypatch.setattr(module, "datetime", FixedClock)
    argv = [
        BLOB_PATH,
        "--procedimiento",
        PROCEDURE,
        "--version-datos",
        "synthetic-v1",
        "--salida",
        str(destination),
    ]
    for name, path in paths.items():
        argv.extend([f"--{name}", str(path)])
    monkeypatch.setattr(sys, "argv", argv)
    module.main()
    # Normalize only the historical text writer transport; production hashes remain raw bytes.
    outputs = {
        path.name: path.read_text(encoding="utf-8").encode("utf-8")
        for path in destination.glob("*.json")
    }
    source = subprocess.check_output(
        ["git", "-C", str(Path(__file__).resolve().parents[3]), "show", f"{COMMIT}:{BLOB_PATH}"]
    )
    return outputs, hashlib.sha256(source).hexdigest()
