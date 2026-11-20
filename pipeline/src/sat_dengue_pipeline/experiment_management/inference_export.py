"""Export the verified full-precision logistic T+2 adjustment from Kedro."""

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import KEYS, PREDICTORS
from sat_dengue_pipeline.domain.derived import declared_derived
from sat_dengue_pipeline.domain.temporal import TemporalPolicy, guard_development
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.factory.engine import FactoryRun
from sat_dengue_pipeline.models.logistic import LogisticOnsetAdapter, predict_exported
from sat_dengue_pipeline.raw.contract import sha256

from . import runner
from .evidence import exclusive_json, verify_execution
from .registry import confined


def validate_export_configuration(config: dict[str, Any]) -> None:
    """Require the real fixed-role logistic candidate for the T+2 export."""
    candidate = config["candidate"]
    if (
        config["schema_version"] != 2
        or config.get("protocol", "fixed_roles") != "fixed_roles"
        or config["data"]["mode"] != "raw"
        or config["horizons"] != [2]
        or (candidate["family"], candidate["adapter_version"]) != ("logistic_onset", "v1")
        or config["predictors"] != PREDICTORS
        or declared_derived(config["preparation"])
        or config.get("population") != {"department_codes": ["50", "73"]}
    ):
        raise ValueError("La exportación exige una logística T+2 real con el bloque climático")


def context_bytes(run: FactoryRun) -> bytes:
    """Keep only approved origin predictors after the threshold was frozen."""
    cutoff = run.temporal["2"]["support"]["threshold_selection"]["available"]
    policy = TemporalPolicy(run.config["reserved_start"])
    end = add_months(policy.reserved_start, -3)
    panel = run.table.loc[
        run.table.year_month.gt(cutoff) & run.table.year_month.le(end), [*KEYS, *PREDICTORS]
    ]
    guard_development(run.table[KEYS], panel[KEYS], (2,), policy)
    return panel.to_csv(index=False, lineterminator="\n").encode()


def verified_inference_digests(session: "runner.RegisteredExecution") -> dict[str, str]:
    """Verify export parity against the evaluation probabilities frozen by Kedro."""
    run = session.runs["legacy"]
    adapter = run.fitted[2].model.adapter
    if (
        not isinstance(adapter, LogisticOnsetAdapter)
        or adapter.fit_calls != 1
        or not run.prediction_complete.get(2)
        or adapter.model_sha256() != run.identities["2"]["model_json"]
    ):
        raise ValueError("El ajuste exportado no coincide con el modelo evaluado")
    state = adapter.inference_state()
    exported = predict_exported(run.batches[2]["evaluation"].X, state)
    expected = run.predictions[2].raw_probability
    if not exported.index.equals(expected.index) or not np.allclose(
        exported, expected, atol=1e-12, rtol=0
    ):
        raise ValueError("El estado exportado no reproduce las probabilidades de Kedro")
    return {
        "inference_model_sha256": stable_digest(state),
        "inference_context_sha256": hashlib.sha256(context_bytes(run)).hexdigest(),
    }


def export_fit(session: "runner.RegisteredExecution", receipt: dict[str, Any]) -> dict[str, str]:
    """Publish model and fit receipt atomically in the private execution workspace."""
    execution_id = session.workspace.name
    inventory = (session.folder / "inventory.json").relative_to(session.root).as_posix()
    if (
        not session.finalized
        or receipt != verify_execution(session.root, inventory)
        or receipt["status"] != "COMPLETED"
        or receipt["experiment_type"] != "scientific"
    ):
        raise ValueError("Se requiere una ejecución real completada y verificada")

    run = session.runs["legacy"]
    state = run.fitted[2].model.adapter.inference_state()
    expected = session.lineage["inference_model_sha256"]
    target = confined(
        session.root,
        f"pipeline/data/experiments/{execution_id}/inference-fit",
        "pipeline/data/experiments",
        exists=False,
    )
    if target.exists():
        raise FileExistsError(target)
    with TemporaryDirectory(dir=target.parent, prefix=".fit-") as directory:
        stage = Path(directory) / target.name
        stage.mkdir(mode=0o700)
        model = stage / "model.json"
        exclusive_json(model, state)
        if sha256(model) != expected:
            raise ValueError("El modelo escrito no coincide con el linaje firmado")
        context = stage / "context.csv"
        context.write_bytes(context_bytes(run))
        if sha256(context) != session.lineage["inference_context_sha256"]:
            raise ValueError("El contexto canónico cambió durante la exportación")
        stage.rename(target)
    return {"status": "EXPORTED", "execution_id": execution_id, "model_sha256": expected}
