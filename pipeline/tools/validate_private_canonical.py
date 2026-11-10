"""Validar un canónico histórico con recibo nuevo exclusivo bajo data/."""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

from sat_dengue_pipeline.canonical_cache import reject_cache_symlinks
from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import CLIMATE, COUNTS, KEYS, predictor_matrix
from sat_dengue_pipeline.domain.temporal import TemporalPolicy, guard_development
from sat_dengue_pipeline.experiment_management.evidence import exclusive_json
from sat_dengue_pipeline.preparation import PREDICTOR_AVAILABILITY, prepare_horizon
from sat_dengue_pipeline.raw.serialization import (
    CanonicalArtifact,
    canonical_serialization,
    load_canonical,
)
from sat_dengue_pipeline.raw.worker import enforce_boundaries


def validate(certification: Path, reference: Path, workspace: Path) -> dict:
    """Reutilizar guards y serialización para el contrato histórico cerrado.

    Args:
        certification: Recibo N=3 de entrada, exclusivamente de lectura.
        reference: Referencia al artefacto local que se valida.
        workspace: Directorio nuevo para el roundtrip temporal.

    Returns:
        Agregados de calidad; un fallo no modifica las entradas.
    """
    record = json.loads(certification.read_bytes())
    if record["status"] != "PASSED" or (
        len(record["reconstruction_hashes"]) != 3 or len(set(record["reconstruction_hashes"])) != 1
    ):
        raise ValueError("Certificación histórica N=3 no aprobada")
    payload = json.loads(reference.read_bytes())
    artifact = CanonicalArtifact(**{**payload, "path": Path(payload["path"])})
    if artifact.serialized_sha256 != record["serialized_sha256"]:
        raise ValueError("Artefacto distinto del certificado histórico")
    table, schema = load_canonical(artifact)
    if (
        len(table) != 182886
        or table.municipality_code.nunique() != 1122
        or table.year_month.nunique() != 163
        or table.duplicated(KEYS).any()
        or table.year_month.min() != "2011-06"
        or table.year_month.max() != "2024-12"
    ):
        raise ValueError("Cobertura o claves fuera del perfil histórico")
    with tempfile.TemporaryDirectory(dir=workspace) as directory:
        restored = canonical_serialization((table, schema), Path(directory))
        if (restored.serialized_sha256, restored.semantic_digest) != (
            artifact.serialized_sha256,
            artifact.semantic_digest,
        ):
            raise ValueError("Roundtrip canónico diferente")
    report = {
        "status": "PASSED",
        "rows": len(table),
        "municipalities": 1122,
        "months": 163,
        "period_start": "2011-06",
        "period_end": "2024-12",
        "duplicate_keys": 0,
        "reserved_observations": int(table.year_month.ge("2025-01").sum()),
        "format": "satd-canonical-json-v1",
        "roundtrip_bytes_identical": True,
        "columns": schema["columns"],
        "complete_climate_rows": int(table[CLIMATE].notna().all(axis=1).sum()),
        "complete_predictor_rows": int(predictor_matrix(table, schema).notna().all(axis=1).sum()),
        "counts": {name: int(table[name].sum()) for name in COUNTS},
        "departments": {},
        "horizons": {},
        "scientific_experiment": "PENDING_APPROVED_SPECIFICATION",
        "learned_components_invoked": 0,
        "operational_availability": "UNPROVEN; retrospective consolidated data",
    }
    for code, group in table.groupby("department_code", sort=True):
        report["departments"][str(code)] = {
            "rows": len(group),
            "municipalities": int(group.municipality_code.nunique()),
            "complete_climate_rows": int(group[CLIMATE].notna().all(axis=1).sum()),
            "zero_epi_rows": int(group.epi_count_status.eq("zero_in_coverage").sum()),
        }
    for horizon in (1, 2):
        latest = add_months("2024-12", -horizon)
        origins = table.loc[table.year_month.le(latest), KEYS].reset_index(drop=True)
        guard_development(table[KEYS], origins, (horizon,), TemporalPolicy())
        _, _, prepared, audit = prepare_horizon(
            table, schema, origins, horizon, PREDICTOR_AVAILABILITY
        )
        audit.update(
            positive_usable_labels=int(prepared.y.sum()),
            negative_usable_labels=int(prepared.y.eq(0).sum()),
            municipalities_with_usable_rows=int(prepared.keys.municipality_code.nunique()),
        )
        crossing = table.loc[table.year_month.eq(add_months(latest, 1)), KEYS]
        try:
            prepare_horizon(table, schema, crossing, horizon, PREDICTOR_AVAILABILITY)
        except ValueError:
            audit["reserved_target_rejected_before_preparation"] = True
        else:
            raise AssertionError("Cruce de 2025 no rechazado")
        report["horizons"][str(horizon)] = audit
    return report


def run(root: Path, certification: Path, reference: Path) -> int:
    """Reservar una salida nueva y conservar recibo de éxito o fallo sin microdatos.

    Args:
        root: Raíz del subproyecto Kedro.
        certification: Recibo N=3, relativo a root o absoluto; nunca se escribe.
        reference: Referencia al artefacto, relativa a root o absoluta; solo lectura.

    Returns:
        Cero si la validación pasa, uno ante fallo controlado.
    """
    os.chdir(root)
    started = time.perf_counter()
    try:
        data = root / "data"
        reject_cache_symlinks(data)
        data.mkdir(parents=True, exist_ok=True)
        workspace = Path(tempfile.mkdtemp(prefix="private-canonical-validation-", dir=data))
    except (OSError, ValueError):
        print(json.dumps({"status": "FAILED", "error_type": "ReceiptError"}))
        return 1
    report = {"status": "FAILED"}
    try:
        report = validate(root / certification, root / reference, workspace)
    except Exception as error:
        # Los parsers pueden incluir valores o rutas privadas en su texto de excepción.
        report["error_type"] = type(error).__name__
    report.update(
        workspace=workspace.relative_to(root).as_posix(),
        wall_seconds=time.perf_counter() - started,
    )
    try:
        exclusive_json(workspace / "canonical-quality.json", report)
    except (OSError, ValueError):
        print(json.dumps({"status": "FAILED", "error_type": "ReceiptError"}))
        return 1
    print(json.dumps({k: v for k, v in report.items() if k not in {"columns", "departments"}}))
    return 0 if report["status"] == "PASSED" else 1


def main() -> int:
    """Leer las entradas históricas por defecto; escribir únicamente una salida nueva."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--certification", type=Path, default=Path("../docs/evidence/task16/certify-real.json")
    )
    parser.add_argument(
        "--artifact", type=Path, default=Path("data/task16-real/certify-artifact.json")
    )
    args = parser.parse_args()
    os.environ.pop("HF_TOKEN", None)
    enforce_boundaries(False)
    return run(Path(__file__).resolve().parents[1], args.certification, args.artifact)


if __name__ == "__main__":
    sys.exit(main())
