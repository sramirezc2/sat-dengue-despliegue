"""Pesos de ajuste por historia disponible del fold, sin acceso a otros roles."""

import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd

from sat_dengue_pipeline.domain.calendar import validate_period
from sat_dengue_pipeline.domain.temporal import TemporalPolicy


def validate_weighting(configuration: dict[str, Any]) -> None:
    """Aceptar únicamente peso uniforme o recencia exponencial fija de 36 meses."""
    if not isinstance(configuration, dict) or configuration not in (
        {"method": "uniform"},
        {"method": "exponential_recency", "half_life_months": 36},
    ):
        raise ValueError("Ponderación cerrada inválida; solo uniform o exponential_recency de 36m")
    if configuration["method"] == "exponential_recency" and (
        type(configuration["half_life_months"]) is not int
    ):
        raise ValueError("Vida media debe ser el entero 36")


def training_weights(
    keys: pd.DataFrame, configuration: dict[str, Any]
) -> tuple[pd.Series, dict[str, Any]]:
    """Calcular pesos solo con las claves de entrenamiento ya autorizadas.

    Args:
        keys: Claves del train efectivo, después de sus guards de madurez.
        configuration: Política cerrada; nunca recibe filas de evaluación.

    Returns:
        Pesos con media uno y resumen sin filas. El peso crudo más reciente es
        uno; al normalizar, su peso aplicado puede superar uno.
    """
    validate_weighting(configuration)
    if keys.empty or "target_period" not in keys or not keys.index.is_unique:
        raise ValueError("Claves de entrenamiento vacías o inválidas")
    policy = TemporalPolicy()
    for column in ("origin_period", "target_period", "label_available_period"):
        if column in keys:
            for period in keys[column]:
                validate_period(period)
            if keys[column].ge(policy.reserved_start).any():
                raise ValueError("Periodo reservado en ponderación de entrenamiento")
    periods = pd.PeriodIndex(keys.target_period, freq="M").asi8
    age = periods.max() - periods
    raw = (
        np.ones(len(keys), dtype=float)
        if configuration["method"] == "uniform"
        else np.exp2(-age.astype(float) / configuration["half_life_months"])
    )
    weights = pd.Series(raw / raw.mean(), index=keys.index, name="sample_weight")
    payload = {"keys": keys.to_dict("records"), "weights": weights.tolist()}
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return weights, {
        "policy": configuration.copy(),
        "normalization": "mean_one_within_training_fold",
        "rows": len(keys),
        "reference_target": str(keys.target_period.max()),
        "oldest_target": str(keys.target_period.min()),
        "raw_latest_weight": float(raw[age == 0][0]),
        "raw_mean": float(raw.mean()),
        "min": float(weights.min()),
        "max": float(weights.max()),
        "mean": float(weights.mean()),
        "sum": float(weights.sum()),
        "effective_sample_size": float(weights.sum() ** 2 / np.square(weights).sum()),
        "keyed_weights_sha256": digest,
        "application": "model_fit_only",
    }


def validate_sample_weight(weights: pd.Series, index: pd.Index) -> None:
    """Rechazar pesos desalineados, no numéricos, nulos, infinitos o no positivos."""
    if (
        not isinstance(weights, pd.Series)
        or not weights.index.equals(index)
        or not pd.api.types.is_numeric_dtype(weights)
        or pd.api.types.is_bool_dtype(weights)
        or not np.isfinite(weights.to_numpy(dtype=float)).all()
        or not weights.gt(0).all()
    ):
        raise ValueError("sample_weight inválido o desalineado")
