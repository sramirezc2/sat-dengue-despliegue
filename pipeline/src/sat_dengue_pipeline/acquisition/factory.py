"""Adquisición de fábrica; única frontera que conoce transporte o credencial."""

import logging
import os
from pathlib import Path
from typing import Any

from .contracts import ReleaseManifest, ResolvedBundle
from .raw_manifest import validate_raw_manifest
from .resolver import resolve_release
from .sources import create_source


def acquire(configuration: dict[str, Any], project: Path) -> tuple[ResolvedBundle | None, dict]:
    """Resolver exclusivamente cinco fuentes; devolver errores permitidos sin secretos."""
    old_logging = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    try:
        settings = configuration["acquisition"]
        manifest = ReleaseManifest.from_json((project / settings["manifest"]).read_text())
        validate_raw_manifest(manifest)
        source = create_source(
            manifest, use_env_token=True, require_private=settings["require_private"]
        )
        bundle = resolve_release(manifest, project / settings["cache"], source)
        return bundle, {
            "status": "PASSED", "revision": manifest.revision,
            "private_verified": settings["require_private"],
            "file_count": len(bundle.files), "excel_acquired": False,
        }
    except Exception as error:
        return None, {
            "status": "FAILED", "gate": "acquisition",
            "error_type": type(error).__name__,
            "http_status": getattr(getattr(error, "response", None), "status_code", None),
        }
    finally:
        logging.disable(old_logging)
