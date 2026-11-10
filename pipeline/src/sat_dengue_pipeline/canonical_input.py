"""Entrada local neutral para el dominio canónico; no registra releases inexistentes."""

import hashlib
from typing import Any

import pandas as pd

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle
from sat_dengue_pipeline.domain.canonical import build_table


def canonical_from_bundle(bundle: ResolvedBundle) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Leer el archivo lógico panel de un bundle ya resuelto y verificar identidad.

    Args:
        bundle: Rutas y metadatos locales neutrales; sin URLs o clientes.

    Returns:
        Tabla canónica y esquema de roles.

    Raises:
        ValueError: Si falta el panel, cambió su integridad o escapa de la cobertura.
    """
    files = [file for file in bundle.files if file.logical_name == "panel"]
    if len(files) != 1:
        raise ValueError("El bundle exige exactamente un archivo lógico panel")
    file = files[0]
    with file.path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if file.path.stat().st_size != file.size_bytes or digest != file.sha256:
        raise ValueError("El panel local cambió respecto al bundle")
    panel = pd.read_csv(file.path, dtype={"municipality_code": "str", "department_code": "str"})
    if not panel.year_month.between(bundle.coverage_start[:7], bundle.coverage_end[:7]).all():
        raise ValueError("Panel fuera de cobertura declarada por el bundle")
    return build_table(panel)
