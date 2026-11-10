"""Construcción real y certificación local con recibos agregados, sin microdatos."""

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from sat_dengue_pipeline.acquisition.raw_manifest import HISTORICAL_MANIFEST
from sat_dengue_pipeline.pipelines.canonical.nodes import build_input, observe
from sat_dengue_pipeline.raw.build import build
from sat_dengue_pipeline.raw.reproducibility import canonical_reproducibility
from sat_dengue_pipeline.raw.worker import enforce_boundaries


def main() -> int:
    """Reutilizar productores y gate existentes; persistir solo evidencia agregada."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("build", "certify"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    os.environ.pop("HF_TOKEN", None)
    enforce_boundaries(False)
    source = build_input({
        "mode": "approved", "workspace": "data/task16-real", "tracking": True,
        "manifest": HISTORICAL_MANIFEST, "profile": "approved",
    })
    evidence = root.parent / "docs/evidence/task16"
    evidence.mkdir(parents=True, exist_ok=True)
    stages = {}
    started, cpu = time.perf_counter(), time.process_time()
    record = {"phase": args.phase, "status": "FAILED"}
    try:
        if args.phase == "build":
            artifact, audit = build(
                source.bundle,
                source.config,
                source.workspace / "provisional",
                measurements=stages,
            )
            hashes = ()
        else:
            certificate = canonical_reproducibility(
                source.bundle, source.config, source.workspace / "n3"
            )
            artifact, audit, hashes = certificate.artifact, certificate.audit, certificate.hashes
            record.update(
                reconstruction_hashes=hashes,
                semantic_digests=certificate.semantic_digests,
                distinct_worker_processes=len(set(certificate.worker_pids)),
                reconstructions=certificate.measurements,
            )
        receipt = observe(source, artifact, audit, hashes)
        record.update(
            status="PASSED",
            audit=audit,
            tracking=asdict(receipt),
            semantic_digest=artifact.semantic_digest,
            serialized_sha256=artifact.serialized_sha256,
            serialized_bytes=artifact.path.stat().st_size,
        )
        local = source.workspace / (args.phase + "-artifact.json")
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps({**asdict(artifact), "path": str(artifact.path.resolve())}))
    except Exception as error:
        record["error_type"] = type(error).__name__
        # No exception text: third-party parsers may include source values or paths.
        record["completed_stages"] = list(stages)
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        record["peak_rss_bytes"] = int(rss if sys.platform == "darwin" else rss * 1024)
    except ImportError:
        record["peak_rss_bytes"] = None
    record.update(
        wall_seconds=time.perf_counter() - started,
        cpu_seconds=time.process_time() - cpu,
        stages_seconds=stages,
    )
    (evidence / (args.phase + "-real.json")).write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k not in {"audit", "tracking"}}))
    return 0 if record["status"] == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
