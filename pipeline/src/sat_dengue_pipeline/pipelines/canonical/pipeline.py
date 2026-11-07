"""Grafos explícitos para construcción y certificación desde crudos."""

from kedro.pipeline import Pipeline, node, pipeline

from sat_dengue_pipeline.raw.temporal import raw_temporal_projection

from . import nodes as n


def create_pipeline() -> Pipeline:
    """Construir desde cinco fuentes artificiales con nodos inspeccionables."""
    return pipeline(
        [
            node(n.fixture_input, "params:canonical", "raw_input", name="synthetic_raw_input"),
            node(n.validate_input, "raw_input", "raw_verified", name="raw_contract_validation"),
            node(
                raw_temporal_projection,
                "raw_verified",
                "raw_projection",
                name="raw_temporal_projection",
            ),
            node(
                n.quarantine,
                ["raw_projection", "raw_input"],
                "raw_quarantine",
                name="raw_temporal_quarantine",
            ),
            node(
                n.geography,
                ["raw_verified", "raw_quarantine", "raw_input"],
                "raw_geography",
                name="geography_normalization",
            ),
            node(
                n.epidemiology,
                ["raw_verified", "raw_quarantine", "raw_geography", "raw_input"],
                "raw_epidemiology",
                name="epidemiology_normalization",
            ),
            node(
                n.daily,
                [
                    "raw_verified",
                    "raw_quarantine",
                    "raw_geography",
                    "raw_input",
                    "raw_epidemiology",
                ],
                "raw_daily",
                name="climate_daily_normalization",
            ),
            node(n.monthly, "raw_daily", "raw_monthly", name="climate_monthly_aggregation"),
            node(
                n.sources,
                ["raw_geography", "raw_epidemiology", "raw_monthly", "raw_input"],
                "canonical_sources",
                name="canonical_sources",
            ),
            node(
                n.panel,
                ["canonical_sources", "raw_input"],
                "canonical_panel",
                name="canonical_panel",
            ),
            node(
                n.validate,
                ["canonical_panel", "raw_input", "raw_epidemiology"],
                "canonical_validated",
                name="canonical_validation",
            ),
            node(
                n.serialize,
                ["canonical_validated", "raw_input"],
                "canonical_artifact",
                name="canonical_serialization",
            ),
            node(
                n.audit,
                [
                    "canonical_validated",
                    "raw_quarantine",
                    "raw_epidemiology",
                    "raw_daily",
                    "raw_monthly",
                ],
                "canonical_audit",
                name="canonical_audit",
            ),
            node(
                n.observe,
                ["raw_input", "canonical_artifact", "canonical_audit"],
                "canonical_tracking_receipt",
                name="canonical_tracking",
            ),
        ]
    )


def create_reproducibility_pipeline() -> Pipeline:
    """Certificar N=3 sin reutilizar canonical_build."""
    return pipeline(
        [
            node(n.fixture_input, "params:canonical", "raw_input", name="synthetic_raw_input"),
            node(n.certify, "raw_input", "canonical_certificate", name="canonical_reproducibility"),
            node(
                n.observe_certificate,
                ["raw_input", "canonical_certificate"],
                "canonical_tracking_receipt",
                name="canonical_tracking",
            ),
        ]
    )
