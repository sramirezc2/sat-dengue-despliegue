"""Shared logistic preparation and scoring for fitted artifacts."""

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit

from .canonical import PREDICTORS
from .features import validate_feature_frame, validate_probabilities

ZONES = {"EXITO": 0, "SEGURIDAD": 1, "ALERTA": 2, "EXCESO": 3}
MODOS_FIJOS = (
    "early_stopping",
    "hyperparameter_search",
    "class_balancing",
    "refit",
    "seed_selection",
)


def canonical_json(value: Any) -> bytes:
    """Serializar estado JSON con floats finitos y orden estable.

    Args:
        value: Estado serializable.

    Returns:
        Bytes UTF-8 deterministas.
    """
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def validate_settings(
    settings: dict[str, Any],
    derived: tuple[str, ...],
    *,
    family: str,
    version: str,
    library_version: str,
) -> None:
    """Require the approved logistic configuration and feature layout."""
    if set(settings) != {"candidate", "preparation", "predictors"}:
        raise ValueError("Configuración de adaptador incompleta o adicional")
    candidate = settings["candidate"]
    preparation = settings["preparation"]
    predictors = settings["predictors"]
    if (
        not predictors
        or predictors != [p for p in PREDICTORS if p in predictors]
        or family != candidate["family"]
        or version != candidate["adapter_version"]
        or candidate["library"] != "scikit-learn"
        or candidate["library_version"] != library_version
        or any(candidate[name] is not False for name in MODOS_FIJOS)
    ):
        raise ValueError("Identidad, versión o modo del candidato no autorizado")
    c, max_iter = candidate["C"], candidate["max_iter"]
    if not (isinstance(c, (int, float)) and c > 0) or type(max_iter) is not int or max_iter < 1:
        raise ValueError("Regularización o iteraciones inválidas")
    if (
        preparation["zone_encoding"] != "fixed_onehot"
        or preparation["zone_mapping"] != ZONES
        or preparation["zone_columns"] != ["zona_canal_t__" + z for z in ZONES]
        or preparation["missing"] != "error"
        or preparation["scaling"] != "standard_train"
        or preparation["imputation"] != "none"
        or preparation["matrix_dtype"] != "float64"
        or type(preparation["variables_g"]) is not bool
        or preparation["channel_budget"] is not False
    ):
        raise ValueError("Preparación diferente de la autorizada")
    expected = [
        column
        for name in predictors
        for column in (preparation["zone_columns"] if name == "zona_canal_t" else [name])
    ]
    # Los bloques derivados van al final y solo si la receta los declara; sin
    # ellos la matriz es idéntica a la histórica. La comprobación que vale es
    # la de `matrix_columns`: compara lo que la receta escribió contra lo que
    # los interruptores resuelven, que son dos cosas distintas.
    if preparation["matrix_columns"] != [*expected, *derived]:
        raise ValueError("Orden o cardinalidad de matriz interna alterados")
    if not set(preparation["log1p_columns"]) <= set(predictors) - {"zona_canal_t"}:
        raise ValueError("log1p declarado sobre columnas inexistentes")


def logistic_matrix(
    X: pd.DataFrame,
    preparation: dict[str, Any],
    predictors: list[str],
    derived: tuple[str, ...],
) -> np.ndarray:
    """Apply the canonical zone and log1p transforms to a validated frame."""
    log1p = set(preparation["log1p_columns"])
    parts = []
    # Las derivadas entran crudas: son márgenes con signo y log1p no está
    # definido en los negativos. La estandarización del fold las escala.
    for name in [*predictors, *derived]:
        if name == "zona_canal_t":
            codes = X[name].map(ZONES).to_numpy(dtype=int)
            parts.append(np.eye(len(ZONES))[codes])
        else:
            col = X[name].to_numpy(dtype=float)
            parts.append((np.log1p(np.clip(col, 0, None)) if name in log1p else col).reshape(-1, 1))
    result = np.concatenate(parts, axis=1)
    if (
        result.shape != (len(X), len(preparation["matrix_columns"]))
        or not np.isfinite(result).all()
    ):
        raise ValueError("Matriz interna inválida o no finita")
    return result


def load_inference_state(path: Path, expected_sha256: str) -> dict[str, Any]:
    """Read a bounded JSON model pinned by a trusted SHA-256."""
    with path.open("rb") as stream:
        data = stream.read(128 * 1024 + 1)
    if len(data) > 128 * 1024 or hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("El archivo de modelo no coincide con la huella esperada")
    state = json.loads(data)
    if not isinstance(state, dict):
        raise ValueError("Estado logístico exportado inválido")
    return state


def validate_state_version(state: dict[str, Any]) -> None:
    """Read only the supported binary logistic export format."""
    if state.get("schema_version") != 1 or state.get("classes") != [0, 1]:
        raise ValueError("Versión o clases del modelo exportado incompatibles")


def score_matrix(matrix: np.ndarray, index: pd.Index, state: dict[str, Any]) -> pd.Series:
    """Score an already prepared matrix with the exported parameters."""
    coef, mean, std = (np.asarray(state[key], dtype=float) for key in ("coef", "mean", "std"))
    intercept = float(state["intercept"])
    if (
        any(v.shape != (matrix.shape[1],) or not np.isfinite(v).all() for v in (coef, mean, std))
        or (std <= 0).any()
        or not np.isfinite(intercept)
    ):
        raise ValueError("Coeficientes o escalado del modelo exportado inválidos")
    scores = ((matrix - mean) / std) @ coef + intercept
    if not np.isfinite(scores).all():
        raise ValueError("Puntuación logística no finita")
    probability = pd.Series(expit(scores), index=index)
    validate_probabilities(probability, index)
    return probability


def predict_exported(X: pd.DataFrame, state: dict[str, Any]) -> pd.Series:
    """Score the served logistic model from canonical predictors without a trainer."""
    validate_state_version(state)
    settings = state["adapter"]
    preparation = settings["preparation"]
    predictors = settings["predictors"]
    if preparation["variables_g"] or type(state["seed"]) is not int or state["seed"] < 0:
        raise ValueError("El ajuste exportado usa una preparación no admitida")
    validate_settings(settings, (), family="logistic_onset", version="v1", library_version="1.7.2")
    validate_feature_frame(X, None, predictors=tuple(PREDICTORS), derived=())
    return score_matrix(logistic_matrix(X, preparation, predictors, ()), X.index, state)
