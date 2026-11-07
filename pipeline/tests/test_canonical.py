"""Paridad de ingeniería con V2 fijado y contrato del panel de V3."""

import copy
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
from fixtures.canonical_fixture import canonical_bytes, frame_payload, make_panel

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle, ResolvedFile
from sat_dengue_pipeline.canonical_input import canonical_from_bundle
from sat_dengue_pipeline.domain.calendar import add_months, history_periods_for_target
from sat_dengue_pipeline.domain.canonical import (
    CLIMATE,
    COUNTS,
    KEYS,
    PREDICTORS,
    build_table,
    coverage_report,
    predictor_matrix,
)
from sat_dengue_pipeline.domain.endemic_channel import classify_endemic_zone, percentile_type7

FIXTURES = Path(__file__).parent / "fixtures"


def test_exact_synthetic_v2_reference() -> None:
    """Comparar valores, tipos, orden, nulos, roles, X y cobertura sin tolerancias."""
    panel = make_panel()
    before = panel.copy(deep=True)
    table, schema = build_table(panel)
    actual = {
        "table": frame_payload(table),
        "schema": schema,
        "predictors": frame_payload(predictor_matrix(table, schema)),
        "coverage": coverage_report(table, schema),
    }
    receipt = json.loads((FIXTURES / "canonical_receipt.json").read_text(encoding="utf-8"))
    expected = (FIXTURES / "canonical_expected.json").read_bytes()
    assert (
        hashlib.sha256(canonical_bytes(frame_payload(panel))).hexdigest() == receipt["input_sha256"]
    )
    assert hashlib.sha256(expected).hexdigest() == receipt["output_sha256"]
    assert actual == json.loads(expected)
    assert hashlib.sha256(canonical_bytes(actual)).hexdigest() == receipt["output_sha256"]
    assert list(schema["column_roles"]) == ["key", "metadata", "feature", "target", "control"]
    pd.testing.assert_frame_equal(panel, before)
    reordered, reordered_schema = build_table(panel.sample(frac=1, random_state=11))
    pd.testing.assert_frame_equal(table, reordered)
    assert schema == reordered_schema


@pytest.mark.parametrize(
    "fault",
    [
        "duplicate",
        "code",
        "period",
        "department",
        "negative",
        "fraction",
        "total",
        "coverage",
        "status",
        "climate",
        "channel",
        "derived",
    ],
)
def test_invalid_panel_fails_closed(fault: str) -> None:
    """Rechazar entradas ambiguas y errores de contrato sin repararlos."""
    panel = make_panel()
    i = 1
    if fault == "duplicate":
        panel = pd.concat([panel, panel.iloc[:1]], ignore_index=True)
    elif fault == "code":
        panel.loc[i, "municipality_code"] = "5000"
    elif fault == "period":
        panel.loc[i, "year_month"] = "2020-13"
    elif fault == "department":
        panel.loc[i, "department_code"] = "73"
    elif fault == "negative":
        panel.loc[i, COUNTS[0]] = -1.0
    elif fault == "fraction":
        panel.loc[i, COUNTS[0]] = 0.5
    elif fault == "total":
        panel.loc[i, COUNTS[2]] = 100.0
    elif fault == "coverage":
        panel.loc[i, COUNTS[0]] = float("nan")
    elif fault == "status":
        panel.loc[i, "epi_count_status"] = "zero_in_coverage"
    elif fault == "climate":
        panel.loc[i, f"{CLIMATE[0]}_valid_days"] = 2
    elif fault == "channel":
        panel["p75_canal_t"] = -1.0
    else:
        panel["month_of_year"] = 1
    with pytest.raises(ValueError):
        build_table(panel)


def test_observed_zero_missingness_climate_and_exact_lags() -> None:
    """Preservar ceros y ausencias y no puentear el mes ausente del fixture."""
    table, schema = build_table(make_panel())
    indexed = table.set_index(KEYS)
    assert indexed.loc[("50998", "2018-01"), COUNTS].isna().all()
    assert (table.loc[table.epi_count_status.eq("zero_in_coverage"), COUNTS] == 0).all().all()
    row = indexed.loc[("50998", "2022-03")]
    assert pd.isna(row[f"{COUNTS[0]}_lag1"])
    assert row[f"{COUNTS[0]}_lag2"] == indexed.loc[("50998", "2022-01"), COUNTS[0]]
    assert pd.isna(indexed.loc[("50998", "2023-02"), "p75_canal_t"])
    assert pd.isna(indexed.loc[("50998", "2023-04"), CLIMATE[0]])
    assert pd.notna(indexed.loc[("73998", "2024-10"), "p75_h5_t1"])
    report = coverage_report(table, schema)
    assert report["departments"]["Meta"]["missing_epi_rows"] == 1
    assert report["departments"]["Tolima"]["observed_zero_rows"] > 0


def test_future_observations_cannot_change_origin_predictors() -> None:
    """Comprobar causalidad del canal, rezagos y umbrales históricos T+1/T+2."""
    panel = make_panel()
    original, schema = build_table(panel)
    future = panel.year_month.gt("2023-03")
    panel.loc[future, COUNTS[0]] = 9999.0
    panel.loc[future, COUNTS[2]] = panel.loc[future, COUNTS[0]] + panel.loc[future, COUNTS[1]]
    panel.loc[future, "epi_count_status"] = "records_present"
    for name in CLIMATE:
        panel.loc[future & panel[f"{name}_valid_days"].eq(panel.expected_days_in_month), name] = (
            123.0
        )
    changed, _ = build_table(panel)
    mask = original.year_month.le("2023-03")
    pd.testing.assert_frame_equal(
        predictor_matrix(original, schema).loc[mask], predictor_matrix(changed, schema).loc[mask]
    )


@pytest.mark.parametrize("column", ["y_t1", "target_period_t1", "eligible_t2", "future_count"])
def test_target_and_control_columns_cannot_enter_x(column: str) -> None:
    """La selección cerrada protege X incluso si se altera el esquema de roles."""
    panel = make_panel()
    panel[column] = 0
    table, schema = build_table(panel)
    assert column not in predictor_matrix(table, schema)
    changed = copy.deepcopy(schema)
    changed["column_roles"]["feature"].append(column)
    with pytest.raises(ValueError, match="Roles"):
        predictor_matrix(table, changed)
    changed = copy.deepcopy(schema)
    changed["column_roles"]["control"].append(KEYS[0])
    with pytest.raises(ValueError, match="Roles"):
        predictor_matrix(table, changed)


def test_calendar_percentile_and_zone_boundaries() -> None:
    """Conservar calendario, tipo 7 y desigualdades exactas en las zonas."""
    assert add_months("2023-12", 2) == "2024-02"
    assert history_periods_for_target("2024-01") == [f"{year}-01" for year in range(2019, 2024)]
    assert percentile_type7([0, 10, 20, 30, 40], 0.25) == 10
    assert percentile_type7([0, 10], 0.25) == 2.5
    assert [classify_endemic_zone(v, 10, 20, 30) for v in (9, 10, 20, 21, 30, 31)] == [
        "EXITO",
        "SEGURIDAD",
        "SEGURIDAD",
        "ALERTA",
        "ALERTA",
        "EXCESO",
    ]


def test_resolved_bundle_input_has_no_provider_dependency(tmp_path: Path) -> None:
    """Consumir solo una ruta local verificada y rechazar alteraciones posteriores."""
    panel = make_panel()
    path = tmp_path / "panel.csv"
    panel.to_csv(path, index=False)
    content = path.read_bytes()
    bundle = ResolvedBundle(
        "synthetic",
        "a" * 64,
        "2018-01-01",
        "2024-12-31",
        (ResolvedFile("panel", path, len(content), hashlib.sha256(content).hexdigest()),),
    )
    table, schema = canonical_from_bundle(bundle)
    expected, expected_schema = build_table(panel)
    pd.testing.assert_frame_equal(table, expected)
    assert schema == expected_schema
    assert list(predictor_matrix(table, schema)) == PREDICTORS
    path.write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="cambió"):
        canonical_from_bundle(bundle)
