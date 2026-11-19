"""Input validation shared by training and the serving runtime."""

import numpy as np
import pandas as pd

from .canonical import PREDICTORS


def validate_feature_frame(
    X: pd.DataFrame,
    dtypes: tuple[str, ...] | None,
    *,
    predictors: tuple[str, ...],
    derived: tuple[str, ...],
) -> None:
    """Require ordered, complete, finite predictors of the declared types."""
    if (
        not predictors
        or list(predictors) != [p for p in PREDICTORS if p in predictors]
        or X.empty
        or list(X) != [*predictors, *derived]
        or X.isna().any().any()
    ):
        raise ValueError("Esquema de características inválido, futuro o incompleto")
    if dtypes is not None and tuple(str(t) for t in X.dtypes) != dtypes:
        raise ValueError("Tipos de características alterados")
    names = [name for name in (*predictors, *derived) if name != "zona_canal_t"]
    if any(
        not pd.api.types.is_numeric_dtype(X[name]) or pd.api.types.is_bool_dtype(X[name])
        for name in names
    ) or (
        "zona_canal_t" in X
        and not X.zona_canal_t.isin(["EXITO", "SEGURIDAD", "ALERTA", "EXCESO"]).all()
    ):
        raise ValueError("Tipos/estados de características inválidos")
    numeric = X[names]
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Características no finitas")


def validate_probabilities(probability: pd.Series, index: pd.Index) -> None:
    """Rechazar probabilidades inválidas o sin alineación exacta.

    Args:
        probability: P(clase positiva), sin coerción de strings o ausencias.
        index: Índice exacto esperado de X o claves.
    """
    if (
        not isinstance(probability, pd.Series)
        or not probability.index.equals(index)
        or not pd.api.types.is_numeric_dtype(probability)
        or pd.api.types.is_bool_dtype(probability)
    ):
        raise ValueError("Probabilidades sin esquema o alineación válidos")
    values = probability.to_numpy(dtype=float, na_value=np.nan)
    if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
        raise ValueError("Probabilidades nulas, no finitas o fuera de [0,1]")
