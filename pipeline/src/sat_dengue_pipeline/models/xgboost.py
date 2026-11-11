"""Adaptador mínimo XGBoost de fábrica; sin orquestación, búsqueda o persistencia."""

import copy
import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb

from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.domain.derived import declared_derived
from sat_dengue_pipeline.models.adapters import (
    AdapterSpec,
    validate_features,
    validate_probabilities,
)

PARAMETER_NAMES = frozenset(
    (
        "booster objective tree_method device nthread n_jobs seed random_state "
        "seed_per_iteration validate_parameters verbosity disable_default_eval_metric eta "
        "max_depth min_child_weight lambda alpha gamma max_delta_step subsample "
        "colsample_bytree colsample_bylevel colsample_bynode max_bin max_leaves grow_policy "
        "sampling_method base_score boost_from_average num_parallel_tree max_cached_hist_node "
        "debug_synchronize multi_strategy scale_pos_weight process_type cache_opt "
        "max_cat_threshold max_cat_to_onehot monotone_constraints interaction_constraints "
        "refresh_leaf sketch_ratio sparse_threshold extmem_single_page fail_on_invalid_gpu_id"
    ).split()
)


def canonical_json(value: Any) -> bytes:
    """Serializar todo el estado JSON con floats finitos y orden estable."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


class XGBoostOnsetAdapter:
    """Un ajuste CPU/hist de configuración explícita y codificación fija de zona."""

    def __init__(self, spec: AdapterSpec) -> None:
        """Validar identidad y configuración sin crear ni ajustar un modelo."""
        self.spec = spec
        self.settings = json.loads(spec.config_json)
        self.fitted = False
        self.fit_calls = 0
        self._booster: xgb.Booster | None = None
        self._dtypes: tuple[str, ...] | None = None
        if set(self.settings) != {"candidate", "preparation", "predictors"}:
            raise ValueError("Configuración de adaptador incompleta o adicional")
        self.candidate = self.settings["candidate"]
        self.preparation = self.settings["preparation"]
        # Derivadas de preparación: vacías salvo que la receta declare el bloque
        # de margen. Nunca son canónicas y siempre van al final de la matriz.
        self.derived: tuple[str, ...] = declared_derived(self.preparation)
        if (
            not self.settings["predictors"]
            or self.settings["predictors"]
            != [p for p in PREDICTORS if p in self.settings["predictors"]]
            or spec.family != self.candidate["family"]
            or spec.version != self.candidate["adapter_version"]
            or xgb.__version__ != self.candidate["library_version"]
            or self.candidate["library"] != "xgboost"
            or any(
                self.candidate[name] is not False
                for name in (
                    "early_stopping",
                    "hyperparameter_search",
                    "class_balancing",
                    "refit",
                    "seed_selection",
                )
            )
        ):
            raise ValueError("Identidad, versión o modo del candidato no autorizado")
        parameters = self.candidate["parameters"]
        if set(parameters) != PARAMETER_NAMES:
            raise ValueError("Parámetros efectivos faltantes o adicionales")
        if (
            parameters["seed"] != spec.seed
            or parameters["random_state"] != spec.seed
            or parameters["nthread"] != 1
            or parameters["n_jobs"] != 1
            or parameters["device"] != "cpu"
            or parameters["tree_method"] != "hist"
            or parameters["objective"] != "binary:logistic"
            or type(self.candidate["rounds"]) is not int
            or self.candidate["rounds"] < 1
        ):
            raise ValueError("Receta CPU/hist/semilla/hilo alterada")
        zones = {"EXITO": 0, "SEGURIDAD": 1, "ALERTA": 2, "EXCESO": 3}
        if (
            self.preparation["zone_encoding"] != "fixed_onehot"
            or self.preparation["zone_mapping"] != zones
            or self.preparation["zone_columns"] != ["zona_canal_t__" + z for z in zones]
            or self.preparation["matrix_dtype"] != "float32"
            or type(self.preparation["variables_g"]) is not bool
            or self.preparation["channel_budget"] is not False
            or self.preparation["missing"] != "error"
            or self.preparation["scaling"] != "none"
            or self.preparation["imputation"] != "none"
        ):
            raise ValueError("Preparación fija diferente de la autorizada")
        expected = [
            column
            for name in self.settings["predictors"]
            for column in (self.preparation["zone_columns"] if name == "zona_canal_t" else [name])
        ]
        # Los bloques derivados van al final y solo si la receta los declara; sin
        # ellos la matriz es byte a byte la histórica.
        if self.preparation["matrix_columns"] != [*expected, *self.derived]:
            raise ValueError("Orden o cardinalidad de matriz interna alterados")

    def matrix(self, X: pd.DataFrame) -> np.ndarray:
        """Validar las entradas y proyectar los predictores declarados a float32.

        X puede llegar de dos formas y las dos son válidas: con el contrato
        canónico completo más las derivadas que la receta declare, que es como
        lo entrega el retroanálisis, o ya recortada al subconjunto declarado más
        esas derivadas, que es como lo entrega la fábrica. La proyección es la
        misma en los dos casos; lo único que cambia es contra qué se valida.

        Sin esta distinción, una receta que quite columnas canónicas y encienda
        un bloque derivado rechaza todos sus orígenes con «esquema inválido»,
        que es lo que pasó al medir la línea U.
        """
        entrada_canonica = list(X) == [*PREDICTORS, *self.derived]
        validate_features(
            X,
            self._dtypes,
            predictors=tuple(PREDICTORS if entrada_canonica else self.settings["predictors"]),
            derived=self.derived,
        )
        parts = []
        for name in [*self.settings["predictors"], *self.derived]:
            if name == "zona_canal_t":
                codes = X[name].map(self.preparation["zone_mapping"]).to_numpy(dtype=int)
                parts.append(np.eye(len(self.preparation["zone_mapping"]), dtype=np.float32)[codes])
            else:
                parts.append(X[name].to_numpy(dtype=np.float32).reshape(-1, 1))
        result = np.concatenate(parts, axis=1)
        if (
            result.shape != (len(X), len(self.preparation["matrix_columns"]))
            or not np.isfinite(result).all()
        ):
            raise ValueError("Matriz interna inválida o no finita")
        return result

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Ajustar una sola vez con train; no acepta evaluación, callbacks o refit."""
        if self.fitted or self.fit_calls:
            raise ValueError("Refit o reutilización de modelo no autorizados")
        matrix = self.matrix(X)
        if not X.index.equals(y.index) or y.isna().any() or set(y.unique()) != {0, 1}:
            raise ValueError("Etiquetas de entrenamiento incompletas o desalineadas")
        self.fit_calls += 1
        self._booster = xgb.train(
            params=self.candidate["parameters"],
            dtrain=xgb.DMatrix(
                matrix,
                label=y.to_numpy(dtype=int),
                feature_names=self.preparation["matrix_columns"],
                nthread=1,
            ),
            num_boost_round=self.candidate["rounds"],
        )
        self._dtypes = tuple(str(dtype) for dtype in X.dtypes)
        self.native_configuration()
        self.fitted = True

    def native_configuration(self) -> dict[str, Any]:
        """Verificar todos los parámetros resueltos; conservar intercepto aprendido."""
        if self._booster is None:
            raise ValueError("No existe modelo ajustado")
        actual = json.loads(self._booster.save_config())
        contract = copy.deepcopy(actual)
        model = contract["learner"]["learner_model_param"]
        if not 0 < float(model["base_score"]) < 1:
            raise ValueError("Intercepto inicial aprendido inválido")
        # Solo el cotejo de configuración usa el marcador. La identidad conserva
        # el valor real, sin omitir ningún estado predictivo del modelo.
        model["base_score"] = "ESTIMATED_FROM_TRAIN_ONLY"
        if contract != self.candidate["expected_native_configuration"]:
            raise ValueError("Configuración efectiva XGBoost distinta de la aprobada")
        return actual

    def predict_positive(self, X: pd.DataFrame) -> pd.Series:
        """Aplicar el único modelo sin etiquetas ni modificación de estado predictivo."""
        if not self.fitted or self._booster is None:
            raise ValueError("Inferencia antes del ajuste")
        probability = pd.Series(
            self._booster.predict(
                xgb.DMatrix(
                    self.matrix(X), feature_names=self.preparation["matrix_columns"], nthread=1
                )
            ).astype(float),
            index=X.index,
        )
        validate_probabilities(probability, X.index)
        return probability

    def model_json(self) -> bytes:
        """Incluir árboles, estado predictivo, configuración efectiva y representación."""
        if not self.fitted or self._booster is None:
            raise ValueError("Serialización antes del ajuste")
        return canonical_json(
            {
                "model": json.loads(self._booster.save_raw(raw_format="json")),
                "native_configuration": self.native_configuration(),
                "adapter": self.settings,
                "input_dtypes": self._dtypes,
                "fit_calls": self.fit_calls,
                "library_version": xgb.__version__,
            }
        )

    def model_sha256(self) -> str:
        """Calcular SHA-256 sobre JSON canónico completo, nunca un archivo binario."""
        return hashlib.sha256(self.model_json()).hexdigest()
