"""Pipeline de publicación explícito, fuera del pipeline científico predeterminado."""

from kedro.pipeline import Pipeline, node, pipeline

from . import nodes as n
from .io import load_schema, promote, validate_staging


def create_pipeline() -> Pipeline:
    """Construir, validar y promover únicamente tras aprobar todos los gates."""
    return pipeline(
        [
            node(
                n.prepare_inputs,
                "params:publication",
                "publication_inputs",
                name="publication_inputs",
            ),
            node(load_schema, None, "publication_schema", name="publication_contract"),
            node(
                n.construct,
                "publication_inputs",
                "publication_package",
                name="publication_construct",
            ),
            node(
                n.stage,
                ["publication_package", "publication_inputs", "publication_schema"],
                "publication_staging",
                name="publication_staging",
            ),
            node(
                validate_staging,
                ["publication_staging", "publication_schema"],
                "publication_validated",
                name="publication_validate",
            ),
            node(
                promote,
                ["publication_validated", "publication_schema"],
                "publication_receipt",
                name="publication_promote",
            ),
            node(
                n.manifest,
                "publication_package",
                "publication_manifest",
                name="publication_manifest",
            ),
        ]
    )
