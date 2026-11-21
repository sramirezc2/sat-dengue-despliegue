"""Comprobar carga mensual, modelo congelado y regla de prioridad sin datos privados."""

import hashlib
import io
import json
import shutil
import tomllib

import inferencia
import pandas as pd
import pytest
from configuracion import CONTEXT_DIR, ROOT, resource_directory
from ejemplos import HEADERS, sample_csv, template_csv
from inferencia import (
    ARTIFACT,
    METADATA,
    capacity,
    capacity_warning,
    geography,
    load_context,
    load_model,
    parse_upload,
    ranking,
    select_capacity,
)
from sat_dengue_pipeline.domain.canonical import COUNTS, KEYS, PREDICTORS
from sat_dengue_pipeline.raw.contract import BuildConfig
from sat_dengue_pipeline.raw.producers import epidemiology_normalization
from sat_dengue_pipeline.risk.configuration import procedure
from sat_dengue_pipeline.risk.inference import prioritize

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
    result = select_capacity(ranking(model, MONTH, counts, context(model)))
    assert result.loc[["50001", "73001"], "Resultado"].eq("Exceso en el mes de origen").all()
    assert result.loc[["50001", "73001"], "Posición"].isna().all()
    eligible = result.loc[result["Posición"].notna()]
    assert len(eligible) == 74 and result["Priorizado"].sum() == 8
    assert eligible.index.tolist() == sorted(eligible.index)
    assert eligible["Posición"].tolist() == list(range(1, 75))
    assert not any("Puntuación" in c or "Probabilidad" in c for c in result)


@pytest.mark.parametrize("available", [0, 5, 7])
def test_priority_with_insufficient_eligible(model, available) -> None:
    """La simulación informa déficit y nunca rellena con municipios no elegibles."""
    counts = pd.DataFrame(9, index=geography().index, columns=COUNTS, dtype="Int64")
    counts.iloc[:available] = 0
    ordered = ranking(model, MONTH, counts, context(model))
    for percentage in (5, 10, 15, 20):
        result = select_capacity(ordered, percentage)
        assert result.Priorizado.sum() == min(available, capacity(percentage))
        assert not result.loc[result["Posición"].isna(), "Priorizado"].any()
        warning = capacity_warning(available, percentage)
        if available < capacity(percentage):
            assert f"se seleccionan {available}" in warning
        else:
            assert warning is None


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


@pytest.mark.parametrize(("percentage", "expected"), [(5, 4), (10, 8), (15, 12), (20, 16)])
def test_capacity_keeps_ranking_without_scoring(model, monkeypatch, percentage, expected) -> None:
    """Cada capacidad reutiliza posiciones y no llama al modelo ni muta la entrada."""
    _, counts, _ = parse_upload(sample_csv(MONTH), ".csv", geography().index)
    ordered = ranking(model, MONTH, counts, context(model))
    before = ordered.copy(deep=True)

    def forbidden(*args, **kwargs):
        """Prohibir un segundo scoring durante la selección."""
        pytest.fail("La selección no debe puntuar")

    monkeypatch.setattr(type(model), "score", forbidden)
    result = select_capacity(ordered, percentage)
    assert capacity(percentage) == expected
    assert result.Priorizado.sum() == expected
    pd.testing.assert_frame_equal(result.drop(columns="Priorizado"), before)
    pd.testing.assert_frame_equal(ordered, before)
    assert list(result) == [
        "Posición", "Municipio", "Departamento", "Notificaciones", "Zona en T", "Resultado",
        "Priorizado",
    ]


def test_default_matches_historical_selection(model, monkeypatch) -> None:
    """El 10 % usa las mismas ocho posiciones que la publicación con el mismo input."""
    historical = []
    shared = inferencia.rank_eligible

    def compare(table, schema, origin, frozen):
        """Cotejar ambas interfaces sobre los mismos predictores de la demo."""
        rows, feature_hash = shared(table, schema, origin, frozen)
        approved, approved_hash = prioritize(table, schema, origin, frozen)
        assert feature_hash == approved_hash
        assert rows == [
            {k: v for k, v in row.items() if k != "selected_for_attention"} for row in approved
        ]
        historical.extend(r["municipality_code"] for r in approved if r["selected_for_attention"])
        return rows, feature_hash

    monkeypatch.setattr(inferencia, "rank_eligible", compare)
    _, counts, _ = parse_upload(sample_csv(MONTH), ".csv", geography().index)
    result = select_capacity(ranking(model, MONTH, counts, context(model)))
    assert sorted(result.index[result.Priorizado]) == historical
    assert len(historical) == 8 and procedure()["budget"] == 8


@pytest.mark.parametrize("percentage", [0, 8, 25, -10, "10"])
def test_unsupported_percentage(percentage) -> None:
    """No aceptar capacidades fuera del selector aprobado para la demo."""
    with pytest.raises(ValueError, match="porcentaje"):
        capacity(percentage)


def write_context(directory, model, *, frame=None, frames=None, index_change=None) -> None:
    """Crear un paquete artificial verificable sin consultar el contexto privado."""
    frames = frames if frames is not None else {MONTH: context(model) if frame is None else frame}
    files = {}
    for month, current in frames.items():
        data = current.to_csv(index=False).encode()
        (directory / f"contexto-{month}.csv").write_bytes(data)
        files[month] = hashlib.sha256(data).hexdigest()
    index = {
        "raw_manifest_sha256": model.payload["provenance"]["raw_manifest_sha256"],
        "files": files,
    }
    if index_change:
        index.update(index_change)
    (directory / "contexto.json").write_text(json.dumps(index), encoding="utf-8")


def test_default_directories(model, tmp_path, monkeypatch) -> None:
    """Los defaults conservan las rutas locales originales y permiten cargar recursos."""
    assert ARTIFACT == ROOT / "modelos/logistica-conclima-t2"
    assert CONTEXT_DIR == ROOT / "pipeline/data/demo"
    assert load_model().artifact_sha256 == model.artifact_sha256
    write_context(tmp_path, model)
    # Ejercitar el fallback sin necesitar ni tocar contexto privado real del host.
    monkeypatch.setattr(inferencia, "CONTEXT_DIR", tmp_path)
    assert list(load_context(model)) == [MONTH]


def test_configured_directories(model, tmp_path, monkeypatch) -> None:
    """Las variables reubican recursos sin sustituir la identidad congelada."""
    target = tmp_path / "modelo"
    shutil.copytree(ARTIFACT, target)
    write_context(tmp_path, model)
    monkeypatch.setenv("SATD_DEMO_MODEL_DIR", str(target))
    monkeypatch.setenv("SATD_DEMO_CONTEXT_DIR", str(tmp_path))
    assert load_model().artifact_sha256 == model.artifact_sha256
    assert list(load_context(model)) == [MONTH]
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SATD_DEMO_MODEL_DIR", "modelos/logistica-conclima-t2")
    assert load_model().artifact_sha256 == model.artifact_sha256


def test_configured_model_rejects_tamper(model, tmp_path, monkeypatch) -> None:
    """Cambiar modelo y manifiesto juntos no permite cambiar el SHA aprobado."""
    shutil.copytree(ARTIFACT, tmp_path / "model")
    target = tmp_path / "model"
    raw = (target / "model.json").read_bytes() + b"\n"
    (target / "model.json").write_bytes(raw)
    monkeypatch.setenv("SATD_DEMO_MODEL_DIR", str(target))
    with pytest.raises(ValueError, match="SHA-256"):
        load_model()
    manifest = json.loads((target / "manifest.json").read_bytes())
    manifest["artifact_sha256"] = hashlib.sha256(raw).hexdigest()
    (target / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Manifiesto"):
        load_model()


@pytest.mark.parametrize("value", ["", "../demo", "https://example.com/context"])
def test_unsafe_directory(value, monkeypatch) -> None:
    """Las rutas configuradas no admiten vacíos, traversal ni URL remota."""
    monkeypatch.setenv("SATD_DEMO_CONTEXT_DIR", value)
    with pytest.raises(ValueError):
        resource_directory("SATD_DEMO_CONTEXT_DIR", CONTEXT_DIR)


def test_context_rejects_other_release(model, tmp_path) -> None:
    """Un índice íntegro de otro release no es válido para este modelo."""
    write_context(tmp_path, model, index_change={"raw_manifest_sha256": "0" * 64})
    with pytest.raises(ValueError, match="release distinto"):
        load_context(model, tmp_path)


@pytest.mark.parametrize("change", [{"files": {}}, {"files": {"../escape": "0" * 64}}])
def test_context_rejects_invalid_index(model, tmp_path, change) -> None:
    """Los nombres del índice no permiten escapar ni servir un contexto vacío."""
    write_context(tmp_path, model, index_change=change)
    with pytest.raises(ValueError):
        load_context(model, tmp_path)


def test_context_rejects_mismatched_month(model, tmp_path) -> None:
    """Incluso con hash coherente, el mes interno debe corresponder al índice."""
    write_context(tmp_path, model, frame=context(model, "2024-12"))
    with pytest.raises(ValueError, match="origen"):
        load_context(model, tmp_path)


def test_context_rejects_symlinks(model, tmp_path) -> None:
    """Un enlace no puede desviar la lectura de un recurso validado."""
    write_context(tmp_path, model)
    path = tmp_path / f"contexto-{MONTH}.csv"
    data = path.read_bytes()
    path.unlink()
    other = tmp_path / "other.csv"
    other.write_bytes(data)
    path.symlink_to(other)
    with pytest.raises(ValueError, match="enlazado"):
        load_context(model, tmp_path)


def test_template_and_artificial_sample_end_to_end(model, tmp_path) -> None:
    """Plantilla completada y muestra recorren carga, contexto, modelo y selección."""
    template = template_csv()
    assert template.decode().strip().split(",") == list(HEADERS)
    _, counts, summary = parse_upload(
        template + b"50,001,2024-11-01,210\n", ".csv", geography().index
    )
    assert summary["Notificaciones"] == 1 and counts.loc["50001", COUNTS[0]] == 1
    data = sample_csv(MONTH)
    assert data == sample_csv(MONTH)
    frame = pd.read_csv(io.BytesIO(data), dtype=str)
    assert set(frame.COD_DPTO_R) == {"50", "73"} and set(frame.COD_EVE) == {"210", "220"}
    month, counts, summary = parse_upload(data, ".csv", geography().index)
    assert summary["Notificaciones"] == 24 and summary["Municipios con casos"] == 6
    write_context(tmp_path, model)
    result = select_capacity(ranking(model, month, counts, load_context(model, tmp_path)[month]))
    assert len(result) == 76 and result.Priorizado.sum() == 8


def test_demo_lock_preserves_direct_and_scientific_versions() -> None:
    """El lock adicional fija las dependencias directas y respeta las compartidas."""
    locked = dict(
        line.split("==", 1) for line in (ROOT / "demo/requirements.lock").read_text().splitlines()
        if "==" in line and not line.startswith("#")
    )
    locked = {name: version.split()[0] for name, version in locked.items()}
    for line in (ROOT / "demo/requirements.txt").read_text().splitlines():
        name, version = line.split("==", 1)
        assert locked[name] == version
    scientific = tomllib.loads((ROOT / "pipeline/uv.lock").read_text())
    for package in scientific["package"]:
        if package["name"] in locked:
            assert package["version"] == locked[package["name"]]
