"""Etapas deterministas que prueban orquestación, sin validez científica."""

import logging
from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticObservation:
    """Observación artificial usada exclusivamente por el smoke test."""

    year: int
    value: float


def generate_synthetic_data(years: list[int]) -> tuple[SyntheticObservation, ...]:
    """Generar valores artificiales sin leer archivos ni usar aleatoriedad.

    Args:
        years: Años del fixture de desarrollo sintético.

    Returns:
        Observaciones con valores consecutivos pares.
    """
    return tuple(SyntheticObservation(year, float(2 * (i + 1))) for i, year in enumerate(years))


def prepare_synthetic_data(
    observations: tuple[SyntheticObservation, ...],
) -> tuple[tuple[SyntheticObservation, ...], tuple[SyntheticObservation, ...]]:
    """Validar el fixture y reservar su última observación artificial.

    Args:
        observations: Secuencia artificial ordenada por año.

    Returns:
        Observaciones de ajuste y una observación de comprobación.

    Raises:
        ValueError: Si faltan filas o los años no son crecientes hasta 2024.
    """
    years = [row.year for row in observations]
    if len(years) < 2 or years != sorted(set(years)) or max(years) > 2024:
        raise ValueError("El fixture sintético exige años crecientes y únicos hasta 2024")
    return observations[:-1], observations[-1:]


def train_synthetic_baseline(training: tuple[SyntheticObservation, ...]) -> float:
    """Ajustar un predictor constante con la media artificial.

    Args:
        training: Observaciones sintéticas destinadas al ajuste.

    Returns:
        Constante que predice la línea base trivial.
    """
    return sum(row.value for row in training) / len(training)


def evaluate_synthetic_baseline(
    constant: float, checking: tuple[SyntheticObservation, ...]
) -> tuple[float, ...]:
    """Calcular errores sobre observaciones artificiales de comprobación.

    Args:
        constant: Predicción constante de la línea base sintética.
        checking: Observaciones artificiales reservadas.

    Returns:
        Errores firmados de la predicción constante.
    """
    return tuple(row.value - constant for row in checking)


def summarize_synthetic_metrics(errors: tuple[float, ...]) -> dict[str, float | int]:
    """Producir métricas del smoke test, sin publicar artefactos.

    Args:
        errors: Errores de las observaciones artificiales reservadas.

    Returns:
        Cantidad de comprobaciones, error absoluto medio y error cuadrático medio.
    """
    metrics = {
        "synthetic_check_rows": len(errors),
        "synthetic_mae": sum(abs(error) for error in errors) / len(errors),
        "synthetic_mse": sum(error**2 for error in errors) / len(errors),
    }
    logging.getLogger(__name__).info("Synthetic smoke metrics (no científicas): %s", metrics)
    return metrics
