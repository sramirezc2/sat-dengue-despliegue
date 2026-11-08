"""Comparación determinista de registro y evidencia pequeña, sin acceso a datos o MLflow."""

import json
from pathlib import Path

from .evidence import verify_execution
from .registry import Registry, confined


def compare(
    root: Path,
    *,
    status: str | None = None,
    candidate: str | None = None,
    horizon: int | None = None,
) -> list[dict]:
    """Listar métricas y procedencia; conservar filas de fallos sin inventar valores."""
    registry = Registry(root, verify_documents=False)
    rows = []
    for eid, entry in sorted(registry.entries.items()):
        folder = confined(
            root, f"docs/evidence/experiments/{eid}", "docs/evidence/experiments", exists=False
        )
        for execution in sorted(folder.iterdir()) if folder.exists() else []:
            reference = (execution / "inventory.json").relative_to(root).as_posix()
            record = verify_execution(root, reference)
            if status and status not in (entry["status"], record["status"]):
                continue
            if candidate and record["candidate"] != candidate:
                continue
            registry.assert_identity(entry)
            lineage = json.loads((execution / "lineage.json").read_bytes())
            metrics = json.loads((execution / "metrics.json").read_bytes())
            common = {
                "experiment_id": eid,
                "execution_id": record["execution_id"],
                "experiment_type": entry["experiment_type"],
                "status": record["status"],
                "registry_status": entry["status"],
                "scientific_result": entry["scientific_result"],
                "candidate": record["candidate"],
                "seed": record["seed"],
                "protocol": entry["protocol"],
                "protocol_sha256": entry["protocol_sha256"],
                "configuration_sha256": entry["configuration_sha256"],
                "dataset_sha256": lineage["dataset_manifest_sha256"],
                "git_sha": lineage["git_sha"],
                "dirty": lineage["dirty"],
                "code_sha256": lineage["source_sha256"],
                "evidence": reference,
            }
            for h in record["horizons"]:
                if horizon is not None and h != horizon:
                    continue
                result = metrics.get(str(h), {})
                for baseline, records in sorted(result.get("metrics", {}).items()) or [(None, [])]:
                    for metric in records or [{"metric": None, "value": None}]:
                        rows.append(
                            {
                                **common,
                                "horizon": h,
                                "reference": baseline,
                                "metric": metric["metric"],
                                "value": metric["value"],
                            }
                        )
    return rows
