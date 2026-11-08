"""Ejecutar los comandos oficiales desde la raíz y emitir evidencia del SO real."""

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

PIPELINES = ("synthetic", "canonical_build", "canonical_reproducibility", "deployment_publication")
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "pipeline/data/portability"


def print_log_tail(path: Path) -> None:
    """Mostrar diagnósticos sin perder la causa por el encoding de la consola."""
    tail = path.read_bytes()[-12000:].decode("utf-8", errors="backslashreplace")
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    printable = tail.encode(encoding, errors="backslashreplace").decode(encoding)
    print(printable, flush=True)


def native_symlink_capability() -> dict:
    """Medir la capacidad real separadamente de los dobles de pruebas de guards."""
    with tempfile.TemporaryDirectory(prefix="satd-link-") as temporary:
        root = Path(temporary)
        (root / "target").write_bytes(b"fixture")
        try:
            (root / "link").symlink_to(root / "target")
            return {"available": (root / "link").is_symlink(), "test_logic_fallback": "controlled"}
        except OSError as error:
            return {
                "available": False,
                "errno": error.errno,
                "winerror": getattr(error, "winerror", None),
                "test_logic_fallback": "controlled",
            }


def test_counts(path: Path) -> dict:
    """Leer el reporte de la ejecución actual; omisiones impiden un gate verde."""
    suites = ET.parse(path).getroot().iter("testsuite")
    counts = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    for suite in suites:
        for key in counts:
            counts[key] += int(suite.get(key, "0"))
    if not counts["tests"] or any(counts[key] for key in ("failures", "errors", "skipped")):
        raise ValueError(f"Suite incompleta: {counts}")
    return counts


def run(uv: list[str]) -> int:
    """Ejecutar gates secuenciales y conservar recibo FAILED incluso ante un fallo."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    env = {
        **os.environ,
        "DO_NOT_TRACK": "1",
        "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "MLFLOW_DISABLE_TELEMETRY": "true",
        "MLFLOW_DISABLE_AGENT_HINT": "1",
        "NO_COLOR": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    receipt = {
        "runtime": "github-actions" if env.get("GITHUB_ACTIONS") == "true" else "local",
        "system": platform.system(),
        "release": platform.release(),
        "os_version": platform.mac_ver()[0] or platform.version(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "lock_sha256": hashlib.sha256((ROOT / "pipeline/uv.lock").read_bytes()).hexdigest(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "result": "FAILED",
        "gates": [],
        "pipelines": [],
        "native_symlink": native_symlink_capability(),
    }

    def git(*args: str) -> str:
        """Consultar metadatos sin publicar cambios ni acceder a proveedores."""
        return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8").strip()

    try:
        receipt["commit"] = git("rev-parse", "HEAD")
        receipt["tree"] = git("rev-parse", "HEAD^{tree}")
        receipt["dirty_before"] = bool(git("status", "--porcelain", "--untracked-files=all"))
        receipt["uv"] = subprocess.check_output([*uv, "--version"], cwd=ROOT).decode().strip()
        if receipt["dirty_before"]:
            raise ValueError("Se requiere un árbol limpio antes de ejecutar")
        if sys.version_info[:2] != (3, 12) or receipt["uv"].split()[:2] != ["uv", "0.11.19"]:
            raise ValueError("Se requieren Python 3.12 y uv 0.11.19")
        commands = [
            ("lock", ["lock", "--check", "--project", "pipeline"]),
            ("sync", ["sync", "--locked", "--project", "pipeline"]),
            ("ruff", ["run", "--directory", "pipeline", "ruff", "check", "."]),
            (
                "pytest",
                [
                    "run",
                    "--directory",
                    "pipeline",
                    "pytest",
                    "--junitxml=data/portability/pytest.xml",
                ],
            ),
            (
                "portability",
                [
                    "run",
                    "--directory",
                    "pipeline",
                    "pytest",
                    "tests/test_portability.py",
                    "--junitxml=data/portability/portability.xml",
                ],
            ),
            *[
                (name, ["run", "--directory", "pipeline", "kedro", "run", "--pipelines", name])
                for name in PIPELINES
            ],
            (
                "outputs",
                ["run", "--directory", "pipeline", "python", "tools/portability_outputs.py"],
            ),
        ]
        for name, args in commands:
            before = time.monotonic()
            print(f"Portability gate: {name}", flush=True)
            with (OUTPUT / f"{name}.log").open("wb") as log:
                completed = subprocess.run(
                    [*uv, *args],
                    cwd=ROOT,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=1800,
                    check=False,
                )
            receipt["gates"].append(
                {
                    "name": name,
                    "exit_code": completed.returncode,
                    "seconds": round(time.monotonic() - before, 2),
                }
            )
            if completed.returncode:
                print_log_tail(OUTPUT / f"{name}.log")
                raise ValueError(f"Gate {name} falló: consultar su log local")
            if name in PIPELINES:
                receipt["pipelines"].append(name)
        receipt["tests"] = test_counts(OUTPUT / "pytest.xml")
        receipt["portability_tests"] = test_counts(OUTPUT / "portability.xml")
        receipt["outputs"] = json.loads((OUTPUT / "outputs.json").read_bytes())
        warning = re.search(
            r"(\d+) warnings? in", (OUTPUT / "pytest.log").read_text(encoding="utf-8")
        )
        receipt["pytest_warnings"] = int(warning[1]) if warning else 0
        receipt["dirty_after"] = bool(git("status", "--porcelain", "--untracked-files=all"))
        if receipt["dirty_after"]:
            raise ValueError("La ejecución alteró el árbol versionado")
        receipt["result"] = "PASSED"
    except (OSError, ValueError, subprocess.SubprocessError, ET.ParseError) as error:
        # No full environment, private paths, command output or credentials in the artifact.
        receipt["failure_type"] = type(error).__name__
        print(f"Portability FAILED ({type(error).__name__}); inspect local gate logs", flush=True)
    finally:
        receipt["duration_seconds"] = round(time.monotonic() - started, 2)
        receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (OUTPUT / "receipt.json").write_bytes(
            json.dumps(receipt, sort_keys=True, indent=2).encode()
        )
    print(
        json.dumps(
            {
                "result": receipt["result"],
                "system": receipt["system"],
                "receipt": "pipeline/data/portability/receipt.json",
            }
        ),
        flush=True,
    )
    return 0 if receipt["result"] == "PASSED" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uv-python", help="Intérprete Colab que contiene el módulo uv fijado")
    options = parser.parse_args()
    raise SystemExit(run([options.uv_python, "-m", "uv"] if options.uv_python else ["uv"]))
