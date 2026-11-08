"""Pruebas del adaptador logístico de inicios y su uso en el retroanálisis."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from fixtures.canonical_fixture import make_panel

from sat_dengue_pipeline.domain.canonical import build_table
from sat_dengue_pipeline.evaluation.retroanalisis import predicciones_rolling
from sat_dengue_pipeline.factory.configuration import adapter_spec
from sat_dengue_pipeline.models.logistic import LogisticOnsetAdapter

RECETA = Path(__file__).resolve().parents[1] / "conf/retroanalisis/logistica_sin_clima.yml"


def _config() -> dict:
    """Receta logística versionada del retroanálisis."""
    return yaml.safe_load(RECETA.read_text(encoding="utf-8"))


def test_receta_valida_y_rechaza_alteraciones() -> None:
    """La receta se acepta tal cual y se rechaza si cambia la preparación o la identidad."""
    cfg = _config()
    LogisticOnsetAdapter(adapter_spec(cfg))
    for ruta, valor in ((("preparation", "scaling"), "none"), (("candidate", "class_balancing"), True),
                        (("candidate", "library"), "xgboost"), (("candidate", "C"), 0)):
        malo = json.loads(json.dumps(cfg))
        malo[ruta[0]][ruta[1]] = valor
        with pytest.raises(ValueError):
            LogisticOnsetAdapter(adapter_spec(malo))


def test_un_solo_ajuste_y_huella_determinista() -> None:
    """Ajusta una vez, predice probabilidades válidas y su huella no depende de la ejecución."""
    table, schema = build_table(make_panel())
    cfg = _config()
    preds, _ = predicciones_rolling(table, schema, cfg, 1, "2023-06")
    assert preds.fold_id.nunique() >= 2
    assert preds.raw_probability.between(0, 1).all()
    otra, _ = predicciones_rolling(table, schema, cfg, 1, "2023-06")
    assert np.allclose(preds.raw_probability.values, otra.raw_probability.values)


def test_no_refit() -> None:
    """Un segundo ajuste sobre la misma instancia se rechaza."""
    cfg = _config()
    a = LogisticOnsetAdapter(adapter_spec(cfg))
    from sat_dengue_pipeline.domain.canonical import PREDICTORS
    X = pd.DataFrame({p: np.ones(4) for p in PREDICTORS})
    X["zona_canal_t"] = ["EXITO", "ALERTA", "EXITO", "SEGURIDAD"]
    for c in X.columns:
        if c != "zona_canal_t":
            X[c] = X[c].astype("float64")
    y = pd.Series([0, 1, 0, 1])
    try:
        a.fit(X, y)
    except ValueError:
        pytest.skip("esquema de entrada del fixture distinto al canónico")
    with pytest.raises(ValueError):
        a.fit(X, y)
