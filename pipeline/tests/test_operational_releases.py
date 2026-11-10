"""Coexistencia de releases inmutables usando solo fuentes artificiales."""

import hashlib
import runpy
from dataclasses import replace
from pathlib import Path

import pytest

from sat_dengue_pipeline.acquisition import raw_manifest
from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest
from sat_dengue_pipeline.acquisition.resolver import resolve_release
from sat_dengue_pipeline.acquisition.sources import LocalSource
from sat_dengue_pipeline.pipelines.canonical import nodes
from sat_dengue_pipeline.raw import contract
from sat_dengue_pipeline.raw.fixture import fixture_inventory, synthetic_bundle

ROOT = Path(__file__).resolve().parents[1]
OLD = "conf/releases/approved-raw.json"
NEW = "conf/releases/operational-raw-173d5856.json"


def manifest(name: str) -> ReleaseManifest:
    """Leer metadatos versionados sin consultar datos o credenciales."""
    return ReleaseManifest.from_json((ROOT / name).read_text(encoding="utf-8"))


def test_only_climate_changes_and_historical_manifest_is_immutable() -> None:
    """Conservar bytes históricos y aceptar dos identidades explícitas distintas."""
    assert hashlib.sha256((ROOT / OLD).read_bytes()).hexdigest() == (
        "667f4273add97d874ea70344fc698c454c499bea5e9d3e3c5e74c82d8eb70f0c"
    )
    old, new = manifest(OLD), manifest(NEW)
    assert old.revision == "a1a7f237a4baa6ffa848fabeef474f811f3b3f33"
    assert new.revision == "173d5856874b89d8aeb0566accc65ce7f6759820"
    assert old.release_id != new.release_id and old.manifest_sha256 != new.manifest_sha256
    assert [a.logical_name for a, b in zip(old.files, new.files, strict=True) if a != b] == [
        "daily_climate"
    ]
    for release in (old, new):
        raw_manifest.validate_raw_manifest(release)


@pytest.mark.parametrize("kind", ["old_identity", "new_identity", "revision", "other_file"])
def test_mixed_or_unapproved_identities_fail_closed(kind: str) -> None:
    """No permitir promover bytes corregidos como históricos o alterar otro archivo."""
    old, new = manifest(OLD), manifest(NEW)
    candidate = {
        "old_identity": replace(new, release_id=old.release_id),
        "new_identity": replace(old, release_id=new.release_id, revision=new.revision),
        "revision": replace(new, revision=old.revision),
        "other_file": replace(new, files=(replace(new.files[0], sha256="f" * 64), *new.files[1:])),
    }[kind]
    with pytest.raises(ValueError):
        raw_manifest.validate_raw_manifest(candidate)


def test_releases_coexist_in_cache_and_historical_input_remains_valid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Resolver ambos, validar entradas reales del constructor y conservar caché vieja."""
    inventories = []
    releases = []
    for index, name in enumerate((OLD, NEW)):
        source = tmp_path / f"source-{index}"
        synthetic_bundle(source / "datos-crudos")
        if index:
            with (source / "datos-crudos/google_earth_engine.csv").open("ab") as stream:
                stream.write(b"\n")
        _, inventory = fixture_inventory(source / "datos-crudos")
        inventories.append(inventory)
        release = manifest(name)
        files = tuple(
            replace(f, size_bytes=inventory[f.logical_name][1], sha256=inventory[f.logical_name][2])
            for f in release.files
        )
        releases.append((replace(release, files=files), source))
    for module in (contract, raw_manifest):
        monkeypatch.setattr(module, "INVENTORY", inventories[0])
        monkeypatch.setattr(module, "OPERATIONAL_INVENTORY", inventories[1])
    monkeypatch.chdir(tmp_path)
    sources = []
    for name, (release, source) in zip((OLD, NEW), releases, strict=True):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # Usar el serializador del contrato existente, sin crear un formato alternativo.
        import json
        from dataclasses import asdict

        path.write_text(json.dumps(asdict(release)), encoding="utf-8")
        bundle = resolve_release(release, Path("data/01_raw/inbox"), LocalSource(source))
        params = {"mode": "approved", "workspace": "data/work", "tracking": False}
        params["manifest"] = name
        if name == OLD:
            params["profile"] = "approved"
        built = nodes.build_input(params)
        assert nodes.validate_input(built) is built.bundle
        assert built.bundle.manifest_sha256 == bundle.manifest_sha256
        assert [f.path.resolve() for f in built.bundle.files] == [f.path for f in bundle.files]
        assert built.config == (
            contract.BuildConfig() if name == OLD else contract.BuildConfig.operational_full()
        )
        sources.append(built)
    assert sources[0].bundle.files[-1].path != sources[1].bundle.files[-1].path
    assert nodes.validate_input(nodes.build_input(
        {"mode": "approved", "workspace": "data/old-again", "tracking": False,
         "manifest": OLD, "profile": "approved"}
    )) == sources[0].bundle
    for source in sources:
        climate = source.bundle.files[-1].path
        assert contract.sha256(climate) == source.bundle.files[-1].sha256
        with climate.open("ab") as stream:
            stream.write(b"corrupt")
        with pytest.raises(ValueError, match="Caché corrupta"):
            nodes.validate_input(source)


def test_unknown_operational_manifest_rejected_before_cache_access() -> None:
    """La selección operacional no admite manifiestos arbitrarios o rutas privadas."""
    with pytest.raises(ValueError):
        nodes.build_input({
            "mode": "approved", "workspace": "data/work", "tracking": False,
            "manifest": "conf/releases/unapproved.json",
        })


@pytest.mark.parametrize("name", [OLD, NEW])
def test_acquisition_tool_selects_manifest_without_rewriting_history(
    name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Transmitir la selección al adquiridor y conservar recibos exclusivos existentes."""
    run = runpy.run_path(str(ROOT / "tools/acquire_private_raw.py"))["run"]
    bundle, _ = synthetic_bundle(tmp_path / "fixture")
    calls = []

    def acquire(configuration: dict, root: Path) -> tuple:
        """Simular transporte y comprobar metadatos sin usar credenciales."""
        calls.append(configuration["acquisition"]["manifest"])
        return bundle, {}

    monkeypatch.setitem(run.__globals__, "acquire", acquire)
    monkeypatch.setitem(run.__globals__, "raw_contract_validation", lambda *args: bundle)
    monkeypatch.setitem(run.__globals__, "preflight_cache", lambda *args, **kwargs: None)
    selected = tmp_path / name
    selected.parent.mkdir(parents=True, exist_ok=True)
    selected.write_text((ROOT / name).read_text(encoding="utf-8"), encoding="utf-8")
    assert run(tmp_path, manifest=name) == 0
    assert calls == [name]
    assert not (tmp_path / "docs").exists()
