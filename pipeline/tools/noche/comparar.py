"""Comparar recetas entre sí, emparejadas, sobre predicciones.csv del retroanálisis.

Para cada receta contra la de referencia y cada horizonte, ambas emiten en cada mes de origen
el mismo número de alertas: el del canal condicionado y presupuestos fijos del 5, 10 y 20 % de
los 76 municipios del mes (sección 0.1; antes de las 23:00 eran filas elegibles).
Diferencia de inicios detectados con IC 95 % por bootstrap de
municipios (el mismo de validar_candidato), carga por 100 municipio-mes y detalle por año.
Uso: python tools/noche/comparar.py <carpeta> <referencia> [receta ...]  (sin recetas: todas)
Lee también resumen_ensambles/predicciones_ensambles.csv si existen.
"""

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sat_dengue_pipeline.evaluation import validacion_anual as va
from sat_dengue_pipeline.raw.serialization import CanonicalArtifact, load_canonical

CERT = "de49b11bad43c35983a098ead2faa149d4e744da4172432aecdaadd828c73158"
p = Path(f"data/noche_panel/{CERT}/canonical.json")
table, _ = load_canonical(CanonicalArtifact(p, CERT, hashlib.sha256(p.read_bytes()).hexdigest()))
table = table[table.department_code.isin(["50", "73"])].reset_index(drop=True)
carpeta, ref = Path(sys.argv[1]), sys.argv[2]
preds = pd.concat(
    [pd.read_csv(f, dtype={"municipality_code": str}) for f in carpeta.glob("predicciones*.csv")],
    ignore_index=True,
)
recetas = sys.argv[3:] or [r for r in preds.receta.unique() if r != ref]


def tabla(receta, h):
    """Filas evaluadas de una receta y horizonte, en el formato de validacion_anual."""
    q = preds[(preds.receta == receta) & (preds.horizon == h)].drop(columns="receta")
    df = va.desde_pipeline(table, q, str(q.candidate.iloc[0]), h)
    return df


def topk(d, frac):
    """Alertar en cada mes de origen la fracción declarada de filas, por score."""
    # Sección 0.1: fracción de los 76 municipios del mes, no de las filas elegibles.
    r = d.score.groupby(d.origen).rank(ascending=False, method="first")
    return (r <= np.round(frac * 76)).astype(int).values


filas, anual = [], []
historias = {h: va.historia_desde_panel(table, h) for h in (1, 2)}
for h in (1, 2):
    dref = tabla(ref, h)
    anios = tuple(sorted(int(a) for a in dref.anio_objetivo.unique() if a < 2025))
    big = va.lineas_base_por_anio(va.validar_entrada(dref, anios), anios, historias[h])
    claves = ["municipio", "origen"]
    for receta in recetas:
        dx = tabla(receta, h)[claves + ["score"]].rename(columns={"score": "score_x"})
        m = big.merge(dx, on=claves, how="left")
        assert len(m) == len(big) and m.score_x.notna().all(), f"{receta}: filas distintas"
        mx = m.assign(score=m.score_x)
        for presupuesto in ("canal_fuera_exceso", 0.05, 0.10, 0.20):
            a_r, a_x = np.zeros(len(m), int), np.zeros(len(m), int)
            for _, g in m.groupby("anio_objetivo"):
                i = g.index.values
                if presupuesto == "canal_fuera_exceso":
                    a_r[i] = va.emparejar(g, g[presupuesto].values)
                    a_x[i] = va.emparejar(mx.loc[i], g[presupuesto].values)
                else:
                    a_r[i] = topk(g, presupuesto)
                    a_x[i] = topk(mx.loc[i], presupuesto)
            mr, mmx = va.metricas(a_r, m), va.metricas(a_x, m)
            dif, lo, hi = va.bootstrap_dif(m, a_x, a_r, 1000)
            por_mes = pd.Series((a_x - a_r) * (m.inicio.values == 1)).groupby(m.origen.values).sum()
            bm = np.random.default_rng(42).choice(por_mes.values, size=(2000, len(por_mes)))
            lo_mes, hi_mes = np.percentile(bm.sum(axis=1), [2.5, 97.5])
            filas.append(
                {
                    "horizonte": h,
                    "receta": receta,
                    "presupuesto": presupuesto,
                    "inicios": mr["inicios"],
                    "alertas": mr["alertas"],
                    "ref_detectados": mr["inicios_detectados"],
                    "receta_detectados": mmx["inicios_detectados"],
                    "diferencia": dif,
                    "ic95_lo": lo,
                    "ic95_hi": hi,
                    "ic95_mes_lo": float(lo_mes),
                    "ic95_mes_hi": float(hi_mes),
                    "dif_pp": round(100 * dif / mr["inicios"], 1),
                    "ref_carga_100mm": round(mr["carga_100mm"], 2),
                    "receta_carga_100mm": round(mmx["carga_100mm"], 2),
                }
            )
            if presupuesto == "canal_fuera_exceso":
                ini = m.inicio.values == 1
                for anio, g in m.groupby("anio_objetivo"):
                    i = g.index.values
                    anual.append(
                        {
                            "horizonte": h,
                            "receta": receta,
                            "anio": anio,
                            "inicios": int(ini[i].sum()),
                            "ref": int((a_r[i] * ini[i]).sum()),
                            "receta_det": int((a_x[i] * ini[i]).sum()),
                        }
                    )
res = pd.DataFrame(filas)
res.to_csv(carpeta / f"comparacion_vs_{ref}.csv", index=False)
pd.DataFrame(anual).to_csv(carpeta / f"comparacion_anual_vs_{ref}.csv", index=False)
print(res.to_string())
