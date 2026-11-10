"""Preflight estructural de la caché local, sin adquisición ni reglas científicas."""

from pathlib import Path

ACQUIRE_COMMAND = "uv run --locked --directory pipeline python tools/acquire_private_raw.py"


def acquire_command(manifest: str) -> str:
    """Recomendar la adquisición del mismo manifiesto admitido que se solicitó."""
    return f"{ACQUIRE_COMMAND} --manifest {manifest}"


def reject_cache_symlinks(path: Path) -> None:
    """Rechazar enlaces en la ruta léxica antes de resolverla o escribir crudos."""
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("Caché con enlaces simbólicos no permitida")


def preflight_cache(
    cache: Path, expected: set[str], *, manifest: str, allow_missing: bool = False
) -> None:
    """Rechazar rutas e inventarios inseguros antes de consumir los archivos.

    Args:
        cache: Directorio local determinado por el manifiesto.
        expected: Los cinco nombres públicos aprobados.
        manifest: Selección explícita para la recomendación de recuperación.
        allow_missing: Permitir adquirir faltantes, sin tolerar adicionales o enlaces.

    Raises:
        ValueError: Con diagnóstico controlado, sin rutas o excepciones externas.
    """
    try:
        reject_cache_symlinks(cache)
        command = acquire_command(manifest)
        if not cache.exists():
            if allow_missing:
                return
            raise ValueError(f"Caché inexistente. Ejecute: {command}")
        if not cache.is_dir():
            raise ValueError("La caché debe ser un directorio; revise su ubicación operacional")
        entries = {path.name: path for path in cache.iterdir()}
        missing, extra = expected - entries.keys(), entries.keys() - expected
        if extra:
            raise ValueError(
                "Caché con archivos adicionales; revise el inventario sin borrado automático"
            )
        if any(path.is_symlink() for path in entries.values()):
            raise ValueError("Archivos de caché con enlaces simbólicos no permitidos")
        if any(not path.is_file() for path in entries.values()):
            raise ValueError("Cada entrada de caché debe ser un archivo regular")
        if missing and not allow_missing:
            raise ValueError(
                "Caché con archivos faltantes: " + ", ".join(sorted(missing))
                + f". Ejecute: {command}"
            )
    except OSError:
        raise ValueError(
            f"Caché no accesible. Revise permisos y ejecute: {acquire_command(manifest)}"
        ) from None
