"""Frontera local: lectura, staging privado y promoción con rollback por archivo."""

import csv
import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .contract import decode_json, validate_package
from .errors import PublicationInputError, PublicationTransactionError
from .package import PublicationFile, PublicationPackage

MANIFEST = ".publication/manifest.json"


def load_schema() -> dict:
    """Leer el snapshot del contrato incluido en el paquete, sin importar consumidores."""
    return decode_json(Path(__file__).with_name("dashboard.schema.json").read_bytes())


def read_csv(path: Path) -> list[dict[str, str]]:
    """Leer CSV local con encabezado único y errores de entrada explícitos."""
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            header = reader.fieldnames
            if not header or len(header) != len(set(header)):
                raise PublicationInputError("ERROR: encabezado CSV inválido")
            return list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise PublicationInputError(f"ERROR: no se puede leer {path.name}") from exc


def read_retro(path: Path | None) -> dict | None:
    """Omitir retroanálisis ausente, conservando el comportamiento del CLI legado."""
    if path is None or not path.exists():
        return None
    try:
        return decode_json(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise PublicationInputError(f"ERROR: retroanalisis inválido: {path.name}") from exc


def _safe_path(path: Path) -> Path:
    """Rechazar symlinks en cada componente, sin resolverlos silenciosamente."""
    absolute = path.absolute()
    for part in (absolute, *absolute.parents):
        if part.is_symlink():
            raise PublicationTransactionError("La publicación no admite symlinks")
    return absolute


def _safe_destination(destination: Path) -> Path:
    """Confinar cada salida al destino y preservar la frontera con app/."""
    destination = _safe_path(destination)
    repo = Path(__file__).resolve().parents[5]
    if destination.resolve().is_relative_to(repo / "app"):
        raise PublicationTransactionError("El pipeline no escribe en app/")
    if destination.exists() and not destination.is_dir():
        raise PublicationTransactionError("El destino no es un directorio")
    if destination.exists() and any(path.is_symlink() for path in destination.rglob("*")):
        raise PublicationTransactionError("Symlink dentro del destino")
    return destination


def _write_file(path: Path, data: bytes) -> None:
    """Completar y sincronizar un archivo dentro del staging privado."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


@dataclass(frozen=True)
class StagedPackage:
    """Directorio temporal controlado y paquete esperado, todavía sin promover."""

    root: Path
    destination: Path
    package: PublicationPackage


@dataclass(frozen=True)
class ValidatedStage:
    """Compuerta explícita entre validación completa y promoción."""

    stage: StagedPackage
    manifest_sha256: str


def stage_package(package: PublicationPackage, destination: Path, schema: dict) -> StagedPackage:
    """Preparar todos los bytes fuera del destino; un fallo no toca la publicación."""
    validate_package(package, schema)
    destination = _safe_destination(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix=".satd-publication-", dir=destination.parent))
    try:
        for file in package.files:
            _write_file(root / "new" / file.name, file.content)
        _write_file(root / "new" / MANIFEST, package.manifest)
        return StagedPackage(root, destination, package)
    except BaseException:
        shutil.rmtree(root)
        raise


def _read_stage(stage: StagedPackage, schema: dict) -> dict:
    """Releer bytes reales y verificar integridad, nombres y contrato antes de promover."""
    _safe_path(stage.root)
    tree = stage.root / "new"
    actual = set()
    for path in tree.rglob("*"):
        if path.is_symlink():
            raise PublicationTransactionError("Symlink en staging")
        if path.is_file():
            actual.add(path.relative_to(tree).as_posix())
    expected = {file.name for file in stage.package.files} | {MANIFEST}
    if actual != expected:
        raise PublicationTransactionError("Archivos inesperados en staging")
    package = PublicationPackage(
        tuple(
            PublicationFile(file.name, (tree / file.name).read_bytes())
            for file in stage.package.files
        ),
        (tree / MANIFEST).read_bytes(),
        stage.package.audit,
    )
    if package.files != stage.package.files or package.manifest != stage.package.manifest:
        raise PublicationTransactionError("Staging alterado después de construirlo")
    return validate_package(package, schema)


def validate_staging(stage: StagedPackage, schema: dict) -> ValidatedStage:
    """Eliminar staging fallido y emitir una compuerta solo tras validar todo el conjunto."""
    try:
        _read_stage(stage, schema)
        return ValidatedStage(stage, hashlib.sha256(stage.package.manifest).hexdigest())
    except BaseException:
        shutil.rmtree(stage.root)
        raise


def _replace(source: Path, destination: Path) -> None:
    """Promover un archivo completo mediante reemplazo atómico."""
    os.replace(source, destination)


def promote(validated: ValidatedStage, schema: dict) -> dict:
    """Promover el conjunto aprobado; restaurar backups ante excepciones.

    Args:
        validated: Staging con compuerta de contrato aprobada.
        schema: Contrato explícito para revalidar antes de cualquier reemplazo.

    Returns:
        Recibo de éxito con manifiesto y hashes; un fallo no produce recibo.
    """
    stage = validated.stage
    changed, existed, created_dirs = [], {}, []
    lock = None
    recovery_failed = False
    try:
        manifest = _read_stage(stage, schema)
        if hashlib.sha256(stage.package.manifest).hexdigest() != validated.manifest_sha256:
            raise PublicationTransactionError("Compuerta de manifiesto alterada")
        destination = _safe_destination(stage.destination)
        lock_path = _safe_path(destination.parent / f".{destination.name}.publication.lock")
        try:
            lock = lock_path.open("x")
        except FileExistsError:
            raise PublicationTransactionError("Otra publicación mantiene el lock") from None
        names = [file.name for file in stage.package.files] + [MANIFEST]
        for name in names:
            target = _safe_path(destination / name)
            existed[name] = target.exists()
            if target.exists():
                if not target.is_file():
                    raise PublicationTransactionError("Nombre ocupado por un directorio")
                backup = stage.root / "old" / name
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
        for name in names:
            target = _safe_path(destination / name)
            for directory in (destination, destination / ".publication"):
                if not directory.exists() and (directory == destination or name == MANIFEST):
                    directory.mkdir()
                    created_dirs.append(directory)
            changed.append(name)
            _replace(stage.root / "new" / name, target)
        return {
            "status": "COMMITTED",
            "manifest_sha256": validated.manifest_sha256,
            "files": manifest["files"],
            "candidate": manifest["candidate"],
            "procedure": manifest["procedure"],
        }
    except BaseException as exc:
        try:
            for name in reversed(changed):
                target = _safe_path(stage.destination / name)
                if existed[name]:
                    os.replace(stage.root / "old" / name, target)
                else:
                    target.unlink(missing_ok=True)
            for directory in reversed(created_dirs):
                directory.rmdir()
        except OSError as recovery:
            recovery_failed = True
            raise PublicationTransactionError(
                f"Recuperación incompleta; conservar backups en {stage.root}"
            ) from recovery
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise PublicationTransactionError(
            "Publicación cancelada; versión anterior conservada"
        ) from exc
    finally:
        if lock is not None:
            lock.close()
            lock_path.unlink()
        if not recovery_failed:
            shutil.rmtree(stage.root)
