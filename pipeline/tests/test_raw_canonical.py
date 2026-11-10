"""Contratos crudos, cuarentena, productores y serialización, solo datos artificiales."""

import csv
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from sat_dengue_pipeline.acquisition.contracts import ReleaseFile, ReleaseManifest
from sat_dengue_pipeline.acquisition.raw_manifest import validate_raw_manifest
from sat_dengue_pipeline.acquisition.resolver import resolve_release
from sat_dengue_pipeline.domain.canonical import CLIMATE, COUNTS, KEYS
from sat_dengue_pipeline.domain.temporal import TemporalPolicy, guard_development
from sat_dengue_pipeline.raw import serialization
from sat_dengue_pipeline.raw.build import build, daily_climate, epidemiology, geography
from sat_dengue_pipeline.raw.contract import (
    INVENTORY,
    BuildConfig,
    raw_contract_validation,
)
from sat_dengue_pipeline.raw.fixture import fixture_config, fixture_inventory, synthetic_bundle
from sat_dengue_pipeline.raw.panel import (
    canonical_panel,
    canonical_sources,
    canonical_validation,
    municipality_month_grid,
)
from sat_dengue_pipeline.raw.producers import climate_monthly_aggregation, geography_normalization
from sat_dengue_pipeline.raw.serialization import canonical_serialization, verify_artifact
from sat_dengue_pipeline.raw.temporal import raw_temporal_projection, raw_temporal_quarantine


@pytest.fixture
def raw(tmp_path):
    """Crear únicamente cinco fuentes de ingeniería artificiales."""
    bundle, inventory = synthetic_bundle(tmp_path / "raw")
    return bundle, inventory, fixture_config()


def stages(raw):
    """Ejecutar etapas comunes sin saltar contrato ni cuarentena."""
    bundle, inventory, config = raw
    raw_contract_validation(bundle, config, inventory)
    keys = raw_temporal_projection(bundle)
    q = raw_temporal_quarantine(keys, TemporalPolicy(config.reserved_start))
    geo = geography(bundle, config, q)
    epi = epidemiology(bundle, q, geo, config)
    climate = daily_climate(bundle, q, geo, config)
    monthly = climate_monthly_aggregation(climate[0])
    return q, geo, epi, climate, monthly


def rewrite_csv(path, change):
    """Editar solo un fixture y conservar su encabezado completo."""
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    rows = change(rows)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_closed_contract_valid_and_real_profile_cannot_be_overridden(raw):
    """Un fixture válido no puede hacerse pasar por los hashes aprobados."""
    bundle, inventory, config = raw
    assert raw_contract_validation(bundle, config, inventory) is bundle
    with pytest.raises(ValueError):
        raw_contract_validation(bundle, BuildConfig(), inventory)
    with pytest.raises(ValueError):
        raw_contract_validation(bundle, BuildConfig())
    with pytest.raises(ValueError):
        raw_contract_validation(bundle, config)


@pytest.mark.parametrize(
    "mutation", ["missing", "additional", "duplicate", "corrupt", "hash", "absent"]
)
def test_inventory_rejects_before_projection(raw, mutation, monkeypatch):
    """Toda alteración falla antes de interpretar valores científicos."""
    bundle, inventory, config = raw
    file = bundle.files[0]
    if mutation == "missing":
        bundle = replace(bundle, files=bundle.files[1:])
    elif mutation in {"additional", "duplicate"}:
        extra = replace(file, logical_name="features") if mutation == "additional" else file
        bundle = replace(bundle, files=(*bundle.files, extra))
    elif mutation == "hash":
        bundle = replace(bundle, files=(replace(file, sha256="a" * 64), *bundle.files[1:]))
    elif mutation == "corrupt":
        data = file.path.read_bytes()
        file.path.write_bytes(b"X" + data[1:])
    else:
        file.path.unlink()
    calls = []
    monkeypatch.setattr(
        "sat_dengue_pipeline.raw.build.raw_temporal_projection", lambda b: calls.append(b)
    )
    with pytest.raises(ValueError):
        build(bundle, config, Path("unused"), inventory)
    assert calls == []


@pytest.mark.parametrize(
    "name",
    [
        "google_earth_engine-selected-columns.csv",
        "Listados_DIVIPOLA.xlsx",
        "canonical.csv",
        "features.csv",
        "prepared-matrix.csv",
    ],
)
def test_forbidden_input_names(raw, name):
    """No se acepta un derivado aunque tenga bytes o metadatos de apariencia válida."""
    bundle, inventory, config = raw
    files = (*bundle.files[:-1], replace(bundle.files[-1], path=Path(name)))
    with pytest.raises(ValueError):
        raw_contract_validation(replace(bundle, files=files), config, inventory)
    with pytest.raises(ValueError):
        raw_contract_validation(replace(bundle, release_kind="legacy"), config, inventory)


@pytest.mark.parametrize("provider", ["local", "huggingface", "zenodo", "s3"])
@pytest.mark.parametrize("revision", ["main", "latest", "develop"])
def test_mutable_revisions_rejected_before_acquisition(provider, revision, tmp_path):
    """Todos los transportes rechazan referencias mutables antes de materializar."""
    files = tuple(ReleaseFile(k, v[0], v[0], v[1], v[2]) for k, v in INVENTORY.items())
    calls = []

    class Source:
        """Espía que no debe materializar ningún archivo."""

        def materialize(self, *args):
            """Registrar una llamada indebida."""
            calls.append(args)

    with pytest.raises(ValueError):
        manifest = ReleaseManifest(
            1,
            "raw-v1",
            provider,
            "unconnected",
            revision,
            "2011-06-01",
            "2025-01-01",
            files,
            "raw_sources",
        )
        resolve_release(manifest, tmp_path, Source())
    assert calls == []


def test_approved_manifest_metadata_without_reading_real_sources():
    """Comprobar los cinco tamaños/hashes aprobados usando solo constantes."""
    files = tuple(ReleaseFile(k, v[0], v[0], v[1], v[2]) for k, v in INVENTORY.items())
    manifest = ReleaseManifest(
        1,
        "raw-v1",
        "huggingface",
        "unconnected/raw",
        "f" * 40,
        "2011-06-01",
        "2025-01-01",
        files,
        "raw_sources",
    )
    validate_raw_manifest(manifest)
    with pytest.raises(ValueError):
        validate_raw_manifest(replace(manifest, files=files[:-1]))
    with pytest.raises(ValueError):
        validate_raw_manifest(replace(manifest, release_kind="legacy"))


@pytest.mark.parametrize("which", ["epi", "climate", "json", "provenance"])
def test_schema_rejected_even_with_synthetic_hash_updated(raw, which):
    """El esquema es un contrato adicional a la huella del fixture."""
    bundle, _, config = raw
    root = bundle.files[0].path.parent
    if which in {"epi", "climate"}:
        path = root / ("dengue.csv" if which == "epi" else "google_earth_engine.csv")
        text = path.read_text(encoding="utf-8")
        text = (
            text.replace("INI_SIN", "MISSING")
            if which == "epi"
            else text.replace("wind_v_mean_ms,", "")
        )
        path.write_text(text, encoding="utf-8")
    elif which == "json":
        (root / "Divipola-municipios.md").write_text("[]", encoding="utf-8")
    else:
        (root / "divipola-provenance.json").write_text('{"files": {}}', encoding="utf-8")
    bundle, inventory = fixture_inventory(root)
    with pytest.raises(ValueError):
        raw_contract_validation(bundle, config, inventory)


def test_projection_quarantine_precedes_values_and_reconciles(raw):
    """El valor climático venenoso de 2025 jamás llega al productor."""
    bundle, _, _ = raw
    keys = raw_temporal_projection(bundle)
    assert set(keys["daily_climate"]) == {"date", "mpio_cdpmp"}
    assert set(keys["dengue_notifications"]) == {"COD_DPTO_R", "COD_MUN_R", "INI_SIN"}
    q, _, epi, climate, _ = stages(raw)
    assert q.audit["daily_climate"]["reserved"] == 1
    assert q.audit["dengue_notifications"]["invalid_date"] == 1
    assert q.audit["dengue_notifications"]["reserved"] == 1
    assert len(climate[0]) == 61
    for name, row in epi[1].items():
        assert row["accepted"] == 56
        assert row["rejected"]["unknown_municipality"] == 1
        original = q.audit[name]
        assert original["input"] == (
            original["reserved"]
            + original["invalid_date"]
            + row["accepted"]
            + sum(row["rejected"].values())
        )
    assert "MUST NEVER" not in json.dumps(q.audit)
    assert "50998" not in json.dumps(q.audit)


def test_residence_ini_sin_and_no_consecutive_dedup(raw):
    """Todos los consecutivos repetidos cuentan por residencia/INI_SIN, sin fallback."""
    _, _, epi, _, _ = stages(raw)
    june = epi[0].loc[epi[0].year_month.eq("2024-06")]
    assert set(june.municipality_code) == {"50998", "73998"}
    assert june[COUNTS[0]].tolist() == [7, 7]
    assert june[COUNTS[1]].tolist() == [7, 7]
    assert june[COUNTS[2]].tolist() == [14, 14]
    assert not epi[0].year_month.str.endswith("07").any()
    assert not epi[0].year_month.eq("2024-01").any()


@pytest.mark.parametrize(
    "cause,changes",
    [
        ("wrong_event", {"COD_EVE": "220"}),
        ("invalid_residence", {"COD_DPTO_R": "X"}),
        ("unknown_municipality", {"COD_MUN_R": "999"}),
        ("outside_period", {"INI_SIN": "2010-01-01"}),
    ],
)
def test_rejection_reasons_reconcile(raw, cause, changes):
    """Cada fila rechazada tiene exactamente una causa conciliable."""
    bundle, _, config = raw
    root = bundle.files[0].path.parent
    rewrite_csv(root / "dengue.csv", lambda rows: [{**rows[0], **changes}, *rows[1:]])
    b, inventory = fixture_inventory(root)
    _, _, epi, _, _ = stages((b, inventory, config))
    audit = epi[1]["dengue_notifications"]
    assert audit["rejected"][cause] >= 1
    assert audit["accepted"] == 55
    assert audit["input"] == audit["accepted"] + sum(audit["rejected"].values())


def test_climate_sums_means_and_incomplete_month_are_null(raw):
    """Cuatro sumas, cinco medias; las ausencias no se convierten en cero."""
    q, geo, epi, daily, monthly = stages(raw)
    complete = monthly.loc[monthly.municipality_code.eq("50998")].iloc[0]
    incomplete = monthly.loc[monthly.municipality_code.eq("73998")].iloc[0]
    assert complete[CLIMATE[0]] == pytest.approx(3.1)
    assert complete[CLIMATE[4]] == pytest.approx(0.5)
    assert incomplete[CLIMATE].isna().all()
    assert incomplete.climate_days_observed == 30
    table, _ = canonical_panel(canonical_sources(geo, epi[0], monthly, raw[2]), raw[2])
    absent = table.loc[table.year_month.eq("2024-02")]
    assert absent[CLIMATE].isna().all().all()
    assert absent.climate_days_observed.isna().all()
    assert table[COUNTS[0]].sum() == 56
    assert daily[1]["input"] == q.audit["daily_climate"]["retained"]


def test_variable_missing_day_preserves_other_climate_aggregates(raw):
    """Un valor ausente invalida solo el agregado de esa variable."""
    bundle, _, config = raw
    root = bundle.files[0].path.parent
    rewrite_csv(
        root / "google_earth_engine.csv", lambda rows: [{**rows[0], "rain_mm_day": ""}, *rows[1:]]
    )
    b, inventory = fixture_inventory(root)
    *_, monthly = stages((b, inventory, config))
    row = monthly.iloc[0]
    assert pd.isna(row[CLIMATE[0]])
    assert row[CLIMATE[1:]].notna().all()
    assert row[f"{CLIMATE[0]}_valid_days"] == 30


@pytest.mark.parametrize(
    "changes",
    [
        {"mpio_cdpmp": "99999"},
        {"date": "2024-02-31"},
        {"month": "2"},
        {"day_of_year": "3"},
        {"rain_mm_day": "inf"},
        {"dpto_ccdgo": "73"},
    ],
)
def test_invalid_daily_calendar_keys_or_values(raw, changes):
    """Fechas inválidas se descartan en cuarentena; otras incoherencias fallan cerrado."""
    bundle, _, config = raw
    root = bundle.files[0].path.parent
    rewrite_csv(root / "google_earth_engine.csv", lambda rows: [{**rows[0], **changes}, *rows[1:]])
    b, inventory = fixture_inventory(root)
    if "date" in changes:
        q, *_ = stages((b, inventory, config))
        assert q.audit["daily_climate"]["invalid_date"] == 1
    else:
        with pytest.raises(ValueError):
            stages((b, inventory, config))


def test_duplicate_daily_key_rejected(raw):
    """Duplicar un día no puede fingir un mes completo."""
    bundle, _, config = raw
    root = bundle.files[0].path.parent
    rewrite_csv(root / "google_earth_engine.csv", lambda rows: [rows[0], *rows])
    b, inventory = fixture_inventory(root)
    with pytest.raises(ValueError, match="duplicado"):
        stages((b, inventory, config))


@pytest.mark.parametrize("which", ["dimension", "epi", "climate", "unknown", "period"])
def test_join_contracts(raw, which):
    """El panel no permite multiplicación de filas ni claves sin correspondencia."""
    _, geo, epi, _, monthly = stages(raw)
    epi = epi[0]
    if which == "dimension":
        geo = pd.concat([geo, geo.iloc[[0]]])
    elif which == "epi":
        epi = pd.concat([epi, epi.iloc[[0]]])
    elif which == "climate":
        monthly = pd.concat([monthly, monthly.iloc[[0]]])
    elif which == "unknown":
        epi.loc[0, "municipality_code"] = "99999"
    else:
        epi.loc[0, "year_month"] = "2025-01"
    with pytest.raises(ValueError):
        canonical_sources(geo, epi, monthly, raw[2])


def test_production_grid_contract_182886_without_real_data():
    """Probar los 1122×163 elementos sobre una dimensión generada artificialmente."""
    config = BuildConfig()
    rows = [
        {
            "CODIGO_DPTO_MPIO": f"50{i:03}",
            "CODIGO_DEPARTAMENTO": "50",
            "CODIGO_MUNICIPIO": f"{i:03}",
            "NOMBRE_MUNICIPIO": "FICTICIO",
        }
        for i in range(1000)
    ] + [
        {
            "CODIGO_DPTO_MPIO": f"73{i:03}",
            "CODIGO_DEPARTAMENTO": "73",
            "CODIGO_MUNICIPIO": f"{i:03}",
            "NOMBRE_MUNICIPIO": "FICTICIO",
        }
        for i in range(122)
    ]
    geo = geography_normalization(
        {"conteo": 1122, "resultado": rows},
        {"authority": "TEST", "files": {"Divipola-municipios.md": {"sha256": "a" * 64}}},
        "a" * 64,
        config,
    )
    grid = municipality_month_grid(geo, config)
    assert len(config.periods) == 163
    assert len(grid) == 182886
    assert not grid.duplicated(KEYS).any()
    assert grid.year_month.min() == "2011-06"
    assert grid.year_month.max() == "2024-12"


def test_null_epi_outside_explicit_coverage_is_not_zero(raw):
    """El rango anterior a cobertura permanece ausente en conteos y predictores."""
    b, i, c = raw
    c = replace(c, epi_start="2019-01")
    _, geo, epi, _, monthly = stages((b, i, c))
    result = canonical_panel(canonical_sources(geo, epi[0], monthly, c), c)
    table, _ = canonical_validation(result, c, epi[1])
    assert table.loc[table.year_month.lt("2019-01"), COUNTS].isna().all().all()
    assert table.loc[table.year_month.eq("2024-01"), COUNTS].eq(0).all().all()


@pytest.mark.parametrize("horizon,origin", [(1, "2024-12"), (2, "2024-11"), (2, "2024-12")])
def test_cross_horizons_use_existing_guard(raw, horizon, origin):
    """La tabla conserva diciembre como observación; no habilita objetivos 2025."""
    _, geo, epi, _, monthly = stages(raw)
    result = canonical_panel(canonical_sources(geo, epi[0], monthly, raw[2]), raw[2])
    table, _ = canonical_validation(result, raw[2], epi[1])
    with pytest.raises(ValueError, match="Objetivo reservado"):
        guard_development(
            table[KEYS], table.loc[table.year_month.eq(origin), KEYS], (horizon,), TemporalPolicy()
        )
    last = "2024-11" if horizon == 1 else "2024-10"
    guard_development(
        table[KEYS], table.loc[table.year_month.eq(last), KEYS], (horizon,), TemporalPolicy()
    )


@pytest.mark.parametrize("mutation", ["dtype", "nullable", "order", "count"])
def test_canonical_validation_checks_schema_and_conservation(raw, mutation):
    """Alteraciones en la salida no pueden recibir certificación."""
    _, geo, epi, _, monthly = stages(raw)
    table, schema = canonical_panel(canonical_sources(geo, epi[0], monthly, raw[2]), raw[2])
    if mutation == "dtype":
        schema["columns"][0]["dtype"] = "float64"
    elif mutation == "nullable":
        schema["columns"][0]["nullable"] = True
    elif mutation == "order":
        table = table.iloc[::-1].reset_index(drop=True)
    else:
        epi[1]["dengue_notifications"]["accepted"] += 1
    with pytest.raises(ValueError):
        canonical_validation((table, schema), raw[2], epi[1])


def test_raw_reordering_exact_semantics_bytes_nulls_and_quarantine(raw, tmp_path):
    """Invertir filas crudas no cambia contenido canónico ni digest de cuarentena."""
    bundle, inventory, config = raw
    first, audit1 = build(bundle, config, tmp_path / "first", inventory)
    before = verify_artifact(first)
    root = bundle.files[0].path.parent
    for filename in ("dengue.csv", "dengue_grave.csv", "google_earth_engine.csv"):
        rewrite_csv(root / filename, lambda rows: rows[::-1])
    path = root / "Divipola-municipios.md"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    catalog["resultado"].reverse()
    path.write_text(json.dumps(catalog), encoding="utf-8")
    from sat_dengue_pipeline.raw.contract import sha256

    provenance = json.loads((root / "divipola-provenance.json").read_text(encoding="utf-8"))
    provenance["files"][path.name]["sha256"] = sha256(path)
    (root / "divipola-provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
    b, i = fixture_inventory(root)
    second, audit2 = build(b, config, tmp_path / "second", i)
    assert b.manifest_sha256 != bundle.manifest_sha256
    assert first.semantic_digest == second.semantic_digest
    assert first.serialized_sha256 == second.serialized_sha256
    assert before == verify_artifact(second)
    assert audit1 == audit2


def test_atomic_serialization_preserves_prior_output_on_failure(raw, tmp_path, monkeypatch):
    """Un rename fallido no trunca el artefacto previo ni deja temporales."""
    _, geo, epi, _, monthly = stages(raw)
    result = canonical_panel(canonical_sources(geo, epi[0], monthly, raw[2]), raw[2])
    first = canonical_serialization(result, tmp_path / "out")
    before = first.path.read_bytes()

    def fail(*args):
        """Simular fallo de filesystem antes de reemplazar."""
        raise OSError("injected")

    monkeypatch.setattr(serialization.os, "replace", fail)
    with pytest.raises(OSError, match="injected"):
        canonical_serialization(result, tmp_path / "out")
    assert first.path.read_bytes() == before
    assert list(first.path.parent.glob(".canonical-*")) == []


@pytest.mark.parametrize("mutation", ["duplicate", "count", "code", "provenance", "authority"])
def test_geography_unique_dimension_and_provenance(raw, mutation):
    """Ni códigos incoherentes ni procedencia inválida producen una dimensión."""
    bundle, _, config = raw
    files = {file.logical_name: file for file in bundle.files}
    catalog = json.loads(files["divipola_catalog"].path.read_bytes())
    provenance = json.loads(files["divipola_provenance"].path.read_bytes())
    if mutation == "duplicate":
        catalog["resultado"][1] = dict(catalog["resultado"][0])
    elif mutation == "count":
        catalog["conteo"] = 1122
    elif mutation == "code":
        catalog["resultado"][0]["CODIGO_DPTO_MPIO"] = "73998"
    elif mutation == "provenance":
        provenance["files"]["Divipola-municipios.md"]["sha256"] = "b" * 64
    else:
        provenance["authority"] = ""
    with pytest.raises(ValueError):
        geography_normalization(catalog, provenance, files["divipola_catalog"].sha256, config)


def test_raw_change_during_build_is_detected_before_serialization(raw, tmp_path, monkeypatch):
    """Una fuente modificada después de cuarentena no conserva su linaje inicial."""
    from sat_dengue_pipeline.raw import build as module

    bundle, inventory, config = raw
    original = module.canonical_validation

    def change_after_validation(*args):
        """Simular edición concurrente del fixture, nunca de datos reales."""
        result = original(*args)
        bundle.files[-1].path.write_bytes(bundle.files[-1].path.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(module, "canonical_validation", change_after_validation)
    with pytest.raises(ValueError, match="SHA-256"):
        build(bundle, config, tmp_path / "out", inventory)
    assert not (tmp_path / "out").exists()


def test_serialization_round_trip_preserves_schema_types_values_and_nulls(raw, tmp_path):
    """El artefacto permite recuperar una tabla utilizable por los contratos de V3."""
    from sat_dengue_pipeline.raw.serialization import load_canonical

    _, geo, epi, _, monthly = stages(raw)
    table, schema = canonical_panel(canonical_sources(geo, epi[0], monthly, raw[2]), raw[2])
    artifact = canonical_serialization((table, schema), tmp_path / "out")
    restored, restored_schema = load_canonical(artifact)
    pd.testing.assert_frame_equal(table, restored, check_exact=True)
    assert schema == restored_schema
    assert list(schema["column_roles"]) == list(restored_schema["column_roles"])


def test_fixed_synthetic_digest_receipt(raw, tmp_path):
    """Congelar la identidad del fixture, incluyendo orden, tipos, valores y nulos."""
    bundle, inventory, config = raw
    artifact, _ = build(bundle, config, tmp_path / "out", inventory)
    assert (
        artifact.semantic_digest
        == "26cc689566b05ffaf46a42aaa8311cca0ffc3137e31af6f64cfb1e9834f6b957"
    )
    assert (
        artifact.serialized_sha256
        == "4ca14c3c07079130606a91274a516e083b513c6a1a7afe41d8df92be9b3bb046"
    )
