"""Linaje canónico agregado con esquema cerrado; nunca acepta microdatos o rutas."""

import re
import subprocess
from pathlib import Path

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle
from sat_dengue_pipeline.domain.canonical import CLIMATE, COUNTS, KEYS, LAGS
from sat_dengue_pipeline.domain.endemic_channel import CHANNEL
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.raw.contract import INVENTORY, BuildConfig, sha256
from sat_dengue_pipeline.raw.producers import REJECTIONS
from sat_dengue_pipeline.raw.serialization import CanonicalArtifact

FIELDS = {
    "builder_git_dirty",
    "raw_manifest_digest",
    "source_hashes",
    "builder_git_sha",
    "builder_config_digest",
    "lock_digest",
    "quarantine",
    "coverage",
    "stages",
    "canonical_semantic_digest",
    "serialized_sha256",
    "reconstruction_hashes",
    "certification",
    "profile",
}
NULL_COLUMNS = {
    *KEYS,
    *COUNTS,
    *CLIMATE,
    *CHANNEL,
    "department_code",
    "municipality_name",
    "in_epi_coverage",
    "epi_count_status",
    "expected_days_in_month",
    "climate_days_observed",
    *(f"{name}_valid_days" for name in CLIMATE),
    "month_of_year",
    *(f"{name}_lag{lag}" for name in COUNTS for lag in LAGS),
    *(f"{stat}_h5_t{h}" for h in (1, 2) for stat in ("p25", "p75", "history_valid_years")),
}


def _closed(value: dict, keys: set[str]) -> None:
    """Exigir exactamente las claves admitidas."""
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("Metadatos canónicos desconocidos")


def _count(value: object) -> None:
    """Rechazar texto arbitrario, booleanos y conteos negativos."""
    if type(value) is not int or value < 0:
        raise ValueError("Conteo agregado inválido")


def _digest(value: object, length: int = 64) -> None:
    """Admitir únicamente huellas hexadecimales."""
    if not isinstance(value, str) or re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is None:
        raise ValueError("Huella inválida")


def validate_canonical_tracking(payload: dict) -> None:
    """Validar recursivamente la allowlist antes de abrir el SDK o almacenamiento."""
    _closed(payload, FIELDS)
    for name in (
        "raw_manifest_digest",
        "builder_config_digest",
        "lock_digest",
        "canonical_semantic_digest",
        "serialized_sha256",
    ):
        _digest(payload[name])
    _digest(payload["builder_git_sha"], 40)
    if type(payload["builder_git_dirty"]) is not bool:
        raise ValueError("Estado Git inválido")
    _closed(payload["source_hashes"], set(INVENTORY))
    for value in payload["source_hashes"].values():
        _digest(value)
    if payload["profile"] not in {"approved", "operational_full", "synthetic"}:
        raise ValueError("Perfil inválido")
    hashes = payload["reconstruction_hashes"]
    if not isinstance(hashes, list):
        raise ValueError("Reconstrucciones inválidas")
    if payload["certification"] == "PASSED_N3":
        if len(hashes) != 3 or any(value != payload["serialized_sha256"] for value in hashes):
            raise ValueError("Falsa certificación N=3")
    elif payload["certification"] != "UNCERTIFIED" or hashes:
        raise ValueError("Estado de certificación inválido")
    names = {"dengue_notifications", "severe_dengue_notifications", "daily_climate"}
    _closed(payload["quarantine"], names)
    for row in payload["quarantine"].values():
        _closed(row, {"input", "retained", "reserved", "invalid_date", "digest"})
        _digest(row["digest"])
        for name in ("input", "retained", "reserved", "invalid_date"):
            _count(row[name])
        if row["input"] != row["retained"] + row["reserved"] + row["invalid_date"]:
            raise ValueError("Cuarentena no conciliada")
    coverage = payload["coverage"]
    _closed(coverage, {"start", "end", "municipalities", "rows", "nulls"})
    for name in ("start", "end"):
        if (
            not isinstance(coverage[name], str)
            or re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", coverage[name]) is None
        ):
            raise ValueError("Cobertura inválida")
    for name in ("rows", "municipalities"):
        _count(coverage[name])
    _closed(coverage["nulls"], NULL_COLUMNS)
    for value in coverage["nulls"].values():
        _count(value)
    stages = payload["stages"]
    _closed(stages, {"epidemiology", "climate", "monthly_climate_rows"})
    _count(stages["monthly_climate_rows"])
    _closed(stages["climate"], {"input", "accepted", "outside_period"})
    for value in stages["climate"].values():
        _count(value)
    if (
        stages["climate"]["input"]
        != stages["climate"]["accepted"] + stages["climate"]["outside_period"]
    ):
        raise ValueError("Clima no conciliado")
    _closed(stages["epidemiology"], names - {"daily_climate"})
    for row in stages["epidemiology"].values():
        _closed(row, {"input", "accepted", "rejected"})
        _count(row["input"])
        _count(row["accepted"])
        _closed(row["rejected"], REJECTIONS)
        for value in row["rejected"].values():
            _count(value)
        if row["input"] != row["accepted"] + sum(row["rejected"].values()):
            raise ValueError("Epidemiología no conciliada")


def collect_canonical_tracking(
    repo: Path,
    bundle: ResolvedBundle,
    config: BuildConfig,
    artifact: CanonicalArtifact,
    audit: dict,
    hashes: tuple[str, ...] = (),
) -> dict:
    """Capturar linaje operacional sin importar proveedores ni leer filas."""
    git_sha = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    payload = {
        "raw_manifest_digest": bundle.manifest_sha256,
        "source_hashes": {file.logical_name: file.sha256 for file in bundle.files},
        "builder_git_sha": git_sha,
        "builder_git_dirty": dirty,
        "builder_config_digest": stable_digest(config.payload()),
        "lock_digest": sha256(repo / "pipeline/uv.lock"),
        **audit,
        "canonical_semantic_digest": artifact.semantic_digest,
        "serialized_sha256": artifact.serialized_sha256,
        "reconstruction_hashes": list(hashes),
        "certification": "PASSED_N3" if hashes else "UNCERTIFIED",
        "profile": config.profile,
    }
    validate_canonical_tracking(payload)
    return payload
