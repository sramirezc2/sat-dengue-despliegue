"""Evidencia agregada exclusiva e inventario verificable sin store MLflow."""

import json
import os
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
    if set(artifacts) != NAMES or artifacts["receipt.json"]["status"] not in TERMINAL:
        raise ValueError("Paquete o estado terminal inválido")
    for name in sorted(artifacts):
        exclusive_json(folder / name, artifacts[name])
    exclusive_json(
        folder / "inventory.json", {name: sha256(folder / name) for name in sorted(NAMES)}
    )


def verify_execution(root: Path, reference: str) -> dict:
    """Verificar esquema de archivos, inventario y estado antes de comparar o concluir."""
    inventory_path = confined(root, reference, "docs/evidence/experiments")
    folder = inventory_path.parent
    if {p.name for p in folder.iterdir()} != NAMES | {"inventory.json"}:
        raise ValueError("Evidencia incompleta o desconocida")
    inventory = json.loads(inventory_path.read_bytes())
    if set(inventory) != NAMES:
        raise ValueError("Inventario incompleto")
    for name, digest in inventory.items():
        path = confined(root, str((folder / name).relative_to(root)), "docs/evidence/experiments")
        if path.stat().st_size > 512_000 or sha256(path) != digest:
            raise ValueError("Inventario de ejecución alterado")
    record = json.loads((folder / "receipt.json").read_bytes())
    if (
        record["status"] not in TERMINAL
        or record["execution_id"] != folder.name
        or (record["experiment_id"] != folder.parent.name)
    ):
        raise ValueError("Recibo de ejecución inconsistente")
    lineage = json.loads((folder / "lineage.json").read_bytes())
    if stable_digest(lineage) != record["execution_signature"] or any(
        lineage[k] != record[k]
        for k in ("experiment_id", "protocol_sha256", "configuration_sha256")
    ):
        raise ValueError("Firma de ejecución inconsistente")
    return record
