"""Corregir únicamente el orden no definido del legado, después de caracterizarlo."""

from copy import deepcopy

from fixtures.publication_fixture import GENERATED, PROCEDURE, publication_rows

from sat_dengue_pipeline.pipelines.deployment_publication.domain import elegir_candidato
from sat_dengue_pipeline.pipelines.deployment_publication.package import (
    PublicationConfig,
    build_package,
)


def test_exact_selection_tie_uses_candidate_identifier():
    """El empate exacto conserva cobertura/coste y deja de depender del orden físico."""
    rows = [
        {"candidate": c, "horizon": "1", "detected_onsets": "2", "false_alerts": "3"}
        for c in ("lightgbm", "gam")
    ]
    assert elegir_candidato(rows)[0] == elegir_candidato(rows[::-1])[0] == "gam"


def test_reordered_inputs_and_tied_comparison_produce_identical_bytes():
    """Panel, predicciones y comparaciones con empates tienen orden estable."""
    panel, predictions, comparison, retro = publication_rows()
    for row in comparison:
        if row["candidate"] == "gam":
            row["detected_onsets"] = "4"
    config = PublicationConfig(PROCEDURE, "synthetic-v1", GENERATED)
    first = build_package(panel, predictions, comparison, retro, config)
    second = build_package(panel[::-1], predictions[::-1], comparison[::-1], retro, config)
    assert first.files == second.files
    assert first.manifest == second.manifest


def test_retro_order_and_input_mutation_protection():
    """Ordenar listas/claves conserva los datos científicos y no altera las entradas."""
    panel, predictions, comparison, retro = publication_rows()
    retro["rows"] += [{**retro["rows"][0], "year": year} for year in (2022, 2021)]
    retro["seeds_checked"] = [42, 1]
    retro["curve"] = [
        {"horizon": "T1", "candidate": "lightgbm", "alerts_emitted": n, "onsets_detected": 1}
        for n in (10, 5)
    ]
    original = deepcopy((panel, predictions, comparison, retro))
    reversed_retro = dict(reversed(list(deepcopy(retro).items())))
    for name in ("rows", "curve"):
        reversed_retro[name] = [
            dict(reversed(list(row.items()))) for row in reversed_retro[name][::-1]
        ]
    reversed_retro["seeds_checked"].reverse()
    config = PublicationConfig(PROCEDURE, "synthetic-v1", GENERATED)
    first = build_package(panel, predictions, comparison, retro, config)
    second = build_package(panel, predictions, comparison, reversed_retro, config)
    assert first.files == second.files
    assert first.manifest == second.manifest
    assert original == (panel, predictions, comparison, retro)
