"""Grafo del retroanálisis sobre el panel canónico construido desde crudos."""

from kedro.pipeline import Pipeline, node, pipeline

from sat_dengue_pipeline.pipelines.canonical.pipeline import create_pipeline as canonical_build

from .nodes import retroanalisis


def create_pipeline() -> Pipeline:
    """Construir el panel canónico y correr la validación de ventana expansiva.

    Returns:
        canonical_build más el nodo de retroanálisis.
    """
    return canonical_build() + pipeline(
        [
            node(
                retroanalisis,
                ["canonical_artifact", "params:retroanalisis"],
                [
                    "retroanalisis_resumen",
                    "retroanalisis_por_anio",
                    "retroanalisis_curva",
                    "retroanalisis_omitidos",
                ],
                name="retroanalisis_ventana_expansiva",
            )
        ]
    )
