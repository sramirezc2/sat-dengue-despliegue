"""Validación año a año (ventana expansiva) de un candidato contra líneas base del canal endémico.

Definiciones de docs/politica-de-decision-v2.md:

- inicio: exceso en el mes objetivo y no exceso en el mes anterior al objetivo.
- una alerta es verdadera solo si coincide con un inicio; falsas = alertas - inicios detectados.
- carga: falsas por cada 100 municipio-mes de la cohorte (denominador fijo).

Elegibilidad observable: el municipio no está en exceso en el mes de origen T. En T+1 equivale a
"puede empezar un inicio"; en T+2 es la versión sin fuga (no usa el exceso de T+1).

Líneas base, todas sin modelo:

- canal_p75: casos de T > P75 del mes objetivo (regla de vigilancia actual).
- canal_ajustado: casos de T > f * P75, con f elegido en el año t-1 (máximo F1 sobre inicios).
- canal_fuera_exceso: canal_ajustado, pero solo alerta si el municipio no está en exceso en T.
- persistencia: alerta si el municipio está en exceso en T (descriptiva).

El candidato emite en cada mes de origen el mismo número de alertas que la línea base (las de
mayor score). Se evalúa 2018-2024; 2025 está reservado hasta tener campeón.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ANIOS_DEFECTO = tuple(range(2018, 2025))
GRILLA_F = tuple(float(x) for x in np.round(np.arange(0.0, 1.51, 0.05), 2))
COLUMNAS = [
    "municipio",
    "anio_objetivo",
    "origen",
    "score",
    "objetivo",
    "inicio",
    "casos_t",
    "p75_objetivo",
    "exceso_t",
]


def validar_entrada(
    df: pd.DataFrame, anios=ANIOS_DEFECTO, permitir_2025: bool = False
) -> pd.DataFrame:
    """Revisar columnas y años, y conservar los años evaluados más el previo.

    Args:
        df: Tabla con las columnas de COLUMNAS; origen ordena los meses (anio * 12 + mes).
        anios: Años objetivo a evaluar.
        permitir_2025: Habilita 2025, reservado por defecto.

    Returns:
        Copia filtrada con tipos enteros en las banderas.

    Raises:
        ValueError: Si faltan columnas o se pide 2025 sin permiso.
    """
    falta = [c for c in COLUMNAS if c not in df.columns]
    if falta:
        raise ValueError(f"Faltan columnas: {falta}")
    if not permitir_2025 and max(anios) >= 2025:
        raise ValueError("2025 está reservado hasta tener campeón")
    out = df[df.anio_objetivo.isin([*anios, min(anios) - 1])].copy()
    for c in ("objetivo", "inicio", "exceso_t"):
        out[c] = out[c].astype(int)
    return out


def desde_pipeline(
    panel: pd.DataFrame,
    predicciones: pd.DataFrame,
    candidato: str,
    horizonte: int,
    col_casos: str = "dengue_notifications_count",
    col_fold: str = "fold_year",
) -> pd.DataFrame:
    """Adaptar panel y predicciones por fila al formato de entrada de la validación.

    panel trae municipality_code, year_month, <col_casos>, p75_canal_t y p75_t<h>. predicciones
    trae municipality_code, year_month, horizon, candidate, prediction_probability, y_true y
    <col_fold>, el año con el que se reentrenó el modelo que produjo cada fila.

    Args:
        panel: Panel mensual del canal.
        predicciones: Predicciones fuera de muestra por fila.
        candidato: Candidato a evaluar.
        horizonte: 1 o 2.
        col_casos: Columna de casos que usa el canal.
        col_fold: Columna con el año de reentrenamiento.

    Returns:
        DataFrame con las columnas de COLUMNAS y fold.

    Raises:
        ValueError: Si las predicciones no traen el año de reentrenamiento.
    """
    p = panel.copy()
    p["periodo"] = pd.PeriodIndex(p.year_month, freq="M")
    p["exceso_t"] = (p[col_casos].astype(float) > p.p75_canal_t.astype(float)).astype(int)
    exceso = p.set_index(["municipality_code", "periodo"]).exceso_t

    q = predicciones[
        (predicciones.candidate == candidato)
        & (predicciones.horizon.astype(str) == str(horizonte))
    ].copy()
    if col_fold not in q.columns:
        raise ValueError(f"Las predicciones no traen '{col_fold}' (año de reentrenamiento)")
    q["periodo"] = pd.PeriodIndex(q.year_month, freq="M")
    cols = ["municipality_code", "periodo", col_casos, f"p75_t{horizonte}", "exceso_t"]
    q = q.merge(p[cols], on=["municipality_code", "periodo"], how="inner")
    objetivo = q.periodo + horizonte
    previo = [exceso.get((m, x - 1), np.nan) for m, x in zip(q.municipality_code, objetivo)]
    q["exceso_prev_obj"] = previo
    keep = q.exceso_prev_obj.notna().values
    q, objetivo = q[keep], objetivo[keep]
    y = q.y_true.astype(int)
    return pd.DataFrame(
        {
            "municipio": q.municipality_code.values,
            "anio_objetivo": [o.year for o in objetivo],
            "origen": [o.year * 12 + o.month for o in q.periodo],
            "score": q.prediction_probability.astype(float).values,
            "objetivo": y.values,
            "inicio": ((y == 1) & (q.exceso_prev_obj == 0)).astype(int).values,
            "casos_t": q[col_casos].astype(float).values,
            "p75_objetivo": q[f"p75_t{horizonte}"].astype(float).values,
            "exceso_t": q.exceso_t.values,
            "fold": q[col_fold].values,
        }
    )


def metricas(alerta, d: pd.DataFrame) -> dict:
    """Calcular alertas, inicios detectados, falsas, carga y falsas por acierto.

    Args:
        alerta: Vector 0/1 alineado con d.
        d: Filas evaluadas, con la columna inicio.

    Returns:
        Diccionario de métricas con la definición v2.
    """
    a = np.asarray(alerta).astype(bool)
    ini = d.inicio.values == 1
    n_alertas, det = int(a.sum()), int((a & ini).sum())
    falsas = n_alertas - det
    return {
        "alertas": n_alertas,
        "inicios": int(ini.sum()),
        "inicios_detectados": det,
        "falsas": falsas,
        "sensibilidad_inicios": det / max(int(ini.sum()), 1),
        "carga_100mm": 100 * falsas / max(len(d), 1),
        "falsas_por_acierto": falsas / det if det else np.inf,
    }


def canal(d: pd.DataFrame, f: float = 1.0, fuera_exceso: bool = False) -> np.ndarray:
    """Alertas del canal: casos de T > f * P75 del mes objetivo.

    Args:
        d: Filas con casos_t, p75_objetivo y exceso_t.
        f: Fracción del P75.
        fuera_exceso: Alerta solo si el municipio no está en exceso en T.

    Returns:
        Vector 0/1.
    """
    a = d.casos_t.values > f * d.p75_objetivo.values
    if fuera_exceso:
        a &= d.exceso_t.values == 0
    return a.astype(int)


def elegir_f(d_prev: pd.DataFrame, fuera_exceso: bool, grilla=GRILLA_F) -> float:
    """Elegir ex ante el f que maximiza el F1 sobre inicios en el año previo.

    Args:
        d_prev: Filas del año anterior al evaluado.
        fuera_exceso: Si el canal solo alerta fuera de exceso.
        grilla: Valores candidatos de f.

    Returns:
        El f elegido.
    """
    mejor, f_mejor = -1.0, 1.0
    ini = d_prev.inicio.values == 1
    for f in grilla:
        a = canal(d_prev, f, fuera_exceso).astype(bool)
        f1 = 2 * (a & ini).sum() / max(a.sum() + ini.sum(), 1)
        if f1 > mejor:
            mejor, f_mejor = f1, f
    return float(f_mejor)


def emparejar(d: pd.DataFrame, alerta_base) -> np.ndarray:
    """Emitir en cada mes de origen tantas alertas como la línea base, las de mayor score.

    Args:
        d: Filas con origen y score.
        alerta_base: Vector 0/1 de la línea base alineado con d.

    Returns:
        Vector 0/1 del candidato.
    """
    k = pd.Series(np.asarray(alerta_base), index=d.index).groupby(d.origen).transform("sum")
    r = d.score.groupby(d.origen).rank(ascending=False, method="first")
    return (r <= k).astype(int).values


def bootstrap_dif(d: pd.DataFrame, a_mod, a_base, n: int = 1000, semilla: int = 42):
    """IC 95 % bootstrap por municipio de la diferencia de inicios detectados.

    Args:
        d: Filas evaluadas.
        a_mod: Alertas del candidato.
        a_base: Alertas de la línea base.
        n: Remuestreos.
        semilla: Semilla del generador.

    Returns:
        Tupla (diferencia, límite inferior, límite superior).
    """
    ini = d.inicio.values == 1
    dif = pd.Series((np.asarray(a_mod) - np.asarray(a_base)) * ini, index=d.index)
    pm = dif.groupby(d.municipio).sum().values
    b = np.random.default_rng(semilla).choice(pm, size=(n, len(pm)), replace=True).sum(axis=1)
    return int(pm.sum()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def lineas_base_por_anio(df: pd.DataFrame, anios=ANIOS_DEFECTO) -> pd.DataFrame:
    """Agregar una columna 0/1 por línea base y el f usado, solo en los años evaluados.

    Args:
        df: Salida de validar_entrada.
        anios: Años evaluados.

    Returns:
        DataFrame con índice nuevo y columnas de líneas base.
    """
    partes = []
    for t in anios:
        d = df[df.anio_objetivo == t].copy()
        prev = df[df.anio_objetivo == t - 1]
        f_aj = elegir_f(prev, False) if len(prev) else 1.0
        f_fe = elegir_f(prev, True) if len(prev) else 1.0
        d["canal_p75"] = canal(d, 1.0)
        d["canal_ajustado"] = canal(d, f_aj)
        d["canal_fuera_exceso"] = canal(d, f_fe, True)
        d["persistencia"] = d.exceso_t.values
        d["f_ajustado"], d["f_fuera_exceso"] = f_aj, f_fe
        partes.append(d)
    return pd.concat(partes, ignore_index=True)


def comparar(
    df: pd.DataFrame,
    anios=ANIOS_DEFECTO,
    permitir_2025: bool = False,
    bases=("canal_p75", "canal_ajustado", "canal_fuera_exceso"),
    n_boot: int = 1000,
) -> pd.DataFrame:
    """Comparar el candidato contra cada línea base con las mismas alertas por mes.

    Args:
        df: Tabla de entrada.
        anios: Años evaluados.
        permitir_2025: Habilita 2025.
        bases: Líneas base a comparar.
        n_boot: Remuestreos del IC.

    Returns:
        Una fila por línea base, más persistencia como referencia descriptiva.
    """
    big = lineas_base_por_anio(validar_entrada(df, anios, permitir_2025), anios)
    periodo = f"{min(anios)}-{max(anios)}"
    filas = []
    for base in bases:
        a_base = big[base].values
        a_mod = np.zeros(len(big), int)
        for _, g in big.groupby("anio_objetivo"):
            a_mod[g.index.values] = emparejar(g, g[base].values)
        mb, mm = metricas(a_base, big), metricas(a_mod, big)
        dif, lo, hi = bootstrap_dif(big, a_mod, a_base, n_boot)
        filas.append(
            {
                "linea_base": base,
                "anios": periodo,
                "inicios": mb["inicios"],
                "alertas": mb["alertas"],
                "base_detectados": mb["inicios_detectados"],
                "candidato_detectados": mm["inicios_detectados"],
                "diferencia": dif,
                "ic95_lo": lo,
                "ic95_hi": hi,
                "base_falsas": mb["falsas"],
                "candidato_falsas": mm["falsas"],
                "base_carga_100mm": round(mb["carga_100mm"], 2),
                "candidato_carga_100mm": round(mm["carga_100mm"], 2),
                "base_falsas_por_acierto": round(mb["falsas_por_acierto"], 2),
                "candidato_falsas_por_acierto": round(mm["falsas_por_acierto"], 2),
            }
        )
    pers = metricas(big.persistencia.values, big)
    filas.append(
        {
            "linea_base": "persistencia (descriptiva)",
            "anios": periodo,
            "inicios": pers["inicios"],
            "alertas": pers["alertas"],
            "base_detectados": pers["inicios_detectados"],
            "base_falsas": pers["falsas"],
            "base_carga_100mm": round(pers["carga_100mm"], 2),
        }
    )
    return pd.DataFrame(filas)


def por_anio(
    df: pd.DataFrame,
    base: str = "canal_fuera_exceso",
    anios=ANIOS_DEFECTO,
    permitir_2025: bool = False,
) -> pd.DataFrame:
    """Detalle anual del candidato contra una línea base.

    Args:
        df: Tabla de entrada.
        base: Línea base.
        anios: Años evaluados.
        permitir_2025: Habilita 2025.

    Returns:
        Una fila por año con f, inicios, alertas y detectados.
    """
    big = lineas_base_por_anio(validar_entrada(df, anios, permitir_2025), anios)
    col_f = {"canal_ajustado": "f_ajustado", "canal_fuera_exceso": "f_fuera_exceso"}.get(base)
    filas = []
    for t, g in big.groupby("anio_objetivo"):
        mb, mm = metricas(g[base].values, g), metricas(emparejar(g, g[base].values), g)
        filas.append(
            {
                "anio": t,
                "f": g[col_f].iloc[0] if col_f else 1.0,
                "inicios": mb["inicios"],
                "alertas": mb["alertas"],
                "base_detectados": mb["inicios_detectados"],
                "candidato_detectados": mm["inicios_detectados"],
            }
        )
    return pd.DataFrame(filas)


def curva(
    df: pd.DataFrame,
    anios=ANIOS_DEFECTO,
    permitir_2025: bool = False,
    solo_elegibles: bool = True,
    grilla=GRILLA_F,
) -> pd.DataFrame:
    """Inicios detectados según alertas emitidas: canal f * P75 contra el candidato emparejado.

    Args:
        df: Tabla de entrada.
        anios: Años evaluados.
        permitir_2025: Habilita 2025.
        solo_elegibles: El canal solo alerta fuera de exceso.
        grilla: Valores de f.

    Returns:
        Una fila por f, ordenada por alertas.
    """
    d = validar_entrada(df, anios, permitir_2025)
    d = d[d.anio_objetivo.isin(anios)].reset_index(drop=True)
    filas = []
    for f in grilla:
        a = canal(d, f, fuera_exceso=solo_elegibles)
        m = emparejar(d, a)
        filas.append(
            {
                "f": f,
                "alertas": int(a.sum()),
                "canal_detectados": metricas(a, d)["inicios_detectados"],
                "candidato_detectados": metricas(m, d)["inicios_detectados"],
            }
        )
    return pd.DataFrame(filas).sort_values("alertas")


def validar_candidato(panel: pd.DataFrame, predictions: pd.DataFrame, params: dict):
    """Nodo de Kedro: resumen, detalle por año y curva para un candidato y un horizonte.

    Args:
        panel: Panel mensual con casos y umbrales del canal.
        predictions: Predicciones por fila con el año de reentrenamiento.
        params: candidato, horizonte y anios ([inicio, fin]).

    Returns:
        Tupla (resumen, por_anio, curva) de DataFrames.
    """
    h = int(params["horizonte"])
    a0, a1 = params.get("anios", [2018, 2024])
    anios = tuple(range(int(a0), int(a1) + 1))
    df = desde_pipeline(panel, predictions, params["candidato"], h)
    return comparar(df, anios), por_anio(df, anios=anios), curva(df, anios)
