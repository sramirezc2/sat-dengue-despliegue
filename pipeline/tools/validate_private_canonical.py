"""Validar cobertura, formato y fronteras de la única salida certificada real."""

import json
import os
import tempfile
import time
from pathlib import Path

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import CLIMATE, COUNTS, KEYS, predictor_matrix
from sat_dengue_pipeline.domain.temporal import TemporalPolicy, guard_development
from sat_dengue_pipeline.preparation import PREDICTOR_AVAILABILITY, prepare_horizon
from sat_dengue_pipeline.raw.serialization import (
    CanonicalArtifact,
    canonical_serialization,
    load_canonical,
)
from sat_dengue_pipeline.raw.worker import enforce_boundaries


def main() -> None:
    """Rechazar cruces antes de preparación; guardar solo agregados sin municipios."""
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    os.environ.pop("HF_TOKEN", None)
    enforce_boundaries(False)
    started = time.perf_counter()
    evidence = root.parent / "docs/evidence/task16"
    record = json.loads((evidence / "certify-real.json").read_text())
    assert record["status"] == "PASSED" and len(set(record["reconstruction_hashes"])) == 1
    reference = json.loads((root / "data/task16-real/certify-artifact.json").read_text())
    artifact = CanonicalArtifact(**{**reference, "path": Path(reference["path"])})
    assert artifact.serialized_sha256 == record["serialized_sha256"]
    table, schema = load_canonical(artifact)
    assert len(table) == 182886 and table.municipality_code.nunique() == 1122
    assert table.year_month.nunique() == 163 and not table.duplicated(KEYS).any()
    assert table.year_month.min() == "2011-06" and table.year_month.max() == "2024-12"
    with tempfile.TemporaryDirectory(dir=root / "data/task16-real") as directory:
        restored = canonical_serialization((table, schema), Path(directory))
        assert restored.serialized_sha256 == artifact.serialized_sha256
        assert restored.semantic_digest == artifact.semantic_digest
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
    report["wall_seconds"] = time.perf_counter() - started
    (evidence / "canonical-quality.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"columns", "departments"}}))


if __name__ == "__main__":
    main()
