"""Contratos enlazados, estratos, diagnósticos y bootstrap municipal emparejado."""

import json
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from sat_dengue_pipeline.domain.calendar import add_months, validate_period
from sat_dengue_pipeline.experiments.procedure import (
    EvaluationPrediction,
    FittedProcedure,
    FrozenDecisions,
    predict_frozen,
)
from sat_dengue_pipeline.experiments.roles import RoleBatch
from sat_dengue_pipeline.experiments.rolling import KEY_COLUMNS, LINK, stable_digest
from sat_dengue_pipeline.models.adapters import PREDICTION_KEYS

from .metrics import DEFINITIONS_DIGEST, DIRECTIONS, metric_records, numeric

KEY = [*PREDICTION_KEYS, "candidate"]
METHODS = ("candidate", "train_prevalence", "persistence")


@dataclass(frozen=True)
class EvaluationTables:
    """Entradas separadas, cada tabla enlazada por las mismas seis claves."""

    keys: pd.DataFrame
    labels: pd.DataFrame
    probabilities: pd.DataFrame
    decisions: pd.DataFrame
    controls: pd.DataFrame
    strata: pd.DataFrame
    frozen_digest: str


@dataclass(frozen=True)
class EvaluationConfig:
    """Configuración descriptiva predeclarada; no selecciona umbrales ni modelos."""

    thresholds: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0)
    bootstrap_replicates: int = 200
    seed: int = 42
    min_clusters: int = 5
    percentiles: tuple[float, float] = (0.025, 0.975)

    def __post_init__(self) -> None:
        """Rechazar grillas, percentiles o soportes ambiguos."""
        if (
            not isinstance(self.thresholds, tuple)
            or not self.thresholds
            or self.thresholds != tuple(sorted(set(self.thresholds)))
            or any(not np.isfinite(t) or not 0 <= t <= 1 for t in self.thresholds)
            or type(self.bootstrap_replicates) is not int
            or self.bootstrap_replicates < 1
            or type(self.seed) is not int
            or self.seed < 0
            or type(self.min_clusters) is not int
            or self.min_clusters < 2
            or not 0 <= self.percentiles[0] < self.percentiles[1] <= 1
        ):
            raise ValueError("Configuración de evaluación inválida")


@dataclass(frozen=True)
class EvaluationReport:
    """Resultado agregado inmutable; no contiene filas o códigos municipales."""

    canonical_json: str

    @property
    def payload(self) -> dict[str, Any]:
        """Entregar una copia independiente de los agregados."""
        return json.loads(self.canonical_json)

    @property
    def digest(self) -> str:
        """Identificar todos los agregados, configuración y recibos."""
        return stable_digest(self.payload)


def validate_key_table(frame: pd.DataFrame) -> None:
    """Rechazar claves inválidas/reservadas antes de leer resultados observados.

    Args:
        frame: Tabla enlazada con las seis claves obligatorias.
    """
    if frame.empty or not set(KEY) <= set(frame) or frame.columns.duplicated().any():
        raise ValueError("Esquema de claves inválido")
    if frame[KEY].isna().any().any() or frame.duplicated(KEY).any():
        raise ValueError("Claves nulas o duplicadas")
    for code, origin, target, h, fold, candidate in frame[KEY].itertuples(index=False, name=None):
        if (
            not isinstance(code, str)
            or len(code) != 5
            or not code.isascii()
            or not code.isdigit()
            or type(h) is not int
            or h not in (1, 2)
            or not isinstance(fold, str)
            or not fold
            or not isinstance(candidate, str)
            or not candidate
        ):
            raise ValueError("Identidad de claves inválida")
        validate_period(origin)
        validate_period(target)
        if origin >= "2025-01" or target >= "2025-01":
            raise ValueError("Periodo reservado antes de leer etiquetas")
        if target != add_months(origin, h):
            raise ValueError("Calendario objetivo alterado")


def _joined(
    tables: EvaluationTables, frozen: FrozenDecisions, expected_digest: str
) -> pd.DataFrame:
    """Validar congelación y unir tablas uno a uno por claves, nunca posiciones."""
    if frozen.digest != expected_digest or tables.frozen_digest != expected_digest:
        raise ValueError("Decisiones no congeladas o digest alterado")
    frames = (
        tables.keys,
        tables.labels,
        tables.probabilities,
        tables.decisions,
        tables.controls,
        tables.strata,
    )
    for frame in frames:
        validate_key_table(frame)
    expected_columns = (
        KEY,
        KEY + ["onset"],
        KEY + ["candidate_probability", "train_prevalence"],
        KEY + ["candidate_decision", "persistence_decision"],
        KEY + ["context_evaluable", "label_available_period"],
        KEY + ["department_code"],
    )
    base = tables.keys.sort_values(KEY).reset_index(drop=True).copy()
    expected_keys = set(base[KEY].itertuples(index=False, name=None))
    for frame, columns in zip(frames, expected_columns, strict=True):
        if (
            list(frame) != columns
            or set(frame[KEY].itertuples(index=False, name=None)) != expected_keys
        ):
            raise ValueError("Tablas desalineadas o columnas desconocidas")
    if (
        not base.candidate.eq(frozen.candidate).all()
        or not base.horizon.eq(frozen.horizon).all()
        or not base.fold_id.eq("procedure-" + frozen.digest[:20]).all()
    ):
        raise ValueError("Identidad de evaluación alterada")
    for frame in frames[1:]:
        base = base.merge(frame, on=KEY, how="left", validate="one_to_one", sort=False)
    context = base.context_evaluable
    if not pd.api.types.is_bool_dtype(context) or context.isna().any():
        raise ValueError("Contexto de evaluabilidad inválido")
    for period in base.label_available_period:
        validate_period(period)
        if period >= "2025-01":
            raise ValueError("Disponibilidad reservada")
    if base.label_available_period.lt(base.target_period).any():
        raise ValueError("Disponibilidad anterior al objetivo")
    trace = json.loads(frozen.trace_json)
    linked = base[KEY_COLUMNS].sort_values(LINK).reset_index(drop=True)
    if stable_digest(linked.to_dict("records")) != trace["support"]["evaluation"]["keys_digest"]:
        raise ValueError("Cohorte diferente de la congelada")
    for name in ("onset", "candidate_decision", "persistence_decision"):
        base[name] = numeric(base[name], binary=True)
    for name in ("candidate_probability", "train_prevalence"):
        base[name] = numeric(base[name])
    known = base.candidate_decision.notna() & base.candidate_probability.notna()
    if (
        not base.loc[known, "candidate_decision"]
        .eq(base.loc[known, "candidate_probability"].ge(frozen.threshold).astype(int))
        .all()
    ):
        raise ValueError("La evaluación no puede reemplazar el umbral congelado")
    if (
        not base.train_prevalence.dropna().eq(frozen.train_prevalence).all()
        or not base.persistence_decision.dropna().eq(0).all()
    ):
        raise ValueError("Referencia no corresponde a decisiones congeladas")
    if (
        not base.department_code.map(
            lambda v: isinstance(v, str) and len(v) == 2 and v.isascii() and v.isdigit()
        ).all()
        or base.groupby("municipality_code").department_code.nunique().gt(1).any()
    ):
        raise ValueError("Estratos departamentales incompletos o contradictorios")
    base["prediction_missing"] = (
        base[
            [
                "candidate_probability",
                "train_prevalence",
                "candidate_decision",
                "persistence_decision",
            ]
        ]
        .isna()
        .any(axis=1)
    )
    return base


def tables_from_prediction(
    output: EvaluationPrediction,
    labels: pd.DataFrame,
    controls: pd.DataFrame,
    strata: pd.DataFrame,
) -> EvaluationTables:
    """Enlazar la salida coherente de tarea 10 con tablas externas ya identificadas.

    Args:
        output: Claves y series separadas de predict_frozen.
        labels: Etiquetas observadas con claves completas.
        controls: Contexto/disponibilidad con claves completas.
        strata: Departamento declarado explícitamente por claves.

    Returns:
        Contrato separado; no se derivan etiquetas de predicciones.
    """
    probabilities, decisions = output.keys.copy(), output.keys.copy()
    for series in (
        output.probability,
        output.prevalence_probability,
        output.decision,
        output.persistence_decision,
    ):
        if not series.index.equals(output.keys.index):
            raise ValueError("Salida de inferencia desalineada")
    probabilities["candidate_probability"] = output.probability
    probabilities["train_prevalence"] = output.prevalence_probability
    decisions["candidate_decision"] = output.decision
    decisions["persistence_decision"] = output.persistence_decision
    return EvaluationTables(
        output.keys.copy(),
        labels,
        probabilities,
        decisions,
        controls,
        strata,
        output.artifact_digest,
    )


def _method_metrics(frame: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    """Compartir soporte y disponibilidad entre los tres métodos."""
    usable = frame.context_evaluable & frame.onset.notna()
    support = frame.loc[usable]
    missing = int(support.prediction_missing.sum())
    missing_y = int(frame.onset.isna().sum())
    return {
        name: metric_records(
            support.onset,
            support[score],
            support[decision] if decision else None,
            probabilistic=probabilistic,
            missing_predictions=missing,
            missing_labels=missing_y,
        )
        for name, score, decision, probabilistic in (
            ("candidate", "candidate_probability", "candidate_decision", True),
            ("train_prevalence", "train_prevalence", None, True),
            ("persistence", "persistence_decision", "persistence_decision", False),
        )
    }


def _differences(methods: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Restar registros de exactamente la misma réplica/cohorte/estrato."""
    rows = []
    for reference in METHODS[1:]:
        for left, right in zip(methods["candidate"], methods[reference], strict=True):
            valid = left["evaluable"] and right["evaluable"]
            rows.append(
                {
                    "metric": left["metric"],
                    "reference": reference,
                    "value": left["value"] - right["value"] if valid else None,
                    "status": "OK" if valid else "NON_EVALUABLE_COMPARISON",
                    "evaluable": valid,
                    "improvement_direction": DIRECTIONS[left["metric"]],
                    "support_rows": left["support_rows"],
                }
            )
    return rows


def cluster_draws(frame: pd.DataFrame, config: EvaluationConfig) -> tuple[tuple[str, ...], ...]:
    """Remuestrear municipios completos con reemplazo y semilla explícita.

    Args:
        frame: Cohorte de un estrato, con toda su historia temporal.
        config: Número solicitado y semilla.

    Returns:
        Un único calendario de conglomerados compartido por todos los métodos.
    """
    codes = sorted(frame.municipality_code.unique())
    rng = np.random.default_rng(config.seed)
    return tuple(
        tuple(rng.choice(codes, size=len(codes), replace=True).tolist())
        for _ in range(config.bootstrap_replicates)
    )


def _uncertainty(
    frame: pd.DataFrame, config: EvaluationConfig
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Conservar réplicas indefinidas; intervalos solo si todas son válidas."""
    point = _differences(_method_metrics(frame))
    count = frame.loc[frame.context_evaluable & frame.onset.notna()].municipality_code.nunique()
    draws = cluster_draws(frame, config) if count >= config.min_clusters else ()
    replicas = []
    values = {(row["reference"], row["metric"]): [] for row in point}
    for number, draw in enumerate(draws):
        sample = pd.concat(
            [frame.loc[frame.municipality_code.eq(code)] for code in draw], ignore_index=True
        )
        for row in _differences(_method_metrics(sample)):
            values[row["reference"], row["metric"]].append(row["value"])
            replicas.append({**row, "replicate": number})
    intervals = []
    for row in point:
        samples = values[row["reference"], row["metric"]]
        valid = [value for value in samples if value is not None]
        status = (
            "INSUFFICIENT_CLUSTERS"
            if count < config.min_clusters
            else "OK_DESCRIPTIVE"
            if len(valid) == config.bootstrap_replicates
            else "UNDEFINED_REPLICATES"
        )
        bounds = (
            np.quantile(valid, config.percentiles, method="linear").tolist()
            if (status == "OK_DESCRIPTIVE")
            else [None, None]
        )
        intervals.append(
            {
                **row,
                "point_evaluable": row["evaluable"],
                "interval_evaluable": status == "OK_DESCRIPTIVE",
                "lower": bounds[0],
                "upper": bounds[1],
                "status": status,
                "requested_replicates": config.bootstrap_replicates,
                "valid_replicates": len(valid),
                "invalid_replicates": len(samples) - len(valid),
                "clusters": int(count),
                "min_clusters": config.min_clusters,
                "draws_digest": stable_digest(draws),
                "descriptive_only": True,
            }
        )
    return intervals, replicas


def evaluate(
    tables: EvaluationTables,
    frozen: FrozenDecisions,
    *,
    expected_digest: str,
    config: EvaluationConfig = EvaluationConfig(),
) -> EvaluationReport:
    """Evaluar después del freeze sin devolver decisiones de ajuste o campeón.

    Args:
        tables: Todas las entradas separadas y enlazadas por claves completas.
        frozen: Parámetros/decisiones de tarea 10 inmutables.
        expected_digest: Identidad congelada aprobada por el llamador.
        config: Diagnósticos y bootstrap predeclarados.

    Returns:
        Solo agregados deterministas, sin códigos municipales ni filas científicas.
    """
    frame = _joined(tables, frozen, expected_digest)
    metrics, comparisons, strata, curves, intervals, replicas = [], [], [], [], [], []
    groups = [("global", frame), (f"horizon:{frozen.horizon}", frame)]
    groups += [
        (f"department:{code}", group) for code, group in frame.groupby("department_code", sort=True)
    ]
    for stratum, group in groups:
        support = group.loc[group.context_evaluable & group.onset.notna()]
        keys_digest = stable_digest(support[KEY].to_dict("records"))
        identity = {
            "candidate": frozen.candidate,
            "horizon": frozen.horizon,
            "stratum": stratum,
            "paired_keys_digest": keys_digest,
        }
        methods = _method_metrics(group)
        for method, records in methods.items():
            metrics.extend({**row, **identity, "reference": method} for row in records)
        comparisons.extend({**row, **identity} for row in _differences(methods))
        strata.append(
            {
                **identity,
                "total_rows": len(group),
                "evaluable_rows": len(support),
                "positive_rows": int(support.onset.eq(1).sum()),
                "negative_rows": int(support.onset.eq(0).sum()),
                "municipalities": int(support.municipality_code.nunique()),
                "target_months": int(support.target_period.nunique()),
                "excluded_context": int((~group.context_evaluable).sum()),
                "excluded_missing_labels": int(
                    (group.context_evaluable & group.onset.isna()).sum()
                ),
                "missing_predictions": int(support.prediction_missing.sum()),
                "status": (
                    "MISSING_PREDICTIONS"
                    if support.prediction_missing.any()
                    else "SUFFICIENT_DESCRIPTIVE"
                    if support.onset.nunique() == 2
                    else "INSUFFICIENT_CLASSES"
                ),
            }
        )
        for threshold in config.thresholds:
            records = metric_records(
                support.onset,
                support.candidate_probability,
                support.candidate_probability.ge(threshold).astype("Int64"),
                probabilistic=True,
                missing_predictions=int(support.prediction_missing.sum()),
            )
            by_name = {row["metric"]: row for row in records}
            curves.append(
                {
                    **identity,
                    "threshold": threshold,
                    "diagnostic_only": True,
                    "alerts": by_name["alert_volume"]["value"],
                    "true_positives": by_name["onset_sensitivity"]["numerator"],
                    "false_alerts": by_name["false_alarm_ratio"]["numerator"],
                    "sensitivity": by_name["onset_sensitivity"]["value"],
                    "false_alarm_ratio": by_name["false_alarm_ratio"]["value"],
                    "relative_volume": by_name["alert_fraction"]["value"],
                    "status": by_name["alert_volume"]["status"],
                }
            )
        bounds, samples = _uncertainty(group, config)
        intervals.extend({**row, **identity} for row in bounds)
        replicas.extend({**row, **identity} for row in samples)
    payload = {
        "schema": "paired-evaluation-v1",
        "frozen_digest": frozen.digest,
        "definitions_digest": DEFINITIONS_DIGEST,
        "keys_digest": stable_digest(frame[KEY].to_dict("records")),
        "config": asdict(config),
        "metrics": metrics,
        "comparisons": comparisons,
        "strata": strata,
        "curves": curves,
        "uncertainty": intervals,
        "replicates": replicas,
    }
    return EvaluationReport(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
    )


def evaluate_procedure(
    fitted: FittedProcedure,
    batch: RoleBatch,
    strata: pd.DataFrame,
    *,
    expected_digest: str,
    config: EvaluationConfig = EvaluationConfig(),
) -> EvaluationReport:
    """Leer evaluation.y únicamente después de verificar freeze y producir inferencia.

    Args:
        fitted: Modelo y decisiones ya congeladas.
        batch: Evaluación con callback de etiquetas separadas de X.
        strata: Departamento enlazado por las seis claves, sin inferencias por posición.
        expected_digest: Identidad congelada que debe verificarse primero.
        config: Diagnósticos de evaluación.

    Returns:
        Agregados posteriores sin modificar el modelo o los parámetros congelados.
    """
    output = predict_frozen(fitted, batch, expected_digest=expected_digest)
    y = batch.read_y()
    if not y.index.equals(output.keys.index):
        raise ValueError("Etiquetas de evaluación desalineadas")
    labels = output.keys.copy()
    labels["onset"] = y
    controls = output.keys.copy()
    controls["context_evaluable"] = batch.controls.eligible_at_t
    controls["label_available_period"] = batch.keys.label_available_period
    tables = tables_from_prediction(output, labels, controls, strata)
    return evaluate(tables, fitted.decisions, expected_digest=expected_digest, config=config)
