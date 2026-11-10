"""Salidas auxiliares exclusivas y preservación portable, solo con datos artificiales."""

import json
import os
import runpy
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path, PureWindowsPath

import pandas as pd
import pytest

from sat_dengue_pipeline.domain.canonical import CLIMATE, COUNTS
from sat_dengue_pipeline.pipelines.canonical.nodes import BuildInput
from sat_dengue_pipeline.raw.build import build
from sat_dengue_pipeline.raw.contract import BuildConfig, sha256
from sat_dengue_pipeline.raw.fixture import fixture_config, synthetic_bundle
from sat_dengue_pipeline.raw.panel import canonical_panel
from sat_dengue_pipeline.raw.reproducibility import CertifiedCanonical
from sat_dengue_pipeline.raw.serialization import canonical_serialization
from sat_dengue_pipeline.tracking.local import TrackingReceipt

ROOT = Path(__file__).resolve().parents[1]


def tool(name: str, root: Path, monkeypatch: pytest.MonkeyPatch):
    """Cargar la entrada CLI real con raíz temporal y sin instalar guards persistentes."""
    main = runpy.run_path(str(ROOT / "tools" / name))["main"]
    monkeypatch.setitem(main.__globals__, "__file__", str(root / "tools" / name))
    if "enforce_boundaries" in main.__globals__:
        monkeypatch.setitem(main.__globals__, "enforce_boundaries", lambda _: None)
    monkeypatch.chdir(root)
    return main


def historical_receipts(root: Path) -> dict[Path, str]:
    """Copiar tres recibos cerrados reales como metadatos; nunca leer crudos."""
    folder = root.parent / "docs/evidence/task16"
    folder.mkdir(parents=True)
    for name in ("build-real.json", "certify-real.json", "canonical-quality.json"):
        shutil.copyfile(ROOT.parent / "docs/evidence/task16" / name, folder / name)
    return {path: sha256(path) for path in folder.iterdir()}


@pytest.mark.parametrize("phase", ["build", "certify"])
@pytest.mark.parametrize("failure", [None, "input", "producer", "observe"])
def test_reproducer_cli_preserves_history_on_every_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str, failure: str | None
) -> None:
    """Repetir éxitos/fallos en carpetas distintas, sin N=3 real ni sobreescrituras."""
    root = tmp_path / "pipeline"
    root.mkdir()
    before = historical_receipts(root)
    legacy = root / "data/task16-real"
    legacy.mkdir(parents=True)
    (legacy / "certify-artifact.json").write_bytes(b"closed legacy reference")
    before[legacy / "certify-artifact.json"] = sha256(legacy / "certify-artifact.json")
    main = tool("reproduce_private_raw.py", root, monkeypatch)
    bundle, inventory = synthetic_bundle(root / "fixture-raw")
    destinations = []

    def stop():
        """Representar una excepción de productor con texto que no debe filtrarse."""
        raise ValueError("private_marker /private/source")

    def source(parameters):
        """Observar la selección histórica explícita y sustituir únicamente la entrada."""
        assert parameters["manifest"] == "conf/releases/approved-raw.json"
        assert parameters["profile"] == "approved" and parameters["tracking"] is False
        if failure == "input":
            stop()
        workspace = Path(parameters["workspace"])
        assert workspace.is_relative_to("data")
        destinations.append(workspace)
        return BuildInput(bundle, fixture_config(), inventory, workspace, False)

    def producer(bundle, config, destination, **kwargs):
        """Reutilizar el constructor real sobre los cinco archivos artificiales."""
        if failure == "producer":
            stop()
        return build(bundle, config, destination, inventory, **kwargs)

    def certify(bundle, config, destination):
        """Simular el gate N=3 ya probado; esta reparación no lanza workers nuevos."""
        artifact, audit = producer(bundle, config, destination)
        return CertifiedCanonical(
            artifact,
            (artifact.serialized_sha256,) * 3,
            (artifact.semantic_digest,) * 3,
            (101, 102, 103),
            audit,
        )

    def observe(*args):
        """Devolver solo el recibo local, sin SDK ni persistencia compartida."""
        if failure == "observe":
            stop()
        return TrackingReceipt("satd-canonical", None, None, "DISABLED", False, "0" * 64)

    for name, value in (
        ("build_input", source),
        ("build", producer),
        ("canonical_reproducibility", certify),
        ("observe", observe),
    ):
        monkeypatch.setitem(main.__globals__, name, value)
    monkeypatch.setattr(sys, "argv", ["reproduce_private_raw.py", phase])
    for _ in range(2):
        monkeypatch.setenv("HF_TOKEN", "unused-fixture")
        assert main() == (0 if failure is None else 1)
        if _ == 0:
            first = {p: sha256(p) for p in root.glob("data/private-raw-*/*") if p.is_file()}
    receipts = list(root.glob(f"data/private-raw-{phase}-*/{phase}-real.json"))
    assert len(receipts) == 2 and receipts[0].parent != receipts[1].parent
    assert all(sha256(p) == digest for p, digest in first.items())
    for path in receipts:
        record = json.loads(path.read_bytes())
        assert record["status"] == ("PASSED" if failure is None else "FAILED")
        assert "private_marker" not in path.read_text(encoding="utf-8")
        assert root / record["workspace"] == path.parent
        if failure is None:
            reference = json.loads((path.parent / (phase + "-artifact.json")).read_bytes())
            assert Path(reference["path"]).is_relative_to(path.parent)
        else:
            assert record["error_type"] == "ValueError"
    assert {p: sha256(p) for p in before} == before
    assert len(set(destinations)) == (0 if failure == "input" else 2)
    assert not (root / ".tracking").exists()


@pytest.fixture(scope="module")
def historical_artifact(tmp_path_factory: pytest.TempPathFactory):
    """Crear el grano histórico completo con valores ficticios y productores existentes."""
    config = BuildConfig(profile="synthetic", start="2011-06", municipalities=1)
    geo = pd.DataFrame(
        {
            "municipality_code": ["50998"],
            "department_code": ["50"],
            "municipality_name": ["FIXTURE"],
        }
    )
    epi = pd.DataFrame({"municipality_code": ["50998"] * 163, "year_month": config.periods})
    for name in COUNTS:
        epi[name] = pd.array([0] * 163, dtype="Int64")
    climate = epi[["municipality_code", "year_month"]].copy()
    days = pd.PeriodIndex(climate.year_month, freq="M").days_in_month
    for name in ("expected_days_in_month", "climate_days_observed"):
        climate[name] = pd.array(days, dtype="Int64")
    for name in CLIMATE:
        climate[name] = pd.array([1.0] * 163, dtype="Float64")
        climate[f"{name}_valid_days"] = pd.array(days, dtype="Int64")
    template, schema = canonical_panel((geo, epi, climate), config)
    parts = []
    for i in range(1122):
        frame = template.copy()
        frame["municipality_code"] = pd.array([f"{10000 + i}"] * 163, dtype="string")
        frame["department_code"] = pd.array([str(10000 + i)[:2]] * 163, dtype="string")
        parts.append(frame)
    table = pd.concat(parts, ignore_index=True)
    return canonical_serialization((table, schema), tmp_path_factory.mktemp("artificial-history"))


@pytest.mark.parametrize("failure", [None, "certificate", "artifact"])
def test_validator_cli_keeps_new_and_closed_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, historical_artifact, failure: str | None
) -> None:
    """Validar con carga/roundtrip/guards reales o fallar; conservar todos los recibos."""
    root = tmp_path / "pipeline"
    root.mkdir()
    before = historical_receipts(root)
    inputs = root / "data/fixture-input"
    inputs.mkdir(parents=True)
    reference = inputs / "certify-artifact.json"
    certificate = inputs / "certify-real.json"
    artifact = historical_artifact
    reference.write_text(
        json.dumps({**asdict(artifact), "path": str(artifact.path)}), encoding="utf-8"
    )
    certificate.write_text(
        json.dumps(
            {
                "status": "FAILED" if failure == "certificate" else "PASSED",
                "reconstruction_hashes": [artifact.serialized_sha256] * 3,
                "serialized_sha256": "0" * 64
                if failure == "artifact"
                else artifact.serialized_sha256,
            }
        ),
        encoding="utf-8",
    )
    before.update({p: sha256(p) for p in (reference, certificate, artifact.path)})
    main = tool("validate_private_canonical.py", root, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_private_canonical.py",
            "--certification",
            str(certificate.relative_to(root)),
            "--artifact",
            str(reference.relative_to(root)),
        ],
    )
    for repetition in range(2):
        assert main() == (0 if failure is None else 1)
        if repetition == 0:
            first = {
                p: sha256(p) for p in root.glob("data/private-canonical-*/canonical-quality.json")
            }
    receipts = list(root.glob("data/private-canonical-*/canonical-quality.json"))
    assert len(receipts) == 2 and receipts[0].parent != receipts[1].parent
    assert all(sha256(p) == digest for p, digest in first.items())
    assert {p: sha256(p) for p in before} == before
    for path in receipts:
        report = json.loads(path.read_bytes())
        assert report["status"] == ("PASSED" if failure is None else "FAILED")
        if failure is None:
            assert report["rows"] == 182886 and report["months"] == 163
            assert report["roundtrip_bytes_identical"] and report["learned_components_invoked"] == 0
            assert all(
                h["reserved_target_rejected_before_preparation"]
                for h in report["horizons"].values()
            )
        else:
            assert report["error_type"] == "ValueError"


@pytest.fixture
def protected_repository(tmp_path: Path) -> Path:
    """Inventario artificial de 49 archivos, 22 publicaciones y 16 recibos previos."""
    names = [f"datos/resultados/fixture-{i}.json" for i in range(22)]
    names += [f"docs/evidence/task16/fixture-{i}.json" for i in range(16)]
    comparison = "docs/evidence/task16/factory-experiment/n3-comparison.json"
    names += [comparison] + [f"docs/fixture-{i}.json" for i in range(10)]
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"{}\n")
    identity = "a" * 64
    (tmp_path / comparison).write_text(
        json.dumps(
            {
                "identities": [identity] * 3,
                "all_identities_equal": True,
                "fourth_run_executed": False,
            }
        ),
        encoding="utf-8",
    )
    baseline = tmp_path / "docs/evidence/task17/preservation-baseline.json"
    baseline.parent.mkdir(parents=True)
    baseline.write_text(
        json.dumps(
            {
                "sha256": {name: sha256(tmp_path / name) for name in names},
                "t16_identity_sha256": identity,
            }
        ),
        encoding="utf-8",
    )
    script = tmp_path / "pipeline/tools/check_experiment_preservation.py"
    script.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "tools/check_experiment_preservation.py", script)
    return tmp_path


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("altered", [False, True])
def test_preservation_cli_rejects_tampering_even_optimized(
    protected_repository: Path, optimized: bool, altered: bool
) -> None:
    """La misma CLI real rechaza un archivo alterado con Python normal y -O."""
    root = protected_repository
    if altered:
        (root / "docs/fixture-0.json").write_bytes(b"altered")
    command = [
        sys.executable,
        *(["-O"] if optimized else []),
        str(root / "pipeline/tools/check_experiment_preservation.py"),
    ]
    env = {k: v for k, v in os.environ.items() if k != "HF_TOKEN"}
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    assert result.returncode == (1 if altered else 0)
    if altered:
        assert "Archivo protegido alterado: docs/fixture-0.json" in result.stderr
        assert '"status": "PASSED"' not in result.stdout
    else:
        assert json.loads(result.stdout)["protected_files"] == 49


def test_preservation_compares_windows_relative_paths_as_posix(
    protected_repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ejercitar verify completo con rutas relativas Windows, sin afirmar ejecución nativa."""
    verify = runpy.run_path(str(ROOT / "tools/check_experiment_preservation.py"))["verify"]
    original = Path.relative_to

    def windows_relative(path, *args, **kwargs):
        """Simular el objeto que devuelve relative_to en Windows."""
        return PureWindowsPath(*original(path, *args, **kwargs).parts)

    monkeypatch.setattr(Path, "relative_to", windows_relative)
    assert verify(protected_repository)["published_json"] == 22


@pytest.mark.parametrize("name", ["reproduce_private_raw.py", "validate_private_canonical.py"])
def test_private_tools_reject_redirected_output_without_touching_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, symlink_factory, name: str
) -> None:
    """Reutilizar el guard de enlaces antes de crear salidas, incluso sin privilegios."""
    root = tmp_path / "pipeline"
    root.mkdir()
    before = historical_receipts(root)
    destination = next(iter(before)).parent
    main = tool(name, root, monkeypatch)
    symlink_factory(root / "data", destination, target_is_directory=True)
    arguments = [name, "build"] if name == "reproduce_private_raw.py" else [name]
    monkeypatch.setattr(sys, "argv", arguments)
    assert main() == 1
    assert {p: sha256(p) for p in before} == before
    assert set(destination.iterdir()) == set(before)
