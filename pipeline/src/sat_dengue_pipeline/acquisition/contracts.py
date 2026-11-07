"""Contratos inmutables de release y bundle, sin SDKs de proveedores."""

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Protocol, Self

from .errors import ManifestError


def relative_path(value: str) -> str:
    """Validar una ruta relativa portable sin componentes de escape.

    Args:
        value: Ruta POSIX dentro del origen o del bundle.

    Returns:
        La ruta validada sin normalización implícita.

    Raises:
        ManifestError: Si es absoluta, ambigua o contiene un escape.
    """
    if (
        not isinstance(value, str)
        or not value
        or any(char in value for char in "\\:\x00")
        or PurePosixPath(value).is_absolute()
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ManifestError("Ruta relativa inválida")
    return value


def _identifier(value: str) -> None:
    """Exigir un identificador simple apto para nombres locales."""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
        raise ManifestError("Identificador inválido")


@dataclass(frozen=True, slots=True)
class ReleaseFile:
    """Archivo declarado por el release, con integridad obligatoria."""

    logical_name: str
    remote_path: str
    relative_path: str
    size_bytes: int
    sha256: str

    def __post_init__(self) -> None:
        """Validar campos al construir el contrato, también fuera de JSON."""
        _identifier(self.logical_name)
        relative_path(self.remote_path)
        relative_path(self.relative_path)
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ManifestError("Tamaño esperado inválido")
        if not isinstance(self.sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise ManifestError("SHA-256 esperado inválido")


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    """Definición de adquisición versionada; no viaja al dominio científico."""

    schema_version: int
    release_id: str
    provider: str
    location: str
    revision: str
    coverage_start: str
    coverage_end: str
    files: tuple[ReleaseFile, ...]

    def __post_init__(self) -> None:
        """Validar esquema, cobertura declarada y unicidad del release."""
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ManifestError("Versión de esquema no soportada")
        _identifier(self.release_id)
        _identifier(self.provider)
        for value in (self.location, self.revision):
            if not isinstance(value, str) or not value.strip() or "\x00" in value:
                raise ManifestError("Origen o revisión inválidos")
        try:
            start = date.fromisoformat(self.coverage_start)
            end = date.fromisoformat(self.coverage_end)
            if start > end or start.isoformat() != self.coverage_start:
                raise ValueError
            if end.isoformat() != self.coverage_end:
                raise ValueError
        except (TypeError, ValueError):
            raise ManifestError("Cobertura temporal declarada inválida") from None
        if not isinstance(self.files, tuple) or not self.files:
            raise ManifestError("El release debe contener archivos en una tupla inmutable")
        if not all(isinstance(file, ReleaseFile) for file in self.files):
            raise ManifestError("Declaración de archivo inválida")
        names = [file.logical_name for file in self.files]
        paths = [file.relative_path.casefold() for file in self.files]
        if len(set(names)) != len(names) or len(set(paths)) != len(paths):
            raise ManifestError("Nombres lógicos o destinos duplicados")
        for path in paths:
            if any(other.startswith(path + "/") for other in paths if other != path):
                raise ManifestError("Destinos de archivo y directorio incompatibles")

    @classmethod
    def from_json(cls, text: str) -> Self:
        """Construir un manifiesto estricto a partir de JSON.

        Args:
            text: Contenido completo del manifiesto, sin secretos.

        Returns:
            Manifiesto validado.

        Raises:
            ManifestError: Si hay campos ausentes, desconocidos o inválidos.
        """
        try:
            data = json.loads(text)
            files = tuple(ReleaseFile(**item) for item in data.pop("files"))
            return cls(**data, files=files)
        except ManifestError:
            raise
        except (TypeError, ValueError, KeyError, AttributeError):
            raise ManifestError("Campos de manifiesto inválidos") from None

    @property
    def manifest_sha256(self) -> str:
        """Calcular el digest sobre JSON canónico UTF-8, sin espacios."""
        canonical = json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ResolvedFile:
    """Archivo local validado que puede consumir una etapa científica."""

    logical_name: str
    path: Path
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ResolvedBundle:
    """Referencia inmutable a archivos locales y metadatos neutrales."""

    release_id: str
    manifest_sha256: str
    coverage_start: str
    coverage_end: str
    files: tuple[ResolvedFile, ...]


class DataSource(Protocol):
    """Capacidad mínima de una fuente: materializar un archivo en un temporal."""

    def materialize(self, file: ReleaseFile, destination: Path) -> None:
        """Transferir bytes al destino sin decidir sobre caché o integridad.

        Args:
            file: Archivo declarado en el manifiesto.
            destination: Temporal local creado por el resolver.
        """
