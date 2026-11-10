"""Regresiones operativas con cinco archivos artificiales, sin proveedor real."""

import hashlib
import json
import runpy
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest
from sat_dengue_pipeline.pipelines.canonical import nodes

ROOT = Path(__file__).resolve().parents[1]
COMMAND = "uv run --locked --directory pipeline python tools/acquire_private_raw.py"
PARAMS = {
    "mode": "approved", "workspace": "data/test-work", "tracking": False,
    "manifest": "conf/releases/approved-raw.json", "profile": "approved",
}


@pytest.fixture
def cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, ReleaseManifest]:
    """Preparar nombres aprobados con bytes diminutos y hashes artificiales explícitos."""
    payload = json.loads((ROOT / "conf/releases/approved-raw.json").read_bytes())
    for file in payload["files"]:
        file["size_bytes"] = 4
        file["sha256"] = hashlib.sha256(b"test").hexdigest()
    manifest = ReleaseManifest.from_json(json.dumps(payload))
    conf = tmp_path / "conf/releases"
    conf.mkdir(parents=True)
    (conf / "approved-raw.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(nodes, "validate_raw_manifest", lambda manifest: None)
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "data/01_raw/inbox" / manifest.release_id / manifest.manifest_sha256
    folder.mkdir(parents=True)
    for file in manifest.files:
        (folder / file.relative_path).write_bytes(b"test")
    return folder, manifest


@pytest.mark.parametrize("kind", ["absent", "not_directory", "missing", "extra"])
def test_cache_structure_is_actionable_and_private(
    cache: tuple[Path, ReleaseManifest], kind: str
) -> None:
    """Distinguir fallos estructurales sin exponer rutas ni llegar a productores."""
    folder, manifest = cache
    if kind in {"absent", "not_directory"}:
        for path in folder.iterdir():
            path.unlink()
        folder.rmdir()
        if kind == "not_directory":
            folder.write_bytes(b"not a folder")
    elif kind == "missing":
        (folder / manifest.files[0].relative_path).unlink()
    else:
        (folder / "private-extra-name").write_bytes(b"extra")
    with pytest.raises(ValueError) as caught:
        nodes.build_input(PARAMS)
    rendered = "".join(traceback.format_exception(caught.value))
    assert str(folder) not in rendered and "private-extra-name" not in rendered
    message = str(caught.value)
    assert {
        "absent": "inexistente",
        "not_directory": "directorio",
        "missing": "faltantes",
        "extra": "adicionales",
    }[kind] in message
    if kind in {"absent", "missing"}:
        assert COMMAND in message


@pytest.mark.parametrize("kind", ["cache", "ancestor", "file"])
def test_cache_symlinks_rejected(
    cache: tuple[Path, ReleaseManifest],
    symlink_factory: Callable[..., None],
    tmp_path: Path,
    kind: str,
) -> None:
    """Rechazar enlaces también en ancestros y archivos, con fallback Windows."""
    folder, manifest = cache
    target = tmp_path / "outside"
    target.mkdir()
    path = (
        folder
        if kind == "cache"
        else (folder.parent if kind == "ancestor" else folder / manifest.files[0].relative_path)
    )
    if path.is_file():
        path.unlink()
    else:
        import shutil

        shutil.rmtree(path)
    symlink_factory(path, target, target_is_directory=True)
    with pytest.raises(ValueError, match="enlac"):
        nodes.build_input(PARAMS)


def test_valid_cache_reaches_existing_validator_once(
    cache: tuple[Path, ReleaseManifest], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Delegar integridad sin duplicar hashes en el preflight estructural."""
    _, manifest = cache
    source = nodes.build_input(PARAMS)
    calls = []

    def validate(bundle: Any, config: Any, inventory: Any) -> Any:
        """Observar la frontera sin interpretar datos reales."""
        calls.append(bundle)
        return bundle

    monkeypatch.setattr(nodes, "raw_contract_validation", validate)
    assert nodes.validate_input(source) is source.bundle
    assert len(calls) == 1 and source.bundle.manifest_sha256 == manifest.manifest_sha256


@pytest.mark.parametrize("failure", [ValueError("bad hash"), OSError("private path")])
def test_corrupt_cache_error_has_no_exception_chain(
    cache: tuple[Path, ReleaseManifest], monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    """Conservar rechazo del validador y suprimir detalles externos de filesystem."""
    source = nodes.build_input(PARAMS)

    def reject(*args: Any) -> None:
        """Simular el rechazo existente de integridad sin productores."""
        raise failure

    monkeypatch.setattr(nodes, "raw_contract_validation", reject)
    with pytest.raises(ValueError, match="corrupta") as caught:
        nodes.validate_input(source)
    rendered = "".join(traceback.format_exception(caught.value))
    assert "private path" not in rendered and "bad hash" not in rendered
    assert COMMAND in str(caught.value)


def acquisition_tool(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, success: bool
) -> Callable[[Path], int]:
    """Cargar el CLI y sustituir toda adquisición por un doble local."""
    module = runpy.run_path(str(ROOT / "tools/acquire_private_raw.py"))
    run = module["run"]
    manifest_path = "conf/releases/operational-raw-173d5856.json"
    content = (ROOT / manifest_path).read_text()
    manifest = ReleaseManifest.from_json(content)
    local = tmp_path / manifest_path
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(content, encoding="utf-8")
    cache = tmp_path / "data/01_raw/inbox" / manifest.release_id / manifest.manifest_sha256
    from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle, ResolvedFile

    bundle = ResolvedBundle(
        manifest.release_id,
        manifest.manifest_sha256,
        manifest.coverage_start,
        manifest.coverage_end,
        tuple(
            ResolvedFile(f.logical_name, cache / f.relative_path, f.size_bytes, f.sha256)
            for f in manifest.files
        ),
        manifest.release_kind,
    )
    def acquire(config: dict, root: Path) -> tuple:
        """Simular transporte; el inventario físico conserva el contrato de Kedro."""
        if success:
            cache.mkdir(parents=True, exist_ok=True)
            for file in bundle.files:
                file.path.write_bytes(b"fixture")
            return bundle, {"status": "PASSED"}
        return None, {
            "status": "FAILED", "error_type": "SecretType_private_marker",
            "message": "private_marker /private/location",
        }

    monkeypatch.setitem(run.__globals__, "acquire", acquire)
    monkeypatch.setitem(run.__globals__, "raw_contract_validation", lambda *args: args[0])
    return run


@pytest.mark.parametrize("success", [False, True])
def test_operational_receipts_are_exclusive_private_and_ignored(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    success: bool,
) -> None:
    """Dos intentos, incluso fallidos, conservan recibos nuevos fuera de evidencia Git."""
    run = acquisition_tool(monkeypatch, tmp_path, success)
    history = tmp_path / "docs/evidence/task16/acquisition.json"
    history.parent.mkdir(parents=True)
    history.write_bytes(b"historical")
    assert run(tmp_path) == (0 if success else 1)
    first = {p: p.read_bytes() for p in (tmp_path / "data/acquisition").glob("*/receipt.json")}
    assert len(first) == 1
    assert run(tmp_path) == (0 if success else 1)
    receipts = list((tmp_path / "data/acquisition").glob("*/receipt.json"))
    assert len(receipts) == 2
    assert all(p.read_bytes() == value for p, value in first.items())
    assert history.read_bytes() == b"historical"
    output = capsys.readouterr().out
    assert str(tmp_path) not in output and "private_marker" not in output
    for path in receipts:
        data = json.loads(path.read_bytes())
        assert data["status"] == ("VERIFIED" if success else "FAILED")
        assert data["elapsed_seconds"] >= 0
        assert "private_marker" not in path.read_text()
    assert "data/" in (ROOT / ".gitignore").read_text()


def test_receipt_symlink_rejected_without_historical_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, symlink_factory: Callable[..., None]
) -> None:
    """El directorio operacional no puede escapar mediante un enlace."""
    run = acquisition_tool(monkeypatch, tmp_path, False)
    outside = tmp_path / "docs/evidence/task16"
    outside.mkdir(parents=True)
    symlink_factory(tmp_path / "data", outside, target_is_directory=True)
    assert run(tmp_path) == 1
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("kind", ["missing", "size", "hash", "valid"])
def test_real_integrity_validator_remains_authoritative(
    cache: tuple[Path, ReleaseManifest], monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """Ejercitar tamaño y hash reales sobre fixtures, sin duplicar el algoritmo."""
    from sat_dengue_pipeline.raw import contract

    folder, manifest = cache
    monkeypatch.setattr(
        contract,
        "INVENTORY",
        {f.logical_name: (f.relative_path, f.size_bytes, f.sha256) for f in manifest.files},
    )
    monkeypatch.setattr(contract, "HEADERS", {})
    # JSON y procedencia artificiales válidos, también identificados por hash.
    payloads = {
        "divipola_catalog": b'{"resultado":[]}',
        "divipola_provenance": json.dumps(
            {
                "files": {
                    "Divipola-municipios.md": {
                        "sha256": hashlib.sha256(b'{"resultado":[]}').hexdigest()
                    }
                }
            }
        ).encode(),
    }
    from dataclasses import replace

    files = []
    for file in manifest.files:
        content = payloads.get(file.logical_name, b"test")
        (folder / file.relative_path).write_bytes(content)
        files.append(
            replace(file, size_bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
        )
    monkeypatch.setattr(
        contract,
        "INVENTORY",
        {f.logical_name: (f.relative_path, f.size_bytes, f.sha256) for f in files},
    )
    source = nodes.build_input(PARAMS)
    from sat_dengue_pipeline.acquisition.contracts import ResolvedFile

    source = replace(
        source,
        bundle=replace(
            source.bundle,
            files=tuple(
                ResolvedFile(f.logical_name, folder / f.relative_path, f.size_bytes, f.sha256)
                for f in files
            ),
        ),
    )
    file = folder / files[-1].relative_path
    if kind == "missing":
        file.unlink()
    elif kind == "size":
        file.write_bytes(b"longer")
    elif kind == "hash":
        file.write_bytes(b"xxxx")
    if kind == "valid":
        assert nodes.validate_input(source) is source.bundle
    else:
        with pytest.raises(ValueError, match="corrupta"):
            nodes.validate_input(source)


@pytest.mark.parametrize("kind", ["absent", "corrupt"])
def test_kedro_preflight_stops_before_producers(
    cache: tuple[Path, ReleaseManifest], monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """El grafo Kedro real no puede iniciar productores con una entrada inválida."""
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue_pipeline.pipelines.canonical.pipeline import create_pipeline

    folder, _ = cache
    if kind == "absent":
        import shutil

        shutil.rmtree(folder)
    invoked = []

    def producer(*args: Any) -> None:
        """Detectar una invocación científica indebida."""
        invoked.append(True)
        raise AssertionError("producer must not run")

    monkeypatch.setattr(nodes, "geography", producer)
    with pytest.raises(ValueError):
        SequentialRunner().run(
            create_pipeline(), DataCatalog({"params:canonical": MemoryDataset(PARAMS)})
        )
    assert invoked == []
