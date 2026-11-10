"""Dos contratos reales cerrados, sin leer fuentes privadas ni modificar T16."""

import hashlib
import json
import runpy
import subprocess
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest
from sat_dengue_pipeline.pipelines.canonical.nodes import build_input
from sat_dengue_pipeline.raw.contract import BuildConfig, raw_contract_validation
from sat_dengue_pipeline.raw.fixture import synthetic_bundle
from sat_dengue_pipeline.raw.panel import municipality_month_grid

ROOT = Path(__file__).resolve().parents[1]


def test_two_closed_real_calendars_and_historical_payload() -> None:
    """Conservar el payload histórico y obtener exactamente 242.352 claves nuevas."""
    historical = BuildConfig()
    assert historical.payload() == {
        "profile": "approved", "start": "2011-06", "end": "2024-12",
        "municipalities": 1122, "epi_start": "2011-06", "reserved_start": "2025-01",
    }
    full = BuildConfig.operational_full()
    assert len(historical.periods) == 163 and len(full.periods) == 216
    assert full.periods[0] == "2007-01" and full.periods[-1] == "2024-12"
    dimension = pd.DataFrame({"municipality_code": [f"{n:05d}" for n in range(1122)]})
    grid = municipality_month_grid(dimension, full)
    assert len(grid) == 242352 and not grid.duplicated().any()
    assert not grid.year_month.ge("2025-01").any()


@pytest.mark.parametrize("config", [BuildConfig(), BuildConfig.operational_full()])
@pytest.mark.parametrize("change", [
    {"start": "2008-01"}, {"end": "2024-11"}, {"epi_start": "2008-01"},
    {"municipalities": 76}, {"reserved_start": "2026-01"}, {"profile": "arbitrary"},
])
def test_real_profiles_cannot_change_dates_or_population(config: BuildConfig, change: dict) -> None:
    """Rechazar contratos parciales, reserva alterada y nombres desconocidos."""
    with pytest.raises(ValueError):
        replace(config, **change)


@pytest.mark.parametrize("profile", ["approved", "operational_full"])
def test_kedro_selects_profile_independently_of_provider(
    profile: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Seleccionar por parámetro Kedro sin duplicar nodos ni acoplar al transporte."""
    name = "conf/releases/operational-raw-173d5856.json"
    content = (ROOT / name).read_text(encoding="utf-8")
    manifest = ReleaseManifest.from_json(content)
    path = tmp_path / name
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")
    cache = tmp_path / "data/01_raw/inbox" / manifest.release_id / manifest.manifest_sha256
    cache.mkdir(parents=True)
    for item in manifest.files:
        (cache / item.relative_path).touch()
    monkeypatch.chdir(tmp_path)
    source = build_input({
        "mode": "approved", "workspace": "data/work", "tracking": False,
        "manifest": name, "profile": profile,
    })
    assert source.config == (
        BuildConfig.operational_full() if profile == "operational_full" else BuildConfig()
    )


@pytest.mark.parametrize("parameters", [
    {"mode": "approved", "profile": "arbitrary"},
    {"mode": "approved", "profile": "synthetic"},
    {"mode": "synthetic", "profile": "operational_full"},
    {"mode": "approved", "start": "2007-01"},
])
def test_kedro_rejects_unregistered_profiles_before_io(parameters: dict) -> None:
    """No aceptar fechas libres o sustituir el fixture por un contrato real."""
    with pytest.raises(ValueError):
        build_input({"workspace": "data/work", "tracking": False, **parameters})


def test_full_profile_never_accepts_synthetic_inventory(tmp_path: Path) -> None:
    """El contrato completo mantiene integridad real y cobertura declarada mínima."""
    bundle, inventory = synthetic_bundle(tmp_path / "raw")
    with pytest.raises(ValueError, match="sustituir"):
        raw_contract_validation(bundle, BuildConfig.operational_full(), inventory)
    with pytest.raises(ValueError, match="cobertura"):
        raw_contract_validation(bundle, BuildConfig.operational_full())


@pytest.mark.parametrize("profile", [None, "approved"])
def test_helper_selects_full_by_default_and_historical_explicitly(
    profile: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Transmitir el perfil al único pipeline, sin cambios de ciencia o proveedor."""
    run = runpy.run_path(str(ROOT / "tools/build_approved_canonical.py"))["run"]
    calls = []

    def process(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        """Interceptar procesos antes de cualquier transporte o construcción."""
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", process)
    if profile is None:
        assert run(tmp_path) == 0
    else:
        assert run(tmp_path, "conf/releases/approved-raw.json", profile) == 0
    params = dict(item.split("=", 1) for item in calls[1][-1].split(","))
    assert params["canonical.profile"] == (profile or "operational_full")


def test_operational_manifest_changes_only_declared_start() -> None:
    """Conservar revisión, nombres, tamaños, hashes y fin del release corregido."""
    path = ROOT / "conf/releases/operational-raw-173d5856.json"
    current = json.loads(path.read_text(encoding="utf-8"))
    assert current["coverage_start"] == "2007-01-01"
    historical_metadata = {**current, "coverage_start": "2011-06-01"}
    # Identidad previa fijada, sin exigir objetos Git ausentes en clones superficiales.
    encoded = (json.dumps(historical_metadata, indent=2) + "\n").encode()
    assert hashlib.sha256(encoded).hexdigest() == (
        "ee36be0affe23b1bad99044853e48f6396c556f39851852c769002d029f8b550"
    )
