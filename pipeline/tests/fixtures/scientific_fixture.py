"""Recetas técnicas temporales: ninguna entrada científica real o aprobada del equipo."""

import copy
import shutil
from pathlib import Path

import yaml

from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.raw.contract import sha256

ROOT = Path(__file__).resolve().parents[3]


def recipe() -> dict:
    """Preparar dos brazos mínimos para verificar selección de variables y población común."""
    config = yaml.safe_load(
        (ROOT / "pipeline/conf/experiments/EXP001.yml").read_text(encoding="utf-8")
    )
    epi = ["dengue_notifications_count", "total_notifications_count", "month_of_year"]
    climate = [p for p in PREDICTORS if p in epi + ["rain_mm_month_sum"]]
    config["schema_version"] = 3
    config["predictors"] = climate
    config["preparation"]["matrix_columns"] = climate
    config["candidate"]["expected_native_configuration"]["learner"]["learner_model_param"][
        "num_feature"
    ] = str(len(climate))
    config["scientific_evaluation"] = {
        "contract": {
            "path": "docs/experiments/contrato.md",
            "sha256": sha256(ROOT / "docs/experiments/contrato.md"),
        },
        "readings": ["primary", "secondary_t2"],
        "seeds": [53],
        "arms": [{"id": "epi", "predictors": epi}, {"id": "climate", "predictors": climate}],
        "cuts": [{"id": "cut2024", "roles_by_horizon": copy.deepcopy(config["roles_by_horizon"])}],
        "channel_fraction_grid": {"1": [0.0, 0.5, 1.0, 2.0, 3.0], "2": [0.0, 0.5, 1.0, 2.0, 3.0]},
        "channel_selection": "max_f1_then_fewer_alerts_then_larger_fraction_on_threshold_selection",
        "budget_rate_by_horizon": {"1": 1.0, "2": 1.0},
        "budget_rule": "fixed_rate_monthly_department_cap_floor_ties_by_municipality",
        "consistency_rule": "strict_majority_min_three",
        "consistency_vote": "both_rules_cumple",
        "uncertainty": {
            "method": "paired_target_month_bootstrap",
            "replicates": 2000,
            "seed": 42,
            "level": 0.95,
        },
    }
    return config


def repository(root: Path) -> tuple[dict, dict]:
    """Materializar registro y aprobación solo técnica en un repositorio temporal aislado."""
    config = recipe()
    document = yaml.safe_load((ROOT / "docs/experiments/registry.yml").read_text(encoding="utf-8"))
    entry = copy.deepcopy(document["experiments"][0])
    eid = "SYNTHSCIENCE"
    entry.update(
        experiment_id=eid,
        experiment_slug="synth-science",
        hypothesis_id="SYNTH-H0",
        status="APPROVED",
        experiment_type="synthetic_fixture",
        scientific_result="NOT_APPLICABLE",
        configuration=f"pipeline/conf/experiments/{eid}.yml",
        protocol=f"docs/experiments/{eid}/SPECIFICATION.md",
        conclusions=f"docs/experiments/{eid}/CONCLUSIONS.md",
    )
    for name, text in [
        (entry["protocol"], "Aceptación técnica artificial; no aprobación científica.\n"),
        (entry["configuration"], yaml.safe_dump(config)),
    ]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (root / "docs/experiments/registry.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "experiments": [
                    {
                        **entry,
                        "protocol_sha256": sha256(root / entry["protocol"]),
                        "configuration_sha256": sha256(root / entry["configuration"]),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    shutil.copyfile(ROOT / "docs/experiments/contrato.md", root / "docs/experiments/contrato.md")
    return config, entry
