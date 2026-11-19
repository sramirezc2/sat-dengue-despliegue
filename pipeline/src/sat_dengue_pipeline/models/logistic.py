"""Adaptador de regresión logística regularizada para inicios; mismo contrato que XGBoost.

Sin orquestación, búsqueda ni persistencia. La matriz usa la misma codificación fija de zona que
XGBoost; los conteos y umbrales declarados en ``log1p_columns`` se transforman con log1p y todas las
columnas se estandarizan con media y desviación aprendidas solo en el entrenamiento del fold.
"""

import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression

from sat_dengue_pipeline.domain.derived import declared_derived
from sat_dengue_pipeline.models.adapters import (
    AdapterSpec,
    validate_features,
    validate_probabilities,
)
from sat_dengue_runtime.logistic import (
    canonical_json as canonical_json,
)
from sat_dengue_runtime.logistic import (
    load_inference_state as load_inference_state,
)
from sat_dengue_runtime.logistic import (
    logistic_matrix,
    score_matrix,
    validate_settings,
    validate_state_version,
)


class LogisticOnsetAdapter:
    """Logística L2 con log1p declarado y estandarización ajustada solo en train."""

    def __init__(self, spec: AdapterSpec) -> None:
        """Validar identidad y configuración sin ajustar un modelo.

        Args:
            spec: Identidad, configuración JSON y semilla.

        Raises:
            ValueError: Si la receta, la preparación o la identidad no están autorizadas.
        """
        self.spec = spec
        self.settings = json.loads(spec.config_json)
        self.fitted = False
        self.fit_calls = 0
        self._model: LogisticRegression | None = None
        self._mean: np.ndarray | None = None
        self._std: np.ndarray | None = None
        self._dtypes: tuple[str, ...] | None = None
        if set(self.settings) != {"candidate", "preparation", "predictors"}:
            raise ValueError("Configuración de adaptador incompleta o adicional")
        self.candidate = self.settings["candidate"]
        self.preparation = self.settings["preparation"]
        # Derivadas de preparación: vacías salvo que la receta declare el bloque
        # de margen. Nunca son canónicas y siempre van al final de la matriz.
        self.derived: tuple[str, ...] = declared_derived(self.preparation)
        validate_settings(
            self.settings,
            self.derived,
            family=spec.family,
            version=spec.version,
            library_version=sklearn.__version__,
        )

    def matrix(self, X: pd.DataFrame) -> np.ndarray:
        """Proyectar predictores declarados, con zona one-hot y log1p, sin aprender.

        Args:
            X: Las 33 entradas canónicas y, si la receta declara el bloque de
                margen, sus seis columnas al final.

        Returns:
            Matriz float64 en el orden de ``matrix_columns``.
        """
        validate_features(X, self._dtypes, derived=self.derived)
        return logistic_matrix(X, self.preparation, self.settings["predictors"], self.derived)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Ajustar una sola vez con train; estandarización aprendida solo aquí.

        Args:
            X: Predictores del entrenamiento.
            y: Etiquetas binarias alineadas.
        """
        if self.fitted or self.fit_calls:
            raise ValueError("Refit o reutilización de modelo no autorizados")
        matrix = self.matrix(X)
        if not X.index.equals(y.index) or y.isna().any() or set(y.unique()) != {0, 1}:
            raise ValueError("Etiquetas de entrenamiento incompletas o desalineadas")
        self.fit_calls += 1
        self._mean = matrix.mean(axis=0)
        self._std = np.where(matrix.std(axis=0) > 0, matrix.std(axis=0), 1.0)
        self._model = LogisticRegression(
            C=float(self.candidate["C"]),
            max_iter=self.candidate["max_iter"],
            random_state=self.spec.seed,
        ).fit((matrix - self._mean) / self._std, y.to_numpy(dtype=int))
        self._dtypes = tuple(str(dtype) for dtype in X.dtypes)
        self.fitted = True

    def predict_positive(self, X: pd.DataFrame) -> pd.Series:
        """Aplicar el único modelo sin etiquetas.

        Args:
            X: Predictores con el esquema del ajuste.

        Returns:
            Probabilidad positiva alineada con X.
        """
        if not self.fitted or self._model is None:
            raise ValueError("Inferencia antes del ajuste")
        z = (self.matrix(X) - self._mean) / self._std
        probability = pd.Series(self._model.predict_proba(z)[:, 1].astype(float), index=X.index)
        validate_probabilities(probability, X.index)
        return probability

    def native_configuration(self) -> dict[str, Any]:
        """Parámetros efectivos del estimador ajustado, para la identidad del motor.

        Returns:
            Diccionario JSON de ``get_params`` y versión de la biblioteca.
        """
        if not self.fitted or self._model is None:
            raise ValueError("No existe modelo ajustado")
        params = {
            k: v
            for k, v in self._model.get_params().items()
            if v is None or isinstance(v, (bool, int, float, str))
        }
        return {
            "estimator": "LogisticRegression",
            "params": params,
            "library_version": sklearn.__version__,
        }

    def model_json(self) -> bytes:
        """Serializar coeficientes, intercepto, escalado y configuración.

        Returns:
            JSON canónico del estado predictivo completo.
        """
        if not self.fitted or self._model is None:
            raise ValueError("Serialización antes del ajuste")
        return canonical_json(
            {
                "coef": [round(float(v), 12) for v in self._model.coef_[0]],
                "intercept": round(float(self._model.intercept_[0]), 12),
                "mean": [round(float(v), 12) for v in self._mean],
                "std": [round(float(v), 12) for v in self._std],
                "adapter": self.settings,
                "input_dtypes": self._dtypes,
                "fit_calls": self.fit_calls,
                "library_version": sklearn.__version__,
            }
        )

    def model_sha256(self) -> str:
        """Calcular SHA-256 del JSON canónico del modelo.

        Returns:
            Huella hexadecimal.
        """
        return hashlib.sha256(self.model_json()).hexdigest()

    def inference_state(self) -> dict[str, Any]:
        """Export the full-precision state of the fitted logistic estimator."""
        if not self.fitted or self._model is None or self._mean is None or self._std is None:
            raise ValueError("Exportación antes del ajuste")
        return {
            "schema_version": 1,
            "seed": self.spec.seed,
            "adapter": self.settings,
            "classes": self._model.classes_.tolist(),
            "coef": self._model.coef_[0].tolist(),
            "intercept": float(self._model.intercept_[0]),
            "mean": self._mean.tolist(),
            "std": self._std.tolist(),
        }

    def coeficientes(self) -> dict[str, float]:
        """Coeficientes estandarizados por columna de la matriz, para interpretar el modelo.

        Returns:
            Diccionario columna -> coeficiente (log-odds por 1 DE).
        """
        if not self.fitted or self._model is None:
            raise ValueError("Modelo sin ajustar")
        return dict(zip(self.preparation["matrix_columns"], map(float, self._model.coef_[0])))


def predict_exported(X: pd.DataFrame, state: dict[str, Any]) -> pd.Series:
    """Score a prepared predictor frame using the exported fit and canonical transform."""
    validate_state_version(state)
    spec = AdapterSpec(
        "logistic_onset", "v1", canonical_json(state["adapter"]).decode(), state["seed"]
    )
    matrix = LogisticOnsetAdapter(spec).matrix(X)
    return score_matrix(matrix, X.index, state)
