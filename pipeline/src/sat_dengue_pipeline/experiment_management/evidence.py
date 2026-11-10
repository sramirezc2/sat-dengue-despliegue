"""Evidencia agregada exclusiva e inventario verificable sin store MLflow."""

import json
import os
import re
from pathlib import Path
from typing import Any

from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.raw.contract import sha256
from sat_dengue_pipeline.raw.serialization import canonical_bytes

from .registry import confined

NAMES = {"receipt.json", "configuration.json", "lineage.json", "metrics.json", "validation.json"}
TERMINAL = {"COMPLETED", "BLOCKED", "FAILED", "KILLED"}


def exclusive_json(path: Path, value: Any) -> None:
    """Crear un archivo nuevo, sincronizado y pequeño; nunca truncar evidencia."""
    data = canonical_bytes(value)
    if len(data) > 512_000:
        raise ValueError("Evidencia demasiado grande")
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def publish(folder: Path, artifacts: dict[str, Any]) -> None:
    """Completar una ejecución reservada; inventario final actúa como marcador de cierre."""
    additional = set(artifacts) - NAMES
    if (
        not NAMES <= set(artifacts)
        or artifacts["receipt.json"]["status"] not in TERMINAL
        or any(not re.fullmatch(r"scientific-[0-9]{4}\.json", name) for name in additional)
        or set(artifacts["receipt.json"].get("scientific_evaluation", {}).get("records", []))
        != additional
    ):
        raise ValueError("Paquete o estado terminal inválido")
    for name in sorted(artifacts):
        exclusive_json(folder / name, artifacts[name])
    exclusive_json(
        folder / "inventory.json", {name: sha256(folder / name) for name in sorted(artifacts)}
    )


def verify_execution(root: Path, reference: str) -> dict:
    """Verificar esquema de archivos, inventario y estado antes de comparar o concluir."""
    inventory_path = confined(root, reference, "docs/evidence/experiments")
    folder = inventory_path.parent
    inventory = json.loads(inventory_path.read_bytes())
    additional = set(inventory) - NAMES
    if (
        not NAMES <= set(inventory)
        or any(not re.fullmatch(r"scientific-[0-9]{4}\.json", name) for name in additional)
        or {p.name for p in folder.iterdir()} != set(inventory) | {"inventory.json"}
    ):
        raise ValueError("Inventario incompleto")
    for name, digest in inventory.items():
        path = confined(
            root, (folder / name).relative_to(root).as_posix(), "docs/evidence/experiments"
        )
        if path.stat().st_size > 512_000 or sha256(path) != digest:
            raise ValueError("Inventario de ejecución alterado")
    record = json.loads((folder / "receipt.json").read_bytes())
    if (
        record["status"] not in TERMINAL
        or record["execution_id"] != folder.name
        or (record["experiment_id"] != folder.parent.name)
    ):
        raise ValueError("Recibo de ejecución inconsistente")
    if set(record.get("scientific_evaluation", {}).get("records", [])) != additional:
        raise ValueError("Inventario científico distinto del recibo")
    lineage = json.loads((folder / "lineage.json").read_bytes())
    if record.get("scientific_evaluation") and record["scientific_evaluation"][
        "contract"
    ] != lineage.get("scientific_contract"):
        raise ValueError("Contrato científico distinto del linaje firmado")
    if stable_digest(lineage) != record["execution_signature"] or any(
        lineage[k] != record[k]
        for k in ("experiment_id", "protocol_sha256", "configuration_sha256")
    ):
        raise ValueError("Firma de ejecución inconsistente")
    return record


def scientific_artifacts(records: list[dict]) -> dict[str, dict]:
    """Dividir agregados grandes en JSON pequeños, exclusivos e inventariados.

    Args:
        records: Configuración/huellas/métricas agregadas; nunca filas de predicción.

    Returns:
        Archivos de menos de 300 kB que el publicador existente guarda atómicamente.
    """
    chunks: list[list[dict]] = [[]]
    for record in records:
        if len(canonical_bytes(record)) > 250_000:
            raise ValueError("Registro científico agregado demasiado grande")
        if len(canonical_bytes(chunks[-1] + [record])) > 290_000:
            chunks.append([])
        chunks[-1].append(record)
    return {
        f"scientific-{i:04d}.json": {"schema": "satd-scientific-proposed-v1", "records": chunk}
        for i, chunk in enumerate(chunks)
    }
