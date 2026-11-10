"""Reproducción histórica local con salidas exclusivas, sin modificar evidencia T16."""

import argparse
import json
import os
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from sat_dengue_pipeline.acquisition.raw_manifest import HISTORICAL_MANIFEST
from sat_dengue_pipeline.canonical_cache import reject_cache_symlinks
from sat_dengue_pipeline.experiment_management.evidence import exclusive_json
from sat_dengue_pipeline.pipelines.canonical.nodes import build_input, observe
from sat_dengue_pipeline.raw.build import build
from sat_dengue_pipeline.raw.reproducibility import canonical_reproducibility
from sat_dengue_pipeline.raw.worker import enforce_boundaries


def run(root: Path, phase: str) -> int:
    """Reutilizar productores históricos y guardar cada intento bajo data/.

    Args:
        root: Raíz del subproyecto Kedro.
        phase: Construcción provisional (build) o certificación (certify).

    Returns:
        Cero ante éxito, uno ante fallo; nunca reabrir un destino existente.
    """
    if phase not in {"build", "certify"}:
        raise ValueError("Fase desconocida")
    os.chdir(root)
    try:
        data = root / "data"
        reject_cache_symlinks(data)
        data.mkdir(parents=True, exist_ok=True)
        workspace = Path(tempfile.mkdtemp(prefix=f"private-raw-{phase}-", dir=data))
    except (OSError, ValueError):
        print(json.dumps({"status": "FAILED", "error_type": "ReceiptError"}))
        return 1
    stages = {}
    started, cpu = time.perf_counter(), time.process_time()
    record = {
        "phase": phase,
        "status": "FAILED",
        "workspace": workspace.relative_to(root).as_posix(),
    }
    try:
        source = build_input(
            {
                "mode": "approved",
                "workspace": record["workspace"],
                "tracking": False,
                "manifest": HISTORICAL_MANIFEST,
                "profile": "approved",
            }
        )
        if phase == "build":
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
        exclusive_json(
            workspace / (phase + "-artifact.json"),
            {**asdict(artifact), "path": str(artifact.path.resolve())},
        )
        record.update(
            status="PASSED",
            audit=audit,
            tracking=asdict(receipt),
            semantic_digest=artifact.semantic_digest,
            serialized_sha256=artifact.serialized_sha256,
            serialized_bytes=artifact.path.stat().st_size,
        )
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
    try:
        exclusive_json(workspace / (phase + "-real.json"), record)
    except (OSError, ValueError):
        print(json.dumps({"status": "FAILED", "error_type": "ReceiptError"}))
        return 1
    print(json.dumps({k: v for k, v in record.items() if k not in {"audit", "tracking"}}))
    return 0 if record["status"] == "PASSED" else 1


def main() -> int:
    """Resolver el proyecto instalado sin aceptar destinos de evidencia histórica."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("build", "certify"))
    args = parser.parse_args()
    os.environ.pop("HF_TOKEN", None)
    enforce_boundaries(False)
    return run(Path(__file__).resolve().parents[1], args.phase)


if __name__ == "__main__":
    sys.exit(main())
