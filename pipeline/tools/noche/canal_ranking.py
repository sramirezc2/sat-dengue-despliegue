"""Modelo contra el canal como ranking (casos/P75), ambos con 8 alertas fijas por mes (tanda 38).

Uso: python tools/noche/canal_ranking.py <carpeta> <receta> [...]
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
carpeta = Path(sys.argv[1])
preds = pd.concat(
    [pd.read_csv(f, dtype={"municipality_code": str}) for f in carpeta.glob("predicciones*.csv")],
    ignore_index=True,
).drop_duplicates(["receta", "municipality_code", "origin_period", "horizon"])
rng = np.random.default_rng(42)
K = round(0.10 * 76)


def top(d, score):
    """Alertar las K filas de mayor score en cada mes de origen."""
    r = pd.Series(score, index=d.index).groupby(d.origen).rank(ascending=False, method="first")
    return (r <= K).astype(int).values


filas = []
for receta in sys.argv[2:]:
    for h in (1, 2):
        q = preds[(preds.receta == receta) & (preds.horizon == h)].drop(columns="receta")
        df = va.desde_pipeline(table, q, str(q.candidate.iloc[0]), h)
        anios = tuple(sorted(int(a) for a in df.anio_objetivo.unique() if a < 2025))
        d = va.validar_entrada(df, anios)
        d = d[d.anio_objetivo.isin(anios)].reset_index(drop=True)
        razon = (d.casos_t / (d.p75_objetivo + 1)).values
        a_c, a_m = top(d, razon), top(d, d.score.values)
        ini = d.inicio.values == 1
        n_inicios = int(ini.sum())
        dif = (a_m - a_c) * ini
        s = pd.Series(dif, index=d.index).groupby(d.origen).sum().values
        lo, hi = np.percentile(rng.choice(s, size=(2000, len(s))).sum(axis=1), [2.5, 97.5])
        mc, mm = va.metricas(a_c, d), va.metricas(a_m, d)
        dpp = 100 * dif.sum() / n_inicios
        filas.append(
            {
                "receta": receta,
                "horizonte": h,
                "alertas": int(a_c.sum()),
                "inicios": n_inicios,
                "canal_ranking": mc["inicios_detectados"],
                "modelo": mm["inicios_detectados"],
                "dif_pp": round(dpp, 1),
                "ic_mes_pp": f"{100 * lo / n_inicios:.1f} a {100 * hi / n_inicios:.1f}",
                "carga_canal": round(mc["carga_100mm"], 2),
                "carga_modelo": round(mm["carga_100mm"], 2),
                "barra_5pp": "CUMPLE" if dpp >= 5 and lo > 0 else "NO",
            }
        )
out = pd.DataFrame(filas)
out.to_csv(carpeta / "canal_ranking.csv", index=False)
print(out.to_string())
