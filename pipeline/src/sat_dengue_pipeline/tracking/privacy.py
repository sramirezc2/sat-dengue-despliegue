"""Proyección cerrada de agregados y linaje; sin datos individuales ni rutas."""

import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle
from sat_dengue_pipeline.evaluation.metrics import METRICS
from sat_dengue_pipeline.evaluation.paired import EvaluationReport
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.models.adapters import AdapterSpec

IDENTITY = {"candidate", "horizon", "stratum", "paired_keys_digest"}
COMPARISON = {
    "metric",
    "reference",
    "value",
    "status",
    "evaluable",
    "improvement_direction",
    "support_rows",
}
FIELDS = {
    "metrics": IDENTITY
    | {
        "metric",
        "reference",
        "value",
        "evaluable",
        "status",
        "numerator",
        "denominator",
        "support_rows",
        "positive_rows",
        "negative_rows",
        "missing_labels",
        "missing_predictions",
    },
    "comparisons": IDENTITY | COMPARISON,
    "strata": IDENTITY
    | {
        "total_rows",
        "evaluable_rows",
        "positive_rows",
        "negative_rows",
        "municipalities",
        "target_months",
        "excluded_context",
        "excluded_missing_labels",
        "missing_predictions",
        "status",
    },
    "curves": IDENTITY
    | {
        "threshold",
        "diagnostic_only",
        "alerts",
        "true_positives",
        "false_alerts",
        "sensitivity",
        "false_alarm_ratio",
        "relative_volume",
        "status",
    },
    "uncertainty": IDENTITY
    | COMPARISON
    | {
        "point_evaluable",
        "interval_evaluable",
        "lower",
        "upper",
        "requested_replicates",
        "valid_replicates",
        "invalid_replicates",
        "clusters",
        "min_clusters",
        "draws_digest",
        "descriptive_only",
    },
    "replicates": IDENTITY | COMPARISON | {"replicate"},
}
CONFIG_FIELDS = {"thresholds", "bootstrap_replicates", "seed", "min_clusters", "percentiles"}
LINEAGE_FIELDS = {
    "git_sha",
    "git_dirty",
    "release_id",
    "manifest_sha256",
    "input_hashes",
    "provider",
    "coverage_start",
    "coverage_end",
    "seed",
    "horizon",
    "candidate",
    "candidate_config",
    "protocol_digest",
    "frozen_digest",
    "definitions_digest",
    "keys_digest",
    "bootstrap",
    "python",
    "system",
    "machine",
    "lock_sha256",
    "dependencies",
    "utc",
}
DEPENDENCIES = ("numpy", "pandas", "scikit-learn", "scipy", "mlflow-skinny")


def canonical_bytes(value: Any) -> bytes:
    """Serializar sin redondear ni aceptar números JSON no finitos.

    Args:
        value: Agregados o configuración ya validados.

    Returns:
        Bytes deterministas UTF-8.
    """
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def safe_values(value: Any) -> None:
    """Rechazar valores con aspecto de secretos, URI, rutas o códigos individuales.

    Args:
        value: Árbol JSON de valores; las allowlists se comprueban por separado.
    """
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or re.search(
                r"token|password|secret|credential|api_key|username|municipality|path|url",
                key,
                re.I,
            ):
                raise ValueError("Clave privada o no permitida")
            safe_values(key)
            safe_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            safe_values(item)
    elif isinstance(value, str):
        if (
            len(value) > 512
            or "/" in value
            or "\\" in value
            or value.startswith("~")
            or re.search(
                r"hf_[A-Za-z0-9]+|gh[pousr]_[A-Za-z0-9]+|AKIA[0-9A-Z]{16}|PRIVATE KEY|"
                r"bearer\s|password=|token=|secret=|(?<!\w)\d{5}(?!\w)",
                value,
                re.I,
            )
        ):
            raise ValueError("Valor privado, secreto o ruta no permitido")
    elif value is not None and not isinstance(value, (int, float, bool)):
        raise ValueError("Solo se permiten valores JSON escalares")
    canonical_bytes(value)


def aggregate_artifacts(report: EvaluationReport) -> dict[str, Any]:
    """Aceptar solo el esquema agregado conocido; nunca cargar tablas científicas.

    Args:
        report: Resultado inmutable de tarea 11.

    Returns:
        Artefactos agregados permitidos, excluyendo las réplicas detalladas.
    """
    payload = report.payload
    if set(payload) != {
        "schema",
        "frozen_digest",
        "definitions_digest",
        "keys_digest",
        "config",
        *FIELDS,
    }:
        raise ValueError("Campos desconocidos en reporte")
    if payload["schema"] != "paired-evaluation-v1" or set(payload["config"]) != CONFIG_FIELDS:
        raise ValueError("Esquema de agregados/configuración inválido")
    for name, fields in FIELDS.items():
        if not isinstance(payload[name], list):
            raise ValueError("Se esperaba una lista de agregados")
        for row in payload[name]:
            if set(row) != fields:
                raise ValueError("Campo desconocido o individual en agregados")
            if "metric" in row and row["metric"] not in METRICS:
                raise ValueError("Métrica no declarada")
            safe_values(row)
    safe_values(payload["config"])
    return {name + ".json": payload[name] for name in FIELDS if name != "replicates"} | {
        "configuration.json": {
            "schema": payload["schema"],
            "config": payload["config"],
            "frozen_digest": payload["frozen_digest"],
            "definitions_digest": payload["definitions_digest"],
            "keys_digest": payload["keys_digest"],
            "scientific_digest": report.digest,
        },
    }


def collect_lineage(
    repo_root: Path,
    bundle: ResolvedBundle,
    *,
    provider: str,
    spec: AdapterSpec,
    protocol_digest: str,
    report: EvaluationReport,
) -> dict[str, Any]:
    """Capturar Git/entorno y proyectar bundle sin rutas ni proveedor en ciencia.

    Args:
        repo_root: Repositorio de ejecución; ruta solo operacional, no registrada.
        bundle: Contrato neutral de adquisición; sus rutas nunca se proyectan.
        provider: Recibo separado de orquestación, no añadido al bundle.
        spec: Configuración/semilla del candidato.
        protocol_digest: Identidad rolling-origin ya calculada.
        report: Resultados ya calculados.

    Returns:
        Linaje permitido, sin variables de entorno, usuarios o rutas.
    """
    git_sha = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = bool(subprocess.check_output(["git", "-C", str(repo_root), "status", "--porcelain=v1"]))
    versions = {}
    for name in DEPENDENCIES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "absent"
    payload = report.payload
    horizons = {row["horizon"] for row in payload["strata"]}
    if len(horizons) != 1 or {row["candidate"] for row in payload["strata"]} != {spec.candidate}:
        raise ValueError("Linaje de candidato/horizonte inconsistente")
    value = {
        "git_sha": git_sha,
        "git_dirty": dirty,
        "release_id": bundle.release_id,
        "manifest_sha256": bundle.manifest_sha256,
        "input_hashes": {file.logical_name: file.sha256 for file in bundle.files},
        "provider": provider,
        "coverage_start": bundle.coverage_start,
        "coverage_end": bundle.coverage_end,
        "seed": spec.seed,
        "horizon": next(iter(horizons)),
        "candidate": spec.candidate,
        "candidate_config": json.loads(spec.config_json),
        "protocol_digest": protocol_digest,
        "frozen_digest": payload["frozen_digest"],
        "definitions_digest": payload["definitions_digest"],
        "keys_digest": payload["keys_digest"],
        "bootstrap": payload["config"],
        "python": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
        "lock_sha256": hashlib.sha256((repo_root / "pipeline/uv.lock").read_bytes()).hexdigest(),
        "dependencies": versions,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    validate_lineage(value, report)
    return value


def validate_lineage(value: dict[str, Any], report: EvaluationReport) -> None:
    """Validar allowlist completa y recibos antes de crear una corrida.

    Args:
        value: Linaje sin run_id: lo asignará exclusivamente MLflow.
        report: Resultado científico que debe coincidir.
    """
    if set(value) != LINEAGE_FIELDS or value["provider"] not in {
        "local",
        "huggingface",
        "zenodo",
        "s3",
    }:
        raise ValueError("Linaje desconocido o proveedor inválido")
    safe_values(value)
    for name in (
        "manifest_sha256",
        "protocol_digest",
        "frozen_digest",
        "definitions_digest",
        "keys_digest",
        "lock_sha256",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", value[name]):
            raise ValueError("Digest de linaje inválido")
    if not re.fullmatch(r"[0-9a-f]{40}", value["git_sha"]) or type(value["git_dirty"]) is not bool:
        raise ValueError("Recibo Git inválido")
    if (
        not value["input_hashes"]
        or any(re.fullmatch(r"[a-z][a-z_]{0,31}", name) is None for name in value["input_hashes"])
        or any(
            not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in value["input_hashes"].values()
        )
        or set(value["dependencies"]) != set(DEPENDENCIES)
        or type(value["seed"]) is not int
        or value["horizon"] not in (1, 2)
        or value["coverage_start"] > value["coverage_end"]
        or value["coverage_end"][:4] >= "2025"
    ):
        raise ValueError("Entradas/cobertura/entorno inválidos")
    family, identity = value["candidate"].split("@", 1)
    version, _ = identity.split(":", 1)
    if (
        AdapterSpec(
            family, version, canonical_bytes(value["candidate_config"]).decode(), value["seed"]
        ).candidate
        != value["candidate"]
    ):
        raise ValueError("Configuración/semilla diferentes del candidato")
    payload = report.payload
    if {row["candidate"] for row in payload["strata"]} != {value["candidate"]} or {
        row["horizon"] for row in payload["strata"]
    } != {value["horizon"]}:
        raise ValueError("Candidato/horizonte diferente del linaje")
    for name in ("frozen_digest", "definitions_digest", "keys_digest"):
        if value[name] != payload[name]:
            raise ValueError("Digest científico diferente del linaje")
    if value["bootstrap"] != payload["config"]:
        raise ValueError("Bootstrap de linaje diferente")
    stable_digest(value)
