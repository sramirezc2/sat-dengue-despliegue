"""Nodos delgados para entradas locales, construcción, staging y compuerta contractual."""

from dataclasses import dataclass
from pathlib import Path

from .errors import PublicationInputError
from .io import StagedPackage, read_csv, read_retro, stage_package
from .package import PublicationConfig, PublicationPackage, build_package
from .synthetic import write_inputs


@dataclass(frozen=True)
class PublicationInputs:
    """Entradas y configuración operacionales, separadas de efectos de publicación."""

    panel: list[dict]
    predictions: list[dict]
    comparison: list[dict]
    retro: dict | None
    config: PublicationConfig
    destination: Path


def local_inputs(
    paths: dict[str, Path], config: PublicationConfig, destination: Path
) -> PublicationInputs:
    """Leer entradas locales ya calculadas sin importar entrenamiento o proveedores."""
    return PublicationInputs(
        read_csv(paths["panel"]),
        read_csv(paths["predicciones"]),
        read_csv(paths["comparacion"]),
        read_retro(paths.get("retroanalisis")),
        config,
        destination,
    )


def prepare_inputs(parameters: dict) -> PublicationInputs:
    """Seleccionar fixture explícito o rutas locales, con destino sintético por defecto."""
    if parameters["mode"] == "synthetic":
        workspace = Path(parameters["workspace"])
        if workspace.is_absolute() or not workspace.resolve().is_relative_to(
            Path("data").resolve()
        ):
            raise PublicationInputError("Workspace sintético relativo bajo data/ requerido")
        paths = write_inputs(workspace / "inputs")
        destination = workspace / "results"
    elif parameters["mode"] == "local":
        paths = {
            key: Path(value) for key, value in parameters["inputs"].items() if value is not None
        }
        destination = Path(parameters["destination"])
    else:
        raise PublicationInputError("Modo de publicación desconocido")
    config = PublicationConfig(
        parameters["procedure"],
        parameters["data_version"],
        parameters["generated_at"],
        parameters.get("candidate", "auto"),
        parameters.get("model_version"),
        parameters.get("justification", "elegido a mano por bandera"),
    )
    return local_inputs(paths, config, destination)


def construct(source: PublicationInputs) -> PublicationPackage:
    """Delegar la construcción al dominio puro."""
    return build_package(
        source.panel, source.predictions, source.comparison, source.retro, source.config
    )


def stage(package: PublicationPackage, source: PublicationInputs, schema: dict) -> StagedPackage:
    """Preparar el paquete completo fuera del directorio publicado."""
    return stage_package(package, source.destination, schema)


def manifest(package: PublicationPackage) -> dict:
    """Exponer el manifiesto agregado como salida Kedro independiente."""
    from .contract import decode_json

    return decode_json(package.manifest)
