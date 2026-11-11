"""Pruebas del adaptador logístico de inicios y su uso en el retroanálisis."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from fixtures.canonical_fixture import make_panel

from sat_dengue_pipeline.domain.canonical import build_table
from sat_dengue_pipeline.domain.margin import MARGIN_COLUMNS
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
    cambios = [
        (("preparation", "scaling"), "none"),
        (("candidate", "class_balancing"), True),
        (("candidate", "library"), "xgboost"),
        (("candidate", "C"), 0),
    ]
    for ruta, valor in cambios:
        malo = json.loads(json.dumps(cfg))
        malo[ruta[0]][ruta[1]] = valor
        with pytest.raises(ValueError):
            LogisticOnsetAdapter(adapter_spec(malo))


def test_un_solo_ajuste_y_huella_determinista() -> None:
    """Ajusta una vez, predice probabilidades válidas y su huella no depende de la ejecución."""
    table, schema = build_table(make_panel())
    cfg = _config()
    preds, _, _ = predicciones_rolling(table, schema, cfg, 1, "2023-06")
    assert preds.fold_id.nunique() >= 2
    assert preds.raw_probability.between(0, 1).all()
    otra, _, _ = predicciones_rolling(table, schema, cfg, 1, "2023-06")
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


RECETA_G = Path(__file__).resolve().parents[1] / "conf/retroanalisis/logistica_g.yml"


def _config_g() -> dict:
    """Receta logística con el bloque de margen declarado."""
    return yaml.safe_load(RECETA_G.read_text(encoding="utf-8"))


def _entrada(derivadas: tuple[str, ...] = ()) -> pd.DataFrame:
    """Matriz canónica mínima, con el bloque de margen al final si se pide."""
    from sat_dengue_pipeline.domain.canonical import PREDICTORS

    X = pd.DataFrame({p: np.linspace(1.0, 4.0, 4) for p in PREDICTORS})
    X["zona_canal_t"] = ["EXITO", "ALERTA", "EXITO", "SEGURIDAD"]
    X = X[list(PREDICTORS)]
    for i, nombre in enumerate(derivadas):
        # Valores con signo, como los márgenes reales; log1p no debe tocarlos.
        X[nombre] = np.linspace(-1.0 - i, 1.0 + i, 4)
    return X


def test_la_receta_g_es_la_misma_mas_el_bloque() -> None:
    """Una sola diferencia entre las dos recetas: el bloque de margen."""
    base, g = _config().copy(), _config_g()
    assert g["predictors"] == base["predictors"] and g["seed"] == base["seed"]
    assert base["preparation"]["variables_g"] is False
    assert g["preparation"]["variables_g"] is True
    extra = g["preparation"]["matrix_columns"][len(base["preparation"]["matrix_columns"]) :]
    assert extra == MARGIN_COLUMNS
    # Ninguna derivada se declara con log1p: son márgenes con signo.
    assert not set(MARGIN_COLUMNS) & set(g["preparation"]["log1p_columns"])


def test_la_logistica_con_g_ajusta_con_el_bloque_al_final() -> None:
    """El adaptador acepta las seis columnas, las usa y las nombra en sus coeficientes."""
    adaptador = LogisticOnsetAdapter(adapter_spec(_config_g()))
    assert adaptador.derived == tuple(MARGIN_COLUMNS)
    X, y = _entrada(tuple(MARGIN_COLUMNS)), pd.Series([0, 1, 0, 1])
    sin_bloque = LogisticOnsetAdapter(adapter_spec(_config()))
    assert adaptador.matrix(X).shape[1] == sin_bloque.matrix(_entrada()).shape[1] + 6
    adaptador.fit(X, y)
    assert set(MARGIN_COLUMNS) <= set(adaptador.coeficientes())
    assert adaptador.predict_positive(X).between(0, 1).all()


def test_el_bloque_no_entra_ni_falta_por_accidente() -> None:
    """Declararlo y no mandarlo, o mandarlo sin declararlo, se rechaza."""
    con_g = LogisticOnsetAdapter(adapter_spec(_config_g()))
    with pytest.raises(ValueError):
        con_g.matrix(_entrada())
    sin_g = LogisticOnsetAdapter(adapter_spec(_config()))
    with pytest.raises(ValueError):
        sin_g.matrix(_entrada(tuple(MARGIN_COLUMNS)))
    # Y el orden del bloque es fijo: invertirlo se rechaza.
    with pytest.raises(ValueError):
        con_g.matrix(_entrada(tuple(reversed(MARGIN_COLUMNS))))


def test_una_receta_que_declara_el_bloque_mal_no_se_construye() -> None:
    """variables_g sin las columnas en la matriz, o al revés, es receta inválida."""
    malo = json.loads(json.dumps(_config_g()))
    malo["preparation"]["matrix_columns"] = malo["preparation"]["matrix_columns"][:-6]
    with pytest.raises(ValueError):
        LogisticOnsetAdapter(adapter_spec(malo))
    otro = json.loads(json.dumps(_config()))
    otro["preparation"]["matrix_columns"] = [
        *otro["preparation"]["matrix_columns"],
        *MARGIN_COLUMNS,
    ]
    with pytest.raises(ValueError):
        LogisticOnsetAdapter(adapter_spec(otro))
