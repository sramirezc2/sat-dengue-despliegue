"""Adquisición de entradas; las etapas futuras consumirán solo ResolvedBundle."""

from typing import Any

from .contracts import DataSource, ReleaseFile, ReleaseManifest, ResolvedBundle, ResolvedFile
from .resolver import resolve_release

__all__ = [
    "DataSource",
    "ReleaseFile",
    "ReleaseManifest",
    "ResolvedBundle",
    "ResolvedFile",
    "create_source",
    "resolve_release",
]


def __getattr__(name: str) -> Any:
    """Cargar la fábrica solo si se solicita, nunca al importar contratos neutrales."""
    if name == "create_source":
        from .sources import create_source

        return create_source
    raise AttributeError(name)
