"""Definición del flujo mínimo de cinco etapas sintéticas."""

from kedro.pipeline import Pipeline, node

from .nodes import (
    evaluate_synthetic_baseline,
    generate_synthetic_data,
    prepare_synthetic_data,
    summarize_synthetic_metrics,
    train_synthetic_baseline,
)


def create_pipeline() -> Pipeline:
    """Conectar generación, preparación, ajuste, evaluación y métricas.

    Returns:
        Grafo Kedro cuyos datasets se mantienen íntegramente en memoria.
    """
    return Pipeline(
        [
            node(
                generate_synthetic_data,
                "params:synthetic_smoke.years",
                "synthetic_raw",
                name="generate_synthetic_smoke",
            ),
            node(
                prepare_synthetic_data,
                "synthetic_raw",
                ["synthetic_train", "synthetic_check"],
                name="prepare_synthetic_smoke",
            ),
            node(
                train_synthetic_baseline,
                "synthetic_train",
                "synthetic_constant",
                name="train_synthetic_smoke",
            ),
            node(
                evaluate_synthetic_baseline,
                ["synthetic_constant", "synthetic_check"],
                "synthetic_errors",
                name="evaluate_synthetic_smoke",
            ),
            node(
                summarize_synthetic_metrics,
                "synthetic_errors",
                "synthetic_metrics",
                name="summarize_synthetic_smoke",
            ),
        ]
    )
