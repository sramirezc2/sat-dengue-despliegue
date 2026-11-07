"""Bootstrap Colab: instalar uv fijado y delegar todos los gates al ejecutor común."""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

REPOSITORY = "https://github.com/sramirezc2/sat-dengue-despliegue.git"
BRANCH = "feature/pipeline-e2e"


def run_colab(repo: Path, *, expected_commit: str, bundle: Path | None = None) -> Path:
    """Ejecutar en un kernel Colab real, sin credenciales ni lógica científica.

    Args:
        repo: Clon nuevo o existente fuera de Google Drive montado.
        expected_commit: SHA completo revisado, que debe coincidir antes de ejecutar.
        bundle: Bundle incremental opcional de commits locales aún no publicados.

    Returns:
        Ruta al recibo pequeño; no exporta entornos, datos ni cachés.
    """
    from IPython import get_ipython

    shell = get_ipython()
    if shell is None or not type(shell).__module__.startswith("google.colab."):
        raise RuntimeError("Se requiere ejecutar desde un kernel real de Google Colab")
    if len(expected_commit) != 40 or any(c not in "0123456789abcdef" for c in expected_commit):
        raise ValueError("Se requiere el commit completo aprobado para esta ejecución")
    repo = Path(repo).absolute()
    if not repo.exists():
        subprocess.run(["git", "clone", "--branch", BRANCH, REPOSITORY, str(repo)], check=True)
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=repo).strip():
        raise ValueError("El clon Colab debe estar limpio")
    if bundle is not None:
        subprocess.run(["git", "fetch", str(Path(bundle).absolute()), BRANCH], cwd=repo, check=True)
        subprocess.run(["git", "merge", "--ff-only", "FETCH_HEAD"], cwd=repo, check=True)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
    if actual != expected_commit:
        raise ValueError("El commit del runtime difiere del solicitado")
    subprocess.run([sys.executable, "-m", "pip", "install", "uv==0.11.19"], check=True)
    uv = [sys.executable, "-m", "uv"]
    env = {**os.environ, "UV_PYTHON": "3.12", "DO_NOT_TRACK": "1"}
    if sys.version_info[:2] != (3, 12):
        subprocess.run([*uv, "python", "install", "3.12"], cwd=repo, env=env, check=True)
    result = subprocess.run(
        [
            *uv,
            "run",
            "--directory",
            "pipeline",
            "python",
            "tools/check_portability.py",
            "--uv-python",
            sys.executable,
        ],
        cwd=repo,
        env=env,
        check=False,
    )
    path = repo / "pipeline/data/portability/receipt.json"
    receipt = json.loads(path.read_bytes())
    receipt.update(
        runtime="google-colab",
        host_python=platform.python_version(),
        colab_kernel_module=type(shell).__module__,
    )
    path.write_bytes(json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8"))
    print(path.read_text(encoding="utf-8"))
    if result.returncode:
        raise RuntimeError("Colab falló; conservar recibo FAILED y revisar logs locales")
    return path
