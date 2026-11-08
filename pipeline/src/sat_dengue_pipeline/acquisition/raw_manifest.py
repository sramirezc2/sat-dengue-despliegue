"""Compuerta de adquisición cruda, anterior a ResolvedBundle y al dominio científico."""

import re

from sat_dengue_pipeline.raw.contract import INVENTORY

from .contracts import ReleaseManifest


def validate_raw_manifest(manifest: ReleaseManifest) -> None:
    """Exigir inventario aprobado y revisión inmutable antes de materializar."""
    if manifest.release_kind != "raw_sources":
        raise ValueError("Solo release_kind raw_sources; derivados prohibidos")
    if manifest.provider == "zenodo":
        pinned = re.fullmatch(r"[1-9][0-9]*", manifest.revision)
    else:
        pinned = re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", manifest.revision)
    if pinned is None:
        raise ValueError("Revisión cruda mutable o no fijada por contenido/registro")
    actual = {f.logical_name: (f.relative_path, f.size_bytes, f.sha256) for f in manifest.files}
    prefixes = ("", "datos-crudos/") if manifest.provider == "huggingface" else ("",)
    if actual != INVENTORY or not any(
        all(file.remote_path == prefix + INVENTORY[file.logical_name][0] for file in manifest.files)
        for prefix in prefixes
    ):
        raise ValueError("Inventario crudo no aprobado")
