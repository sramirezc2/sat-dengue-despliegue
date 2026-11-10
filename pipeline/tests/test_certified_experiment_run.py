"""Aceptación por la entrada Kedro normal, sin datos privados, N=3 ni ajustes reales."""

import copy
import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest
import yaml
from kedro.io import DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner

from sat_dengue_pipeline.acquisition import factory, raw_manifest
from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest
from sat_dengue_pipeline.acquisition.raw_manifest import OPERATIONAL_MANIFEST
from sat_dengue_pipeline.acquisition.sources import LocalSource
from sat_dengue_pipeline.domain.canonical import CLIMATE, COUNTS
from sat_dengue_pipeline.experiment_management import runner
from sat_dengue_pipeline.experiment_management.certification import load_certified_recipe
from sat_dengue_pipeline.experiment_management.compare import compare
from sat_dengue_pipeline.experiment_management.configuration import load_configuration
from sat_dengue_pipeline.experiment_management.evidence import verify_execution
from sat_dengue_pipeline.experiment_management.registry import Registry
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.pipelines.experiment_run.pipeline import create_pipeline
from sat_dengue_pipeline.raw.contract import BuildConfig, sha256
from sat_dengue_pipeline.raw.fixture import fixture_inventory, synthetic_bundle
from sat_dengue_pipeline.raw.panel import canonical_panel
from sat_dengue_pipeline.raw.serialization import canonical_serialization

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = "docs/evidence/task27/canonical-full-93ac27fd-certification.json"
EID = "ACCEPTCERT"


@pytest.fixture(scope="module")
def artifacts(tmp_path_factory: pytest.TempPathFactory) -> tuple:
    """Crear tablas artificiales de cardinalidad real; sin simular el lector del certificado."""
    work = tmp_path_factory.mktemp("canonical-artificial")
    config = BuildConfig(
        profile="synthetic", start="2007-01", epi_start="2007-01", municipalities=1
    )
    geo = pd.DataFrame(
        {
            "municipality_code": ["50998"],
            "department_code": ["50"],
            "municipality_name": ["FIXTURE"],
        }
    )
    epi = pd.DataFrame({"municipality_code": ["50998"] * 216, "year_month": config.periods})
    for index, name in enumerate(COUNTS[:2]):
        epi[name] = pd.array([(i % 7) + index for i in range(216)], dtype="Int64")
    epi[COUNTS[2]] = epi[COUNTS[0]] + epi[COUNTS[1]]
    climate = epi[["municipality_code", "year_month"]].copy()
    days = pd.PeriodIndex(climate.year_month, freq="M").days_in_month
    climate["expected_days_in_month"] = pd.array(days, dtype="Int64")
    climate["climate_days_observed"] = pd.array(days, dtype="Int64")
    for name in CLIMATE:
        climate[name] = pd.array([1.0] * 216, dtype="Float64")
        climate[f"{name}_valid_days"] = pd.array(days, dtype="Int64")
    template, schema = canonical_panel((geo, epi, climate), config)
    tables = []
    for code in (f"{i:05d}" for i in range(10000, 11122)):
        table = template.copy()
        table["municipality_code"] = pd.array([code] * 216, dtype="string")
        table["department_code"] = pd.array([code[:2]] * 216, dtype="string")
        tables.append(table)
    full = pd.concat(tables, ignore_index=True)
    artifact = canonical_serialization((full, schema), work / "full")
    audit = {
        "coverage": {
            "start": "2007-01",
            "end": "2024-12",
            "municipalities": 1122,
            "rows": len(full),
            "nulls": {name: int(full[name].isna().sum()) for name in full},
        },
        "quarantine": {},
        "stages": {},
    }
    historical = full.loc[full.year_month.ge("2011-06")].reset_index(drop=True)
    historical_schema = copy.deepcopy(schema)
    for column in historical_schema["columns"]:
        column["nullable"] = bool(historical[column["name"]].isna().any())
    old = canonical_serialization((historical, historical_schema), work / "historical")
    return artifact, old, audit


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, artifacts: tuple) -> dict:
    """Receta APPROVED temporal, transporte local y constructor artificial observable."""
    root = tmp_path
    source = root / "fixture-input"
    synthetic_bundle(source / "datos-crudos")
    _, inventory = fixture_inventory(source / "datos-crudos")
    monkeypatch.setattr(raw_manifest, "OPERATIONAL_INVENTORY", inventory)
    path = root / "pipeline" / OPERATIONAL_MANIFEST
    path.parent.mkdir(parents=True)
    document = json.loads((ROOT / "pipeline" / OPERATIONAL_MANIFEST).read_text(encoding="utf-8"))
    for file in document["files"]:
        file["size_bytes"], file["sha256"] = inventory[file["logical_name"]][1:]
    path.write_text(json.dumps(document, indent=4) + "\n", encoding="utf-8")
    manifest = ReleaseManifest.from_json(path.read_text(encoding="utf-8"))
    shutil.copyfile(ROOT / "pipeline/uv.lock", root / "pipeline/uv.lock")
    monkeypatch.setattr(factory, "create_source", lambda *args, **kwargs: LocalSource(source))
    artifact, historical, audit = artifacts
    certificate = json.loads((ROOT / REFERENCE).read_text(encoding="utf-8"))
    certificate["configured_operational_manifest_file_sha256"] = sha256(path)
    certificate["manifest_sha256"] = manifest.manifest_sha256
    certificate["preflight"]["files"] = [
        {
            "logical_name": f.logical_name,
            "size_bytes": f.size_bytes,
            "sha256": f.sha256,
            "verified": True,
        }
        for f in manifest.files
    ]
    identity = certificate["n3"]["certified_identity"]
    identity.update(
        semantic_digest=artifact.semantic_digest, serialized_sha256=artifact.serialized_sha256
    )
    certificate["n3"].update(
        serialized_hashes=[artifact.serialized_sha256] * 3,
        semantic_digests=[artifact.semantic_digest] * 3,
        audit=audit,
        audit_sha256=stable_digest(audit),
    )
    cert_path = root / REFERENCE
    cert_path.parent.mkdir(parents=True)
    cert_path.write_text(json.dumps(certificate), encoding="utf-8")
    config = yaml.safe_load(
        (ROOT / "pipeline/conf/experiments/EXP001.yml").read_text(encoding="utf-8")
    )
    config["schema_version"] = 2
    config["data"] = {
        "mode": "raw",
        "manifest": "pipeline/" + OPERATIONAL_MANIFEST,
        "manifest_sha256": sha256(path),
        "release_id": manifest.release_id,
        "require_private": True,
        "canonical": {
            "profile": "operational_full",
            "certificate": REFERENCE,
            "certificate_sha256": sha256(cert_path),
        },
    }
    entry = yaml.safe_load((ROOT / "docs/experiments/registry.yml").read_text(encoding="utf-8"))[
        "experiments"
    ][0]
    entry.update(
        experiment_id=EID,
        experiment_slug="accept-cert",
        hypothesis_id="ACCEPT-H0",
        experiment_type="scientific",
        status="APPROVED",
        scientific_result="PENDING",
        protocol=f"docs/experiments/{EID}/SPECIFICATION.md",
        configuration=f"pipeline/conf/experiments/{EID}.yml",
        conclusions=f"docs/experiments/{EID}/CONCLUSIONS.md",
    )
    protocol = root / entry["protocol"]
    protocol.parent.mkdir(parents=True)
    protocol.write_text("Prueba artificial de compuerta; sin uso científico.\n", encoding="utf-8")
    config_path = root / entry["configuration"]
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    entry.update(protocol_sha256=sha256(protocol), configuration_sha256=sha256(config_path))
    registry = root / "docs/experiments/registry.yml"
    registry.write_text(
        yaml.safe_dump({"schema_version": 1, "experiments": [entry]}), encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "documentation.md").write_text("Cambio documental posterior al certificado.\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    monkeypatch.setattr(runner, "project_root", lambda: root / "pipeline")
    execute = runner.execute
    # La entrada Kedro permanece intacta; configurar solo raíz temporal y tracking desactivado.
    monkeypatch.setattr(runner, "execute", lambda eid: execute(eid, root=root, tracking=False))
    builds, loaded, prepared, fitted = [], [], [], []
    selected = {"artifact": artifact}

    def artificial_build(bundle, build_config, workspace, inventory):
        """Sustituir solo I/O de construcción; la certificación de consumo sigue real."""
        assert build_config == BuildConfig.operational_full()
        builds.append(build_config.payload())
        return selected["artifact"], audit

    def prepare_detector(run):
        """Detectar entrada a preparación sin crear matrices o ajustes científicos."""
        prepared.append(run.artifact.serialized_sha256)
        return run

    def fit_detector(run):
        """Observar la identidad efectiva en el punto normal de ajuste, sin ajustar."""
        assert run.table.shape == (242352, 52)
        assert sha256(run.artifact.path) == artifact.serialized_sha256
        assert run.lineage["canonical"]["semantic_digest"] == artifact.semantic_digest
        fitted.append((run.artifact.serialized_sha256, run.artifact.semantic_digest))
        return run

    monkeypatch.setattr(runner, "build", artificial_build)
    load = runner.load_canonical

    def load_detector(artifact):
        """Detectar la carga que valida también la matriz de predictores."""
        loaded.append(artifact.serialized_sha256)
        return load(artifact)

    monkeypatch.setattr(runner, "load_canonical", load_detector)
    monkeypatch.setattr(runner.engine, "prepare", prepare_detector)
    monkeypatch.setattr(runner.engine, "fit", fit_detector)
    for name in ("preflight", "predict", "evaluate"):
        monkeypatch.setattr(runner.engine, name, lambda run: run)
    return {
        "root": root,
        "config": config,
        "entry": entry,
        "registry": registry,
        "config_path": config_path,
        "certificate_path": cert_path,
        "certificate": certificate,
        "selected": selected,
        "artifact": artifact,
        "historical": historical,
        "builds": builds,
        "loaded": loaded,
        "prepared": prepared,
        "fitted": fitted,
    }


@pytest.mark.parametrize(
    "case,diagnostic",
    [
        ("valid", None),
        ("missing", "certificate_missing_or_unsafe"),
        ("failed_n3", "certificate_n3_not_approved"),
        ("historical", "consumed_serialized_identity_mismatch"),
        ("bytes", "consumed_artifact_integrity_failed"),
        ("semantic", "consumed_semantic_identity_mismatch"),
        ("certificate_hash", "certificate_file_hash_mismatch"),
        ("release", "recipe_release_mismatch"),
        ("profile", "certificate_profile_mismatch"),
        ("lock", "certificate_lock_mismatch"),
        ("legacy", "canonical_selection_missing"),
    ],
)
def test_normal_experiment_run_checks_consumed_identity_before_fit(
    repository: dict, case: str, diagnostic: str | None
) -> None:
    """La entrada Kedro y el runner completos hacen pasar o bloquear la compuerta real."""
    r = repository
    if case == "missing":
        r["certificate_path"].unlink()
    elif case == "failed_n3":
        r["certificate"]["n3"]["status"] = "FAILED"
        r["certificate_path"].write_text(json.dumps(r["certificate"]), encoding="utf-8")
        r["config"]["data"]["canonical"]["certificate_sha256"] = sha256(r["certificate_path"])
    elif case == "historical":
        r["selected"]["artifact"] = r["historical"]
    elif case == "bytes":
        changed = r["root"] / "altered-canonical.json"
        shutil.copyfile(r["artifact"].path, changed)
        with changed.open("ab") as stream:
            stream.write(b" ")
        r["selected"]["artifact"] = replace(r["artifact"], path=changed)
    elif case == "semantic":
        r["selected"]["artifact"] = replace(r["artifact"], semantic_digest="0" * 64)
    elif case == "certificate_hash":
        with r["certificate_path"].open("ab") as stream:
            stream.write(b" ")
    elif case == "release":
        r["config"]["data"]["release_id"] = "different-release"
    elif case == "profile":
        r["config"]["data"]["canonical"]["profile"] = "approved"
    elif case == "lock":
        with (r["root"] / "pipeline/uv.lock").open("ab") as stream:
            stream.write(b"\n")
    elif case == "legacy":
        r["config"]["schema_version"] = 1
        r["config"]["data"].pop("canonical")
        r["config"]["data"].pop("release_id")
    r["config_path"].write_text(yaml.safe_dump(r["config"]), encoding="utf-8")
    r["entry"]["configuration_sha256"] = sha256(r["config_path"])
    r["registry"].write_text(
        yaml.safe_dump({"schema_version": 1, "experiments": [r["entry"]]}), encoding="utf-8"
    )
    if case == "legacy":
        assert load_configuration(r["root"], r["entry"])["schema_version"] == 1
    catalog = DataCatalog({"params:experiment_id": MemoryDataset(EID)})
    if diagnostic is None:
        SequentialRunner().run(create_pipeline(), catalog)
        assert r["prepared"] == [r["artifact"].serialized_sha256]
        assert r["loaded"] == [r["artifact"].serialized_sha256]
        assert r["fitted"] == [(r["artifact"].serialized_sha256, r["artifact"].semantic_digest)]
    else:
        with pytest.raises(runner.ExecutionError, match=diagnostic):
            SequentialRunner().run(create_pipeline(), catalog)
        assert r["loaded"] == [] and r["prepared"] == [] and r["fitted"] == []
    inventories = list((r["root"] / f"docs/evidence/experiments/{EID}").glob("*/inventory.json"))
    assert len(inventories) == 1
    receipt = verify_execution(r["root"], inventories[0].relative_to(r["root"]).as_posix())
    assert receipt["diagnostic"] == diagnostic
    if diagnostic is None:
        lineage = json.loads((inventories[0].parent / "lineage.json").read_bytes())
        manifest_path = r["root"] / r["config"]["data"]["manifest"]
        manifest = ReleaseManifest.from_json(manifest_path.read_text(encoding="utf-8"))
        assert lineage["dataset_manifest_file_sha256"] == sha256(manifest_path)
        assert lineage["dataset_manifest_digest"] == manifest.manifest_sha256
        assert lineage["dataset_manifest_file_sha256"] != lineage["dataset_manifest_digest"]
        assert lineage["git_sha"] != lineage["canonical"]["certified_builder_git_sha"]
        assert all(
            row["canonical"]["profile"]["profile"] == "operational_full"
            for row in compare(r["root"])
        )
    else:
        assert Registry(r["root"]).get(EID)["status"] == "BLOCKED"


def test_versioned_operational_certificate_is_applicable_without_current_head_equality() -> None:
    """Leer la referencia auténtica y sus identidades sin consumir datos privados."""
    manifest_path = ROOT / "pipeline" / OPERATIONAL_MANIFEST
    certificate = ROOT / REFERENCE
    proof = load_certified_recipe(
        ROOT,
        {
            "mode": "raw",
            "release_id": "satd-raw-173d5856",
            "manifest": "pipeline/" + OPERATIONAL_MANIFEST,
            "manifest_sha256": sha256(manifest_path),
            "require_private": True,
            "canonical": {
                "profile": "operational_full",
                "certificate": REFERENCE,
                "certificate_sha256": sha256(certificate),
            },
        },
    )
    assert proof.config == BuildConfig.operational_full()
    assert proof.certificate["n3"]["certified_identity"]["rows"] == 242352


def test_legacy_receipts_remain_readable_and_unchanged() -> None:
    """No reinterpretar como digest explícito el campo ambiguo de evidencia anterior."""
    files = list((ROOT / "docs/evidence/experiments").glob("*/*/*.json"))
    before = {p: sha256(p) for p in files}
    rows = compare(ROOT)
    assert {r["experiment_id"] for r in rows} == {"EXP001", "EXP002"}
    assert all(
        r["dataset_sha256"]
        and r["dataset_manifest_file_sha256"] is None
        and r["dataset_manifest_digest"] is None
        for r in rows
    )
    assert {p: sha256(p) for p in files} == before
