"""Adquirir y construir el canónico aprobado provisional, sin certificar ni entrenar."""

import argparse
import os
import subprocess
import sys
import uuid
from pathlib import Path


def run(root: Path) -> int:
    """Coordinar dos comandos existentes y detenerse ante el primer fallo.

    Args:
        root: Raíz del subproyecto, usada como cwd de ambos procesos.

    Returns:
        Código del primer proceso fallido o del comando Kedro final.
    """
    try:
        acquired = subprocess.run([sys.executable, "tools/acquire_private_raw.py"], cwd=root)
        if acquired.returncode:
            return acquired.returncode
        environment = os.environ.copy()
        environment.pop("HF_TOKEN", None)
        workspace = f"data/canonical-approved/{uuid.uuid4().hex}"
        built = subprocess.run(
            [
                sys.executable,
                "-m",
                "kedro",
                "run",
                "--pipelines",
                "canonical_build",
                "--params",
                f"canonical.mode=approved,canonical.workspace={workspace},canonical.tracking=false",
            ],
            cwd=root,
            env=environment,
        )
        return built.returncode
    except OSError:
        print(
            "No se pudo iniciar el comando operacional; revise el entorno instalado",
            file=sys.stderr,
        )
        return 1


def main() -> int:
    """Mostrar ayuda sin efectos o ejecutar el flujo operacional explícito."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    return run(Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    sys.exit(main())
