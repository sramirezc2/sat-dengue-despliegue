"""Grafo padre y grafo interno de cada proceso limpio de fábrica."""

from kedro.pipeline import Pipeline, node, pipeline


def create_run_pipeline() -> Pipeline:
    """Exponer las etapas científicas compartidas por los tres procesos aislados."""
    from sat_dengue_pipeline.factory import engine

    steps = (
        (engine.reconstruct, "factory_context", "factory_canonical", "factory_canonical_build"),
        (engine.prepare, "factory_canonical", "factory_roles", "factory_prepare_horizons"),
        (engine.preflight, "factory_roles", "factory_checked", "factory_all_support_before_fit"),
        (engine.fit, "factory_checked", "factory_fitted", "factory_fit_calibration_threshold"),
        (engine.predict, "factory_fitted", "factory_predictions", "factory_predict_before_labels"),
        (engine.evaluate, "factory_predictions", "factory_evaluated", "factory_evaluation"),
        (engine.receipt, "factory_evaluated", "factory_receipt", "factory_aggregate_receipt"),
    )
    return pipeline(
        [node(function, inputs, outputs, name=name) for function, inputs, outputs, name in steps]
    )


def create_pipeline() -> Pipeline:
    """Adquirir por configuración, certificar N=3 y emitir solo evidencia agregada."""
    from sat_dengue_pipeline.factory import execution

    return pipeline(
        [
            node(
                execution.configure,
                "params:factory_experiment",
                "factory_configuration",
                name="factory_approved_configuration",
            ),
            node(
                execution.acquire_input,
                "factory_configuration",
                "factory_acquired",
                name="factory_five_source_acquisition",
            ),
            node(
                execution.reproduce,
                "factory_acquired",
                "factory_comparison",
                name="factory_three_clean_sequential_processes",
            ),
            node(
                execution.publish,
                "factory_comparison",
                "factory_validation_receipt",
                name="factory_immutable_evidence",
            ),
        ]
    )
