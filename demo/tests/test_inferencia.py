"""Comprobar carga mensual, modelo congelado y regla de prioridad sin datos privados."""

import hashlib
import io
import json

import pandas as pd
import pytest
from inferencia import (
    ARTIFACT,
    METADATA,
    geography,
    load_context,
    load_model,
    parse_upload,
    ranking,
)
from sat_dengue_pipeline.domain.canonical import COUNTS, KEYS, PREDICTORS
from sat_dengue_pipeline.raw.contract import BuildConfig
from sat_dengue_pipeline.raw.producers import epidemiology_normalization

MONTH = "2024-11"


@pytest.fixture(scope="module")
def model():
    """Artefacto versionado, verificado por su SHA-256."""
    return load_model()


def context(model, month: str = MONTH) -> pd.DataFrame:
    """Contexto artificial con los tipos exactos del ajuste y predictores idénticos."""
    cities = geography()
    frame = pd.DataFrame(
        {
            "municipality_code": cities.index,
            "year_month": month,
            "department_code": cities.index.str[:2],
            "municipality_name": cities.values,
        }
    )
    for name in PREDICTORS:
        frame[name] = 1
    frame[["p25_canal_t", "p50_canal_t", "p75_canal_t"]] = [1.0, 2.0, 3.0]
    frame["zona_canal_t"] = "SEGURIDAD"
    frame["month_of_year"] = int(month[-2:])
    dtypes = dict(zip(PREDICTORS, model.payload["state"]["dtypes"], strict=True))
    return frame.astype({**dict.fromkeys([*KEYS, *METADATA], "string"), **dtypes})


@pytest.mark.parametrize("suffix", [".csv", ".xlsx"])
def test_monthly_upload(suffix: str) -> None:
    """Cuenta todas las notificaciones 210 y 220 por residencia, con ceros explícitos."""
    frame = pd.DataFrame(
        {
            "COD_DPTO_R": ["50", "50", "73", "11"],
            "COD_MUN_R": ["1", "001", "001", "001"],
            "INI_SIN": ["03/11/2024"] * 4,
            "Confirmados": [1, 0, 0, 1],
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
    assert counts.loc["50001"].tolist() == [1, 1, 2]
    assert counts.loc["73001"].tolist() == [1, 0, 1]
    assert len(counts) == 76 and counts.loc["50006"].tolist() == [0, 0, 0]


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ("50,1,2024-11-01,210\n50,1,2024-02-30,210", "fechas"),
        ("50,1,2024-11-01,210\n73,1,2024-10-30,210", "solo mes"),
        ("50,1,2024-11-01,999", "evento"),
    ],
)
def test_invalid_upload(rows: str, message: str) -> None:
    """Un error de entrada no genera un ranking parcial."""
    with pytest.raises(ValueError, match=message):
        parse_upload(
            ("COD_DPTO_R,COD_MUN_R,INI_SIN,COD_EVE\n" + rows).encode(), ".csv", geography().index
        )


def test_upload_requires_residence() -> None:
    """El entrenamiento usa residencia; un código de ocurrencia no lo sustituye."""
    with pytest.raises(ValueError, match="COD_DPTO_R"):
        parse_upload(b"cod_DPTO_O,INI_SIN\n50001,2024-11-01\n", ".csv", geography().index)


def test_upload_counts_match_canonical_producer() -> None:
    """Las filas con confirmados 0 y 1 cuentan igual que en el productor canónico."""
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
    assert actual.loc["50001"].tolist() == [2, 1, 3]
    assert actual.loc["50001"].tolist() == expected.loc[0, COUNTS].tolist()


def test_frozen_model_identity(model) -> None:
    """La demo usa exclusivamente el artefacto del informe y no puede reajustar."""
    manifest = json.loads((ARTIFACT / "manifest.json").read_bytes())
    assert model.artifact_sha256 == manifest["artifact_sha256"]
    assert model.payload["effective_state_sha256"].startswith("d59ce5af")
    assert not hasattr(model, "fit")


def test_priority_order(model) -> None:
    """Ocho cupos entre no excedidos, empate por DIVIPOLA y sin probabilidades."""
    cities = geography()
    counts = pd.DataFrame(0, index=cities.index, columns=COUNTS, dtype="Int64")
    counts.loc[["50001", "73001"]] = [9, 0, 9]
    result = ranking(model, MONTH, counts, context(model))
    assert result.loc[["50001", "73001"], "Resultado"].eq("Exceso en el mes de origen").all()
    assert result.loc[["50001", "73001"], "Posición"].isna().all()
    eligible = result.loc[result["Posición"].notna()]
    assert len(eligible) == 74 and result["Priorizado"].sum() == 8
    assert eligible.index.tolist() == sorted(eligible.index)
    assert eligible["Posición"].tolist() == list(range(1, 75))
    assert not any("Puntuación" in c or "Probabilidad" in c for c in result)


def test_priority_needs_eight_eligible(model) -> None:
    """Con menos de ocho elegibles no se publica el lote."""
    counts = pd.DataFrame(9, index=geography().index, columns=COUNTS, dtype="Int64")
    counts.iloc[:5] = 0
    with pytest.raises(ValueError, match="ocho"):
        ranking(model, MONTH, counts, context(model))


def test_context_checks_digest(model, tmp_path) -> None:
    """El contexto privado se rechaza si sus bytes difieren del índice."""
    data = context(model).to_csv(index=False).encode()
    (tmp_path / f"contexto-{MONTH}.csv").write_bytes(data)
    index = {
        "raw_manifest_sha256": model.payload["provenance"]["raw_manifest_sha256"],
        "files": {MONTH: hashlib.sha256(data).hexdigest()},
    }
    (tmp_path / "contexto.json").write_text(json.dumps(index))
    loaded = load_context(model, tmp_path)[MONTH]
    assert [str(t) for t in loaded[PREDICTORS].dtypes] == model.payload["state"]["dtypes"]
    (tmp_path / f"contexto-{MONTH}.csv").write_bytes(data + b"\n")
    with pytest.raises(ValueError, match="difiere"):
        load_context(model, tmp_path)
