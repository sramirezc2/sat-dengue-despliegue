"""Adquisición de entradas; las etapas futuras consumirán solo ResolvedBundle."""

from .contracts import DataSource, ReleaseFile, ReleaseManifest, ResolvedBundle, ResolvedFile
from .resolver import resolve_release
from .sources import create_source

__all__ = [
    "DataSource",
    "ReleaseFile",
    "ReleaseManifest",
    "ResolvedBundle",
    "ResolvedFile",
    "create_source",
    "resolve_release",
]
