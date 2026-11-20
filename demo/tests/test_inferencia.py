"""Comprobar la carga mensual y la paridad de la inferencia sin datos privados."""

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from inferencia import Model, geography, parse_upload, ranking
from sat_dengue_pipeline.domain.canonical import CLIMATE, COUNTS, PREDICTORS
from sat_dengue_pipeline.factory.configuration import adapter_spec
from sat_dengue_pipeline.models.logistic import LogisticOnsetAdapter

MONTH = "2024-10"


@pytest.mark.parametrize("suffix", [".csv", ".xlsx"])
def test_monthly_upload(suffix: str) -> None:
    """Ambos formatos cuentan notificaciones sin filtrar confirmados."""
    frame = pd.DataFrame(
        {
            "cod_DPTO_O": ["50001", "50001", "73001", "11001"],
            "INI_SIN": ["03/10/2024"] * 4,
            "Confirmados": [1, 1, 0, 1],
            "COD_EVE": [210, 220, 210, 210],
        }
    )
    stream = io.BytesIO()
    if suffix == ".xlsx":
        frame.to_excel(stream, index=False, engine="openpyxl")
    else:
        frame.to_csv(stream, index=False, sep=";")
    month, counts, summary = parse_upload(stream.getvalue(), suffix, geography().index)
    assert month == MONTH and summary["Notificaciones"] == 3
    assert summary["Fuera de Meta y Tolima"] == 1
    assert counts.loc["50001"].tolist() == [1, 1]
    assert counts.at["73001", "dengue"] == 1 and pd.isna(counts.at["73001", "grave"])


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ("50,2024-10-01,1", "cinco dígitos"),
        ("50001,2024-02-30,1", "fechas"),
        ("50001,2024-10-01,1\n73001,2024-09-30,0", "solo mes"),
    ],
)
def test_invalid_upload(rows: str, message: str) -> None:
    """Un error de entrada no genera un ranking parcial."""
    with pytest.raises(ValueError, match=message):
        parse_upload(
            ("cod_DPTO_O,INI_SIN,Confirmados\n" + rows).encode(),
            ".csv",
            geography().index,
        )


def test_frozen_ranking() -> None:
    """El ranking reproduce el margen lineal y explica municipios sin puntuar."""
    cities = geography().iloc[:5]
    config = yaml.safe_load(
        (Path(__file__).resolve().parents[2] / "pipeline/conf/experiments/EXP315.yml").read_bytes()
    )
    model = LogisticOnsetAdapter(adapter_spec(config))
    data = pd.DataFrame({p: np.arange(5, dtype=float) for p in PREDICTORS}, index=cities.index)
    data.zona_canal_t = ["SEGURIDAD", "ALERTA", "SEGURIDAD", "EXCESO", "SEGURIDAD"]
    model.fit(data, pd.Series([0, 1, 0, 1, 0], index=data.index))
    data[COUNTS[1]] = 0.0
    data[COUNTS[2]] = data[COUNTS[0]]
    data[["p25_canal_t", "p50_canal_t", "p75_canal_t"]] = [0.0, 0.0, 2.0]
    data.iloc[2, data.columns.get_loc(CLIMATE[0])] = np.nan
    matrix = model.matrix(data.iloc[:2])
    expected = pd.Series(
        model._model.decision_function((matrix - model._mean) / model._std),
        index=data.index[:2],
    )
    counts = pd.DataFrame({"dengue": [0, 1, 2, 3], "grave": np.nan}, index=cities.index[:4])
    context = data.assign(year_month=MONTH, municipality_code=cities.index)
    bundle = Model("fixture", model.inference_state(), context, {})
    rows = ranking(bundle, MONTH, counts, cities)
    np.testing.assert_allclose(
        rows.loc[expected.index, "Puntuación T+2"], expected, atol=1e-12, rtol=0
    )
    assert rows["Puntuación T+2"].dropna().is_monotonic_decreasing
    assert rows.loc[cities.index[2:], "Resultado"].tolist() == [
        "Clima incompleto",
        "Exceso en el mes de origen",
        "Sin datos en la carga",
    ]
    with pytest.raises(ValueError, match="cobertura"):
        ranking(bundle, "2025-10", counts, cities)


def test_context_excludes_outcomes_and_frozen_selection_periods() -> None:
    """El contexto privado contiene exclusivamente predictores T y respeta ambos cortes."""
    from types import SimpleNamespace

    from sat_dengue_pipeline.experiment_management.inference_export import context_bytes

    months = ["2023-08", "2023-09", "2024-10", "2024-11", "2024-12"]
    table = pd.DataFrame({c: range(len(months)) for c in PREDICTORS})
    table = table.assign(municipality_code="50001", year_month=months, y_t2=1)
    run = SimpleNamespace(
        table=table,
        temporal={"2": {"support": {"threshold_selection": {"available": "2023-08"}}}},
        config={"reserved_start": "2025-01"},
    )
    context = pd.read_csv(io.BytesIO(context_bytes(run)))
    assert context.year_month.tolist() == ["2023-09", "2024-10"]
    assert list(context) == ["municipality_code", "year_month", *PREDICTORS]


def test_export_checks_derived_features_before_reservation() -> None:
    """La demo exige la matriz canónica declarada antes de consumir un ID."""
    from sat_dengue_pipeline.experiment_management.inference_export import (
        validate_export_configuration,
    )

    path = Path(__file__).resolve().parents[2] / "pipeline/conf/experiments/EXP315.yml"
    config = yaml.safe_load(path.read_bytes())
    validate_export_configuration(config)
    config["preparation"]["variables_mes"] = True
    with pytest.raises(ValueError, match="exportación"):
        validate_export_configuration(config)


def test_upload_counts_match_canonical_producer() -> None:
    """Las filas con confirmados 0 y 1 cuentan igual que en el productor canónico."""
    from sat_dengue_pipeline.raw.contract import BuildConfig
    from sat_dengue_pipeline.raw.producers import epidemiology_normalization

    rows = pd.DataFrame(
        {
            "COD_DPTO_R": ["50", "50", "50"],
            "COD_MUN_R": ["001", "001", "001"],
            "INI_SIN": ["2024-10-03"] * 3,
            "COD_EVE": ["210", "210", "220"],
            "Confirmados": ["1", "0", "0"],
        }
    )
    _, actual, _ = parse_upload(rows.to_csv(index=False).encode(), ".csv", geography().index)
    frames = {
        "dengue_notifications": rows.iloc[:2],
        "severe_dengue_notifications": rows.iloc[2:],
    }
    geo = pd.DataFrame({"municipality_code": ["50001"]})
    expected, _ = epidemiology_normalization(frames, geo, BuildConfig())
    assert actual.loc["50001"].tolist() == [2, 1]
    assert actual.loc["50001"].tolist() == expected.loc[0, COUNTS[:2]].tolist()
