"""Grafo E2E explícito que comparte lifecycle y terminales con el ejecutor registrado."""

from functools import partial, update_wrapper

from kedro.pipeline import Pipeline, node, pipeline

from sat_dengue_pipeline.experiment_management import runner


def begin(experiment_id: str) -> runner.RegisteredExecution:
    """Resolver la entrada parametrizada con el registro y las aprobaciones existentes."""
    return runner.begin_execution(experiment_id)


def create_pipeline() -> Pipeline:
    """Registrar adquisición→canónico→roles→fit→predicción→evaluación→evidencia sin handoffs."""
    nodes = [
        node(
            begin,
            "params:experiment_id",
            "experiment_context_0",
            name="registered_experiment_lifecycle",
        )
    ]
    for index, stage in enumerate(runner.STAGES):
        nodes.append(
            node(
                update_wrapper(partial(runner.advance, stage=stage), runner.advance),
                f"experiment_context_{index}",
                f"experiment_context_{index + 1}",
                name=stage,
            )
        )
    nodes.append(
        node(
            runner.finish_execution,
            f"experiment_context_{len(runner.STAGES)}",
            "experiment_receipt",
            name="register_experiment_evidence",
        )
    )
    return pipeline(nodes)
