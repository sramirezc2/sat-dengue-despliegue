"""Reparto del presupuesto entre el canal y el modelo, al 10 % de la sección 0 (tanda 36).

Uso: python tools/noche/hibrido.py <carpeta> <receta> [...]
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


def llenar(g, fijas, k):
    """Conservar las alertas fijas y completar hasta k con el mayor puntaje entre las demás."""
    a = fijas.copy()
    resto = int(k - a.sum())
    if resto > 0:
        libres = np.flatnonzero(a == 0)
        orden = libres[np.argsort(-g.score.values[libres], kind="stable")][:resto]
        a[orden] = 1
    return a


def ic(d, x):
    """IC 95 % por bloques de mes de origen."""
    s = pd.Series(x, index=d.index).groupby(d.origen).sum().values
    b = rng.choice(s, size=(2000, len(s))).sum(axis=1)
    return np.percentile(b, [2.5, 97.5])


filas = []
for receta in sys.argv[2:]:
    for h in (1, 2):
        q = preds[(preds.receta == receta) & (preds.horizon == h)].drop(columns="receta")
        df = va.desde_pipeline(table, q, str(q.candidate.iloc[0]), h)
        anios = tuple(sorted(int(a) for a in df.anio_objetivo.unique() if a < 2025))
        d = va.validar_entrada(df, anios)
        d = d[d.anio_objetivo.isin(anios)].reset_index(drop=True)
        total = 0.10 * 76 * d.origen.nunique()
        a_c = min(
            (va.canal(d, f, fuera_exceso=True) for f in va.GRILLA_F),
            key=lambda a: abs(int(a.sum()) - total),
        )
        a_m = va.emparejar(d, a_c)
        a_s, a_h = np.zeros(len(d), int), np.zeros(len(d), int)
        razon = (d.casos_t / d.p75_objetivo.where(d.p75_objetivo > 0)).fillna(0).values
        for _, g in d.groupby("origen"):
            i = g.index.values
            k = int(a_c[i].sum())
            seguras = (a_c[i] == 1) & (razon[i] >= 1.0)
            a_s[i] = llenar(g, seguras.astype(int), k)
            mitad = k // 2
            cand = np.flatnonzero(a_c[i] == 1)
            top = cand[np.argsort(-razon[i][cand], kind="stable")][:mitad]
            f2 = np.zeros(len(i), int)
            f2[top] = 1
            a_h[i] = llenar(g, f2, k)
        ini = d.inicio.values == 1
        det = {
            n: int((a * ini).sum())
            for n, a in (("canal", a_c), ("modelo", a_m), ("seguras", a_s), ("mitad", a_h))
        }
        n_inicios = int(ini.sum())
        for n, a in (("seguras", a_s), ("mitad", a_h)):
            lo, hi = ic(d, (a - a_m) * ini)
            lc, hc = ic(d, (a - a_c) * ini)
            filas.append(
                {
                    "receta": receta,
                    "horizonte": h,
                    "regla": n,
                    "inicios": n_inicios,
                    "alertas": int(a.sum()),
                    "canal": det["canal"],
                    "modelo": det["modelo"],
                    "regla_det": det[n],
                    "vs_modelo_pp": round(100 * (det[n] - det["modelo"]) / n_inicios, 1),
                    "ic_vs_modelo_pp": f"{100 * lo / n_inicios:.1f} a {100 * hi / n_inicios:.1f}",
                    "vs_canal_pp": round(100 * (det[n] - det["canal"]) / n_inicios, 1),
                    "ic_vs_canal_pp": f"{100 * lc / n_inicios:.1f} a {100 * hc / n_inicios:.1f}",
                }
            )
out = pd.DataFrame(filas)
out.to_csv(carpeta / "hibrido.csv", index=False)
print(out.to_string())
