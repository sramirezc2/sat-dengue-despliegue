"""JSON canónico sin pérdida de floats, direccionado por contenido y atómico."""

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from sat_dengue_pipeline.domain.canonical import ROLE_ORDER, predictor_matrix, validate_source

from .contract import sha256


def canonical_bytes(value: object) -> bytes:
    """Serializar sin NaN, locale, fechas actuales o rutas privadas."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _scalar(value: object) -> object:
    """Representar ausencias como null y escalares NumPy como JSON estándar."""
    if pd.isna(value):
        return None
    return value.item() if isinstance(value, np.generic) else value


@dataclass(frozen=True)
class CanonicalArtifact:
    """Salida provisional; no constituye autorización para entrenamiento."""

    path: Path
    semantic_digest: str
    serialized_sha256: str


def atomic_write(path: Path, data: bytes) -> None:
    """Reemplazar un archivo completo y preservar el anterior ante fallos."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=".canonical-", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def canonical_serialization(result: tuple[pd.DataFrame, dict], root: Path) -> CanonicalArtifact:
    """Incluir esquema/tipos/orden/nulos y valores exactos en ambas huellas."""
    table, schema = result
    payload = {
        "schema": schema,
        "rows": [[_scalar(v) for v in row] for row in table.itertuples(index=False, name=None)],
    }
    semantic = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    serialized = canonical_bytes({"format": "satd-canonical-json-v1", **payload})
    path = root / semantic / "canonical.json"
    atomic_write(path, serialized)
    return CanonicalArtifact(path, semantic, hashlib.sha256(serialized).hexdigest())


def load_canonical(artifact: CanonicalArtifact) -> tuple[pd.DataFrame, dict]:
    """Restaurar orden/tipos/nulos exactos, incluidos los roles cerrados del dominio."""
    payload = json.loads(verify_artifact(artifact))
    schema = payload["schema"]
    roles = schema["column_roles"]
    if set(roles) != set(ROLE_ORDER):
        raise ValueError("Roles serializados inválidos")
    schema["column_roles"] = {role: roles[role] for role in ROLE_ORDER}
    columns = schema["columns"]
    names = [column["name"] for column in columns]
    # Evitar inferencia int->float en columnas enteras con null antes de restaurar tipos.
    table = pd.DataFrame(payload["rows"], columns=names, dtype=object)
    for column in columns:
        name = column["name"]
        table[name] = table[name].astype(column["dtype"])
        if bool(table[name].isna().any()) != column["nullable"]:
            raise ValueError("Nulabilidad serializada inconsistente")
    validate_source(table)
    predictor_matrix(table, schema)
    return table, schema


def verify_artifact(artifact: CanonicalArtifact) -> bytes:
    """Comprobar bytes y digest semántico antes de certificar o entregar."""
    if sha256(artifact.path) != artifact.serialized_sha256:
        raise ValueError("SHA-256 canónico alterado")
    data = artifact.path.read_bytes()
    payload = json.loads(data)
    if payload.pop("format") != "satd-canonical-json-v1" or (
        hashlib.sha256(canonical_bytes(payload)).hexdigest() != artifact.semantic_digest
    ):
        raise ValueError("Digest semántico alterado")
    return data
