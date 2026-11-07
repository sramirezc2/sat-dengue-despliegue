"""Integración mínima Kedro; sin catálogo operativo ni release supuesto."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import check_temporal_gate, prepare_onset


def create_pipeline() -> Pipeline:
    """Construir compuerta y preparación, para ejecución explícita con MemoryDataset.

    Returns:
        Grafo no registrado en pipeline_registry; no requiere datos reales.
    """
    return pipeline(
        [
            node(
                check_temporal_gate,
                ["canonical_table", "onset_origins", "params:onset.reserved_start"],
                "checked_onset_origins",
                name="guard_onset_temporal_boundary",
            ),
            node(
                prepare_onset,
                [
                    "canonical_table",
                    "canonical_schema",
                    "checked_onset_origins",
                    "params:onset.availability",
                    "params:onset.reserved_start",
                ],
                {
                    name: name
                    for name in (
                        "controls",
                        "labels_t1",
                        "labels_t2",
                        "audit",
                        "eligible_t1",
                        "eligible_t2",
                    )
                },
                name="prepare_onset_horizons",
            ),
        ]
    )
