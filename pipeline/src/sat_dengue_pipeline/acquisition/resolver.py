"""Caché común verificable y publicación atómica de entradas científicas."""

import hashlib
import os
import tempfile
from pathlib import Path

from sat_dengue_pipeline.canonical_cache import reject_cache_symlinks

from .contracts import DataSource, ReleaseFile, ReleaseManifest, ResolvedBundle, ResolvedFile
from .errors import AcquisitionError, CacheError, DownloadError, IntegrityError


def contained_path(root: Path, relative: str) -> Path:
    """Resolver una ruta sin permitir escapes por enlaces simbólicos.

    Args:
        root: Directorio de confinamiento.
        relative: Ruta relativa previamente validada por el contrato.

    Returns:
        Ruta absoluta confinada.

    Raises:
        CacheError: Si la ruta resuelta escapa del directorio.
    """
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise CacheError("La ruta escapa del directorio configurado")
    return path


def _verify(path: Path, file: ReleaseFile) -> None:
    """Comprobar tamaño y SHA-256 sin cargar el archivo completo en memoria."""
    if path.stat().st_size != file.size_bytes:
        raise IntegrityError("Tamaño incorrecto respecto al manifiesto")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != file.sha256:
        raise IntegrityError("SHA-256 incorrecto respecto al manifiesto")


def resolve_release(
    manifest: ReleaseManifest, cache_root: Path, source: DataSource
) -> ResolvedBundle:
    """Resolver un bundle sin conocer el proveedor; utilizable desde un nodo Kedro.

    Args:
        manifest: Declaración inmutable de entradas e integridad.
        cache_root: Caché configurable, excluida de Git.
        source: Fuente seleccionada únicamente en la fábrica de adquisición.

    Returns:
        Bundle de archivos locales verificados, sin clientes ni URLs.

    Raises:
        IntegrityError: Si una transferencia no cumple tamaño o hash.
        DownloadError: Si la materialización se interrumpe.
        CacheError: Si la caché no permite una escritura segura.
    """
    if manifest.release_kind == "raw_sources":
        from .raw_manifest import validate_raw_manifest

        validate_raw_manifest(manifest)
    # Conservar la ruta léxica: resolve() ocultaría enlaces en la raíz de caché.
    root = cache_root.absolute()
    bundle_root = contained_path(root, f"{manifest.release_id}/{manifest.manifest_sha256}")
    try:
        reject_cache_symlinks(bundle_root)
        for file in manifest.files:
            reject_cache_symlinks(contained_path(bundle_root, file.relative_path))
    except ValueError:
        raise CacheError(
            "Caché con enlaces simbólicos no permitida; no se escriben crudos"
        ) from None
    resolved: list[ResolvedFile] = []
    for file in manifest.files:
        path = contained_path(bundle_root, file.relative_path)
        try:
            valid = False
            if path.is_file():
                try:
                    _verify(path, file)
                    valid = True
                except IntegrityError:
                    pass  # Caché corrupta: volver a materializar sin borrar la copia previa.
            if not valid:
                path.parent.mkdir(parents=True, exist_ok=True)
                descriptor, name = tempfile.mkstemp(
                    dir=path.parent, prefix=".acquire-", suffix=".tmp"
                )
                os.close(descriptor)
                temporary = Path(name)
                try:
                    try:
                        source.materialize(file, temporary)
                    except AcquisitionError:
                        raise
                    except Exception:
                        raise DownloadError("Descarga interrumpida") from None
                    _verify(temporary, file)
                    os.replace(temporary, path)
                finally:
                    temporary.unlink(missing_ok=True)
            resolved.append(ResolvedFile(file.logical_name, path, file.size_bytes, file.sha256))
        except OSError:
            raise CacheError("No se pudo leer o materializar el archivo en caché") from None
    return ResolvedBundle(
        manifest.release_id,
        manifest.manifest_sha256,
        manifest.coverage_start,
        manifest.coverage_end,
        tuple(resolved),
        manifest.release_kind,
    )
