"""N=3 real en procesos nuevos y bloqueo del consumidor ante divergencias."""

import ast
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from sat_dengue_pipeline.raw.build import build
from sat_dengue_pipeline.raw.fixture import fixture_config, synthetic_bundle
from sat_dengue_pipeline.raw.reproducibility import (
    Reconstruction,
    certify_then_consume,
    isolated_build,
)
from sat_dengue_pipeline.raw.serialization import (
    CanonicalArtifact,
    canonical_bytes,
    verify_artifact,
)
from sat_dengue_pipeline.tracking.canonical import (
    collect_canonical_tracking,
    validate_canonical_tracking,
)
from sat_dengue_pipeline.tracking.local import LocalTracker, TrackingConfig


@pytest.fixture
def raw(tmp_path):
    """Crear un bundle artificial sin SDKs ni datos reales."""
    bundle, inventory = synthetic_bundle(tmp_path / "raw")
    return bundle, inventory, fixture_config()


def test_n3_real_processes_one_output_and_consumer_only_after_pass(raw, tmp_path):
    """Cada proceso/directorio parte de crudos y se libera una única salida."""
    bundle, inventory, config = raw
    calls, directories, pids = [], [], []

    def execute(b, c, root, i):
        """Inspeccionar el aislamiento sin sustituir el ejecutor real."""
        assert list(root.iterdir()) == []
        result = isolated_build(b, c, root, i)
        assert set(path.name for path in (root / "inbox").iterdir()) == {
            file.path.name for file in bundle.files
        }
        directories.append(root)
        pids.append(result.pid)
        assert calls == []
        return result

    def consumer(certificate):
        """Espía representativo de entrenamiento, sin ajustar un modelo."""
        assert len(pids) == 3
        calls.append(certificate)
        return certificate

    certificate = certify_then_consume(
        bundle, config, tmp_path / "gate", consumer, inventory, executor=execute
    )
    assert calls == [certificate]
    assert len(set(pids)) == 3
    assert len(set(directories)) == 3
    assert all(not path.exists() for path in directories)
    assert len(set(certificate.hashes)) == 1
    assert len(set(certificate.semantic_digests)) == 1
    assert list((tmp_path / "gate").rglob("canonical.json")) == [certificate.artifact.path]
    assert verify_artifact(certificate.artifact)
    assert certificate.audit["coverage"]["rows"] == 168
    assert certificate.audit["coverage"]["end"] == "2024-12"
    assert sum(row["reserved"] for row in certificate.audit["quarantine"].values()) == 3


@pytest.mark.parametrize("failure", ["values", "schema", "nulls", "bytes", "worker"])
def test_injected_divergence_stops_before_training(raw, tmp_path, failure):
    """Una tercera reconstrucción distinta o fallida impide llamar al consumidor."""
    bundle, inventory, config = raw
    calls, iteration = [], []

    def execute(b, c, root, i):
        """Inyectar un fallo después de ejecutar el constructor real aislado."""
        iteration.append(root)
        result = isolated_build(b, c, root, i)
        if len(iteration) != 3:
            return result
        if failure == "worker":
            raise ValueError("worker injected")
        if failure == "bytes":
            result.artifact.path.write_bytes(result.artifact.path.read_bytes() + b" ")
            return result
        payload = json.loads(result.artifact.path.read_bytes())
        if failure == "schema":
            payload["schema"]["columns"][0]["dtype"] = "object"
        elif failure == "nulls":
            payload["rows"][0][2] = None
        else:
            payload["rows"][0][2] = "ALTERED"
        data = canonical_bytes(payload)
        payload.pop("format")
        artifact = CanonicalArtifact(
            result.artifact.path,
            hashlib.sha256(canonical_bytes(payload)).hexdigest(),
            hashlib.sha256(data).hexdigest(),
        )
        artifact.path.write_bytes(data)
        return Reconstruction(artifact, result.audit, result.pid)

    with pytest.raises(ValueError):
        certify_then_consume(
            bundle,
            config,
            tmp_path / "gate",
            lambda c: calls.append(c),
            inventory,
            executor=execute,
        )
    assert calls == []
    assert not (tmp_path / "gate/certified").exists()
    assert list((tmp_path / "gate").glob("n3-*")) == []


def test_worker_guards_network_dns_provider_imports_and_protected_files(tmp_path):
    """Los centinelas viven también fuera del proceso de pytest."""
    code = """
import socket
from pathlib import Path
from sat_dengue_pipeline.raw.worker import enforce_boundaries
import sat_dengue_pipeline.raw.worker as worker
enforce_boundaries(True)
repo = Path(worker.__file__).resolve().parents[4]
actions = [
 lambda: socket.getaddrinfo("forbidden.invalid", 443),
 lambda: socket.create_connection(("forbidden.invalid", 443)),
 lambda: __import__("huggingface_hub"),
 lambda: __import__("boto3"),
 lambda: (repo / "datos/datos-crudos/dengue.csv").open(),
 lambda: (repo / "datos/resultados/forbidden.json").open(),
 lambda: (repo.parent / "SAT-Dengue-V2/forbidden.csv").open(),
]
for action in actions:
 try: action()
 except (RuntimeError, ImportError): pass
 else: raise AssertionError("guard absent")
print("7 boundaries blocked")
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "7 boundaries blocked"


def test_scientific_modules_have_no_provider_imports():
    """Comprobar también el árbol AST, sin confiar únicamente en imports ya cacheados."""
    root = Path(__file__).parents[1] / "src/sat_dengue_pipeline"
    for directory in ("raw", "domain", "experiments", "models", "evaluation"):
        for path in (root / directory).glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                names = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                )
                assert not any(
                    name.split(".")[0]
                    in {"huggingface_hub", "boto3", "botocore", "app", "sat_api", "urllib"}
                    or name.endswith("acquisition.sources")
                    for name in names
                ), path


@pytest.fixture
def tracking_payload(raw, tmp_path):
    """Capturar metadatos reales de un repositorio artificial local."""
    repo = tmp_path / "repo"
    (repo / "pipeline").mkdir(parents=True)
    (repo / ".gitignore").write_text(".tracking/\n")
    (repo / "pipeline/uv.lock").write_text("synthetic lock identity")
    subprocess.run(["git", "init", "-q", "-b", "feature/pipeline-e2e", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "synthetic",
        ],
        check=True,
    )
    b, i, c = raw
    artifact, audit = build(b, c, tmp_path / "build", i)
    payload = collect_canonical_tracking(
        repo, b, c, artifact, audit, (artifact.serialized_sha256,) * 3
    )
    return repo, payload, artifact


def test_canonical_tracking_local_opt_in_privacy_and_scientific_identity(tracking_payload):
    """El observador compartido guarda solo agregados y no cambia bytes canónicos."""
    repo, payload, artifact = tracking_payload
    before = verify_artifact(artifact)
    disabled = LocalTracker(repo, TrackingConfig())
    off = disabled.record_canonical(payload)
    assert off.status == "DISABLED"
    assert not (repo / ".tracking").exists()
    tracker = LocalTracker(repo, TrackingConfig(enabled=True, experiment_name="satd-canonical"))
    try:
        receipt = tracker.record_canonical(payload)
        assert receipt.status == "FINISHED"
        assert receipt.artifact_digest == off.artifact_digest
        artifacts = tracker.artifacts(receipt.run_id)
        assert json.loads(artifacts["canonical_build.json"]) == payload
        assert (
            json.loads(tracker.get_run(receipt.run_id).data.params["canonical_semantic_digest"])
            == artifact.semantic_digest
        )
        content = b"".join(artifacts.values())
        assert str(repo).encode() not in content
        for private in (b"50998", b"73998", b"REPEATED", b"MUST NEVER", b"source_url"):
            assert private not in content
        assert len(json.loads(artifacts["canonical_build.json"])["reconstruction_hashes"]) == 3
        assert verify_artifact(artifact) == before
    finally:
        tracker.close()


@pytest.mark.parametrize("where", ["top", "coverage", "stages", "quarantine", "false_gate"])
def test_canonical_tracking_rejects_extra_fields_before_open(tracking_payload, where):
    """La allowlist rechaza filas, texto libre o una certificación incompleta."""
    repo, original, _ = tracking_payload
    payload = copy.deepcopy(original)
    if where == "false_gate":
        payload["reconstruction_hashes"] = [payload["serialized_sha256"]]
    elif where == "top":
        payload["microdata"] = []
    else:
        payload[where]["private_path"] = "/private/forbidden"
    with pytest.raises(ValueError):
        validate_canonical_tracking(payload)
    tracker = LocalTracker(repo, TrackingConfig(enabled=True))
    with pytest.raises(ValueError):
        tracker.record_canonical(payload)
    assert not (repo / ".tracking").exists()


def test_uncertified_build_is_labeled_and_cannot_claim_n3(tracking_payload):
    """Una construcción provisional se distingue de la certificación."""
    _, payload, _ = tracking_payload
    payload = {
        **payload,
        "certification": "UNCERTIFIED",
        "reconstruction_hashes": [],
    }
    validate_canonical_tracking(payload)
    payload["reconstruction_hashes"] = [payload["serialized_sha256"]] * 3
    with pytest.raises(ValueError):
        validate_canonical_tracking(payload)
