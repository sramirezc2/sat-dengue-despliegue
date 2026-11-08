"""Adquisición privada selectiva sin credenciales cacheadas ni Excel."""

from dataclasses import replace
from pathlib import Path

import pytest

from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest
from sat_dengue_pipeline.acquisition.errors import DownloadError
from sat_dengue_pipeline.acquisition.raw_manifest import validate_raw_manifest
from sat_dengue_pipeline.acquisition.sources import create_source
from sat_dengue_pipeline.pipelines.canonical.nodes import build_input, validate_input
from sat_dengue_pipeline.raw.build import retained_frame
from sat_dengue_pipeline.raw.temporal import Quarantine, parse_date, raw_temporal_quarantine


def approved() -> ReleaseManifest:
    """Leer únicamente el manifiesto sin datos o credenciales."""
    path = Path(__file__).parents[1] / "conf/releases/approved-raw.json"
    return ReleaseManifest.from_json(path.read_text())


def test_prefixed_manifest_preserves_closed_mapping() -> None:
    """Rechazar rutas intercambiadas, mixtas, Excel y sustituciones de proveedor."""
    manifest = approved()
    validate_raw_manifest(manifest)
    first, second, *rest = manifest.files
    for files in (
        (replace(first, remote_path=second.remote_path), second, *rest),
        (replace(first, remote_path=first.relative_path), second, *rest),
        (replace(first, remote_path="datos-crudos/Listados_DIVIPOLA.xlsx"), second, *rest),
    ):
        with pytest.raises(ValueError):
            validate_raw_manifest(replace(manifest, files=files))
    with pytest.raises(ValueError):
        validate_raw_manifest(replace(manifest, provider="local"))


def test_environment_auth_is_explicit_and_not_kept_in_source(monkeypatch, tmp_path) -> None:
    """El SDK recibe la variable solo en opt-in; nunca login o token cacheado."""
    manifest = approved()
    calls = []

    def download(**kwargs):
        """Simular el SDK sin red ni guardar el argumento token."""
        calls.append(kwargs.pop("token") == "synthetic-test-credential")
        assert kwargs["filename"] == manifest.files[0].remote_path
        path = Path(kwargs["cache_dir"]) / "fixture"
        path.write_bytes(b"fixture")
        return str(path)

    source = create_source(manifest, hub_download=download, use_env_token=True)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(DownloadError):
        source.materialize(manifest.files[0], tmp_path / "destination")
    assert calls == []
    monkeypatch.setenv("HF_TOKEN", "synthetic-test-credential")
    source.materialize(manifest.files[0], tmp_path / "destination")
    assert calls == [True]
    assert "synthetic-test-credential" not in repr(source)


def test_real_input_rejects_extra_file_and_unverified_bytes(monkeypatch, tmp_path) -> None:
    """Un directorio con Excel o bytes incorrectos nunca llega a productores."""
    manifest = approved()
    conf = tmp_path / "conf/releases"
    conf.mkdir(parents=True)
    (conf / "approved-raw.json").write_text(
        (Path(__file__).parents[1] / "conf/releases/approved-raw.json").read_text()
    )
    cache = tmp_path / "data/01_raw/inbox" / manifest.release_id / manifest.manifest_sha256
    cache.mkdir(parents=True)
    for file in manifest.files:
        (cache / file.relative_path).write_bytes(b"invalid synthetic bytes")
    monkeypatch.chdir(tmp_path)
    params = {"mode": "approved", "workspace": "data/work", "tracking": False}
    source = build_input(params)
    assert source.inventory is None and source.config.profile == "approved"
    with pytest.raises(ValueError):
        validate_input(source)
    (cache / "Listados_DIVIPOLA.xlsx").write_bytes(b"not a scientific input")
    with pytest.raises(ValueError):
        build_input(params)


def test_retained_rows_survive_chunk_boundaries_without_reserved_values(monkeypatch, tmp_path):
    """Conservar posiciones globales, incluidos bloques vacíos y el último parcial."""
    import pandas as pd

    from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle, ResolvedFile

    path = tmp_path / "dengue.csv"
    frame = pd.DataFrame(
        {
            "COD_EVE": ["210"] * 11,
            "COD_DPTO_R": ["50"] * 11,
            "COD_MUN_R": ["001"] * 11,
            "INI_SIN": ["2024-01-01"] * 11,
            "unused": ["not consumed"] * 11,
        }
    )
    frame.to_csv(path, index=False)
    file = ResolvedFile("dengue_notifications", path, path.stat().st_size, "a" * 64)
    bundle = ResolvedBundle("fixture", "b" * 64, "2024-01-01", "2024-12-31", (file,))
    original = pd.read_csv

    def small_chunks(*args, **kwargs):
        """Ejercitar el mismo lector en bloques de tres filas."""
        kwargs["chunksize"] = 3
        return original(*args, **kwargs)

    monkeypatch.setattr(pd, "read_csv", small_chunks)
    retained = (0, 2, 6, 8, 9, 10)
    result = retained_frame(
        bundle, Quarantine({file.logical_name: retained}, {}), file.logical_name
    )
    expected = frame.iloc[list(retained)].drop(columns="unused").reset_index(drop=True).astype(str)
    pd.testing.assert_frame_equal(result, expected)


@pytest.mark.parametrize("space", [" ", "\u00a0"])
def test_localized_dates_are_day_first_and_quarantined(space):
    """No invertir fechas ambiguas ni permitir objetivos reservados/imposibles."""
    import pandas as pd

    from sat_dengue_pipeline.domain.temporal import TemporalPolicy

    assert parse_date(f"1/06/2024 12:00:00 a.{space}m.").isoformat() == "2024-06-01"
    assert parse_date(f"31/02/2024 12:00:00 a.{space}m.") is None
    assert parse_date(f"1/06/2024 12:00:00 p.{space}m.") is None
    assert parse_date("06/13/2024 12:00:00 a. m.") is None
    keys = pd.DataFrame(
        {
            "COD_DPTO_R": ["50"] * 3,
            "COD_MUN_R": ["001"] * 3,
            "INI_SIN": [f"31/12/2024 12:00:00 a.{space}m.", f"1/01/2025 12:00:00 a.{space}m.", ""],
        }
    )
    q = raw_temporal_quarantine({"dengue_notifications": keys}, TemporalPolicy())
    assert q.retained["dengue_notifications"] == (0,)
    assert q.audit["dengue_notifications"]["reserved"] == 1
    assert q.audit["dengue_notifications"]["invalid_date"] == 1
    with pytest.raises(ValueError, match="inferir ceros"):
        raw_temporal_quarantine({"dengue_notifications": keys.iloc[2:]}, TemporalPolicy())
