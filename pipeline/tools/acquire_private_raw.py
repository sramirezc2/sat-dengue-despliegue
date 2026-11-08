"""Adquirir exclusivamente el manifiesto crudo aprobado; nunca hacer login."""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest
from sat_dengue_pipeline.acquisition.raw_manifest import validate_raw_manifest
from sat_dengue_pipeline.acquisition.resolver import resolve_release
from sat_dengue_pipeline.acquisition.sources import create_source
from sat_dengue_pipeline.raw.contract import BuildConfig, raw_contract_validation


def main() -> int:
    """Validar privacidad/SHA antes de transferir cinco archivos y verificar hashes."""
    logging.disable(logging.CRITICAL)
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    from huggingface_hub import HfApi

    root = Path(__file__).resolve().parents[1]
    manifest = ReleaseManifest.from_json((root / "conf/releases/approved-raw.json").read_text())
    validate_raw_manifest(manifest)
    receipt = {"at_utc": datetime.now(timezone.utc).isoformat(), "status": "FAILED"}
    started = time.perf_counter()
    try:
        if not os.environ.get("HF_TOKEN"):
            raise ValueError("Credencial de entorno ausente")
        info = HfApi().dataset_info(
            manifest.location,
            revision=manifest.revision,
            files_metadata=True,
            token=os.environ["HF_TOKEN"],
        )
        if info.private is not True or info.sha != manifest.revision:
            raise ValueError("Precondición de privacidad o revisión incumplida")
        receipt.update(private=True, revision=info.sha, dataset=manifest.location)
        source = create_source(manifest, use_env_token=True)
        bundle = resolve_release(manifest, root / "data/01_raw/inbox", source)
        raw_contract_validation(bundle, BuildConfig())
        receipt.update(
            status="VERIFIED",
            manifest_sha256=manifest.manifest_sha256,
            files=[
                {"name": f.path.name, "size_bytes": f.size_bytes, "sha256": f.sha256}
                for f in bundle.files
            ],
            excel_downloaded=False,
        )
    except Exception as error:
        receipt.update(
            error_type=type(error).__name__,
            http_status=getattr(getattr(error, "response", None), "status_code", None),
        )
    receipt["elapsed_seconds"] = time.perf_counter() - started
    evidence = root.parent / "docs/evidence/task16/acquisition.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))
    return 0 if receipt["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
