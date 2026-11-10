"""Orquestación independiente de T16 con lifecycle controlado por el ejecutor."""

from kedro.pipeline import Pipeline, node, pipeline

from sat_dengue_pipeline.experiment_management.runner import kedro_execute


def create_pipeline() -> Pipeline:
    """Registrar ejecución parametrizada por ID sin rutas YAML ejecutables."""
    return pipeline(
        [
            node(
                kedro_execute,
                "params:experiment_id",
                "experiment_receipt",
                name="registered_experiment_lifecycle",
            )
        ]
    )
