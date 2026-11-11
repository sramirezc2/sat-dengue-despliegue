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

from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.domain.margin import MARGIN_COLUMNS, MES_COLUMNS
from sat_dengue_pipeline.models.adapters import (
    AdapterSpec,
    validate_features,
    validate_probabilities,
)

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
        self.derived: tuple[str, ...] = (
            tuple(MARGIN_COLUMNS) if self.preparation.get("variables_g") else ()
        ) + (tuple(MES_COLUMNS) if self.preparation.get("variables_mes") else ())
        predictors = self.settings["predictors"]
        if (
            not predictors
            or predictors != [p for p in PREDICTORS if p in predictors]
            or spec.family != self.candidate["family"]
            or spec.version != self.candidate["adapter_version"]
            or self.candidate["library"] != "scikit-learn"
            or self.candidate["library_version"] != sklearn.__version__
            or any(self.candidate[name] is not False for name in MODOS_FIJOS)
        ):
            raise ValueError("Identidad, versión o modo del candidato no autorizado")
        c, max_iter = self.candidate["C"], self.candidate["max_iter"]
        if not (isinstance(c, (int, float)) and c > 0) or type(max_iter) is not int or max_iter < 1:
            raise ValueError("Regularización o iteraciones inválidas")
        if (
            self.preparation["zone_encoding"] != "fixed_onehot"
            or self.preparation["zone_mapping"] != ZONES
            or self.preparation["zone_columns"] != ["zona_canal_t__" + z for z in ZONES]
            or self.preparation["missing"] != "error"
            or self.preparation["scaling"] != "standard_train"
            or self.preparation["imputation"] != "none"
            or self.preparation["matrix_dtype"] != "float64"
            or type(self.preparation["variables_g"]) is not bool
            or self.preparation["channel_budget"] is not False
        ):
            raise ValueError("Preparación diferente de la autorizada")
        expected = [
            column
            for name in predictors
            for column in (self.preparation["zone_columns"] if name == "zona_canal_t" else [name])
        ]
        # El bloque de margen va al final y solo si la receta lo declara; sin él
        # la matriz es idéntica a la histórica.
        esperadas = (tuple(MARGIN_COLUMNS) if self.preparation["variables_g"] else ()) + (
            tuple(MES_COLUMNS) if self.preparation.get("variables_mes") else ()
        )
        if self.derived != esperadas:
            raise ValueError("Columnas derivadas alteradas o sin declarar")
        if self.preparation["matrix_columns"] != [*expected, *self.derived]:
            raise ValueError("Orden o cardinalidad de matriz interna alterados")
        if not set(self.preparation["log1p_columns"]) <= set(predictors) - {"zona_canal_t"}:
            raise ValueError("log1p declarado sobre columnas inexistentes")

    def matrix(self, X: pd.DataFrame) -> np.ndarray:
        """Proyectar predictores declarados, con zona one-hot y log1p, sin aprender.

        Args:
            X: Las 33 entradas canónicas y, si la receta declara el bloque de
                margen, sus seis columnas al final.

        Returns:
            Matriz float64 en el orden de ``matrix_columns``.
        """
        validate_features(X, self._dtypes, derived=self.derived)
        log1p = set(self.preparation["log1p_columns"])
        parts = []
        # Las derivadas entran crudas: son márgenes con signo y log1p no está
        # definido en los negativos. La estandarización del fold las escala.
        for name in [*self.settings["predictors"], *self.derived]:
            if name == "zona_canal_t":
                codes = X[name].map(ZONES).to_numpy(dtype=int)
                parts.append(np.eye(len(ZONES))[codes])
            else:
                col = X[name].to_numpy(dtype=float)
                parts.append(
                    (np.log1p(np.clip(col, 0, None)) if name in log1p else col).reshape(-1, 1)
                )
        result = np.concatenate(parts, axis=1)
        if (
            result.shape != (len(X), len(self.preparation["matrix_columns"]))
            or not np.isfinite(result).all()
        ):
            raise ValueError("Matriz interna inválida o no finita")
        return result

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

    def coeficientes(self) -> dict[str, float]:
        """Coeficientes estandarizados por columna de la matriz, para interpretar el modelo.

        Returns:
            Diccionario columna -> coeficiente (log-odds por 1 DE).
        """
        if not self.fitted or self._model is None:
            raise ValueError("Modelo sin ajustar")
        return dict(zip(self.preparation["matrix_columns"], map(float, self._model.coef_[0])))
