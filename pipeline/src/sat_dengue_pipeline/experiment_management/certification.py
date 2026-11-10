"""Vincular una receta real a N=3 aprobado y al artefacto exacto que consumirá."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from sat_dengue_pipeline.acquisition.contracts import ReleaseManifest, ResolvedBundle
from sat_dengue_pipeline.acquisition.raw_manifest import canonical_build_config
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.raw.contract import BuildConfig, sha256
from sat_dengue_pipeline.raw.serialization import CanonicalArtifact, verify_artifact

from .registry import confined


class CertificationError(ValueError):
    """Diagnóstico público controlado, sin excepciones ni rutas privadas de proveedores."""

    def __init__(self, code: str) -> None:
        """Conservar el motivo concreto de la compuerta de certificación."""
        self.code = code
        super().__init__(code)


def require(condition: bool, code: str) -> None:
    """Detener la ejecución antes del consumidor con un motivo controlado."""
    if not condition:
        raise CertificationError(code)


@dataclass(frozen=True)
class CertifiedRecipe:
    """Identidades congeladas de receta, release, constructor y referencia N=3."""

    manifest: ReleaseManifest
    config: BuildConfig
    certificate: dict
    reference: str
    certificate_sha256: str
    manifest_file_sha256: str


def load_certified_recipe(root: Path, data: dict) -> CertifiedRecipe:
    """Validar N=3 e identidades aplicables antes de adquirir o preparar datos.

    Args:
        root: Repositorio de la receta aprobada.
        data: Selección declarativa congelada con los hashes de archivo.

    Returns:
        Referencia verificada sin exigir igualdad entre HEAD y el commit histórico.
    """
    require(bool(data.get("release_id") and data.get("canonical")), "canonical_selection_missing")
    selection = data["canonical"]
    config = canonical_build_config(selection["profile"])
    manifest_path = confined(root, data["manifest"], "pipeline/conf/releases")
    manifest = ReleaseManifest.from_json(manifest_path.read_text(encoding="utf-8"))
    file_hash = sha256(manifest_path)
    require(file_hash == data["manifest_sha256"], "manifest_file_hash_mismatch")
    require(manifest.release_id == data["release_id"], "recipe_release_mismatch")
    try:
        path = confined(root, selection["certificate"], "docs/evidence")
    except ValueError:
        raise CertificationError("certificate_missing_or_unsafe") from None
    require(path.stat().st_size <= 512_000, "certificate_too_large")
    require(sha256(path) == selection["certificate_sha256"], "certificate_file_hash_mismatch")
    try:
        certificate = json.loads(path.read_bytes())
        require(
            certificate["schema"] == "sat-dengue.full-canonical-certification/v1",
            "certificate_format_unsupported",
        )
        n3 = certificate["n3"]
        require(
            certificate["status"] == n3["status"] == "PASSED"
            and n3["repetitions"] == n3["independent_processes"] == 3
            and n3["all_bytes_schema_keys_audits_exactly_equal"] is True,
            "certificate_n3_not_approved",
        )
        require(
            certificate["scientific_review"]["recommendation"]
            in {"APPROVED", "APPROVED_WITH_LIMITATIONS"},
            "certificate_review_not_approved",
        )
        require(certificate["profile"] == config.payload(), "certificate_profile_mismatch")
        require(
            certificate["configured_operational_manifest_file_sha256"] == file_hash
            and certificate["manifest_sha256"] == manifest.manifest_sha256,
            "certificate_manifest_mismatch",
        )
        raw = certificate["preflight"]
        require(
            (raw["release_id"], raw["revision"]) == (manifest.release_id, manifest.revision)
            and {f["logical_name"]: (f["size_bytes"], f["sha256"]) for f in raw["files"]}
            == {f.logical_name: (f.size_bytes, f.sha256) for f in manifest.files},
            "certificate_raw_identity_mismatch",
        )
        require(
            certificate["lock_sha256"] == sha256(root / "pipeline/uv.lock"),
            "certificate_lock_mismatch",
        )
        require(
            re.fullmatch(r"[0-9a-f]{40}", certificate["source_head"]) is not None,
            "certificate_builder_identity_missing",
        )
        identity = n3["certified_identity"]
        require(
            (identity["start"], identity["end"], identity["municipalities"], identity["rows"])
            == (
                config.start,
                config.end,
                config.municipalities,
                config.municipalities * len(config.periods),
            ),
            "certificate_coverage_mismatch",
        )
        require(
            n3["serialized_hashes"] == [identity["serialized_sha256"]] * 3
            and n3["semantic_digests"] == [identity["semantic_digest"]] * 3
            and stable_digest(n3["audit"]) == n3["audit_sha256"],
            "certificate_n3_identity_mismatch",
        )
    except (KeyError, TypeError, json.JSONDecodeError):
        raise CertificationError("certificate_incomplete") from None
    return CertifiedRecipe(
        manifest,
        config,
        certificate,
        selection["certificate"],
        selection["certificate_sha256"],
        file_hash,
    )


def verify_consumed(
    proof: CertifiedRecipe, bundle: ResolvedBundle, artifact: CanonicalArtifact, audit: dict
) -> dict:
    """Verificar los bytes realmente consumidos antes de load_canonical y matrices."""
    manifest = proof.manifest
    require(
        bundle.release_id == manifest.release_id
        and bundle.manifest_sha256 == manifest.manifest_sha256
        and {f.logical_name: (f.size_bytes, f.sha256) for f in bundle.files}
        == {f.logical_name: (f.size_bytes, f.sha256) for f in manifest.files},
        "consumed_release_mismatch",
    )
    identity = proof.certificate["n3"]["certified_identity"]
    require(
        artifact.serialized_sha256 == identity["serialized_sha256"],
        "consumed_serialized_identity_mismatch",
    )
    require(
        artifact.semantic_digest == identity["semantic_digest"],
        "consumed_semantic_identity_mismatch",
    )
    try:
        verify_artifact(artifact)
    except (ValueError, OSError, KeyError):
        raise CertificationError("consumed_artifact_integrity_failed") from None
    require(audit == proof.certificate["n3"]["audit"], "consumed_audit_mismatch")
    return {
        "profile": proof.config.payload(),
        "coverage": audit["coverage"],
        "certificate": proof.reference,
        "certificate_file_sha256": proof.certificate_sha256,
        "certified_builder_git_sha": proof.certificate["source_head"],
        "builder_lock_sha256": proof.certificate["lock_sha256"],
        "builder_config_digest": stable_digest(proof.config.payload()),
        "semantic_digest": artifact.semantic_digest,
        "serialized_sha256": artifact.serialized_sha256,
        "manifest_file_sha256": proof.manifest_file_sha256,
        "manifest_digest": manifest.manifest_sha256,
    }
