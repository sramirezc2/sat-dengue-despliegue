"""Construcción y validación del contrato de ranking, sin desempeño observado."""

from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.models.logistic import canonical_json
from sat_dengue_pipeline.pipelines.deployment_publication.contract import decode_json
from sat_dengue_pipeline.pipelines.deployment_publication.package import (
    PublicationFile,
    PublicationPackage,
)

from .configuration import (
    BASE,
    CONTRACT,
    GENERATED,
    LEGEND,
    PROCEDURE,
    RECIPE_SHA,
    digest,
    procedure,
    recipe,
    sha,
)
from .frozen import FrozenLogistic

NAMES = tuple(f"prioridades_T2_2025-{m:02d}.json" for m in range(1, 13))


def load_schema() -> dict:
    """Leer snapshot exportado del contrato público; nunca importar app/."""
    return decode_json(Path(__file__).with_name("ranking.schema.json").read_bytes())


def validate_document(document: dict, schema: dict) -> None:
    """Validar forma y relaciones globales imposibles de inferir de una fila."""
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)
    origin = add_months(document["target_period"], -2)
    if document["reference_period"] != origin or document["data_cutoff"] != origin:
        raise ValueError("Calendario de ranking incompatible")
    rows = document["municipalities"]
    codes = [r["municipality_code"] for r in rows]
    if codes != sorted(set(codes)) or {
        d: sum(r["department_code"] == d for r in rows) for d in ("50", "73")
    } != {"50": 29, "73": 47}:
        raise ValueError("Universo territorial incompatible")
    ranks = []
    for row in rows:
        d = row["department_code"]
        if (
            row["municipality_code"][:2] != d
            or row["department_name"] != {"50": "Meta", "73": "Tolima"}[d]
        ):
            raise ValueError("Identidad territorial incompatible")
        rank = row["risk_rank"]
        eligible = row["eligibility_status"] == "ELIGIBLE"
        if eligible != (rank is not None) or eligible != (row["ineligibility_reason"] is None):
            raise ValueError("Elegibilidad incoherente")
        if row["selected_for_attention"] != (rank is not None and rank <= 8):
            raise ValueError("Selección incompatible con la posición")
        if eligible:
            ranks.append(rank)
    if sorted(ranks) != list(range(1, int(document["eligible_count"]) + 1)):
        raise ValueError("Ranking incompleto o duplicado")


def document(
    rows: list[dict],
    feature_sha: str,
    target: str,
    model: FrozenLogistic,
    data_version: str,
    data_kind: str,
) -> dict:
    """Proyectar exclusivamente prioridades y trazabilidad permitidas."""
    config = recipe()
    p = model.payload
    provenance = p["provenance"]
    trace = {
        "recipe_sha256": RECIPE_SHA,
        "recipe_commit": BASE,
        "model_family": "logistic_onset",
        "adapter_version": "v1",
        "library_version": "1.7.2",
        "artifact_sha256": model.artifact_sha256,
        "effective_state_sha256": p["effective_state_sha256"],
        "training_keys_sha256": p["training_keys_sha256"],
        "preparation_sha256": digest(config["preparation"]),
        "predictors_sha256": digest(config["predictors"]),
        "raw_manifest_sha256": provenance["raw_manifest_sha256"],
        "code_sha": provenance["code_sha"],
        "code_tree_sha256": provenance["code_tree_sha256"],
        "lock_sha256": provenance["lock_sha256"],
        "feature_sha256": feature_sha,
        "procedure_id": PROCEDURE,
        "procedure_sha256": digest(procedure()),
        "training_target_start": "2012-01",
        "training_target_end": "2024-09",
        "training_available_end": "2024-10",
        "first_origin": "2024-11",
        "artifact_contract": p["contract"],
    }
    origin = add_months(target, -2)
    return {
        "schema_version": CONTRACT,
        "reference_period": origin,
        "target_period": target,
        "horizon": "T2",
        "data_cutoff": origin,
        "logical_generated_at": GENERATED,
        "data_version": data_version,
        "data_kind": data_kind,
        "selection_budget": 8,
        "selection_scope": "META_TOLIMA_GLOBAL",
        "population_count": 76,
        "eligible_count": sum(r["risk_rank"] is not None for r in rows),
        "tie_break": "SCORE_DESC_DIVIPOLA_ASC",
        "trace": trace,
        "governance": {
            "report_selection": "SELECTED",
            "historical_reproduction": "APPROVED",
            "operational_use": "NOT_AUTHORIZED",
            "champion_status": "NOT_SELECTED",
            "limitation": LEGEND,
        },
        "municipalities": rows,
    }


def build_package(documents: list[dict]) -> PublicationPackage:
    """Exigir los doce meses completos antes de preparar una transacción."""
    files = tuple(
        sorted(
            (
                PublicationFile(
                    f"prioridades_{d['horizon']}_{d['target_period']}.json", canonical_json(d)
                )
                for d in documents
            ),
            key=lambda f: f.name,
        )
    )
    manifest = {
        "schema": CONTRACT,
        "candidate": "logistic_onset",
        "procedure": PROCEDURE,
        "artifact_sha256": documents[0]["trace"]["artifact_sha256"] if documents else "",
        "files": [
            {"name": f.name, "size_bytes": len(f.content), "sha256": sha(f.content)} for f in files
        ],
    }
    package = PublicationPackage(files, canonical_json(manifest), {})
    validate_package(package, load_schema())
    return package


def validate_package(package: PublicationPackage, schema: dict) -> dict:
    """Revalidar calendario completo, linaje común y hashes de cada documento."""
    manifest = decode_json(package.manifest)
    if set(manifest) != {"schema", "candidate", "procedure", "artifact_sha256", "files"} or (
        manifest["schema"] != CONTRACT
        or manifest["candidate"] != "logistic_onset"
        or manifest["procedure"] != PROCEDURE
        or tuple(f.name for f in package.files) != NAMES
    ):
        raise ValueError("Manifiesto o paquete de prioridades incompleto")
    expected = [
        {"name": f.name, "size_bytes": len(f.content), "sha256": sha(f.content)}
        for f in package.files
    ]
    if manifest["files"] != expected:
        raise ValueError("SHA-256 o tamaño incompatible")
    common = None
    for f in package.files:
        d = decode_json(f.content)
        validate_document(d, schema)
        if f.name != f"prioridades_{d['horizon']}_{d['target_period']}.json" or (
            d["trace"]["artifact_sha256"] != manifest["artifact_sha256"]
        ):
            raise ValueError("Identidad del documento incompatible")
        identity = {k: v for k, v in d["trace"].items() if k != "feature_sha256"}
        identity.update(data_version=d["data_version"], data_kind=d["data_kind"])
        if common is not None and identity != common:
            raise ValueError("Paquete mezcla modelos, datos o procedimientos")
        common = identity
    return manifest
