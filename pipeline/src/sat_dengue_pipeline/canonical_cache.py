"""Preflight estructural de la caché local, sin adquisición ni reglas científicas."""

from pathlib import Path

ACQUIRE_COMMAND = "uv run --locked --directory pipeline python tools/acquire_private_raw.py"


def preflight_cache(cache: Path, expected: set[str]) -> None:
    """Rechazar rutas e inventarios inseguros antes de consumir los archivos.

    Args:
        cache: Directorio local determinado por el manifiesto.
        expected: Los cinco nombres públicos aprobados.

    Raises:
        ValueError: Con diagnóstico controlado, sin rutas o excepciones externas.
    """
    try:
        if any(part.is_symlink() for part in (cache, *cache.parents)):
            raise ValueError("Caché con enlaces simbólicos no permitida")
        if not cache.exists():
            raise ValueError(f"Caché inexistente. Ejecute: {ACQUIRE_COMMAND}")
        if not cache.is_dir():
            raise ValueError("La caché debe ser un directorio; revise su ubicación operacional")
        entries = {path.name: path for path in cache.iterdir()}
        missing, extra = expected - entries.keys(), entries.keys() - expected
        if missing or extra:
            reasons = []
            if missing:
                reasons.append("archivos faltantes: " + ", ".join(sorted(missing)))
            if extra:
                reasons.append("archivos adicionales; revise el inventario sin borrado automático")
            raise ValueError("Caché con " + "; ".join(reasons) + f". Ejecute: {ACQUIRE_COMMAND}")
        if any(path.is_symlink() for path in entries.values()):
            raise ValueError("Archivos de caché con enlaces simbólicos no permitidos")
        if any(not path.is_file() for path in entries.values()):
            raise ValueError("Cada entrada de caché debe ser un archivo regular")
    except OSError:
        raise ValueError(
            f"Caché no accesible. Revise permisos y ejecute: {ACQUIRE_COMMAND}"
        ) from None
