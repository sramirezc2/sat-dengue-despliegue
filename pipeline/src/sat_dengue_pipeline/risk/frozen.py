"""Materialización única y carga verificable de la logística aprobada."""

import subprocess
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.domain.canonical import KEYS
from sat_dengue_pipeline.domain.temporal import TemporalPolicy, guard_development
from sat_dengue_pipeline.factory.configuration import adapter_spec
from sat_dengue_pipeline.models.logistic import LogisticOnsetAdapter, canonical_json
from sat_dengue_pipeline.pipelines.deployment_publication.contract import decode_json

from .configuration import BASE, GENERATED, RECIPE_SHA, ROOT, digest, procedure, recipe, sha

ARTIFACT_CONTRACT = "satd-frozen-logistic-v1"


@dataclass(frozen=True)
class FrozenLogistic:
    """Estado predictivo completo; esta interfaz no expone fit."""

    payload: dict[str, Any]
    artifact_sha256: str

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """Aplicar el margen lineal congelado, sin etiquetas o probabilidades públicas."""
        state = self.payload["state"]
        adapter = LogisticOnsetAdapter(adapter_spec(recipe()))
        if list(X) != self.payload["predictors"] or [str(t) for t in X.dtypes] != state["dtypes"]:
            raise ValueError("Predictores, orden o tipos distintos del ajuste")
        matrix = adapter.matrix(X)
        score = ((matrix - state["mean"]) / state["std"]) @ np.array(state["coef"])
        score += state["intercept"]
        if not np.isfinite(score).all():
            raise ValueError("Score no finito")
        return score


def materialize(table: pd.DataFrame, schema: dict, provenance: dict) -> FrozenLogistic:
    """Ajustar una vez, solo en train anterior al ancla aprobada.

    Args:
        table: Prefijo de desarrollo, como máximo 2024-10.
        schema: Roles del constructor canónico.
        provenance: Identidad de código, lock y manifiesto crudo.

    Returns:
        Estado canónico exacto del estimador y su preparación, aún sin publicación.
    """
    from sat_dengue_pipeline.preparation import prepare_horizon

    config = recipe()
    if table.year_month.max() > "2024-10":
        raise ValueError("Observaciones posteriores al corte de aprendizaje")
    targets = table.year_month.map(lambda t: add_months(t, 2))
    available = targets.map(lambda t: add_months(t, config["label_delay_months"]))
    origins = table.loc[
        targets.between("2012-01", "2024-09") & available.le("2024-10"), KEYS
    ].copy()
    guard_development(table, origins, (2,), TemporalPolicy())
    _, _, train, _ = prepare_horizon(table, schema, origins, 2, config["predictor_availability"])
    if train.X.empty or set(train.y.unique()) != {0, 1}:
        raise ValueError("Soporte de entrenamiento insuficiente")
    adapter = LogisticOnsetAdapter(adapter_spec(config))
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        adapter.fit(train.X, train.y)
    # model_json histórico redondea: conservarlo intacto y guardar aquí los mismos
    # parámetros efectivos con float JSON de ida y vuelta, sin pérdida deliberada.
    state = {
        "coef": adapter._model.coef_[0].tolist(),
        "intercept": float(adapter._model.intercept_[0]),
        "mean": adapter._mean.tolist(),
        "std": adapter._std.tolist(),
        "dtypes": [str(t) for t in train.X.dtypes],
        "native_configuration": adapter.native_configuration(),
    }
    keys = train.keys.to_dict("records")
    payload = {
        "contract": ARTIFACT_CONTRACT,
        "recipe_sha256": RECIPE_SHA,
        "recipe_commit": BASE,
        "recipe": config,
        "procedure": procedure(),
        "logical_generated_at": GENERATED,
        "provenance": provenance,
        "predictors": config["predictors"],
        "matrix_columns": config["preparation"]["matrix_columns"],
        "training_keys_sha256": digest(keys),
        "training_matrix_sha256": digest(train.X.to_dict("records")),
        "training_labels_sha256": digest(train.y.astype(int).tolist()),
        "training_rows": len(keys),
        "last_training_target": max(add_months(k["year_month"], 2) for k in keys),
        "last_training_available": max(add_months(k["year_month"], 3) for k in keys),
        "state": state,
        "effective_state_sha256": digest(state),
        "fit_calls": adapter.fit_calls,
    }
    raw = canonical_json(payload)
    frozen = decode_artifact(raw, sha(raw), provenance)
    expected = adapter._model.decision_function(
        (adapter.matrix(train.X) - adapter._mean) / adapter._std
    )
    if not np.array_equal(frozen.score(train.X), expected):
        raise ValueError("La persistencia modifica el estado efectivo")
    return frozen


def decode_artifact(raw: bytes, expected_sha: str, provenance: dict) -> FrozenLogistic:
    """Fallar antes de scoring si cambia identidad, esquema, corte o estado."""
    if sha(raw) != expected_sha:
        raise ValueError("SHA-256 del artefacto no aprobado")
    p = decode_json(raw)
    config = recipe()
    fields = {
        "contract",
        "recipe_sha256",
        "recipe_commit",
        "recipe",
        "procedure",
        "logical_generated_at",
        "provenance",
        "predictors",
        "matrix_columns",
        "training_keys_sha256",
        "training_matrix_sha256",
        "training_labels_sha256",
        "training_rows",
        "last_training_target",
        "last_training_available",
        "state",
        "effective_state_sha256",
        "fit_calls",
    }
    if (
        set(p) != fields
        or p["contract"] != ARTIFACT_CONTRACT
        or p["recipe_sha256"] != RECIPE_SHA
        or p["recipe_commit"] != BASE
        or p["recipe"] != config
        or p["procedure"] != procedure()
        or p["logical_generated_at"] != GENERATED
        or {k: v for k, v in p["provenance"].items() if k != "code_sha"}
        != {k: v for k, v in provenance.items() if k != "code_sha"}
        or p["predictors"] != config["predictors"]
        or p["matrix_columns"] != config["preparation"]["matrix_columns"]
        or p["fit_calls"] != 1
        or p["training_rows"] < 2
        or not "2012-01" <= p["last_training_target"] <= "2024-09"
        or p["last_training_available"] != add_months(p["last_training_target"], 1)
        or p["last_training_available"] > "2024-10"
        or digest(p["state"]) != p["effective_state_sha256"]
    ):
        raise ValueError("Identidad o corte del artefacto incompatible")
    if p["provenance"]["code_sha"] != provenance["code_sha"]:
        ancestor = subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                p["provenance"]["code_sha"],
                provenance["code_sha"],
            ],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if ancestor.returncode:
            raise ValueError("El commit del artefacto no es un ancestro verificable")
    state = p["state"]
    adapter = LogisticOnsetAdapter(adapter_spec(config))
    expected_native = {
        "estimator": "LogisticRegression",
        "library_version": config["candidate"]["library_version"],
        "params": LogisticRegression(
            C=float(adapter.candidate["C"]),
            max_iter=adapter.candidate["max_iter"],
            random_state=adapter.spec.seed,
        ).get_params(),
    }
    if state["native_configuration"] != expected_native:
        raise ValueError("Versión o parámetros efectivos incompatibles")
    if set(state) != {"coef", "intercept", "mean", "std", "dtypes", "native_configuration"}:
        raise ValueError("Esquema del estado incompatible")
    n = len(p["matrix_columns"])
    for name in ("coef", "mean", "std"):
        values = np.asarray(state[name], dtype=float)
        if values.shape != (n,) or not np.isfinite(values).all():
            raise ValueError("Dimensión o estado no finito")
    if not np.isfinite(state["intercept"]) or np.any(np.array(state["std"]) <= 0):
        raise ValueError("Preparación congelada inválida")
    if len(state["dtypes"]) != len(p["predictors"]):
        raise ValueError("Tipos de entrada incompletos")
    return FrozenLogistic(p, expected_sha)


def save_artifact(model: FrozenLogistic, directory: Path) -> dict:
    """Reservar directorio nuevo; el manifiesto es el marcador final de completitud."""
    directory.mkdir(parents=True, exist_ok=False)
    raw = canonical_json(model.payload)
    if sha(raw) != model.artifact_sha256:
        raise ValueError("Artefacto alterado antes de persistir")
    with (directory / "model.json").open("xb") as stream:
        stream.write(raw)
    manifest = {
        "contract": ARTIFACT_CONTRACT,
        "artifact_sha256": sha(raw),
        "effective_state_sha256": model.payload["effective_state_sha256"],
    }
    with (directory / "manifest.json").open("xb") as stream:
        stream.write(canonical_json(manifest))
    return manifest


def load_artifact(directory: Path, expected_sha: str, provenance: dict) -> FrozenLogistic:
    """Exigir artefacto y manifiesto aprobados; nunca ajustar como fallback."""
    from sat_dengue_pipeline.canonical_cache import reject_cache_symlinks

    for name in ("model.json", "manifest.json"):
        reject_cache_symlinks(directory / name)
    manifest = decode_json((directory / "manifest.json").read_bytes())
    if set(manifest) != {"contract", "artifact_sha256", "effective_state_sha256"} or (
        manifest["contract"] != ARTIFACT_CONTRACT or manifest["artifact_sha256"] != expected_sha
    ):
        raise ValueError("Manifiesto de artefacto no aprobado")
    frozen = decode_artifact((directory / "model.json").read_bytes(), expected_sha, provenance)
    if manifest["effective_state_sha256"] != frozen.payload["effective_state_sha256"]:
        raise ValueError("Estado y manifiesto distintos")
    return frozen
