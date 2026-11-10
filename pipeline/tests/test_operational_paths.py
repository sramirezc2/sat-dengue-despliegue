"""Equivalencia de CLI operacionales y caché segura con cinco crudos artificiales."""

import ast
import json
import runpy
import shlex
import shutil
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Callable

import pytest

from sat_dengue_pipeline.acquisition import factory, raw_manifest
from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest
from sat_dengue_pipeline.acquisition.raw_manifest import (
    HISTORICAL_MANIFEST,
    OPERATIONAL_MANIFEST,
)
from sat_dengue_pipeline.acquisition.sources import LocalSource
from sat_dengue_pipeline.pipelines.canonical import nodes
from sat_dengue_pipeline.raw import contract
from sat_dengue_pipeline.raw.fixture import fixture_inventory, synthetic_bundle

ROOT = Path(__file__).resolve().parents[1]
PARAMS = {"mode": "approved", "workspace": "data/manual", "tracking": False}


@pytest.fixture
def environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple:
    """Crear dos releases diminutos y sustituir solo el transporte privado."""
    root = tmp_path / "project"
    root.mkdir()
    manifests, sources = {}, {}
    for index, name in enumerate((HISTORICAL_MANIFEST, OPERATIONAL_MANIFEST)):
        source = tmp_path / f"source-{index}"
        synthetic_bundle(source / "datos-crudos")
        if index:
            with (source / "datos-crudos/google_earth_engine.csv").open("ab") as stream:
                stream.write(b"\n")
        _, inventory = fixture_inventory(source / "datos-crudos")
        attribute = "OPERATIONAL_INVENTORY" if index else "INVENTORY"
        monkeypatch.setattr(raw_manifest, attribute, inventory)
        monkeypatch.setattr(contract, attribute, inventory)
        original = ReleaseManifest.from_json((ROOT / name).read_text(encoding="utf-8"))
        manifest = replace(
            original,
            files=tuple(
                replace(
                    f, size_bytes=inventory[f.logical_name][1], sha256=inventory[f.logical_name][2]
                )
                for f in original.files
            ),
        )
        local = root / name
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps(asdict(manifest)), encoding="utf-8")
        manifests[name], sources[manifest.release_id] = manifest, source
    tools = root / "tools"
    tools.mkdir()
    for name in ("acquire_private_raw.py", "build_approved_canonical.py"):
        shutil.copy2(ROOT / "tools" / name, tools / name)
    monkeypatch.setattr(
        factory,
        "create_source",
        lambda manifest, **kwargs: LocalSource(sources[manifest.release_id]),
    )
    monkeypatch.chdir(root)
    return root, manifests


def cli(root: Path, script: str, arguments: list[str], monkeypatch: pytest.MonkeyPatch) -> int:
    """Ejercitar argparse y main reales sin iniciar procesos o proveedores privados."""
    path = root / "tools" / script
    with monkeypatch.context() as local:
        local.setattr(sys, "argv", [str(path), *arguments])
        with pytest.raises(SystemExit) as caught:
            runpy.run_path(str(path), run_name="__main__")
    return caught.value.code


def selection(parameters: dict) -> tuple[str, str, str]:
    """Observar release/perfil después del preflight y la integridad reales de Kedro."""
    source = nodes.build_input(parameters)
    assert nodes.validate_input(source) is source.bundle
    return source.bundle.release_id, source.config.profile, source.config.start


def parameters(command: list[str]) -> dict:
    """Interpretar los parámetros planos documentados, sin ejecutar ciencia."""
    values = command[command.index("--params") + 1]
    return {
        key.removeprefix("canonical."): (value == "true" if value in {"true", "false"} else value)
        for key, value in (item.split("=", 1) for item in values.split(","))
    }


def helper(environment: tuple, monkeypatch: pytest.MonkeyPatch, arguments: list[str]) -> tuple:
    """Coordinar los CLI reales e interceptar únicamente el lanzamiento de Kedro."""
    root, _ = environment
    observed = []

    def process(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        """Adquirir fixtures o inspeccionar la entrada real al único grafo científico."""
        if args[1] == "tools/acquire_private_raw.py":
            code = cli(root, "acquire_private_raw.py", args[2:], monkeypatch)
        else:
            assert args[1:6] == ["-m", "kedro", "run", "--pipelines", "canonical_build"]
            assert "HF_TOKEN" not in kwargs["env"]
            observed.append(selection(parameters(args)))
            code = 0
        return subprocess.CompletedProcess(args, code)

    with monkeypatch.context() as local:
        local.setattr(subprocess, "run", process)
        assert cli(root, "build_approved_canonical.py", arguments, monkeypatch) == 0
    assert len(observed) == 1
    return observed[0]


@pytest.mark.parametrize(
    "document",
    [
        "README.md",
        "pipeline/README.md",
        "docs/operations/pipeline-operations.md",
    ],
)
def test_documented_manual_path_equals_single_command(
    environment: tuple, monkeypatch: pytest.MonkeyPatch, document: str
) -> None:
    """Comprobar los ejemplos publicados y los defaults efectivos de los dos main."""
    root, _ = environment
    commands = [
        shlex.split(line)
        for line in (ROOT.parent / document).read_text(encoding="utf-8").splitlines()
        if line.startswith("uv run --locked --directory pipeline ")
    ]
    acquisition = next(
        c for c in commands if "tools/acquire_private_raw.py" in c and "--manifest" not in c
    )
    canonical = next(
        c
        for c in commands
        if "canonical_build" in c
        and "canonical.mode=approved" in c[-1]
        and "canonical.manifest=" not in c[-1]
    )
    single = helper(environment, monkeypatch, [])
    assert cli(root, "acquire_private_raw.py", acquisition[7:], monkeypatch) == 0
    manual = selection(parameters(canonical))
    assert single == manual == ("satd-raw-173d5856", "operational_full", "2007-01")


def test_historical_selection_requires_explicit_manifest_and_profile(
    environment: tuple, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mantener reproducción histórica y evitar fallback cuando falta la caché nueva."""
    root, _ = environment
    assert (
        cli(root, "acquire_private_raw.py", ["--manifest", HISTORICAL_MANIFEST], monkeypatch) == 0
    )
    with pytest.raises(ValueError, match="inexistente") as error:
        nodes.build_input(PARAMS)
    assert f"--manifest {OPERATIONAL_MANIFEST}" in str(error.value)
    historical = {**PARAMS, "manifest": HISTORICAL_MANIFEST, "profile": "approved"}
    manual = selection(historical)
    single = helper(
        environment,
        monkeypatch,
        [
            "--manifest",
            HISTORICAL_MANIFEST,
            "--profile",
            "approved",
        ],
    )
    assert single == manual == ("satd-raw-a1a7f237", "approved", "2011-06")


@pytest.mark.parametrize("kind", ["missing", "corrupt"])
def test_acquisition_still_recovers_missing_or_corrupt_files(
    environment: tuple, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """Permitir reparación atómica y terminar con la misma entrada aceptada por Kedro."""
    root, manifests = environment
    assert cli(root, "acquire_private_raw.py", [], monkeypatch) == 0
    manifest = manifests[OPERATIONAL_MANIFEST]
    cache = root / "data/01_raw/inbox" / manifest.release_id / manifest.manifest_sha256
    file = cache / manifest.files[-1].relative_path
    if kind == "missing":
        file.unlink()
    else:
        file.write_bytes(b"corrupt")
    assert cli(root, "acquire_private_raw.py", [], monkeypatch) == 0
    assert selection(PARAMS) == ("satd-raw-173d5856", "operational_full", "2007-01")


@pytest.mark.parametrize("late", [False, True])
def test_extra_files_are_preserved_and_never_receive_verified(
    environment: tuple,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    late: bool,
) -> None:
    """Rechazar adicionales antes y después del resolver, sin exponer sus nombres."""
    root, manifests = environment
    manifest = manifests[OPERATIONAL_MANIFEST]
    cache = root / "data/01_raw/inbox" / manifest.release_id / manifest.manifest_sha256
    extra = cache / "private-extra-marker"
    if late:
        resolve = factory.resolve_release

        def resolve_with_extra(*args: object) -> object:
            """Simular un adicional aparecido tras verificar los cinco archivos."""
            bundle = resolve(*args)
            extra.write_bytes(b"preserve")
            return bundle

        monkeypatch.setattr(factory, "resolve_release", resolve_with_extra)
    else:
        cache.mkdir(parents=True)
        extra.write_bytes(b"preserve")
    assert cli(root, "acquire_private_raw.py", [], monkeypatch) == 1
    receipt = json.loads(
        next((root / "data/acquisition").glob("*/receipt.json")).read_text(encoding="utf-8")
    )
    assert receipt["status"] == "FAILED" and "adicionales" in receipt["diagnostic"]
    assert extra.read_bytes() == b"preserve"
    assert "private-extra-marker" not in capsys.readouterr().out


@pytest.mark.parametrize("kind", ["data", "raw_parent", "cache_root", "release", "bundle", "file"])
def test_rejected_links_never_write_to_their_target(
    environment: tuple,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    symlink_factory: Callable,
    kind: str,
) -> None:
    """Rechazar enlaces de raíz, ancestros y archivos antes de escribir crudos."""
    root, manifests = environment
    manifest = manifests[OPERATIONAL_MANIFEST]
    bundle = root / "data/01_raw/inbox" / manifest.release_id / manifest.manifest_sha256
    link = {
        "data": root / "data",
        "raw_parent": root / "data/01_raw",
        "cache_root": root / "data/01_raw/inbox",
        "release": bundle.parent,
        "bundle": bundle,
        "file": bundle / manifest.files[-1].relative_path,
    }[kind]
    link.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    protected = outside / "protected"
    protected.write_bytes(b"untouched")
    symlink_factory(
        link, protected if kind == "file" else outside, target_is_directory=kind != "file"
    )
    assert cli(root, "acquire_private_raw.py", [], monkeypatch) == 1
    assert {p.name: p.read_bytes() for p in outside.iterdir()} == {"protected": b"untouched"}


def test_resolver_rejects_cache_root_link_before_materializing(
    environment: tuple, tmp_path: Path, symlink_factory: Callable
) -> None:
    """El resolver compartido también protege llamadores distintos del CLI directo."""
    from sat_dengue_pipeline.acquisition.errors import CacheError
    from sat_dengue_pipeline.acquisition.resolver import resolve_release

    _, manifests = environment
    outside = tmp_path / "outside"
    outside.mkdir()
    cache = tmp_path / "cache-link"
    symlink_factory(cache, outside, target_is_directory=True)

    class NeverMaterialize:
        """Detectar cualquier escritura indebidamente iniciada tras el enlace."""

        def materialize(self, *args: object) -> None:
            """Fallar antes de crear archivos fuera del confinamiento."""
            pytest.fail("materialization must not run")

    with pytest.raises(CacheError):
        resolve_release(manifests[OPERATIONAL_MANIFEST], cache, NeverMaterialize())
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("manifest", [HISTORICAL_MANIFEST, OPERATIONAL_MANIFEST])
def test_recovery_messages_keep_the_requested_manifest(
    environment: tuple, monkeypatch: pytest.MonkeyPatch, manifest: str
) -> None:
    """No recomendar adquirir otro release ante ausencia o corrupción histórica."""
    root, manifests = environment
    params = {**PARAMS, "manifest": manifest, "profile": "approved"}
    with pytest.raises(ValueError) as absent:
        nodes.build_input(params)
    assert f"--manifest {manifest}" in str(absent.value)
    assert cli(root, "acquire_private_raw.py", ["--manifest", manifest], monkeypatch) == 0
    selected = manifests[manifest]
    cache = root / "data/01_raw/inbox" / selected.release_id / selected.manifest_sha256
    (cache / selected.files[-1].relative_path).write_bytes(b"corrupt")
    with pytest.raises(ValueError) as corrupt:
        nodes.validate_input(nodes.build_input(params))
    assert f"--manifest {manifest}" in str(corrupt.value)


def test_historical_reproducer_declares_both_selections() -> None:
    """Evitar que el lanzador cerrado de T16 dependa de defaults operacionales."""
    tree = ast.parse((ROOT / "tools/reproduce_private_raw.py").read_text(encoding="utf-8"))
    call = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "build_input"
    )
    values = dict(zip((k.value for k in call.args[0].keys), call.args[0].values, strict=True))
    assert values["manifest"].id == "HISTORICAL_MANIFEST"
    assert values["profile"].value == "approved"


def test_default_kedro_mode_remains_synthetic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """El cambio de defaults reales no convierte el comando Kedro sintético en adquisición."""
    import yaml

    settings = yaml.safe_load((ROOT / "conf/base/parameters.yml").read_text(encoding="utf-8"))
    monkeypatch.chdir(tmp_path)
    assert settings["canonical"]["mode"] == "synthetic"
    source = nodes.build_input(settings["canonical"])
    assert source.config.profile == "synthetic" and source.inventory is not None


def test_resolver_rejects_internal_valid_file_link(
    environment: tuple, monkeypatch: pytest.MonkeyPatch, symlink_factory: Callable
) -> None:
    """No aceptar un enlace interno aunque sus bytes y hash coincidan con el manifiesto."""
    from sat_dengue_pipeline.acquisition.errors import CacheError
    from sat_dengue_pipeline.acquisition.resolver import resolve_release

    root, manifests = environment
    assert cli(root, "acquire_private_raw.py", [], monkeypatch) == 0
    manifest = manifests[OPERATIONAL_MANIFEST]
    cache = root / "data/01_raw/inbox" / manifest.release_id / manifest.manifest_sha256
    file = cache / manifest.files[-1].relative_path
    content = file.read_bytes()
    target = cache / "internal-target"
    file.rename(target)
    symlink_factory(file, target)
    with pytest.raises(CacheError):
        resolve_release(manifest, root / "data/01_raw/inbox", LocalSource(root))
    assert target.read_bytes() == content
