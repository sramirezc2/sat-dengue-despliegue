"""Comparar listas de decisiones con datos artificiales, sin scoring ni desenlaces."""

import csv
from copy import deepcopy

import pandas as pd
import pytest
from configuracion import ROOT
from inferencia import CHANNEL_FRACTION, capacity, compare_priorities, geography
from sat_dengue_pipeline.domain.canonical import COUNTS


@pytest.fixture
def inputs():
    """Ranking fijo y cobertura completa; todos elegibles y sin alertas del canal."""
    cities = geography().sort_index()
    ordered = pd.DataFrame({
        "Municipio": cities, "Departamento": ["Meta" if c[:2] == "50" else "Tolima"
                                               for c in cities.index],
        "Posición": pd.array(range(1, 77), dtype="Int64"),
    }).rename_axis("DIVIPOLA")
    counts = pd.DataFrame(0, index=cities.index, columns=COUNTS, dtype="Int64")
    context = pd.DataFrame({"municipality_code": cities.index, "p75_h5_t2": 20.0})
    return ordered, counts, context


def test_channel_fraction_reconciles_published_evidence():
    """La fracción congelada coincide con la única fila científica autorizada."""
    with (ROOT / "docs/evidence/reserva-2023-2024-t2/reserva.csv").open() as stream:
        rows = [r for r in csv.DictReader(stream) if r["receta"] == "log_conclima"
                and r["horizonte"] == "2" and float(r["presupuesto"]) == .1]
    assert len(rows) == 1 and CHANNEL_FRACTION == float(rows[0]["f"])


def test_channel_strict_boundary_zero_and_event_210(inputs):
    """Igualdad no alerta; P75 cero exige casos positivos y 220 nunca se suma."""
    ordered, counts, context = inputs
    counts.iloc[:4, 0] = [20, 19, 0, 1]
    counts.iloc[1:3, 1:] = 999
    context.loc[2:3, "p75_h5_t2"] = 0
    table = compare_priorities(ordered, counts, context)
    assert table.index[table["Alerta canal"]].tolist() == ordered.index[[0, 3]].tolist()
    altered = counts.copy()
    altered[COUNTS[1:]] = 10000
    pd.testing.assert_frame_equal(table, compare_priorities(ordered, altered, context))


def test_comparison_categories_union_positions_and_counts(inputs):
    """Las categorías particionan la unión y mantienen las posiciones originales."""
    ordered, counts, context = inputs
    counts.iloc[[0, 3, 10], 0] = [20, 20, 21]
    table = compare_priorities(ordered, counts, context, 5)
    assert table.index.tolist() == ordered.index[[0, 1, 2, 3, 10]].tolist()
    assert table["Comparación"].tolist() == [
        "Ambos", "Solo modelo", "Solo modelo", "Ambos", "Solo canal",
    ]
    assert table["Posición modelo"].tolist() == [1, 2, 3, 4, 11]
    assert table["Comparación"].value_counts().to_dict() == {
        "Ambos": 2, "Solo modelo": 2, "Solo canal": 1,
    }
    assert table["Alerta canal"].sum() == 3
    assert len(table) == sum(table["Comparación"].value_counts())
    assert list(table) == [
        "Municipio", "Departamento", "Posición modelo", "Alerta canal", "Comparación",
    ]
    assert not any(word in str(table.columns).lower() for word in ("score", "probab", "margin"))


@pytest.mark.parametrize(("percentage", "maximum"), [(5, 4), (10, 8), (100, 76)])
def test_capacity_and_deterministic_channel_ties(inputs, percentage, maximum):
    """Empates del canal por DIVIPOLA, sin depender del orden de entrada."""
    ordered, counts, context = inputs
    counts[COUNTS[0]] = 20
    ordered["Posición"] = pd.array(range(76, 0, -1), dtype="Int64")
    before = deepcopy((ordered, counts, context))
    table = compare_priorities(
        ordered.iloc[::-1], counts.iloc[::-1], context.iloc[::-1], percentage,
    )
    assert capacity(percentage) == maximum
    assert sorted(table.index[table["Alerta canal"]]) == sorted(ordered.index[:maximum])
    assert table["Comparación"].ne("Solo canal").sum() == maximum
    pd.testing.assert_frame_equal(table, compare_priorities(*inputs, percentage))
    pd.testing.assert_series_equal(
        table["Posición modelo"].rename("Posición"),
        ordered.loc[table.index, "Posición"], check_names=False,
    )
    assert table["Posición modelo"].is_monotonic_increasing
    for actual, original in zip(inputs, before, strict=True):
        pd.testing.assert_frame_equal(actual, original)


def test_channel_orders_margin_before_code_and_never_fills(inputs):
    """Una alerta más alejada del umbral precede a otras; no se rellenan cupos."""
    ordered, counts, context = inputs
    counts.iloc[8:14, 0] = [20, 20, 20, 20, 20, 30]
    table = compare_priorities(ordered, counts, context, 5)
    assert sorted(table.index[table["Alerta canal"]]) == sorted(ordered.index[[8, 9, 10, 13]])
    counts[COUNTS[0]] = 0
    counts.iloc[[8, 13], 0] = 20
    table = compare_priorities(ordered, counts, context, 100)
    assert table["Alerta canal"].sum() == 2 and len(table) == 76


def test_channel_uses_same_eligible_cohort_without_scoring(inputs, monkeypatch):
    """Fuera de exceso/canal/predictores solo decide el ranking; no se vuelve a puntuar."""
    from sat_dengue_pipeline.risk.frozen import FrozenLogistic

    def forbidden(*args, **kwargs):
        pytest.fail("La comparación no puede ejecutar scoring")

    monkeypatch.setattr(FrozenLogistic, "score", forbidden)
    ordered, counts, context = inputs
    ordered.loc[ordered.index[:3], "Posición"] = pd.NA
    ordered.loc[ordered.index[3:], "Posición"] = range(1, 74)
    counts.iloc[:4, 0] = 1000
    context.loc[2, "p75_h5_t2"] = pd.NA
    table = compare_priorities(ordered, counts, context, 5)
    assert not set(table.index) & set(ordered.index[:3])
    assert table.index[table["Alerta canal"]].tolist() == [ordered.index[3]]
    assert len(table) == 4 and table["Comparación"].ne("Solo canal").sum() == 4
    ordered["Posición"] = pd.NA
    table = compare_priorities(ordered, counts, context, 100)
    assert table.empty and len(table.columns) == 5


@pytest.mark.parametrize("defect", [
    "column", "missing", "infinite", "negative", "row", "duplicate",
])
def test_incomplete_channel_context_fails_without_reducing_cohort(inputs, defect):
    """Datos inválidos provocan un error; no se imputa ni recorta la población."""
    ordered, counts, context = inputs
    if defect == "column":
        context = context.drop(columns="p75_h5_t2")
    elif defect == "row":
        context = context.iloc[1:]
    elif defect == "duplicate":
        context.loc[1, "municipality_code"] = context.loc[0, "municipality_code"]
    else:
        context.loc[0, "p75_h5_t2"] = {
            "missing": float("nan"), "infinite": float("inf"), "negative": -1,
        }[defect]
    before = ordered.copy(deep=True)
    with pytest.raises(ValueError, match="comparación"):
        compare_priorities(ordered, counts, context)
    pd.testing.assert_frame_equal(ordered, before)
