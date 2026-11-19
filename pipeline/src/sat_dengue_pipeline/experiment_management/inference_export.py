"""Export the verified full-precision logistic T+2 adjustment from Kedro."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

import numpy as np

from sat_dengue_pipeline.domain.canonical import CLIMATE
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.models.logistic import LogisticOnsetAdapter, predict_exported
from sat_dengue_pipeline.raw.contract import sha256

from .evidence import exclusive_json, verify_execution
from .registry import confined

if TYPE_CHECKING:
    from .runner import RegisteredExecution


def validate_export_configuration(config: dict[str, Any]) -> None:
    """Require the real fixed-role logistic candidate for the T+2 export."""
    candidate = config["candidate"]
    if (
        config["schema_version"] != 2
        or config.get("protocol", "fixed_roles") != "fixed_roles"
        or config["data"]["mode"] != "raw"
        or config["horizons"] != [2]
        or (candidate["family"], candidate["adapter_version"]) != ("logistic_onset", "v1")
        or not set(CLIMATE) <= set(config["predictors"])
    ):
        raise ValueError("La exportación exige una logística T+2 real con el bloque climático")


def verified_inference_digest(session: "RegisteredExecution") -> str:
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
    return stable_digest(state)


def export_fit(session: "RegisteredExecution", receipt: dict[str, Any]) -> dict[str, str]:
    """Publish model and fit receipt atomically in the private execution workspace."""
    execution_id = session.workspace.name
    experiment_id = session.entry["experiment_id"]
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
    fit = {
        "experiment_id": experiment_id,
        "execution_id": execution_id,
        "horizon": 2,
        "execution_signature": receipt["execution_signature"],
        "configuration_sha256": receipt["configuration_sha256"],
        "protocol_sha256": receipt["protocol_sha256"],
        "training_release_sha256": session.lineage["dataset_manifest_file_sha256"],
        "training_available_through": run.temporal["2"]["support"]["train"]["available"],
        "model_sha256": expected,
        "evaluated_model_sha256": run.identities["2"]["model_json"],
    }
    with TemporaryDirectory(dir=target.parent, prefix=".fit-") as directory:
        stage = Path(directory) / target.name
        stage.mkdir(mode=0o700)
        model = stage / "model.json"
        exclusive_json(model, state)
        if sha256(model) != expected:
            raise ValueError("El modelo escrito no coincide con el linaje firmado")
        exclusive_json(stage / "fit.json", fit)
        stage.rename(target)
    return {"status": "EXPORTED", "execution_id": execution_id, "model_sha256": expected}
