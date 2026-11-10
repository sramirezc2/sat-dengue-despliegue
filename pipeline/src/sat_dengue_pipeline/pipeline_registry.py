"""Registro explícito de los flujos ejecutables del subproyecto."""

from kedro.pipeline import Pipeline

from sat_dengue_pipeline.pipelines.canonical.pipeline import (
    create_pipeline as canonical_build,
)
from sat_dengue_pipeline.pipelines.canonical.pipeline import (
    create_reproducibility_pipeline,
)
from sat_dengue_pipeline.pipelines.deployment_publication import create_pipeline as publication
from sat_dengue_pipeline.pipelines.experiment_run.pipeline import (
    create_pipeline as experiment_run,
)
from sat_dengue_pipeline.pipelines.factory_validation.pipeline import (
    create_pipeline as factory_validation,
)
from sat_dengue_pipeline.pipelines.retroanalisis import create_pipeline as retroanalisis
from sat_dengue_pipeline.pipelines.synthetic.pipeline import create_pipeline


def register_pipelines() -> dict[str, Pipeline]:
    """Registrar el smoke test sintético y su alias predeterminado.

    Returns:
        Pipelines que Kedro puede ejecutar por nombre.
    """
    synthetic = create_pipeline()
    return {
        "__default__": synthetic,
        "synthetic": synthetic,
        "canonical_build": canonical_build(),
        "canonical_reproducibility": create_reproducibility_pipeline(),
        "deployment_publication": publication(),
        "factory_validation": factory_validation(),
        "experiment_run": experiment_run(),
        "retroanalisis": retroanalisis(),
    }
