"""Tres procesos secuenciales y recibos de fábrica inmutables; nunca cuarta corrida."""

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.factory.configuration import (
    configuration_digest,
    project_root,
    validate_configuration,
)
from sat_dengue_pipeline.raw.contract import sha256
from sat_dengue_pipeline.raw.serialization import canonical_bytes

EVIDENCE_NAMES = (
    "run-1.json",
    "run-2.json",
    "run-3.json",
    "n3-comparison.json",
    "support-by-role.json",
    "temporal-guard.json",
    "validation.json",
)


def code_digest() -> str:
    """Identificar código científico sin archivos de datos o directorios privados."""
    root = project_root()
    return stable_digest(
        {str(path.relative_to(root)): sha256(path) for path in sorted((root / "src").rglob("*.py"))}
    )


def configure(parameters: dict[str, Any]) -> dict[str, Any]:
    """Exigir receta aprobada, evidencia nueva y gates previos sobre este código."""
    config = validate_configuration(parameters)
    root = project_root()
    evidence = root.parent / config["runtime"]["evidence"]
    if any((evidence / name).exists() for name in EVIDENCE_NAMES):
        raise ValueError("Evidencia de fábrica existente: se prohíbe sobrescribir o repetir")
    preflight = root / config["runtime"]["workspace"] / "preflight-validation.json"
    gates = json.loads(preflight.read_text())
    if (
        gates["status"] != "PASSED"
        or gates["code_sha256"] != code_digest()
        or gates["lock_sha256"] != sha256(root / "uv.lock")
        or gates["configuration_sha256"] != configuration_digest(config)
    ):
        raise ValueError("Gates previos ausentes, fallidos o de otro código/configuración")
    return config


def acquire_input(config: dict[str, Any]) -> dict[str, Any]:
    """Concentrar transporte antes de liberar un ResolvedBundle neutral a ciencia."""
    from sat_dengue_pipeline.acquisition.factory import acquire

    bundle, acquisition = acquire(config, project_root())
    return {"configuration": config, "bundle": bundle, "acquisition": acquisition}


def isolated_run(
    bundle: ResolvedBundle,
    config: dict[str, Any],
    directory: Path,
) -> dict[str, Any]:
    """Invocar un intérprete nuevo sin HF_TOKEN, con inbox/derivados/tracking propios."""
    request = {
        "bundle": {
            **asdict(bundle),
            "files": [{**asdict(file), "path": str(file.path.resolve())} for file in bundle.files],
        },
        "configuration": config,
    }
    (directory / "request.json").write_bytes(canonical_bytes(request))
    env = {k: v for k, v in os.environ.items() if k != "HF_TOKEN"}
    env.update({key: str(value) for key, value in config["execution_threads"].items()})
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "sat_dengue_pipeline.factory.worker",
            str(directory / "request.json"),
        ],
        cwd=directory,
        env=env,
        capture_output=True,
        timeout=7200,
        check=False,
    )
    path = directory / "receipt.json"
    if not path.is_file():
        return {
            "status": "FAILED",
            "gate": "isolated_process",
            "error_type": "WorkerNoReceipt",
            "exit_code": completed.returncode,
        }
    record = json.loads(path.read_bytes())
    if completed.returncode != 0 and record["status"] == "PASSED":
        raise ValueError("Proceso fallido no puede declarar éxito")
    return record


def reproduce(acquired: dict[str, Any]) -> dict[str, Any]:
    """Detener ante primer gate fallido o primera divergencia; no hay otro intento."""
    config, bundle = acquired["configuration"], acquired["bundle"]
    records = []
    failure = None
    if bundle is None:
        failure = acquired["acquisition"]
    else:
        workspace = project_root() / config["runtime"]["workspace"]
        workspace.mkdir(parents=True, exist_ok=True)
        for number in range(1, config["reproducibility"]["repetitions"] + 1):
            directory = Path(tempfile.mkdtemp(prefix=f"run-{number}-", dir=workspace))
            record = isolated_run(bundle, config, directory)
            records.append({"run": number, **record})
            if record["status"] != "PASSED":
                failure = {
                    "gate": record.get("gate"),
                    "reason": record.get("reason"),
                    "run": number,
                }
                break
            if number > 1 and record["identity"] != records[0]["identity"]:
                failure = {"gate": "exact_n3_comparison", "reason": "DIVERGENCE", "run": number}
                break
            print(f"Factory run {number}: PASSED {record['identity_sha256']}", flush=True)
    observed = len(records)
    while len(records) < 3:
        records.append(
            {
                "run": len(records) + 1,
                "status": "NOT_EXECUTED",
                "reason": "prior_gate_failed_no_retry",
            }
        )
    pids = [r.get("operation", {}).get("pid") for r in records if r["status"] == "PASSED"]
    if failure is None and (len(pids) != 3 or len(set(pids)) != 3):
        failure = {"gate": "distinct_processes", "reason": "three_distinct_processes_required"}
    return {
        "configuration": config,
        "acquisition": acquired["acquisition"],
        "records": records,
        "observed_runs": observed,
        "status": "PASSED" if failure is None else "BLOCKED",
        "failure": failure,
    }


def _exclusive_json(path: Path, value: Any) -> None:
    """Crear evidencia una sola vez; no truncar ni reemplazar archivos existentes."""
    data = canonical_bytes(value)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def publish(comparison: dict[str, Any]) -> dict[str, Any]:
    """Publicar únicamente agregados permitidos, sin artefactos predictivos o rutas."""
    config = comparison["configuration"]
    root = project_root()
    evidence = root.parent / config["runtime"]["evidence"]
    evidence.mkdir(parents=True, exist_ok=True)
    if any((evidence / name).exists() for name in EVIDENCE_NAMES):
        raise ValueError("Recibos inmutables: evidencia existente")
    records = comparison["records"]
    first = records[0]
    summary = {
        "specification": config["specification"],
        "status": comparison["status"],
        "observed_runs": comparison["observed_runs"],
        "requested_runs": 3,
        "comparison": "exact_canonical_json_and_sha256",
        "failure": comparison["failure"],
        "identities": [record.get("identity_sha256") for record in records],
        "all_identities_equal": comparison["status"] == "PASSED",
        "fourth_run_executed": False,
    }
    support = {
        "status": comparison["status"],
        "runs": {str(record["run"]): record.get("support", {}) for record in records},
    }
    temporal = {
        "status": comparison["status"],
        "runs": {
            str(record["run"]): {
                "temporal": record.get("temporal", {}),
                "quarantine": record.get("quarantine", {}),
                "label_reads": record.get("label_reads", {}),
            }
            for record in records
        },
        "reserved_start": config["reserved_start"],
        "reserved_evidence": config["governance"]["reserved_evidence"],
    }
    gates = json.loads(
        (root / config["runtime"]["workspace"] / "preflight-validation.json").read_text()
    )
    validation = {
        "status": comparison["status"],
        "preflight": gates,
        "acquisition": comparison["acquisition"],
        "configuration_sha256": configuration_digest(config),
        "configuration": {k: v for k, v in config.items() if k != "runtime"},
        "governance": config["governance"],
        "factory_results_released": comparison["status"] == "PASSED",
    }
    for number, record in enumerate(records, 1):
        _exclusive_json(evidence / f"run-{number}.json", record)
    for name, payload in (
        ("n3-comparison.json", summary),
        ("support-by-role.json", support),
        ("temporal-guard.json", temporal),
        ("validation.json", validation),
    ):
        _exclusive_json(evidence / name, payload)
    if comparison["status"] != "PASSED":
        raise ValueError("Factory validation BLOCKED; ver recibos agregados sin reintento")
    return {"status": "PASSED", "identity_sha256": first["identity_sha256"]}
