"""Recetas explícitas de brazos, cortes y semillas; sin aprobar decisiones humanas."""

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.experiments.rolling import stable_digest
from sat_dengue_pipeline.factory.configuration import temporal_plan


def validate_scientific(configuration: dict[str, Any]) -> None:
    """Validar el diseño completo antes de adquirir, usando la autoridad temporal existente.

    Args:
        configuration: Receta V3; las políticas pendientes se representan con null.
    """
    science = configuration["scientific_evaluation"]
    stable_digest(science)
    schema = json.loads(Path(__file__).with_name("configuration.schema.json").read_bytes())
    if list(Draft202012Validator(schema).iter_errors(science)):
        raise ValueError("Configuración científica cerrada inválida")
    horizons = {str(h) for h in configuration["horizons"]}
    for name in ("channel_fraction_grid", "budget_rate_by_horizon"):
        if set(science[name]) != horizons:
            raise ValueError("Política científica sin correspondencia de horizontes")
    for grid in science["channel_fraction_grid"].values():
        if grid is not None and (grid != sorted(set(grid)) or not grid):
            raise ValueError("Grilla del canal repetida o desordenada")
    if science["seeds"] != sorted(set(science["seeds"])):
        raise ValueError("Semillas repetidas o desordenadas")
    for collection in ("arms", "cuts"):
        names = [item["id"] for item in science[collection]]
        if len(names) != len(set(names)):
            raise ValueError("Identidades de brazo/corte repetidas")
    from sat_dengue_pipeline.experiments.weighting import validate_weighting

    union = set()
    for arm in science["arms"]:
        weighting = arm.get(
            "training_weighting", configuration.get("training_weighting", {"method": "uniform"})
        )
        validate_weighting(weighting)
        if (
            weighting["method"] != "uniform"
            and configuration["candidate"]["family"] != "logistic_onset"
        ):
            raise ValueError("El adaptador no soporta ponderación de entrenamiento")
        predictors = arm["predictors"]
        if not predictors or predictors != [p for p in PREDICTORS if p in predictors]:
            raise ValueError("Predictores de brazo fuera del contrato canónico")
        union.update(predictors)
    if configuration["predictors"] != [p for p in PREDICTORS if p in union]:
        raise ValueError("La receta debe declarar exactamente la unión de sus brazos")
    weighting_comparison = any("training_weighting" in arm for arm in science["arms"])
    if weighting_comparison and not all("training_weighting" in arm for arm in science["arms"]):
        raise ValueError("Cada brazo debe declarar explícitamente su política de pesos")
    if weighting_comparison and any(
        arm["predictors"] != science["arms"][0]["predictors"] for arm in science["arms"]
    ):
        raise ValueError("La comparación de pesos exige exactamente los mismos predictores")
    seen: dict[str, set[str]] = {h: set() for h in horizons}
    for cut in science["cuts"]:
        if set(cut["roles_by_horizon"]) != horizons:
            raise ValueError("Calendario sin correspondencia de horizontes")
        for horizon in configuration["horizons"]:
            plan = temporal_plan(
                {**configuration, "roles_by_horizon": cut["roles_by_horizon"]}, horizon
            )
            window = plan.windows[-1]
            import pandas as pd

            periods = set(pd.period_range(window.start, window.end, freq="M").astype(str))
            if seen[str(horizon)] & periods:
                raise ValueError("Objetivos de evaluación repetidos entre cortes")
            seen[str(horizon)] |= periods
    if "secondary_t2" in science["readings"] and 2 not in configuration["horizons"]:
        raise ValueError("Lectura secundaria solo existe en T+2")


def variants(configuration: dict[str, Any]) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    """Derivar recetas efectivas deterministas sin cambiar hiperparámetros o elegir semillas.

    Args:
        configuration: Plantilla congelada con todos los brazos, cortes y semillas.

    Returns:
        Identidad, receta efectiva y dimensiones; una instancia independiente por ajuste.
    """
    science = configuration["scientific_evaluation"]
    result = []
    populations = (
        ["common"]
        if any("training_weighting" in arm for arm in science["arms"])
        else ["native", "common"]
        if len(science["arms"]) > 1
        else ["native"]
    )
    for cut in science["cuts"]:
        for seed in science["seeds"]:
            for arm in science["arms"]:
                for population in populations:
                    for reading in science["readings"]:
                        config = copy.deepcopy(configuration)
                        config["roles_by_horizon"] = cut["roles_by_horizon"]
                        config["seed"] = seed
                        config["predictors"] = arm["predictors"]
                        config["horizons"] = (
                            [2] if reading == "secondary_t2" else configuration["horizons"]
                        )
                        config["preparation"]["matrix_columns"] = [
                            column
                            for name in arm["predictors"]
                            for column in (
                                config["preparation"]["zone_columns"]
                                if name == "zona_canal_t"
                                else [name]
                            )
                        ]
                        config["calibration"]["parameters"]["random_state"] = seed
                        candidate = config["candidate"]
                        if "training_weighting" in arm:
                            config["training_weighting"] = copy.deepcopy(arm["training_weighting"])
                        if candidate["family"] == "xgboost_onset":
                            for name in ("seed", "random_state"):
                                candidate["parameters"][name] = seed
                                candidate["expected_native_configuration"]["learner"][
                                    "generic_param"
                                ][name] = str(seed)
                            candidate["expected_native_configuration"]["learner"][
                                "learner_model_param"
                            ]["num_feature"] = str(len(config["preparation"]["matrix_columns"]))
                        dimensions = {
                            "cut": cut["id"],
                            "seed": seed,
                            "arm": arm["id"],
                            "reading": reading,
                            "population": population,
                        }
                        config["scientific_dimensions"] = dimensions
                        name = f"{cut['id']}.{seed}.{arm['id']}.{reading}.{population}"
                        result.append((name, config, dimensions))
    return result


def verify_weighting_cohorts(runs: dict[str, Any]) -> None:
    """Exigir los mismos X, claves y etiquetas productoras antes de cualquier fit.

    Args:
        runs: Variantes después del preflight; evaluation.y permanece diferida.
    """
    groups = {}
    for run in runs.values():
        if "training_weighting" not in run.config:
            continue
        dimensions = run.config["scientific_dimensions"]
        for h, batches in run.batches.items():
            group = (
                dimensions["cut"],
                dimensions["seed"],
                dimensions["reading"],
                dimensions["population"],
                h,
            )
            for role, batch in batches.items():
                key = (*group, role)
                if key not in groups:
                    groups[key] = batch
                    continue
                other = groups[key]
                if not batch.keys.equals(other.keys) or not batch.X.equals(other.X):
                    raise ValueError("Brazos de ponderación con claves o predictores distintos")
                if role != "evaluation" and not batch.read_y().equals(other.read_y()):
                    raise ValueError("Brazos de ponderación con etiquetas distintas")
