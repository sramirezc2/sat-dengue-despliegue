"""Verificar publicaciones/T16 por hash, también con Python -O y rutas Windows."""

import json
from hashlib import sha256 as bytes_sha256
from pathlib import Path

from sat_dengue_pipeline.models.logistic import canonical_json
from sat_dengue_pipeline.raw.contract import sha256


def verify(root: Path) -> dict:
    """Reconciliar snapshot e identidad N=3 sin depender de asserts eliminables.

    Args:
        root: Repositorio que contiene el inventario y los archivos protegidos.

    Returns:
        Resumen de preservación; cualquier discrepancia produce ValueError.
    """
    baseline = json.loads((root / "docs/evidence/task17/preservation-baseline.json").read_bytes())
    if len(baseline["sha256"]) != 49:
        raise ValueError("Inventario protegido incompleto")
    for name, digest in baseline["sha256"].items():
        if sha256(root / name) != digest:
            raise ValueError(f"Archivo protegido alterado: {name}")
    published = {p.relative_to(root).as_posix() for p in (root / "datos/resultados").glob("*.json")}
    expected = {p for p in baseline["sha256"] if p.startswith("datos/resultados/")}
    if published != expected or len(published) != 22:
        raise ValueError("Inventario de publicaciones distinto del snapshot de 22 JSON")
    publication_digest = bytes_sha256(
        canonical_json({name: sha256(root / name) for name in sorted(published)})
    ).hexdigest()
    extension = json.loads((root / "docs/decisions/risk-2025-preservation.json").read_bytes())
    if publication_digest != extension["historical_publication_sha256"]:
        raise ValueError("Digest agregado de publicaciones históricas alterado")
    if not extension["sha256"]:
        raise ValueError("Inventario extendido vacío")
    for name, digest in extension["sha256"].items():
        if sha256(root / name) != digest:
            raise ValueError(f"Archivo protegido alterado: {name}")
    previous = [
        p
        for p in baseline["sha256"]
        if p.startswith("docs/evidence/task16/") and "/factory-experiment/" not in p
    ]
    if len(previous) != 16:
        raise ValueError("Inventario histórico T16 distinto de 16 recibos")
    comparison = json.loads(
        (root / "docs/evidence/task16/factory-experiment/n3-comparison.json").read_bytes()
    )
    if (
        comparison["identities"] != [baseline["t16_identity_sha256"]] * 3
        or comparison["all_identities_equal"] is not True
        or comparison["fourth_run_executed"] is not False
    ):
        raise ValueError("Identidad N=3 de T16 alterada")
    return {
        "status": "PASSED",
        "protected_files": len(baseline["sha256"]),
        "published_json": len(published),
        "historical_publication_sha256": publication_digest,
        "extended_protected_files": len(extension["sha256"]),
        "previous_t16_receipts": len(previous),
        "t16_n3_identity": baseline["t16_identity_sha256"],
    }


def main() -> None:
    """Comprobar el repositorio instalado y fallar con código no nulo ante alteración."""
    print(json.dumps(verify(Path(__file__).resolve().parents[2]), sort_keys=True))


if __name__ == "__main__":
    main()
