"""Adquirir y construir el canónico aprobado provisional, sin certificar ni entrenar."""

import argparse
import os
import subprocess
import sys
import uuid
from pathlib import Path

MANIFESTS = (
    "conf/releases/approved-raw.json",
    "conf/releases/operational-raw-173d5856.json",
)


def run(root: Path, manifest: str = MANIFESTS[1], profile: str = "operational_full") -> int:
    """Coordinar dos comandos existentes y detenerse ante el primer fallo.

    Args:
        root: Raíz del subproyecto, usada como cwd de ambos procesos.
        manifest: Release operacional nuevo o histórico, sin modificar sus metadatos.
        profile: Uno de los dos contratos canónicos cerrados.

    Returns:
        Código del primer proceso fallido o del comando Kedro final.
    """
    try:
        acquired = subprocess.run(
            [sys.executable, "tools/acquire_private_raw.py", "--manifest", manifest], cwd=root
        )
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
                f"canonical.mode=approved,canonical.workspace={workspace},"
                f"canonical.tracking=false,canonical.manifest={manifest},canonical.profile={profile}",
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", choices=MANIFESTS, default=MANIFESTS[1])
    parser.add_argument(
        "--profile", choices=("approved", "operational_full"), default="operational_full"
    )
    arguments = parser.parse_args()
    return run(Path(__file__).resolve().parents[1], arguments.manifest, arguments.profile)


if __name__ == "__main__":
    sys.exit(main())
