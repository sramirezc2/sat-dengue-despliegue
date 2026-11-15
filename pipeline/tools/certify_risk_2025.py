"""Certificación N=3 diferida: no ejecutar mientras EXP006 siga activo."""

import argparse
import json

from sat_dengue_pipeline.models.logistic import canonical_json
from sat_dengue_pipeline.risk.certification import certify
from sat_dengue_pipeline.risk.configuration import local_path


def main() -> None:
    """Lanzar únicamente cuando el equipo autorice la fase intensiva."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", action="store_true", help="Solo fuentes artificiales")
    parser.add_argument(
        "--activate",
        action="store_true",
        help="Registrar hashes certificados para publicación ordinaria",
    )
    args = parser.parse_args()
    if args.activate and args.synthetic:
        parser.error("La certificación artificial no puede activar una publicación científica")
    if args.activate and local_path("data/risk-2025/approved.json").exists():
        parser.error("Ya existe una activación: publicar desde congelado, sin repetir N=3")
    result = certify(synthetic=args.synthetic)
    if args.activate:
        approved = {
            k: result[k]
            for k in ("artifact_directory", "artifact_sha256", "certificate", "certificate_sha256")
        }
        target = local_path("data/risk-2025/approved.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = canonical_json(approved)
        if target.exists() and target.read_bytes() != raw:
            raise ValueError("Ya existe otra activación; conservarla y usar una edición explícita")
        if not target.exists():
            with target.open("xb") as stream:
                stream.write(raw)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
