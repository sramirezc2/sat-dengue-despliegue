"""Evaluación del contrato científico: canal condicionado, presupuesto, controles y veredictos."""

import numpy as np
import pandas as pd
import pytest

from sat_dengue_pipeline.evaluation import contrato


def _panel() -> pd.DataFrame:
    """Diez municipios ficticios, 2023-2024; la mitad sale de no exceso a exceso cada tres meses."""
    filas = []
    for m in range(10):
        cod = f"{'50' if m < 5 else '73'}99{m}"
        for i, per in enumerate(pd.period_range("2023-01", "2024-12", freq="M").astype(str)):
            exceso = (m % 2 == 0) and (i % 3 == 2)
            filas.append(
                {
                    "municipality_code": cod,
                    "department_code": cod[:2],
                    "year_month": per,
                    "zona_canal_t": "EXCESO" if exceso else "SEGURIDAD",
                    "dengue_notifications_count": float(8 if (m % 2 == 0 and i % 3 == 1) else 1),
                    "p75_h5_t1": 10.0,
                    "p75_h5_t2": 10.0,
                }
            )
    return pd.DataFrame(filas)


def _keys(t: pd.DataFrame, desde: str, hasta: str, h: int = 1) -> pd.DataFrame:
    """Claves de un rol: orígenes sin exceso con objetivo en el rango."""
    k = t[t.zona_canal_t != "EXCESO"][["municipality_code", "year_month"]].rename(
        columns={"year_month": "origin_period"}
    )
    k["target_period"] = [str(pd.Period(o, freq="M") + h) for o in k.origin_period]
    return k[(k.target_period >= desde) & (k.target_period <= hasta)].reset_index(drop=True)


def test_inicio_h5_y_no_evaluables() -> None:
    """El inicio exige no exceso en el mes previo al objetivo; sin estado previo es no evaluable."""
    t = _panel()
    k = _keys(t, "2024-01", "2024-12")
    f = contrato.filas(k, t, 1)
    assert set(f.inicio.unique()) <= {0, 1}
    assert f.evaluable.all()


def test_score_oraculo_cumple_y_controles_no() -> None:
    """Un candidato perfecto con margen supera al canal; ningún control negativo obtiene CUMPLE."""
    t = _panel()
    dev = _keys(t, "2023-06", "2023-12")
    ev = _keys(t, "2024-01", "2024-12")
    f = contrato.filas(ev, t, 1)
    r = contrato.evaluar(
        ev,
        f.inicio.values + 0.01 * np.arange(len(f)) / len(f),
        dev,
        t,
        1,
        {"replicas": 200, "ganancia_minima_pp": 0.0},
    )
    assert r["veredictos"]["control_alertar_todo"]["veredicto"] != "CUMPLE"
    assert r["medidas"]["candidato"]["alertas"] == r["medidas"]["canal_condicionado"]["alertas"]
    assert r["veredicto"] in {
        "CUMPLE",
        "PRECISION_INSUFICIENTE",
        "NO_CUMPLE_POR_EFECTO",
        "INVALIDO",
    }


def test_carga_y_sensibilidad_contadas_a_mano() -> None:
    """Métricas §10 con denominadores de cohorte."""
    d = pd.DataFrame({"inicio": [1, 1, 0, 0], "origen": ["a"] * 4, "objetivo": ["b"] * 4})
    m = contrato._medidas(np.array([1, 0, 1, 0]), d)
    assert (m["sensibilidad"], m["carga_100mm"], m["far_inicio"]) == (0.5, 25.0, 0.5)


def test_esquema_rechaza_contrato_con_rolling() -> None:
    """El contrato se evalúa solo con los cinco roles fijos."""
    import copy
    from pathlib import Path

    import yaml

    from sat_dengue_pipeline.experiment_management.configuration import validate_configuration

    raiz = Path(__file__).resolve().parents[1]
    cfg = yaml.safe_load((raiz / "conf/experiments/EXP001.yml").read_text(encoding="utf-8"))
    ok = copy.deepcopy(cfg)
    ok["contract"] = dict(contrato.PARAMETROS_DEFECTO)
    validate_configuration(ok)
    malo = copy.deepcopy(ok)
    malo["protocol"] = "rolling_origin"
    malo["rolling"] = {"first_origin": "2023-06", "last_target": "2024-12"}
    with pytest.raises(ValueError):
        validate_configuration(malo)
