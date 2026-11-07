"""Comando explícito para observar recibos agregados ya calculados."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from sat_dengue_pipeline.evaluation.paired import EvaluationReport

from .local import LocalTracker, TrackingConfig


def main() -> None:
    """Leer agregados/linaje existentes y devolver solo el recibo de observabilidad."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--lineage", type=Path, required=True)
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--store", default=".tracking/local")
    args = parser.parse_args()
    if args.report.stat().st_size > 20_000_000 or args.lineage.stat().st_size > 64_000:
        raise ValueError("Recibo de entrada demasiado grande")
    report = EvaluationReport(args.report.read_text())
    lineage = json.loads(args.lineage.read_text())
    receipt = LocalTracker(Path.cwd(), TrackingConfig(args.enable, args.store)).record(
        report, lineage
    )
    print(json.dumps(asdict(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
