"""Verificar publicaciones/T16 por hash, sin adquirir fuentes ni repetir ciencia."""

import json
from pathlib import Path

from sat_dengue_pipeline.raw.contract import sha256


def main() -> None:
    """Reconciliar el snapshot de preflight con los archivos y la identidad N=3 actuales."""
    root = Path(__file__).resolve().parents[2]
    baseline = json.loads((root / "docs/evidence/task17/preservation-baseline.json").read_bytes())
    assert all(sha256(root / name) == digest for name, digest in baseline["sha256"].items())
    published = {str(p.relative_to(root)) for p in (root / "datos/resultados").glob("*.json")}
    assert published == {p for p in baseline["sha256"] if p.startswith("datos/resultados/")}
    assert len(published) == 22
    previous = [
        p
        for p in baseline["sha256"]
        if p.startswith("docs/evidence/task16/") and "/factory-experiment/" not in p
    ]
    assert len(previous) == 16
    comparison = json.loads(
        (root / "docs/evidence/task16/factory-experiment/n3-comparison.json").read_bytes()
    )
    assert comparison["identities"] == [baseline["t16_identity_sha256"]] * 3
    assert comparison["all_identities_equal"] and not comparison["fourth_run_executed"]
    print(
        json.dumps(
            {
                "status": "PASSED",
                "protected_files": len(baseline["sha256"]),
                "published_json": len(published),
                "previous_t16_receipts": len(previous),
                "t16_n3_identity": baseline["t16_identity_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
