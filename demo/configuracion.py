"""Rutas locales de la demo; la identidad científica nunca es configurable."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "modelos/logistica-conclima-t2"
CONTEXT_DIR = ROOT / "pipeline/data/demo"


def resource_directory(
    variable: str,
    default: Path,
    directory: Path | None = None,
    *,
    required: bool = True,
    create: bool = False,
) -> Path:
    """Resolver un directorio existente sin traversal ni enlaces simbólicos.

    Args:
        variable: Variable de entorno que permite ubicar el recurso.
        default: Directorio predeterminado dentro del repositorio.
        directory: Ruta explícita opcional para validaciones locales.
        required: Exigir que exista; False permite detectar ausencia antes del fallback.
        create: Crear un directorio privado para caché o salida offline.

    Returns:
        Ruta absoluta validada; las rutas relativas parten de la raíz del repo.
    """
    value = str(directory) if directory is not None else os.environ.get(variable, str(default))
    if not value.strip() or "\x00" in value or "://" in value:
        raise ValueError(f"{variable} requiere una ruta local no vacía.")
    path = Path(value).expanduser()
    if ".." in path.parts:
        raise ValueError(f"{variable} no admite componentes '..'.")
    if not path.is_absolute():
        path = ROOT / path
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f"{variable} no admite enlaces simbólicos.")
    if create:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = path.resolve(strict=required or create)
    if path.exists() and not path.is_dir():
        raise ValueError(f"{variable} debe ser un directorio.")
    return path


def resource_file(directory: Path, name: str) -> Path:
    """Exigir un archivo regular dentro del directorio validado."""
    path = directory / name
    if path.parent != directory or path.is_symlink() or not path.is_file():
        raise ValueError("Recurso ausente, enlazado o fuera del directorio configurado.")
    return path
