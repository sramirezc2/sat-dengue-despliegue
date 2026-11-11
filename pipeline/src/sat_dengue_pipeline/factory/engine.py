"""Una corrida de fábrica: cinco fuentes neutrales, dos horizontes y lectura diferida."""

import importlib.metadata
import shutil
import subprocess
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import pandas as pd

from sat_dengue_pipeline.acquisition.contracts import ResolvedBundle, ResolvedFile
from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import KEYS, predictor_matrix
from sat_dengue_pipeline.domain.margin import MARGIN_COLUMNS, MARGIN_SOURCES, margin_features
from sat_dengue_pipeline.domain.temporal import TemporalPolicy, guard_development
from sat_dengue_pipeline.evaluation.metrics import DEFINITIONS_DIGEST, metric_records
from sat_dengue_pipeline.experiments.decisions import ThresholdPolicy, apply_sigmoid
from sat_dengue_pipeline.experiments.procedure import fit_procedure, predict_frozen
from sat_dengue_pipeline.experiments.roles import (
    ROLES,
    RoleBatch,
    observed_support,
    preflight_roles,
    support_passes,
)
from sat_dengue_pipeline.experiments.rolling import (
    ExperimentData,
    stable_digest,
    validate_data,
)
from sat_dengue_pipeline.factory.configuration import (
    adapter_spec,
    configuration_digest,
    project_root,
    temporal_plan,
)
from sat_dengue_pipeline.models.adapters import ModelRegistry
from sat_dengue_pipeline.models.familias import ADAPTERS
from sat_dengue_pipeline.preparation import prepare_horizon
from sat_dengue_pipeline.raw.build import build
from sat_dengue_pipeline.raw.contract import BuildConfig, sha256
from sat_dengue_pipeline.raw.serialization import _scalar, load_canonical


class FactoryGateError(ValueError):
    """Fallo de receta con causa fija, sin filas, rutas o excepciones de proveedores."""


@dataclass
class FactoryRun:
    """Estado privado exclusivo de un proceso; nunca se escribe como evidencia Git."""

    bundle: ResolvedBundle
    config: dict[str, Any]
    workspace: Path
    lineage: dict[str, Any]
    artifact: Any = None
    table: pd.DataFrame | None = None
    schema: dict[str, Any] = field(default_factory=dict)
    audit: dict[str, Any] = field(default_factory=dict)
    batches: dict[int, dict[str, RoleBatch]] = field(default_factory=dict)
    plans: dict[int, Any] = field(default_factory=dict)
    support: dict[str, Any] = field(default_factory=dict)
    temporal: dict[str, Any] = field(default_factory=dict)
    fitted: dict[int, Any] = field(default_factory=dict)
    predictions: dict[int, Any] = field(default_factory=dict)
    identities: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    prediction_complete: dict[int, bool] = field(default_factory=dict)
    label_reads: dict[str, int] = field(default_factory=dict)
    measurements: dict[str, float] = field(default_factory=dict)
    history_cache: dict[str, pd.DataFrame] = field(default_factory=dict)
    scientific_contexts: dict = field(default_factory=dict)
    scientific_outcomes: dict = field(default_factory=dict)
    scientific_policies: dict = field(default_factory=dict)
    stage: str = "initialization"


def table_digest(table: pd.DataFrame) -> str:
    """Identificar valores, orden, nombres, tipos y nulos, sin persistir las filas."""
    return stable_digest(
        {
            "columns": list(table),
            "dtypes": [str(t) for t in table.dtypes],
            "rows": [[_scalar(v) for v in row] for row in table.itertuples(index=False, name=None)],
        }
    )


def reconstruct(run: FactoryRun) -> FactoryRun:
    """Copiar exclusivamente los cinco crudos a inbox nuevo y construir desde cero."""
    run.stage = "canonical_build"
    inbox = run.workspace / "inbox"
    inbox.mkdir()
    files = []
    for file in run.bundle.files:
        destination = inbox / file.path.name
        shutil.copyfile(file.path, destination)
        files.append(ResolvedFile(file.logical_name, destination, file.size_bytes, file.sha256))
    run.bundle = replace(run.bundle, files=tuple(files))
    run.artifact, run.audit = build(
        run.bundle, BuildConfig(), run.workspace / "canonical", measurements=run.measurements
    )
    run.table, run.schema = load_canonical(run.artifact)
    run.identities["canonical"] = {
        "semantic_digest": run.artifact.semantic_digest,
        "serialized_sha256": run.artifact.serialized_sha256,
    }
    return run


def _deferred_batch(
    run: FactoryRun, h: int, role: str, origins: pd.DataFrame, history: pd.DataFrame
) -> RoleBatch:
    """Preparar solo claves y X; y se construye al consumir su rol autorizado."""
    selected = history.set_index(KEYS).loc[pd.MultiIndex.from_frame(origins[KEYS])].reset_index()
    X = predictor_matrix(selected, run.schema)
    scientific = run.config.get("schema_version") == 3
    secondary = scientific and run.config["scientific_dimensions"]["reading"] == "secondary_t2"
    features = run.config["predictors"] if scientific else list(X)
    complete_features = (
        [
            p
            for p in run.config["predictors"]
            + [n for arm in run.config["scientific_evaluation"]["arms"] for n in arm["predictors"]]
            if p in X
        ]
        if scientific and run.config["scientific_dimensions"]["population"] == "common"
        else features
    )
    # Bloque de margen: derivadas de preparación, construidas sobre la historia
    # ordenada del municipio porque las velocidades necesitan el mes anterior
    # aunque ese mes no sea un origen evaluable. Nunca entran al canónico.
    derived: list[str] = []
    if run.config["preparation"].get("variables_g"):
        block = margin_features(
            history, h, run.config["preparation"].get("margin_source", MARGIN_SOURCES[0])
        )
        claves = pd.MultiIndex.from_frame(selected[KEYS])
        for column in MARGIN_COLUMNS:
            X[column] = block[column].reindex(claves).to_numpy()
        derived = list(MARGIN_COLUMNS)
    features = [*features, *derived]
    complete_features = [*complete_features, *derived]
    usable = selected.zona_canal_t.notna() & selected.zona_canal_t.ne("EXCESO")
    if secondary:
        usable = selected.zona_canal_t.notna()
    usable &= X[complete_features].notna().all(axis=1)
    origins = selected.loc[usable, KEYS].reset_index(drop=True)
    X = X.loc[usable, features].reset_index(drop=True)
    keys = origins.rename(columns={"year_month": "origin_period"}).copy()
    keys["target_period"] = keys.origin_period.map(lambda t: add_months(t, h))
    keys["horizon"] = h
    keys["label_available_period"] = keys.target_period.map(
        lambda t: add_months(t, run.config["label_delay_months"])
    )

    def deferred() -> pd.Series:
        """Construir la etiqueta solo tras pasar las compuertas de claves."""
        if role == "evaluation" and not all(
            run.prediction_complete.get(horizon, False) for horizon in run.config["horizons"]
        ):
            raise FactoryGateError("evaluation_labels_before_predictions")
        key = f"{h}:{role}"
        run.label_reads[key] = run.label_reads.get(key, 0) + 1
        if run.label_reads[key] != 1:
            raise FactoryGateError("role_labels_read_more_than_once")
        if scientific:
            from sat_dengue_pipeline.domain.onset import build_labels

            states = history[KEYS].copy()
            states["excess"] = (
                history.zona_canal_t.eq("EXCESO")
                .astype("Int64")
                .where(history.zona_canal_t.notna(), pd.NA)
            )
            outcome = build_labels(states, origins, h, TemporalPolicy(run.config["reserved_start"]))
            run.scientific_outcomes[(h, role)] = outcome
            return outcome[f"y_t{h}"].reset_index(drop=True)
        _, labels, _, _ = prepare_horizon(
            history,
            run.schema,
            origins,
            h,
            run.config["predictor_availability"],
            TemporalPolicy(run.config["reserved_start"]),
        )
        values = labels.set_index(KEYS).loc[pd.MultiIndex.from_frame(origins[KEYS]), f"y_t{h}"]
        return values.reset_index(drop=True)

    if scientific:
        from sat_dengue_pipeline.evaluation.scientific.policy import origin_context

        run.scientific_contexts[(h, role)] = origin_context(run.table, keys, h)
    return RoleBatch(
        role,
        keys,
        X,
        pd.DataFrame({"eligible_at_t": [True] * len(keys)}),
        deferred,
        predictors=tuple(features),
        allow_excess_at_origin=secondary,
    )


def prepare(run: FactoryRun) -> FactoryRun:
    """Reutilizar guard V3 antes de etiquetas y preparar cinco roles por objetivo."""
    run.stage = "preparation"
    table = run.table
    for h in run.config["horizons"]:
        plan = temporal_plan(run.config, h)
        run.plans[h] = plan
        run.batches[h] = {}
        for window in plan.windows:
            targets = table.year_month.map(lambda t: add_months(t, h))
            origins = table.loc[targets.between(window.start, window.end), KEYS].reset_index(
                drop=True
            )
            guard_development(table[KEYS], origins, (h,), TemporalPolicy(plan.reserved_start))
            if window.end not in run.history_cache:
                run.history_cache[window.end] = table.loc[
                    table.year_month.le(window.end)
                ].reset_index(drop=True)
            history = run.history_cache[window.end]
            batch = _deferred_batch(run, h, window.role, origins, history)
            dummy_y = pd.Series(pd.NA, index=batch.keys.index, dtype="Int64")
            validate_data(
                ExperimentData(batch.keys, batch.X, dummy_y, batch.controls, batch.predictors),
                h,
                plan.reserved_start,
            )
            run.batches[h][window.role] = batch
    return run


def preflight(run: FactoryRun) -> FactoryRun:
    """Validar ambos horizontes y todos sus productores antes del primer fit."""
    run.stage = "producer_support"
    run.support = {
        str(h): {
            role: {
                **observed_support(run.batches[h][role]),
                "label_stage": "not_read",
            }
            for role in ROLES
        }
        for h in run.config["horizons"]
    }
    # Todas las claves de ambos horizontes pasan antes de cualquier callback y.
    for h in run.config["horizons"]:
        try:
            run.temporal[str(h)] = preflight_roles(run.batches[h], run.plans[h])
        except ValueError as error:
            raise FactoryGateError(f"role_metadata_failed:T{h}") from error
    failures = []
    for h in run.config["horizons"]:
        run.support[str(h)] = {}
        for role in ROLES:
            batch = run.batches[h][role]
            y = None if role == "evaluation" else batch.read_y()
            counts = observed_support(batch, y)
            counts["passed"] = support_passes(counts, run.plans[h], role)
            counts["label_stage"] = "deferred_until_predictions" if y is None else "before_fit"
            run.support[str(h)][role] = counts
            if not counts["passed"]:
                failures.append(f"T{h}:{role}")
            if y is not None:
                run.batches[h][role] = replace(
                    batch, read_y=lambda values=y: values.copy(deep=True)
                )
    if failures:
        raise FactoryGateError("producer_support_failed:" + ",".join(failures))
    run.temporal["all_producer_support_before_any_fit"] = True
    return run


def fit(run: FactoryRun) -> FactoryRun:
    """Ajustar un modelo independiente por horizonte sin tocar evaluation.y."""
    run.stage = "fit_calibration_threshold"
    registry = ModelRegistry()
    spec = adapter_spec(run.config)
    registry.register(spec.family, spec.version, ADAPTERS[(spec.family, spec.version)])
    for h in run.config["horizons"]:
        policy = ThresholdPolicy(
            tuple(run.config["threshold"]["grid"]),
            run.config["threshold"]["max_false_alarm_ratio_by_horizon"][str(h)],
        )
        run.fitted[h] = fit_procedure(
            run.batches[h],
            run.plans[h],
            spec,
            registry,
            policy,
            calibration_parameters=run.config["calibration"]["parameters"],
            brier_tolerance=run.config["calibration"]["brier_tolerance"],
        )
        if run.label_reads.get(f"{h}:evaluation", 0):
            raise FactoryGateError("evaluation_labels_during_fit")
    if run.config.get("schema_version") == 3:
        from sat_dengue_pipeline.evaluation.scientific.policy import freeze_policy

        freeze_policy(run)
    if len({id(f.model.adapter) for f in run.fitted.values()}) != len(run.fitted):
        raise FactoryGateError("shared_horizon_model")
    return run


def predict(run: FactoryRun) -> FactoryRun:
    """Congelar y producir predicciones antes de liberar etiquetas de evaluación."""
    run.stage = "prediction"
    for h in run.config["horizons"]:
        fitted = run.fitted[h]
        adapter = fitted.model.adapter
        before = adapter.model_sha256()
        run.predictions[h] = predict_frozen(
            fitted, run.batches[h]["evaluation"], expected_digest=fitted.decisions.digest
        )
        roles = {}
        for role in ROLES:
            batch = run.batches[h][role]
            raw = fitted.model.predict_positive(batch.X)
            calibrated = apply_sigmoid(
                raw, fitted.decisions.coefficient, fitted.decisions.intercept
            )
            roles[role] = {
                "keys": table_digest(batch.keys),
                "predictors": table_digest(batch.X),
                "matrix": stable_digest(
                    {
                        "columns": run.config["preparation"]["matrix_columns"],
                        "dtype": run.config["preparation"]["matrix_dtype"],
                        "values": adapter.matrix(batch.X).astype(float).tolist(),
                    }
                ),
                "raw_probability": table_digest(raw.to_frame("probability")),
                "calibrated_probability": table_digest(calibrated.to_frame("probability")),
            }
        if before != adapter.model_sha256() or adapter.fit_calls != 1:
            raise FactoryGateError("model_state_changed_during_prediction")
        output = run.predictions[h]
        run.identities[str(h)] = {
            "roles": roles,
            "model_json": before,
            "native_configuration": stable_digest(adapter.native_configuration()),
            "frozen_decisions": fitted.decisions.digest,
            "prediction_keys": table_digest(output.keys),
            "probability": table_digest(output.probability.to_frame("probability")),
            "decisions": table_digest(output.decision.to_frame("decision")),
        }
        run.prediction_complete[h] = True
    return run


def evaluate(run: FactoryRun) -> FactoryRun:
    """Leer y_eval una vez después de predicciones; fallar sin reajustar si falta soporte."""
    if run.config.get("schema_version") == 3:
        from sat_dengue_pipeline.evaluation.scientific.reporting import read_outcomes

        read_outcomes(run)
        return run
    run.stage = "evaluation_support"
    labels = {}
    failures = []
    for h in run.config["horizons"]:
        batch = run.batches[h]["evaluation"]
        y = batch.read_y()
        labels[h] = y
        counts = observed_support(batch, y)
        counts["passed"] = support_passes(counts, run.plans[h], "evaluation")
        counts["label_stage"] = "after_freeze_and_predictions"
        run.support[str(h)]["evaluation"] = counts
        if not counts["passed"]:
            failures.append(f"T{h}:evaluation")
    if failures:
        raise FactoryGateError("evaluation_support_failed:" + ",".join(failures))
    run.stage = "metrics"
    for h in run.config["horizons"]:
        output, y, fitted = run.predictions[h], labels[h], run.fitted[h]
        metrics = {
            "candidate": metric_records(y, output.probability, output.decision, probabilistic=True),
            "train_prevalence": metric_records(
                y, output.prevalence_probability, None, probabilistic=True
            ),
            "persistence": metric_records(
                y, output.persistence_decision, output.persistence_decision, probabilistic=False
            ),
        }
        run.results[str(h)] = {
            "representation": fitted.decisions.representation,
            "threshold": fitted.decisions.threshold,
            "calibrator": {
                "coefficient": fitted.decisions.coefficient,
                "intercept": fitted.decisions.intercept,
            },
            "fit_calls": fitted.model.adapter.fit_calls,
            "metrics": metrics,
        }
        run.identities[str(h)]["evaluation_labels"] = table_digest(y.to_frame("onset"))
        run.identities[str(h)]["metrics"] = stable_digest(metrics)
    run.temporal["evaluation_reads_after_both_predictions"] = True
    return run


def receipt(run: FactoryRun) -> dict[str, Any]:
    """Proyectar solo agregados y huellas; nunca modelos, matrices o códigos de filas."""
    run.stage = "complete"
    identity = {
        "configuration": configuration_digest(run.config),
        "lineage": run.lineage,
        "artifacts": run.identities,
        "decisions_metrics": stable_digest(run.results),
        "support": stable_digest(run.support),
        "temporal": stable_digest(run.temporal),
        "canonical_audit": stable_digest(run.audit),
    }
    return {
        "status": "PASSED",
        "specification": run.config["specification"],
        "identity_sha256": stable_digest(identity),
        "identity": identity,
        "support": run.support,
        "temporal": run.temporal,
        "results": run.results,
        "quarantine": run.audit["quarantine"],
        "coverage": run.audit["coverage"],
        "governance": run.config["governance"],
        "label_reads": run.label_reads,
    }


def source_lineage(bundle: ResolvedBundle, config: dict[str, Any]) -> dict[str, Any]:
    """Trazar ciencia/lock/fuentes, sin rutas, reloj, ID de corrida o credenciales."""
    root = project_root()
    code = {
        str(path.relative_to(root)): sha256(path) for path in sorted((root / "src").rglob("*.py"))
    }
    return {
        "builder_git_sha": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "source_code_sha256": stable_digest(code),
        "lock_sha256": sha256(root / "uv.lock"),
        "configuration_sha256": configuration_digest(config),
        "release_id": bundle.release_id,
        "raw_manifest_sha256": bundle.manifest_sha256,
        "raw_hashes": {file.logical_name: file.sha256 for file in bundle.files},
        "definitions_sha256": DEFINITIONS_DIGEST,
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in (
                "xgboost",
                "numpy",
                "pandas",
                "scikit-learn",
                "scipy",
                "kedro",
            )
        },
    }
