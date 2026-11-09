"""Adquirir cinco crudos aprobados y conservar un recibo operacional exclusivo."""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sat_dengue_pipeline.acquisition.factory import acquire
from sat_dengue_pipeline.acquisition.raw_manifest import RAW_MANIFESTS
from sat_dengue_pipeline.raw.contract import BuildConfig, raw_contract_validation

ERROR_TYPES = {
    "ValueError",
    "OSError",
    "PermissionError",
    "FileNotFoundError",
    "RuntimeError",
    "DownloadError",
    "ManifestError",
    "IntegrityError",
    "CacheError",
    "MutableRevisionError",
    "ConnectionError",
    "TimeoutError",
    "HTTPError",
    "HfHubHTTPError",
}


def run(root: Path, manifest: str = RAW_MANIFESTS[0]) -> int:
    """Adquirir sin login implícito y escribir solo agregados bajo data/acquisition/.

    Args:
        root: Raíz del subproyecto; las pruebas suministran un directorio temporal.
        manifest: Manifiesto histórico o nuevo operacional, seleccionado explícitamente.

    Returns:
        Cero si se verificaron los crudos y el recibo; uno ante fallo controlado.
    """
    execution_id = uuid.uuid4().hex
    receipt = {
        "execution_id": execution_id,
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FAILED",
    }
    started = time.perf_counter()
    try:
        data = root / "data"
        operational = data / "acquisition"
        if data.is_symlink() or operational.is_symlink():
            raise ValueError("Recibos operacionales sin enlaces requeridos")
        operational.mkdir(parents=True, exist_ok=True)
        folder = operational / execution_id
        folder.mkdir()  # Reserva exclusiva; nunca reabrir una ejecución anterior.
    except (OSError, ValueError):
        print(json.dumps({"status": "FAILED", "error_type": "ReceiptError"}))
        return 1
    try:
        if manifest not in RAW_MANIFESTS:
            raise ValueError("Manifiesto operacional no aprobado")
        bundle, result = acquire(
            {
                "acquisition": {
                    "manifest": manifest,
                    "cache": "data/01_raw/inbox",
                    "require_private": True,
                }
            },
            root,
        )
        if bundle is None:
            error_type = result.get("error_type", "AcquisitionError")
            receipt["error_type"] = error_type if error_type in ERROR_TYPES else "AcquisitionError"
        else:
            raw_contract_validation(bundle, BuildConfig())
            receipt.update(
                status="VERIFIED",
                release_id=bundle.release_id,
                revision=result.get("revision"),
                manifest_sha256=bundle.manifest_sha256,
                files=[
                    {"name": file.path.name, "size_bytes": file.size_bytes, "sha256": file.sha256}
                    for file in bundle.files
                ],
                excel_downloaded=False,
            )
    except Exception as error:
        kind = type(error).__name__
        receipt["error_type"] = kind if kind in ERROR_TYPES else "AcquisitionError"
    receipt["elapsed_seconds"] = time.perf_counter() - started
    try:
        with (folder / "receipt.json").open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(receipt, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        print(json.dumps({"status": "FAILED", "error_type": "ReceiptError"}))
        return 1
    print(json.dumps(receipt))
    return 0 if receipt["status"] == "VERIFIED" else 1


def main() -> int:
    """Resolver únicamente el proyecto instalado, sin aceptar destinos históricos."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", choices=RAW_MANIFESTS, default=RAW_MANIFESTS[0])
    arguments = parser.parse_args()
    return run(Path(__file__).resolve().parents[1], arguments.manifest)


if __name__ == "__main__":
    sys.exit(main())
