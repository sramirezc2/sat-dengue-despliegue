"""Pruebas de la validación año a año contra líneas base del canal."""

import pandas as pd
import pytest

from sat_dengue_pipeline.evaluation import validacion_anual as va


def _sintetico() -> pd.DataFrame:
    """Dos municipios, años 2017 y 2018, dos meses de origen por año."""
    filas = []
    for anio in (2017, 2018):
        for mes in (1, 2):
            o = anio * 12 + mes
            filas += [
                {"municipio": "A", "anio_objetivo": anio, "origen": o, "score": 0.9,
                 "objetivo": 1, "inicio": 1, "casos_t": 8, "p75_objetivo": 10, "exceso_t": 0},
                {"municipio": "B", "anio_objetivo": anio, "origen": o, "score": 0.1,
                 "objetivo": 0, "inicio": 0, "casos_t": 12, "p75_objetivo": 10, "exceso_t": 1},
            ]
    return pd.DataFrame(filas)


def test_metricas_contadas_a_mano() -> None:
    """El canal P75 alerta solo B: 2 alertas, 0 inicios, carga 50 por 100 municipio-mes."""
    d = _sintetico().query("anio_objetivo == 2018")
    m = va.metricas(va.canal(d, 1.0), d)
    assert (m["alertas"], m["inicios_detectados"], m["falsas"], m["inicios"]) == (2, 0, 2, 2)
    assert m["carga_100mm"] == 50.0


def test_canal_fuera_exceso_y_emparejado() -> None:
    """Fuera de exceso solo alerta A; el candidato toma las de mayor score."""
    d = _sintetico().query("anio_objetivo == 2018").reset_index(drop=True)
    assert va.canal(d, 0.5, fuera_exceso=True).tolist() == [1, 0, 1, 0]
    assert va.emparejar(d, va.canal(d, 1.0)).tolist() == [1, 0, 1, 0]


def test_f_ex_ante_con_anio_previo() -> None:
    """El f elegido en el año previo permite alertar a A (8 casos contra P75 10)."""
    assert va.elegir_f(_sintetico().query("anio_objetivo == 2017"), True) <= 0.8


def test_rechaza_2025() -> None:
    """2025 queda reservado salvo permiso explícito."""
    with pytest.raises(ValueError):
        va.comparar(_sintetico(), anios=(2024, 2025))


def _panel_y_predicciones(folds: bool = True):
    """Panel canónico y predicciones del arnés para dos municipios."""
    meses = [str(p) for p in pd.period_range("2016-11", "2018-12", freq="M")]
    panel = pd.DataFrame(
        [{"municipality_code": m, "year_month": x, "dengue_notifications_count": c,
          "p75_canal_t": 5, "p75_h5_t1": 5, "p75_h5_t2": 5}
         for m, c in (("A", 1), ("B", 9)) for x in meses]
    )
    pred = pd.DataFrame(
        [{"municipality_code": m, "origin_period": x,
          "target_period": str(pd.Period(x, freq="M") + 1), "horizon": 1,
          "fold_id": f"fold-{x[:4]}" if folds else "procedure-x", "candidate": "xgb",
          "raw_probability": p}
         for m, p in (("A", 0.8), ("B", 0.2)) for x in meses[:-1]]
    )
    return panel, pred


def test_adaptador_desde_pipeline() -> None:
    """El adaptador deriva exceso, objetivo e inicio desde el panel canónico."""
    panel, pred = _panel_y_predicciones()
    df = va.desde_pipeline(panel, pred, "xgb", 1)
    assert set(df.columns) >= set(va.COLUMNAS)
    assert df.query("municipio == 'A'").objetivo.eq(0).all()  # A nunca supera el P75
    assert df.query("municipio == 'B'").inicio.eq(0).all()  # B siempre en exceso
    assert df.query("municipio == 'B'").exceso_t.eq(1).all()
    r = va.comparar(df, anios=(2018,), n_boot=50)
    assert {"canal_p75", "canal_fuera_exceso"} <= set(r.linea_base)


def test_adaptador_exige_ventana_expansiva() -> None:
    """Un corte fijo (un solo fold) se rechaza salvo permiso explícito."""
    panel, pred = _panel_y_predicciones(folds=False)
    with pytest.raises(ValueError):
        va.desde_pipeline(panel, pred, "xgb", 1)
    assert len(va.desde_pipeline(panel, pred, "xgb", 1, permitir_un_fold=True)) > 0
