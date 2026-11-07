"""Cohorte artificial adicional con municipios completos para probar bootstrap."""

import pandas as pd

from sat_dengue_pipeline.evaluation.paired import tables_from_prediction
from sat_dengue_pipeline.experiments.procedure import fit_procedure, predict_frozen
from sat_dengue_pipeline.experiments.roles import split_roles
from sat_dengue_pipeline.experiments.rolling import ExperimentData
from sat_dengue_pipeline.models.adapters import AdapterSpec

from .adapter_fixture import make_registry
from .experiment_fixture import make_experiment
from .procedure_fixture import make_procedure, threshold_policy


def make_evaluation(municipalities: int = 2):
    """Crear cohorte/decisiones ficticias; no copiar ninguna fila de V2.

    Args:
        municipalities: Dos o seis municipios para suficiencia/insuficiencia.

    Returns:
        Tablas separadas, decisiones congeladas y batch posterior.
    """
    codes = (
        ["50991", "73991"]
        if municipalities == 2
        else ["50991", "50992", "50993", "73991", "73992", "73993"]
    )
    departments = {
        code: dept
        for code, dept in zip(
            codes, ["50", "73"] if municipalities == 2 else ["50"] * 3 + ["73"] * 3, strict=True
        )
    }
    source = make_experiment(include_missing=False)
    mask = source.keys.municipality_code.eq("50998")
    keys, features, labels, controls = [], [], [], []
    for code in codes:
        keys.append(source.keys.loc[mask].assign(municipality_code=code))
        features.append(source.X.loc[mask])
        labels.append(source.y.loc[mask])
        controls.append(source.controls.loc[mask])
    data = ExperimentData(
        *(pd.concat(parts, ignore_index=True) for parts in (keys, features, labels, controls))
    )
    plan, _ = make_procedure()
    batches = split_roles(data, plan)
    fitted = fit_procedure(
        batches, plan, AdapterSpec("signal_double", "1"), make_registry(), threshold_policy()
    )
    batch = batches["evaluation"]
    output = predict_frozen(fitted, batch, expected_digest=fitted.decisions.digest)
    y, context, strata = (output.keys.copy() for _ in range(3))
    y["onset"] = batch.read_y()
    context["context_evaluable"] = True
    context["label_available_period"] = batch.keys.label_available_period
    strata["department_code"] = strata.municipality_code.map(departments)
    return tables_from_prediction(output, y, context, strata), fitted.decisions, batch
