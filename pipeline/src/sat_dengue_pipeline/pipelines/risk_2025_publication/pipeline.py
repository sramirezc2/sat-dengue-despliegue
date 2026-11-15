"""Grafo único desde fuentes crudas hasta la frontera de publicación."""

from kedro.pipeline import Pipeline, node, pipeline

from sat_dengue_pipeline.risk import nodes as n


def create_pipeline() -> Pipeline:
    """Componer etapas explícitas sin CSV ni transferencias manuales intermedias."""
    return pipeline(
        [
            node(n.preflight, "params:risk_2025", "risk_context", name="risk_preflight"),
            node(n.sources, "risk_context", "risk_raw", name="risk_sources"),
            node(n.frozen_model, ["risk_context", "risk_raw"], "risk_model", name="risk_model"),
            node(
                n.monthly,
                ["risk_context", "risk_raw", "risk_model"],
                "risk_documents",
                name="risk_monthly",
            ),
            node(
                n.package, ["risk_context", "risk_documents"], "risk_package", name="risk_package"
            ),
            node(n.publish, ["risk_context", "risk_package"], "risk_receipt", name="risk_publish"),
        ]
    )
