"""Congelar candidato, calibración y umbral antes de consumir evaluación."""

import json
from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

import pandas as pd
import sklearn

from sat_dengue_pipeline.domain.calendar import add_months, validate_period
from sat_dengue_pipeline.models.adapters import (
    AdapterSpec,
    CheckedAdapter,
    ModelRegistry,
    validate_probabilities,
)

from .decisions import (
    ThresholdPolicy,
    apply_sigmoid,
    choose_representation,
    fit_sigmoid,
    select_threshold,
)
from .roles import RoleBatch, TemporalPlan, preflight_roles, role_labels
from .rolling import LINK, ExperimentData, stable_digest, validate_data


@dataclass(frozen=True)
class FrozenDecisions:
    """Parámetros numéricos y decisiones serializables, sin estimadores o pickle."""

    candidate: str
    horizon: int
    representation: str
    coefficient: float
    intercept: float
    threshold: float
    train_prevalence: float
    available_period: str
    trace_json: str

    def __post_init__(self) -> None:
        """Rechazar estados inválidos o umbrales alterados respecto de la selección."""
        validate_period(self.available_period)
        trace = json.loads(self.trace_json)
        if (
            type(self.horizon) is not int
            or self.horizon not in (1, 2)
            or self.representation not in {"original", "sigmoid"}
            or self.available_period >= "2025-01"
            or not all(
                isfinite(v)
                for v in (self.coefficient, self.intercept, self.threshold, self.train_prevalence)
            )
            or not 0 <= self.threshold <= 1
            or not 0 <= self.train_prevalence <= 1
            or trace["selected_threshold"] != self.threshold
            or trace["representation"] != self.representation
            or trace["candidate"] != self.candidate
            or trace["calibrator"]["coefficient"] != self.coefficient
            or trace["calibrator"]["intercept"] != self.intercept
            or trace["train_prevalence"] != self.train_prevalence
            or trace["plan"]["horizon"] != self.horizon
            or trace["support"]["threshold_selection"]["available"] != self.available_period
        ):
            raise ValueError("Decisión congelada inconsistente o alterada")
        stable_digest(trace)

    @property
    def digest(self) -> str:
        """Identificar parámetros, políticas, fuentes de ajuste y decisión."""
        return stable_digest(asdict(self))

    def to_json(self) -> str:
        """Serializar con recibo de integridad estable, sin persistencia implícita.

        Returns:
            JSON canónico con payload y SHA-256.
        """
        return json.dumps(
            {"schema": "temporal-decisions-v1", "payload": asdict(self), "sha256": self.digest},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def from_json(cls, text: str) -> "FrozenDecisions":
        """Restaurar parámetros verificados sin ajustar o seleccionar de nuevo.

        Args:
            text: Serialización generada por to_json.

        Returns:
            Decisión inmutable, o error si cambió payload/digest/esquema.
        """
        record = json.loads(text)
        if (
            set(record) != {"schema", "payload", "sha256"}
            or record["schema"] != ("temporal-decisions-v1")
            or stable_digest(record["payload"]) != record["sha256"]
        ):
            raise ValueError("Recibo de decisión inválido")
        try:
            return cls(**record["payload"])
        except (TypeError, KeyError) as exc:
            raise ValueError("Payload de decisión inválido") from exc


@dataclass(frozen=True)
class FittedProcedure:
    """Modelo ajustado una vez y parámetros congelados de sus decisiones."""

    model: CheckedAdapter
    decisions: FrozenDecisions


@dataclass(frozen=True)
class EvaluationPrediction:
    """Claves, probabilidades, decisiones y referencias; ninguna etiqueta observada."""

    keys: pd.DataFrame
    raw_probability: pd.Series
    probability: pd.Series
    decision: pd.Series
    prevalence_probability: pd.Series
    persistence_decision: pd.Series
    artifact_digest: str


def fit_procedure(
    batches: dict[str, RoleBatch],
    plan: TemporalPlan,
    spec: AdapterSpec,
    registry: ModelRegistry,
    threshold_policy: ThresholdPolicy,
    *,
    calibration_parameters: dict[str, Any] | None = None,
    brier_tolerance: float = 1e-12,
    training_weighting: dict | None = None,
) -> FittedProcedure:
    """Ajustar y congelar etapas usando exclusivamente su rol autorizado.

    Args:
        batches: Cinco roles; evaluation.read_y jamás se invoca aquí.
        plan: Calendario, disponibilidad y soporte mínimos.
        spec: Candidato predeclarado; no se hace búsqueda de hiperparámetros.
        registry: Constructor neutral del candidato.
        threshold_policy: Cuadrícula y límite explícitos, definidos antes del ajuste.
        calibration_parameters: Parámetros completos aprobados, sin decisiones implícitas.
        brier_tolerance: Mejora mínima aprobada antes de escoger sigmoide.
        training_weighting: Pesos solo del modelo; otros ajustes permanecen sin ponderar.

    Returns:
        Procedimiento listo para inferencia posterior, sin consumir evaluación.
    """
    audit = preflight_roles(batches, plan)
    labels = {
        name: role_labels(batches[name], plan)
        for name in ("train", "calibration_fit", "calibration_selection", "threshold_selection")
    }
    train = batches["train"]
    y_train = labels["train"]
    model = CheckedAdapter(registry.create(spec), predictors=train.predictors)
    weight_summary = None
    if training_weighting is not None:
        from .weighting import training_weights

        weights, weight_summary = training_weights(train.keys, training_weighting)
    if training_weighting is not None and training_weighting["method"] != "uniform":
        model.fit(train.X, y_train, sample_weight=weights)
    else:
        model.fit(train.X, y_train)
    prevalence = float(y_train.mean())
    fit = batches["calibration_fit"]
    raw_fit = model.predict_positive(fit.X)
    y_fit = labels["calibration_fit"]
    if calibration_parameters is None:
        coefficient, intercept = fit_sigmoid(raw_fit, y_fit, spec.seed)
    else:
        coefficient, intercept = fit_sigmoid(
            raw_fit, y_fit, spec.seed, parameters=calibration_parameters
        )
    selection = batches["calibration_selection"]
    raw_selection = model.predict_positive(selection.X)
    calibrated = apply_sigmoid(raw_selection, coefficient, intercept)
    y_selection = labels["calibration_selection"]
    if brier_tolerance == 1e-12:
        representation, scores = choose_representation(raw_selection, calibrated, y_selection)
    else:
        representation, scores = choose_representation(
            raw_selection, calibrated, y_selection, tolerance=brier_tolerance
        )
    threshold_batch = batches["threshold_selection"]
    raw_threshold = model.predict_positive(threshold_batch.X)
    probability = (
        apply_sigmoid(raw_threshold, coefficient, intercept)
        if representation == "sigmoid"
        else raw_threshold
    )
    y_threshold = labels["threshold_selection"]
    threshold, grid = select_threshold(probability, y_threshold, threshold_policy)
    labels = {
        "train": y_train,
        "calibration_fit": y_fit,
        "calibration_selection": y_selection,
        "threshold_selection": y_threshold,
    }
    trace: dict[str, Any] = {
        **audit,
        "candidate": spec.candidate,
        "train_prevalence": prevalence,
        "adapter": model.provenance(),
        "representation": representation,
        "calibration_selection": scores,
        "calibrator": {
            "coefficient": coefficient,
            "intercept": intercept,
            "method": "logistic_on_raw_probability",
            "sklearn": sklearn.__version__,
        },
        "threshold_policy": asdict(threshold_policy),
        "threshold_grid": grid,
        "selected_threshold": threshold,
        "input_digests": {},
        "persistence": "non_excess_persists_no_new_onset; deterministic_only",
    }
    for name, y in labels.items():
        trace["input_digests"][name] = stable_digest(
            {
                "keys": batches[name].keys.to_dict("records"),
                "X": batches[name].X.to_dict("records"),
                "y": [int(v) for v in y],
            }
        )
    if weight_summary is not None:
        trace["training_weighting"] = weight_summary
    if train.allow_excess_at_origin:
        trace["allow_excess_at_origin"] = True
    if list(train.predictors) != list(batches["evaluation"].X):
        raise ValueError("Esquema de evaluación distinto del entrenamiento")
    # Ni etiquetas ni valores X de evaluación intervienen en el artefacto.
    frozen = FrozenDecisions(
        spec.candidate,
        plan.horizon,
        representation,
        coefficient,
        intercept,
        threshold,
        prevalence,
        audit["support"]["threshold_selection"]["available"],
        json.dumps(
            trace, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ),
    )
    return FittedProcedure(model, frozen)


def predict_frozen(
    fitted: FittedProcedure, evaluation: RoleBatch, *, expected_digest: str
) -> EvaluationPrediction:
    """Aplicar decisiones congeladas y referencias con las mismas claves, sin y.

    Args:
        fitted: Un solo modelo y decisiones ya congeladas.
        evaluation: Entrada posterior; no se consulta read_y.
        expected_digest: Identidad aprobada por el llamador, sin override de umbral.

    Returns:
        Predicción y referencias sobre todo el soporte declarado. Ausencias de
        etiquetas se preservan externamente para la futura evaluación de tarea 11.
    """
    frozen = fitted.decisions
    if frozen.digest != expected_digest or fitted.model.spec.candidate != frozen.candidate:
        raise ValueError("Identidad congelada alterada; no se permite override silencioso")
    dummy = pd.Series(pd.NA, index=evaluation.keys.index, dtype="Int64")
    trace = json.loads(frozen.trace_json)
    validate_data(
        ExperimentData(
            evaluation.keys, evaluation.X, dummy, evaluation.controls, evaluation.predictors
        ),
        frozen.horizon,
        trace["plan"]["reserved_start"],
    )
    if (
        evaluation.role != "evaluation"
        or stable_digest(evaluation.keys.to_dict("records"))
        != trace["support"]["evaluation"]["keys_digest"]
        or not evaluation.controls.eligible_at_t.all()
        or (
            not trace.get("allow_excess_at_origin", False)
            and "zona_canal_t" in evaluation.X
            and evaluation.X.zona_canal_t.eq("EXCESO").any()
        )
        or add_months(frozen.available_period, trace["plan"]["embargo_months"])
        >= str(evaluation.keys.origin_period.min())
    ):
        raise ValueError("Evaluación sin soporte común o disponibilidad previa")
    raw = fitted.model.predict_positive(evaluation.X)
    probability = (
        apply_sigmoid(raw, frozen.coefficient, frozen.intercept)
        if frozen.representation == "sigmoid"
        else raw.copy()
    )
    decision = probability.ge(frozen.threshold).astype("Int64")
    prevalence = pd.Series(frozen.train_prevalence, index=raw.index, dtype=float)
    validate_probabilities(prevalence, raw.index)
    # Persistir no exceso observado no produce una transición de inicio.
    persistence = pd.Series(0, index=raw.index, dtype="Int64")
    keys = evaluation.keys[LINK].copy()
    keys["fold_id"] = "procedure-" + frozen.digest[:20]
    keys["candidate"] = frozen.candidate
    return EvaluationPrediction(
        keys, raw, probability, decision, prevalence, persistence, frozen.digest
    )
