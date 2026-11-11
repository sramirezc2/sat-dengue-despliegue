"""Contrato común de familias, validación de entradas y ejecución sin evaluación."""

import json
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, Protocol

import numpy as np
import pandas as pd

from sat_dengue_pipeline.domain.calendar import add_months, validate_period
from sat_dengue_pipeline.domain.canonical import PREDICTORS
from sat_dengue_pipeline.domain.margin import MARGIN_COLUMNS, MES_COLUMNS
from sat_dengue_pipeline.domain.temporal import TemporalPolicy
from sat_dengue_pipeline.experiments.rolling import (
    LINK,
    ExperimentData,
    ExperimentSpec,
    run_rolling,
    stable_digest,
)

PREDICTION_KEYS = [*LINK, "fold_id"]


@dataclass(frozen=True)
class AdapterSpec:
    """Identidad inmutable, configuración JSON canónica y semilla de una familia."""

    family: str
    version: str
    config_json: str = "{}"
    seed: int = 42

    def __post_init__(self) -> None:
        """Validar identidad y congelar configuración, sin objetos ejecutables."""
        if any(
            not isinstance(v, str) or re.fullmatch(r"[A-Za-z0-9_.-]+", v) is None
            for v in (self.family, self.version)
        ):
            raise ValueError("Identidad de familia inválida")
        config = json.loads(self.config_json)
        if not isinstance(config, dict) or type(self.seed) is not int or self.seed < 0:
            raise ValueError("Configuración o semilla inválida")
        stable_digest(config)
        object.__setattr__(
            self,
            "config_json",
            json.dumps(
                config, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
            ),
        )

    @property
    def candidate(self) -> str:
        """Identificar familia/versión/configuración/semilla sin etiquetas observadas."""
        return f"{self.family}@{self.version}:{stable_digest(asdict(self))[:16]}"


class ModelAdapter(Protocol):
    """Un backend sin Kedro, proveedores, folds, calibración o publicación."""

    spec: AdapterSpec
    fitted: bool

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Ajustar solo con X/y de entrenamiento autorizados y separados."""
        ...

    def predict_positive(self, X: pd.DataFrame) -> pd.Series:
        """Inferir P(y=1), alineada con X, sin recibir y ni claves/controles."""
        ...


class ModelRegistry:
    """Registro explícito pequeño, vacío por defecto y sin imports dinámicos."""

    def __init__(self) -> None:
        """Inicializar familias/versiones sin cargar frameworks."""
        self._builders: dict[tuple[str, str], Callable[[AdapterSpec], ModelAdapter]] = {}

    def register(
        self, family: str, version: str, builder: Callable[[AdapterSpec], ModelAdapter]
    ) -> None:
        """Registrar una única fábrica por identidad, sin reemplazo silencioso.

        Args:
            family: Nombre estable de familia.
            version: Versión explícita de implementación.
            builder: Constructor de una instancia nueva sin ajustar.
        """
        AdapterSpec(family, version)
        key = (family, version)
        if key in self._builders or not callable(builder):
            raise ValueError("Familia duplicada o constructor inválido")
        self._builders[key] = builder

    def create(self, spec: AdapterSpec) -> ModelAdapter:
        """Construir una instancia y comprobar identidad y estado inicial.

        Args:
            spec: Configuración serializable aprobada por el llamador.

        Returns:
            Adaptador neutral sin ajustar.
        """
        key = (spec.family, spec.version)
        if key not in self._builders:
            raise ValueError("Familia/versión no registrada")
        model = self._builders[key](spec)
        if model.spec != spec or model.fitted is not False:
            raise ValueError("Adaptador con identidad alterada o previamente ajustado")
        return model


def validate_features(
    X: pd.DataFrame,
    dtypes: tuple[str, ...] | None = None,
    *,
    predictors: tuple[str, ...] = tuple(PREDICTORS),
    derived: tuple[str, ...] = (),
) -> None:
    """Exigir esquema/orden canónico, sin columnas futuras ni valores ausentes.

    Args:
        X: Los predictores cerrados del productor canónico y, al final y solo
            si la receta las declara, las derivadas de preparación.
        dtypes: Tipos congelados en el ajuste, si se está infiriendo.
        predictors: Subconjunto canónico explícito; por defecto el contrato histórico.
        derived: Columnas construidas en preparación, nunca canónicas. Van
            después de los predictores y en su orden fijo; la lista vacía deja
            el contrato histórico intacto.
    """
    if derived and (
        list(derived) != [c for c in (*MARGIN_COLUMNS, *MES_COLUMNS) if c in derived]
        or set(derived) & set(PREDICTORS)
    ):
        raise ValueError("Derivadas de preparación no declaradas, repetidas o canónicas")
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


class CheckedAdapter:
    """Frontera común que protege entradas y congela esquema y procedencia."""

    def __init__(
        self,
        adapter: ModelAdapter,
        *,
        predictors: tuple[str, ...] = tuple(PREDICTORS),
        derived: tuple[str, ...] = (),
    ) -> None:
        """Envolver una instancia nueva, sin copiar estado de otro fold.

        Args:
            adapter: Backend registrado sin ajustar.
            predictors: Subconjunto canónico congelado de esta receta.
            derived: Columnas de preparación que la receta declaró y que X trae
                al final. El envoltorio valida la matriz por su cuenta, así que
                sin esto rechazaría el bloque que el propio adaptador espera.
        """
        if adapter.fitted is not False:
            raise ValueError("Instancia previamente ajustada")
        self.adapter = adapter
        self.predictors = predictors
        self.derived = derived
        self.spec = adapter.spec
        self.dtypes: tuple[str, ...] | None = None

    @property
    def fitted(self) -> bool:
        """Exponer estado de ajuste validado."""
        return self.dtypes is not None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Ajustar una sola vez y detectar mutaciones del backend.

        Args:
            X: Predictores exclusivamente del entrenamiento.
            y: Etiquetas binarias completas y alineadas con ambas clases.
        """
        if self.fitted:
            raise ValueError("No se permite reutilizar una instancia ajustada")
        validate_features(X, predictors=self.predictors, derived=self.derived)
        if not X.index.equals(y.index) or y.isna().any() or set(y.unique()) != {0, 1}:
            raise ValueError("Entrenamiento requiere ambas clases completas y alineadas")
        copied_X, copied_y = X.copy(deep=True), y.copy(deep=True)
        self.adapter.fit(copied_X, copied_y)
        try:
            pd.testing.assert_frame_equal(X, copied_X)
            pd.testing.assert_series_equal(y, copied_y)
        except AssertionError as exc:
            raise ValueError("El adaptador mutó las entradas de ajuste") from exc
        if self.adapter.fitted is not True or self.adapter.spec != self.spec:
            raise ValueError("El backend no registró un ajuste válido")
        self.dtypes = tuple(str(t) for t in X.dtypes)

    def predict_positive(self, X: pd.DataFrame) -> pd.Series:
        """Inferir sin y, proteger X y validar la probabilidad positiva.

        Args:
            X: Esquema congelado durante fit; sin etiquetas o controles.

        Returns:
            Copia de probabilidades válidas y alineadas.
        """
        if not self.fitted:
            raise ValueError("Inferencia antes de ajustar")
        validate_features(X, self.dtypes, predictors=self.predictors, derived=self.derived)
        copied = X.copy(deep=True)
        probability = self.adapter.predict_positive(copied)
        try:
            pd.testing.assert_frame_equal(X, copied)
        except AssertionError as exc:
            raise ValueError("El adaptador mutó las entradas de inferencia") from exc
        validate_probabilities(probability, X.index)
        if self.adapter.fitted is not True or self.adapter.spec != self.spec:
            raise ValueError("El backend alteró identidad o estado de ajuste")
        return probability.copy(deep=True)

    def provenance(self) -> dict[str, Any]:
        """Entregar metadatos JSON del contrato, implementación y esquema ajustado.

        Returns:
            Identidad, configuración, semilla, estado y orden de características.
        """
        return {
            **asdict(self.spec),
            "candidate": self.spec.candidate,
            "implementation": type(self.adapter).__module__ + "." + type(self.adapter).__qualname__,
            "features": [*self.predictors, *self.derived],
            "dtypes": list(self.dtypes or ()),
            "fitted": self.fitted,
        }


def validate_predictions(frame: pd.DataFrame, keys: pd.DataFrame, candidate: str) -> None:
    """Comprobar contrato común de salida sin mezclar etiquetas observadas.

    Args:
        frame: Claves, candidato y probabilidad; no y_true.
        keys: Enlaces exactos autorizados por el arnés.
        candidate: Identidad esperada.
    """
    if (
        list(frame) != [*PREDICTION_KEYS, "candidate", "raw_probability"]
        or not frame[PREDICTION_KEYS].equals(keys[PREDICTION_KEYS])
        or frame.duplicated(PREDICTION_KEYS).any()
        or not frame.candidate.eq(candidate).all()
    ):
        raise ValueError("Claves/longitud/candidato de predicción inconsistentes")
    for column in ("origin_period", "target_period"):
        for period in keys[column]:
            validate_period(period)
        if keys[column].ge("2025-01").any():
            raise ValueError("Predicción con periodo reservado")
    if any(type(h) is not int or h not in (1, 2) for h in keys.horizon):
        raise ValueError("Horizonte de predicción inválido")
    expected = [
        add_months(t, h)
        for t, h in keys[["origin_period", "horizon"]].itertuples(index=False, name=None)
    ]
    if keys.target_period.tolist() != expected:
        raise ValueError("Calendario de predicción alterado")
    validate_probabilities(frame.raw_probability, keys.index)


def run_candidate(
    data: ExperimentData, experiment: ExperimentSpec, spec: AdapterSpec, registry: ModelRegistry
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Usar el mismo arnés para cualquier familia, sin duplicar evaluación.

    Args:
        data: X/y/claves/controles separados.
        experiment: Protocolo temporal aprobado.
        spec: Familia, configuración y semilla.
        registry: Constructores explícitos.

    Returns:
        Predicciones comunes sin etiquetas y auditoría de procedencia.
    """
    TemporalPolicy(experiment.reserved_start)
    if experiment.seed != spec.seed:
        raise ValueError("Semillas del protocolo y adaptador inconsistentes")
    adapters: list[ModelAdapter] = []
    wrappers: list[CheckedAdapter] = []

    def factory() -> CheckedAdapter:
        """Crear backend nuevo y proteger también contra reutilización oculta."""
        adapter = registry.create(spec)
        if any(adapter is previous for previous in adapters):
            raise ValueError("Fábrica reutilizó una instancia entre folds")
        adapters.append(adapter)
        # La receta declara el bloque derivado y la preparación lo adjunta: si
        # los dos no dicen lo mismo, la matriz que entrena no es la declarada.
        declarado = getattr(adapter, "derived", None)
        if declarado is not None and tuple(declarado) != tuple(data.derived):
            raise ValueError(
                "La receta declara derivadas "
                f"{tuple(declarado)} y la preparación entrega {tuple(data.derived)}"
            )
        wrapper = CheckedAdapter(adapter, derived=tuple(data.derived))
        wrappers.append(wrapper)
        return wrapper

    raw, audit = run_rolling(data, experiment, factory)
    frame = raw[PREDICTION_KEYS].copy()
    frame["candidate"] = spec.candidate
    frame["raw_probability"] = raw.raw_probability
    validate_predictions(frame, raw[PREDICTION_KEYS], spec.candidate)
    return frame, {
        **audit,
        "candidate": spec.candidate,
        "adapters": [wrapper.provenance() for wrapper in wrappers],
    }
