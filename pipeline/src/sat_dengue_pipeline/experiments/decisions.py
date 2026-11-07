"""Sigmoide y umbral mínimo: solo estadísticas necesarias para selección."""

import warnings
from dataclasses import dataclass
from math import isfinite
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from sat_dengue_pipeline.models.adapters import validate_probabilities


def fit_sigmoid(probability: pd.Series, y: pd.Series, seed: int) -> tuple[float, float]:
    """Ajustar LogisticRegression sobre probabilidad original, como V2.

    Args:
        probability: Solo predicciones de calibration_fit.
        y: Etiquetas completas del mismo rol, con ambas clases.
        seed: Semilla congelada.

    Returns:
        Coeficiente e intercepto finitos; sin guardar un estimador ni pickle.
    """
    validate_probabilities(probability, y.index)
    if y.isna().any() or set(y.unique()) != {0, 1}:
        raise ValueError("Sigmoide requiere ambas clases completas")
    model = LogisticRegression(solver="lbfgs", max_iter=1000, random_state=seed, C=1.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model.fit(probability.to_numpy(dtype=float).reshape(-1, 1), y.to_numpy(dtype=int))
    coefficient, intercept = float(model.coef_[0, 0]), float(model.intercept_[0])
    if not isfinite(coefficient) or not isfinite(intercept):
        raise ValueError("Parámetros de sigmoide no finitos")
    return coefficient, intercept


def apply_sigmoid(probability: pd.Series, coefficient: float, intercept: float) -> pd.Series:
    """Aplicar parámetros numéricos congelados sin ningún ajuste.

    Args:
        probability: Probabilidades originales válidas.
        coefficient: Parámetro de calibration_fit.
        intercept: Intercepto de calibration_fit.

    Returns:
        Probabilidades finitas mediante la función expit de SciPy.
    """
    validate_probabilities(probability, probability.index)
    if not isfinite(coefficient) or not isfinite(intercept):
        raise ValueError("Parámetros de sigmoide inválidos")
    result = pd.Series(
        expit(coefficient * probability.to_numpy(dtype=float) + intercept),
        index=probability.index,
        dtype=float,
    )
    validate_probabilities(result, probability.index)
    return result


def choose_representation(
    raw: pd.Series, calibrated: pd.Series, y: pd.Series
) -> tuple[str, dict[str, float]]:
    """Elegir por Brier en calibration_selection; empate conserva original.

    Args:
        raw: Probabilidades originales del rol de selección.
        calibrated: Mismas claves con sigmoide ya congelada.
        y: Solo etiquetas de calibration_selection.

    Returns:
        original/sigmoid y Brier mínimo de selección, sin métricas finales.
    """
    validate_probabilities(raw, y.index)
    validate_probabilities(calibrated, y.index)
    if y.isna().any() or not y.isin([0, 1]).all():
        raise ValueError("Etiquetas de selección inválidas")
    raw_brier = float(np.mean((raw.to_numpy(dtype=float) - y.to_numpy(dtype=float)) ** 2))
    sigmoid_brier = float(
        np.mean((calibrated.to_numpy(dtype=float) - y.to_numpy(dtype=float)) ** 2)
    )
    selected = "sigmoid" if sigmoid_brier + 1e-12 < raw_brier else "original"
    return selected, {"original_brier": raw_brier, "sigmoid_brier": sigmoid_brier}


@dataclass(frozen=True)
class ThresholdPolicy:
    """Cuadrícula explícita y cota absoluta de FAR, sin utilidad científica implícita."""

    grid: tuple[float, ...]
    max_false_alarm_ratio: float

    def __post_init__(self) -> None:
        """Rechazar grillas ambiguas o límites ausentes/no finitos."""
        if (
            not isinstance(self.grid, tuple)
            or len(self.grid) < 2
            or any(
                isinstance(t, bool)
                or not isinstance(t, (int, float))
                or not isfinite(t)
                or not 0 <= t <= 1
                for t in self.grid
            )
            or self.grid != tuple(sorted(set(self.grid)))
            or self.grid[0] != 0
            or self.grid[-1] != 1
            or isinstance(self.max_false_alarm_ratio, bool)
            or not isfinite(self.max_false_alarm_ratio)
            or not 0 <= self.max_false_alarm_ratio <= 1
        ):
            raise ValueError("Cuadrícula o cota explícita de FAR inválida")


def select_threshold(
    probability: pd.Series, y: pd.Series, policy: ThresholdPolicy
) -> tuple[float, tuple[dict[str, Any], ...]]:
    """Seleccionar sensibilidad máxima bajo cota FAR sin consultar otros roles.

    Args:
        probability: Representación ya congelada en threshold_selection.
        y: Etiquetas completas exclusivamente del mismo rol.
        policy: Grid y límite declarados previamente.

    Returns:
        Umbral congelable y estadísticas de selección. Empates: menos falsas
        alertas, menor FAR y mayor umbral. Cero alertas no es FAR cero.
    """
    validate_probabilities(probability, y.index)
    if y.isna().any() or set(y.unique()) != {0, 1}:
        raise ValueError("Umbral requiere ambas clases completas")
    rows = []
    positives = int(y.eq(1).sum())
    for threshold in policy.grid:
        alert = probability.ge(threshold)
        emitted = int(alert.sum())
        true = int((alert & y.eq(1)).sum())
        false = int((alert & y.eq(0)).sum())
        rows.append(
            {
                "threshold": float(threshold),
                "true_alerts": true,
                "false_alerts": false,
                "emitted_alerts": emitted,
                "positives": positives,
                "sensitivity": true / positives,
                "false_alarm_ratio": false / emitted if emitted else None,
            }
        )
    feasible = [
        row
        for row in rows
        if row["false_alarm_ratio"] is not None
        and row["false_alarm_ratio"] <= policy.max_false_alarm_ratio
    ]
    if not feasible:
        raise ValueError("No existe umbral factible; no se admite reemplazo manual")
    chosen = min(
        feasible,
        key=lambda r: (
            -r["sensitivity"],
            r["false_alerts"],
            r["false_alarm_ratio"],
            -r["threshold"],
        ),
    )
    return chosen["threshold"], tuple(rows)
