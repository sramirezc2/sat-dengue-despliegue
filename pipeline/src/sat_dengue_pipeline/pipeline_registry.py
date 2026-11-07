"""Registro explícito de los flujos ejecutables del subproyecto."""

from kedro.pipeline import Pipeline

from sat_dengue_pipeline.pipelines.canonical.pipeline import (
    create_pipeline as canonical_build,
)
from sat_dengue_pipeline.pipelines.canonical.pipeline import (
    create_reproducibility_pipeline,
)
from sat_dengue_pipeline.pipelines.synthetic.pipeline import create_pipeline


def register_pipelines() -> dict[str, Pipeline]:
    """Registrar el smoke test sintético y su alias predeterminado.

    Returns:
        Pipelines que Kedro puede ejecutar por nombre.
    """
    synthetic = create_pipeline()
    return {
        "__default__": synthetic, "synthetic": synthetic,
        "canonical_build": canonical_build(),
        "canonical_reproducibility": create_reproducibility_pipeline(),
    }
