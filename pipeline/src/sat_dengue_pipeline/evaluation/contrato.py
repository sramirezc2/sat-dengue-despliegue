"""Evaluación según el contrato científico (docs/experiments/contrato.md, v0.1.0-propuesta).

Se aplica sobre el rol ``evaluation`` de la fábrica de cinco roles, después de congelar el modelo.
Implementa lo que el §16 del contrato marca como faltante:

- canal endémico condicionado como comparador primario (§8.1): alerta si casos de T > f × P75 del
  mes objetivo, solo en la cohorte sin exceso en T; f se elige con el rol ``threshold_selection``
  (máximo F1 sobre inicios) y queda congelado;
- presupuesto de alertas (§9) fijado por una regla predeclarada vinculada al canal condicionado:
  en cada mes de origen se emiten tantas alertas como el canal condicionado, número conocido en T;
- carga de falsas alertas por 100 municipio-mes (§10.1) y métricas complementarias (§10.2);
- intervalo de 2.000 réplicas por bloques de mes objetivo, emparejado (§11, §13);
- controles negativos al mismo presupuesto (§8.3): ranking aleatorio, alertar todo, canal inflado;
- veredicto por horizonte (§12): CUMPLE, NO_CUMPLE_POR_EFECTO, PRECISION_INSUFICIENTE,
  NO_EVALUABLE o INVALIDO si un control negativo cumple.

El inicio sigue H5 (§4.2): exceso en el mes objetivo y no exceso en el mes anterior; si alguno
falta, la fila es no evaluable. Las predicciones del candidato nunca leen etiquetas de evaluación.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from sat_dengue_pipeline.domain.calendar import add_months

PARAMETROS_DEFECTO = {
    "version": "0.1.0-propuesta",
    "grilla_f": [float(round(x, 2)) for x in np.arange(0.0, 1.51, 0.05)],
    "ganancia_minima_pp": 10.0,
    "aumento_maximo_carga": 5.0,
    "replicas": 2000,
    "semilla": 42,
    "nivel": 0.95,
}


def _exceso(table: pd.DataFrame) -> pd.Series:
    """Exceso H5 por (municipio, mes): zona del canal en EXCESO; nulo si la zona es nula.

    Args:
        table: Panel canónico.

    Returns:
        Serie 1/0/NaN indexada por (municipality_code, year_month).
    """
    zona = table.zona_canal_t
    return pd.Series(
        zona.eq("EXCESO").astype(float).where(zona.notna()).values,
        index=pd.MultiIndex.from_frame(table[["municipality_code", "year_month"]]),
    )


def filas(keys: pd.DataFrame, table: pd.DataFrame, h: int) -> pd.DataFrame:
    """Unir claves de un rol con casos en T, P75 del objetivo, exceso en T e inicio H5.

    Args:
        keys: Claves del rol (municipality_code, origin_period, target_period).
        table: Panel canónico.
        h: Horizonte.

    Returns:
        DataFrame alineado con ``keys`` con columnas casos_t, p75_obj, exceso_t, inicio y evaluable.
    """
    exc = _exceso(table)
    base = table.set_index(["municipality_code", "year_month"])
    idx = pd.MultiIndex.from_arrays([keys.municipality_code, keys.origin_period])
    previo = [add_months(t, -1) for t in keys.target_period]
    e_obj = exc.reindex(
        pd.MultiIndex.from_arrays([keys.municipality_code, keys.target_period])
    ).values
    e_prev = exc.reindex(pd.MultiIndex.from_arrays([keys.municipality_code, previo])).values
    out = pd.DataFrame(
        {
            "municipio": keys.municipality_code.values,
            "origen": keys.origin_period.values,
            "objetivo": keys.target_period.values,
            "departamento": keys.municipality_code.str[:2].values,
            "casos_t": base.dengue_notifications_count.reindex(idx).astype(float).values,
            "p75_obj": base[f"p75_h5_t{h}"].reindex(idx).astype(float).values,
            "exceso_t": exc.reindex(idx).values,
        }
    )
    out["evaluable"] = ~np.isnan(e_obj) & ~np.isnan(e_prev) & (out.exceso_t.values == 0)
    out["inicio"] = ((e_obj == 1) & (e_prev == 0)).astype(int)
    return out


def _canal(d: pd.DataFrame, f: float) -> np.ndarray:
    """Canal condicionado: casos de T > f × P75 del objetivo, en filas sin exceso en T."""
    return ((d.casos_t.values > f * d.p75_obj.values) & (d.exceso_t.values == 0)).astype(int)


def elegir_f(dev: pd.DataFrame, grilla) -> float:
    """F del canal condicionado con máximo F1 de inicio en el rol de desarrollo (empate: f mayor).

    Args:
        dev: Filas evaluables del rol threshold_selection.
        grilla: Valores candidatos de f.

    Returns:
        f congelado.
    """
    ini = dev.inicio.values == 1
    mejor, f_mejor = -1.0, 1.0
    for f in sorted(grilla, reverse=True):
        a = _canal(dev, f).astype(bool)
        f1 = 2 * (a & ini).sum() / max(a.sum() + ini.sum(), 1)
        if f1 > mejor:
            mejor, f_mejor = f1, float(f)
    return f_mejor


def _top_k_por_mes(d: pd.DataFrame, score: np.ndarray, k: np.ndarray) -> np.ndarray:
    """En cada mes de origen alertar las k filas de mayor score (k por fila = cupo de su mes)."""
    rank = pd.Series(score, index=d.index).groupby(d.origen).rank(ascending=False, method="first")
    return (rank.values <= k).astype(int)


def _medidas(a: np.ndarray, d: pd.DataFrame) -> dict[str, Any]:
    """Métricas §10 de una regla de alerta sobre la cohorte común."""
    ini = d.inicio.values == 1
    n, i_, tp, al = len(d), int(ini.sum()), int((a.astype(bool) & ini).sum()), int(a.sum())
    fp = al - tp
    return {
        "N": n,
        "inicios": i_,
        "detectados": tp,
        "omitidos": i_ - tp,
        "alertas": al,
        "fraccion_alertas": al / n if n else None,
        "sensibilidad": tp / i_ if i_ else None,
        "carga_100mm": 100 * fp / n if n else None,
        "far_inicio": fp / al if al else None,
        "falsas_por_detectado": fp / tp if tp else None,
    }


def _bootstrap(
    d: pd.DataFrame, a_m: np.ndarray, a_c: np.ndarray, reps: int, semilla: int, nivel: float
):
    """Diferencias emparejadas (pp de sensibilidad y carga) con bloques de mes objetivo."""
    ini = d.inicio.values == 1
    g = (
        pd.DataFrame(
            {
                "obj": d.objetivo.values,
                "ini": ini.astype(int),
                "tp_m": (a_m.astype(bool) & ini).astype(int),
                "tp_c": (a_c.astype(bool) & ini).astype(int),
                "fp_m": (a_m.astype(bool) & ~ini).astype(int),
                "fp_c": (a_c.astype(bool) & ~ini).astype(int),
                "n": 1,
            }
        )
        .groupby("obj")
        .sum()
    )
    M = g.values
    cols = list(g.columns)
    rng = np.random.default_rng(semilla)
    idx = rng.integers(0, len(M), size=(reps, len(M)))
    S = M[idx].sum(axis=1)
    c = {k: S[:, cols.index(k)].astype(float) for k in cols}
    with np.errstate(divide="ignore", invalid="ignore"):
        dS = 100 * (c["tp_m"] - c["tp_c"]) / c["ini"]
        dB = 100 * (c["fp_m"] - c["fp_c"]) / c["n"]
    q = ((1 - nivel) / 2 * 100, (1 + nivel) / 2 * 100)
    dS, dB = dS[np.isfinite(dS)], dB[np.isfinite(dB)]
    return (
        float(np.percentile(dS, q[0])),
        float(np.percentile(dS, q[1])),
        float(np.percentile(dB, q[0])),
        float(np.percentile(dB, q[1])),
    )


def _veredicto(m: dict, c: dict, p: dict, ic: tuple, params: dict) -> dict[str, Any]:
    """Regla §11-§12 para una regla de alerta frente al canal condicionado."""
    if not m["inicios"] or m["sensibilidad"] is None or c["sensibilidad"] is None:
        return {"veredicto": "NO_EVALUABLE"}
    dS = 100 * (m["sensibilidad"] - c["sensibilidad"])
    dB = m["carga_100mm"] - c["carga_100mm"]
    g, b = params["ganancia_minima_pp"], params["aumento_maximo_carga"]
    supera_persistencia = m["detectados"] > p["detectados"]
    puntual_ok = dS >= g and dB <= b and supera_persistencia
    cotas_ok = ic[0] >= g and ic[3] <= b
    ver = (
        "CUMPLE"
        if puntual_ok and cotas_ok
        else ("PRECISION_INSUFICIENTE" if puntual_ok else "NO_CUMPLE_POR_EFECTO")
    )
    return {
        "veredicto": ver,
        "delta_sensibilidad_pp": dS,
        "ic_delta_sensibilidad_pp": [ic[0], ic[1]],
        "delta_carga_100mm": dB,
        "ic_delta_carga_100mm": [ic[2], ic[3]],
        "supera_persistencia": bool(supera_persistencia),
    }


def evaluar(
    keys_eval: pd.DataFrame,
    score: pd.Series | np.ndarray,
    keys_dev: pd.DataFrame,
    table: pd.DataFrame,
    h: int,
    params: dict | None = None,
) -> dict[str, Any]:
    """Evaluación completa del contrato para un horizonte.

    Args:
        keys_eval: Claves del rol evaluation, alineadas con ``score``.
        score: Puntaje del candidato congelado (probabilidad cruda).
        keys_dev: Claves del rol threshold_selection (para fijar f del canal).
        table: Panel canónico (población ya filtrada).
        h: Horizonte.
        params: Parámetros predeclarados; por defecto los del contrato v0.1.0.

    Returns:
        Métricas por método, intervalos, controles negativos, heterogeneidad y veredicto.
    """
    params = {**PARAMETROS_DEFECTO, **(params or {})}
    ev = filas(keys_eval.reset_index(drop=True), table, h).assign(
        score=np.asarray(score, dtype=float)
    )
    dev = filas(keys_dev.reset_index(drop=True), table, h)
    no_eval = int((~ev.evaluable).sum())
    ev, dev = ev[ev.evaluable].reset_index(drop=True), dev[dev.evaluable].reset_index(drop=True)
    f = elegir_f(dev, params["grilla_f"])
    canal = _canal(ev, f)
    k = pd.Series(canal).groupby(ev.origen).transform("sum").values
    rng = np.random.default_rng(params["semilla"])
    reglas = {
        "canal_condicionado": canal,
        "canal_estandar": _canal(ev, 1.0),
        "persistencia": (ev.exceso_t.values == 1).astype(int),
        "candidato": _top_k_por_mes(ev, ev.score.values, k),
        "control_ranking_aleatorio": _top_k_por_mes(ev, rng.random(len(ev)), k),
        "control_alertar_todo": np.ones(len(ev), int),
    }
    extra = np.zeros(len(ev), int)
    for _, g_ in ev.groupby("origen"):
        libres = [i for i in g_.index if canal[i] == 0]
        n_extra = min(int(canal[g_.index].sum()), len(libres))
        if n_extra:
            extra[rng.choice(libres, n_extra, replace=False)] = 1
    reglas["control_canal_inflado"] = np.maximum(canal, extra)
    medidas = {n: _medidas(a, ev) for n, a in reglas.items()}
    veredictos = {}
    for n in (
        "candidato",
        "canal_estandar",
        "control_ranking_aleatorio",
        "control_alertar_todo",
        "control_canal_inflado",
    ):
        ic = _bootstrap(
            ev, reglas[n], canal, params["replicas"], params["semilla"], params["nivel"]
        )
        veredictos[n] = _veredicto(
            medidas[n], medidas["canal_condicionado"], medidas["persistencia"], ic, params
        )
    controles_ok = all(
        veredictos[n]["veredicto"] != "CUMPLE" for n in veredictos if n.startswith("control_")
    )
    final = veredictos["candidato"]["veredicto"] if controles_ok else "INVALIDO"
    hetero = {}
    for col in ("departamento",):
        for val, g_ in ev.groupby(col):
            gi = g_.index.values
            hetero[f"{col}={val}"] = {
                n: _medidas(reglas[n][gi], g_) for n in ("candidato", "canal_condicionado")
            }
    y = ev.inicio.values
    s = ev.score.values
    from sklearn.metrics import average_precision_score, roc_auc_score

    probabilistas = {
        "ap": float(average_precision_score(y, s)) if 0 < y.sum() < len(y) else None,
        "auroc": float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else None,
        "brier": float(np.mean((s - y) ** 2)),
    }
    return {
        "contrato": params["version"],
        "horizonte": h,
        "f_canal_condicionado": f,
        "presupuesto": "mismas alertas por mes de origen que el canal condicionado",
        "filas_no_evaluables": no_eval,
        "medidas": medidas,
        "veredictos": veredictos,
        "controles_negativos_validos": controles_ok,
        "veredicto": final,
        "candidato_probabilistico": probabilistas,
        "heterogeneidad": hetero,
    }
