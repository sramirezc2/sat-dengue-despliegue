"""Arnés mensual expansivo; contrato mínimo V3, sin afirmar reproducción de V2."""

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, Protocol

import numpy as np
import pandas as pd

from sat_dengue_pipeline.domain.calendar import add_months, validate_period
from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.domain.margin import MARGIN_COLUMNS, MES_COLUMNS
from sat_dengue_pipeline.domain.temporal import TemporalPolicy, validate_keys
from sat_dengue_pipeline.preparation import PreparedSet

LINK = ["municipality_code", "origin_period", "target_period", "horizon"]
KEY_COLUMNS = [*LINK, "label_available_period"]


def stable_digest(value: Any) -> str:
    """Identificar contenido JSON finito con serialización canónica.

    Args:
        value: Configuración o calendario serializable, sin estimadores.

    Returns:
        SHA-256 determinista de los bytes UTF-8.
    """
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()
    return hashlib.sha256(raw).hexdigest()


# Piso del primer objetivo entrenable; ver ExperimentSpec.train_target_start.
TRAIN_FLOOR = "2012-01"


@dataclass(frozen=True)
class ExperimentSpec:
    """Protocolo mensual con calentamiento inicial y madurez explícita."""

    horizon: int
    # El primer objetivo entrenable. El piso es 2012-01 y no es arbitrario: el
    # P75 del canal se construye con el mismo mes de los cinco años anteriores,
    # así que con el release operacional, que cubre desde 2007, 2012 es el
    # primer año completamente evaluable. El valor anterior, 2018-01, venía del
    # release histórico de 2011-06 y dejaba fuera seis años de entrenamiento
    # disponibles.
    train_target_start: str = "2018-01"
    first_origin: str = "2019-01"
    last_target: str = "2024-12"
    label_delay_months: int = 0
    seed: int = 42
    reserved_start: str = "2025-01"

    def __post_init__(self) -> None:
        """Rechazar calendarios reservados o sin entrenamiento previo."""
        TemporalPolicy(self.reserved_start)
        for value in (self.train_target_start, self.first_origin, self.last_target):
            validate_period(value)
        if (
            type(self.horizon) is not int
            or self.horizon not in (1, 2)
            or type(self.label_delay_months) is not int
            or self.label_delay_months < 0
            or type(self.seed) is not int
            or self.seed < 0
            or self.train_target_start < TRAIN_FLOOR
            or self.last_target >= self.reserved_start
            or self.first_origin >= self.reserved_start
            or self.train_target_start > add_months(self.first_origin, -1 - self.label_delay_months)
            or add_months(self.first_origin, self.horizon) > self.last_target
        ):
            raise ValueError("Protocolo inválido o reservado")


@dataclass(frozen=True)
class Fold:
    """Un origen mensual, rango expansivo por objetivo y enlace reproducible."""

    fold_id: str
    origin_period: str
    target_period: str
    train_target_start: str
    train_target_end: str
    horizon: int


@dataclass(frozen=True)
class ExperimentData:
    """Claves, X, etiquetas nullable y controles físicamente separados."""

    keys: pd.DataFrame
    X: pd.DataFrame
    y: pd.Series
    controls: pd.DataFrame
    predictors: tuple[str, ...] = tuple(PREDICTORS)
    # Derivadas de preparación que la receta declaró; van al final de X, nunca
    # son canónicas y la lista vacía deja el contrato histórico intacto.
    derived: tuple[str, ...] = ()


class FoldEstimator(Protocol):
    """Interfaz mínima del ejecutor; en tarea 8 se usa solo un doble de prueba."""

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Ajustar únicamente con filas maduras autorizadas."""
        ...

    def predict_positive(self, X: pd.DataFrame) -> pd.Series:
        """Producir probabilidad positiva sin recibir etiquetas."""
        ...


def from_prepared(
    prepared: PreparedSet,
    horizon: int,
    *,
    label_delay_months: int = 0,
    derived: tuple[str, ...] = (),
) -> ExperimentData:
    """Enlazar la preparación aprobada con el arnés sin reconstruir etiquetas.

    Args:
        prepared: Conjunto utilizable con X/y separados.
        horizon: Uno o dos meses.
        label_delay_months: Demora adicional declarada después del objetivo.
        derived: Columnas de preparación que X trae al final, si la receta las
            declara. Sin ellas el contrato histórico no cambia.

    Returns:
        Copias con claves objetivo y mes de disponibilidad explícito.
    """
    if type(horizon) is not int or horizon not in (1, 2):
        raise ValueError("Horizonte inválido")
    if type(label_delay_months) is not int or label_delay_months < 0:
        raise ValueError("Demora inválida")
    keys = prepared.keys.rename(columns={"year_month": "origin_period"}).copy()
    keys["target_period"] = keys.origin_period.map(lambda t: add_months(t, horizon))
    keys["horizon"] = horizon
    keys["label_available_period"] = keys.target_period.map(
        lambda t: add_months(t, label_delay_months)
    )
    data = ExperimentData(
        keys[KEY_COLUMNS],
        prepared.X.copy(),
        prepared.y.copy(),
        pd.DataFrame({"eligible_at_t": [True] * len(keys)}, index=keys.index),
        derived=tuple(derived),
    )
    validate_data(data, horizon)
    return data


def validate_data(data: ExperimentData, horizon: int, reserved_start: str = "2025-01") -> None:
    """Validar claves antes de tocar X o y; nunca consultar etiquetas reservadas.

    Args:
        data: Entradas separadas y alineadas.
        horizon: Horizonte del protocolo.
        reserved_start: Límite reservado inclusivo.
    """
    TemporalPolicy(reserved_start)
    keys = data.keys
    if list(keys) != KEY_COLUMNS:
        raise ValueError("Esquema de claves alterado")
    validate_keys(keys.rename(columns={"origin_period": "year_month"}))
    for column in ("origin_period", "target_period", "label_available_period"):
        for value in keys[column]:
            validate_period(value)
        if keys[column].ge(reserved_start).any():
            raise ValueError("Periodo reservado antes de leer etiquetas")
    expected = keys.origin_period.map(lambda t: add_months(t, horizon))
    if (
        not keys.horizon.map(lambda h: type(h) is int and h == horizon).all()
        or not keys.target_period.eq(expected).all()
        or keys.label_available_period.lt(keys.target_period).any()
    ):
        raise ValueError("Calendario objetivo/disponibilidad inválido")
    if (
        not data.predictors
        or list(data.predictors) != [p for p in PREDICTORS if p in data.predictors]
        or list(data.X) != [*data.predictors, *data.derived]
        or data.X.columns.duplicated().any()
        or set(data.derived) & set(PREDICTORS)
        or (
            data.derived
            and list(data.derived)
            != [c for c in (*MARGIN_COLUMNS, *MES_COLUMNS) if c in data.derived]
        )
    ):
        raise ValueError("Predictores fuera del esquema canónico cerrado")
    if any(not obj.index.equals(keys.index) for obj in (data.X, data.y, data.controls)):
        raise ValueError("Claves/X/y/controles desalineados")
    if (
        list(data.controls) != ["eligible_at_t"]
        or not pd.api.types.is_bool_dtype(data.controls.eligible_at_t)
        or data.controls.eligible_at_t.isna().any()
    ):
        raise ValueError("Elegibilidad al origen inválida")


def build_folds(spec: ExperimentSpec) -> tuple[Fold, ...]:
    """Construir meses calendario independientes de filas o resultados.

    Args:
        spec: Protocolo validado.

    Returns:
        Folds mensuales ordenados con ventana expansiva por objetivo.
    """
    folds = []
    protocol = stable_digest(asdict(spec))
    for month in pd.period_range(
        spec.first_origin, add_months(spec.last_target, -spec.horizon), freq="M"
    ):
        origin = str(month)
        folds.append(
            Fold(
                fold_id="ro-" + stable_digest({"protocol": protocol, "origin": origin})[:20],
                origin_period=origin,
                target_period=add_months(origin, spec.horizon),
                train_target_start=spec.train_target_start,
                train_target_end=add_months(origin, -1 - spec.label_delay_months),
                horizon=spec.horizon,
            )
        )
    return tuple(folds)


def calendar_audit(spec: ExperimentSpec) -> dict[str, Any]:
    """Serializar protocolo y calendario, sin incorporar observaciones.

    Args:
        spec: Especificación del experimento.

    Returns:
        Calendario, regla de madurez y digest reproducible.
    """
    payload = {
        "schema": "rolling-origin-v1",
        "spec": asdict(spec),
        "maturity": "label_available_period < consumer_origin",
        "folds": [asdict(fold) for fold in build_folds(spec)],
    }
    return {**payload, "digest": stable_digest(payload)}


def fold_inputs(
    data: ExperimentData, spec: ExperimentSpec, fold: Fold
) -> tuple[PreparedSet, PreparedSet]:
    """Seleccionar entrenamiento maduro y X de validación sin leer su y.

    Args:
        data: Entradas con ausencias preservadas.
        spec: Protocolo de desarrollo.
        fold: Fold perteneciente exactamente al calendario declarado.

    Returns:
        Entrenamiento y validación separados. La y de validación es ausente por
        diseño; las etiquetas observadas permanecen en data.y, fuera del modelo.
    """
    validate_data(data, spec.horizon, spec.reserved_start)
    if fold not in build_folds(spec):
        raise ValueError("Fold ajeno al protocolo")
    keys = data.keys
    train_mask = keys.target_period.between(fold.train_target_start, fold.train_target_end)
    train_mask &= keys.origin_period.lt(fold.origin_period)
    train_mask &= keys.label_available_period.lt(fold.origin_period)
    train_mask &= data.controls.eligible_at_t
    validation_mask = keys.origin_period.eq(fold.origin_period) & data.controls.eligible_at_t
    chunks = []
    for mask, training in ((train_mask, True), (validation_mask, False)):
        positions = np.flatnonzero(mask.to_numpy())
        order = keys.iloc[positions].reset_index(drop=True).sort_values(LINK).index.to_numpy()
        positions = positions[order]
        X = data.X.iloc[positions].reset_index(drop=True).copy(deep=True)
        selected_keys = keys.iloc[positions].reset_index(drop=True).copy(deep=True)
        y = (
            data.y.iloc[positions].reset_index(drop=True).copy(deep=True)
            if training
            else pd.Series(pd.NA, index=X.index, dtype="Int64", name=data.y.name)
        )
        if training and not y.dropna().isin([0, 1]).all():
            raise ValueError("Etiquetas de entrenamiento no binarias")
        usable = X.notna().all(axis=1) & (y.notna() if training else True)
        chunks.append(
            PreparedSet(
                selected_keys.loc[usable].reset_index(drop=True),
                X.loc[usable].reset_index(drop=True),
                y.loc[usable].reset_index(drop=True),
            )
        )
    if any(chunk.X.empty for chunk in chunks):
        raise ValueError("Fold sin soporte de entrenamiento o predicción")
    return chunks[0], chunks[1]


def run_rolling(
    data: ExperimentData, spec: ExperimentSpec, factory: Callable[[], FoldEstimator]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Ejecutar folds con instancias nuevas y copias de X/y, sin métricas finales.

    Args:
        data: Entradas artificiales o preparación autorizada, nunca publicaciones.
        spec: Calendario congelado.
        factory: Crea una instancia nueva y sin ajustar por fold.

    Returns:
        Probabilidades enlazadas sin y_true y auditoría de soporte efectivo.
    """
    validate_data(data, spec.horizon, spec.reserved_start)
    models, predictions, supports = [], [], []
    for fold in build_folds(spec):
        train, validation = fold_inputs(data, spec, fold)
        model = factory()
        if any(model is previous for previous in models) or getattr(model, "fitted", False):
            raise ValueError("Cada fold requiere una instancia nueva no ajustada")
        models.append(model)
        model.fit(train.X.copy(deep=True), train.y.copy(deep=True))
        probability = model.predict_positive(validation.X.copy(deep=True))
        if not isinstance(probability, pd.Series) or not probability.index.equals(
            validation.X.index
        ):
            raise ValueError("Predicciones desalineadas")
        values = probability.to_numpy(dtype=float, na_value=np.nan)
        if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
            raise ValueError("Probabilidades inválidas")
        frame = validation.keys[LINK].copy()
        frame["fold_id"] = fold.fold_id
        frame["raw_probability"] = values
        predictions.append(frame)
        supports.append(
            {
                "fold_id": fold.fold_id,
                "train_rows": len(train.X),
                "prediction_rows": len(frame),
                "last_training_target": str(train.keys.target_period.max()),
                "last_label_available": str(train.keys.label_available_period.max()),
            }
        )
    return pd.concat(predictions, ignore_index=True), {**calendar_audit(spec), "support": supports}
