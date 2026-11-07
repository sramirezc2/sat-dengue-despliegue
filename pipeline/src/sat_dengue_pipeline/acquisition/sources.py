"""Adaptadores intercambiables; la fábrica concentra la selección de proveedor."""

import json
import re
import shutil
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, BinaryIO, Protocol
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, build_opener

from .contracts import DataSource, ReleaseFile, ReleaseManifest, relative_path
from .errors import (
    DownloadError,
    ManifestError,
    MutableRevisionError,
    SourceFileNotFoundError,
    UnknownProviderError,
)
from .resolver import contained_path

HTTPStream = Callable[..., AbstractContextManager[BinaryIO]]
HubDownload = Callable[..., str]


class _NoRedirect(HTTPRedirectHandler):
    """Evitar que una referencia versionada cambie silenciosamente de origen."""

    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        """Rechazar redirecciones en las URLs HTTPS construidas para Zenodo."""
        return None


def _open_zenodo(url: str, *, timeout: float) -> AbstractContextManager[BinaryIO]:
    """Abrir una URL de Zenodo con timeout y sin seguir redirecciones."""
    return build_opener(_NoRedirect()).open(url, timeout=timeout)


def _hub_download(**kwargs: Any) -> str:
    """Invocar el cliente oficial solo cuando se necesita materializar un archivo."""
    from huggingface_hub import hf_hub_download

    return hf_hub_download(**kwargs)


@dataclass(frozen=True)
class LocalSource:
    """Directorio local configurado, con confinamiento de rutas relativas."""

    root: Path

    def materialize(self, file: ReleaseFile, destination: Path) -> None:
        """Copiar el archivo local al temporal controlado por el resolver.

        Args:
            file: Archivo esperado, incluyendo su ruta relativa de origen.
            destination: Temporal en la caché común.

        Raises:
            SourceFileNotFoundError: Si falta el archivo local.
        """
        path = contained_path(self.root, file.remote_path)
        if not path.is_file():
            raise SourceFileNotFoundError("Archivo ausente en el origen local")
        shutil.copyfile(path, destination)


@dataclass(frozen=True)
class HuggingFaceSource:
    """Dataset público fijado a un commit completo, sin autenticación implícita."""

    repo_id: str
    revision: str
    download: HubDownload = _hub_download

    def __post_init__(self) -> None:
        """Exigir repositorio y commit, excluyendo ramas y etiquetas mutables."""
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repo_id):
            raise ManifestError("repo_id de dataset inválido")
        if not re.fullmatch(r"[0-9a-f]{40}", self.revision):
            raise MutableRevisionError("Hugging Face exige una revisión de commit completa")

    def materialize(self, file: ReleaseFile, destination: Path) -> None:
        """Descargar con el SDK oficial y copiar al temporal común.

        Args:
            file: Archivo dentro del dataset fijado.
            destination: Temporal que verificará el resolver.
        """
        with TemporaryDirectory(dir=destination.parent, prefix=".hf-") as sdk_cache:
            path = self.download(
                repo_id=self.repo_id,
                filename=file.remote_path,
                repo_type="dataset",
                revision=self.revision,
                token=False,
                force_download=True,
                cache_dir=sdk_cache,
            )
            shutil.copyfile(path, destination)


@dataclass(frozen=True)
class ZenodoSource:
    """Registro público de una versión concreta, descargado por bloques HTTPS."""

    record_id: str
    revision: str
    open_http: HTTPStream = _open_zenodo
    timeout: float = 30.0

    def __post_init__(self) -> None:
        """Exigir un identificador numérico de versión y timeout positivo."""
        if not re.fullmatch(r"[1-9][0-9]*", self.record_id) or self.revision != self.record_id:
            raise MutableRevisionError("Zenodo exige el ID de registro versionado como revisión")
        if self.timeout <= 0:
            raise ManifestError("Timeout de Zenodo inválido")

    def materialize(self, file: ReleaseFile, destination: Path) -> None:
        """Comprobar identidad del registro y transferir su archivo por bloques.

        Args:
            file: Archivo declarado dentro del registro.
            destination: Temporal local de la caché común.

        Raises:
            MutableRevisionError: Si el servidor devuelve otro registro o un concepto.
            DownloadError: Si los metadatos del registro son inválidos.
        """
        with self.open_http(
            f"https://zenodo.org/api/records/{self.record_id}", timeout=self.timeout
        ) as response:
            metadata = response.read(1_048_577)
        try:
            if len(metadata) > 1_048_576:
                raise ValueError
            record = json.loads(metadata)
            if str(record["id"]) != self.record_id or str(record["conceptrecid"]) == self.record_id:
                raise MutableRevisionError("Zenodo devolvió una referencia conceptual o distinta")
        except MutableRevisionError:
            raise
        except (ValueError, KeyError, TypeError):
            raise DownloadError("Metadatos de registro Zenodo inválidos") from None
        url = (
            f"https://zenodo.org/records/{self.record_id}/files/{quote(file.remote_path, safe='')}"
        )
        with (
            self.open_http(url, timeout=self.timeout) as response,
            destination.open("wb") as output,
        ):
            while block := response.read(64 * 1024):
                output.write(block)


class S3Client(Protocol):
    """Cliente mínimo de objetos; no requiere boto3 ni credenciales."""

    def download_file(self, *, bucket: str, key: str, destination: Path) -> None:
        """Materializar una clave que incluye la revisión del release.

        Args:
            bucket: Almacén configurado para adquisición.
            key: Clave relativa del archivo.
            destination: Temporal local creado por el resolver.
        """


@dataclass(frozen=True)
class S3Source:
    """Adaptador inyectable para S3 o compatible, probado solo con simulaciones."""

    bucket: str
    revision: str
    client: S3Client

    def __post_init__(self) -> None:
        """Exigir bucket simple y prefijo de revisión explícito del release."""
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", self.bucket):
            raise ManifestError("Bucket de adquisición inválido")
        relative_path(self.revision)
        if self.revision.lower() in {"main", "latest", "null"}:
            raise MutableRevisionError("S3 exige una revisión explícita del release")

    def materialize(self, file: ReleaseFile, destination: Path) -> None:
        """Transferir la versión solicitada usando el cliente inyectado.

        Args:
            file: Archivo cuya ruta se añade al prefijo de revisión inmutable.
            destination: Temporal local de adquisición.
        """
        self.client.download_file(
            bucket=self.bucket,
            key=f"{self.revision}/{file.remote_path}",
            destination=destination,
        )


def create_source(
    manifest: ReleaseManifest,
    *,
    hub_download: HubDownload = _hub_download,
    open_http: HTTPStream = _open_zenodo,
    s3_client: S3Client | None = None,
) -> DataSource:
    """Seleccionar el proveedor exclusivamente dentro de adquisición.

    Args:
        manifest: Fuente y revisión declaradas para el release.
        hub_download: Función oficial o doble local de Hugging Face.
        open_http: Abridor HTTPS por bloques o doble local para Zenodo.
        s3_client: Cliente versionado inyectado; no se crea un SDK implícito.

    Returns:
        Adaptador con la misma interfaz independiente del proveedor.

    Raises:
        UnknownProviderError: Si el proveedor no está implementado.
        ManifestError: Si falta configuración o la revisión es mutable.
    """
    match manifest.provider:
        case "local":
            return LocalSource(Path(manifest.location).resolve())
        case "huggingface":
            return HuggingFaceSource(manifest.location, manifest.revision, hub_download)
        case "zenodo":
            return ZenodoSource(manifest.location, manifest.revision, open_http)
        case "s3":
            if s3_client is None:
                raise ManifestError("S3 requiere un cliente versionado inyectado")
            return S3Source(manifest.location, manifest.revision, s3_client)
        case _:
            raise UnknownProviderError("Proveedor de adquisición desconocido")
