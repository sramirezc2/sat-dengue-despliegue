"""Inicios detectados por tercios de endemicidad y de cercanía al umbral, al 10 % (tanda 35).

Uso: python tools/noche/lectura_tipo.py <carpeta> <receta> [...]
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
filas = []
for receta in sys.argv[2:]:
    for h in (1, 2):
        q = preds[(preds.receta == receta) & (preds.horizon == h)].drop(columns="receta")
        df = va.desde_pipeline(table, q, str(q.candidate.iloc[0]), h)
        anios = tuple(sorted(int(a) for a in df.anio_objetivo.unique() if a < 2025))
        d = va.validar_entrada(df, anios)
        d = d[d.anio_objetivo.isin(anios)].reset_index(drop=True)
        total = 0.10 * 76 * d.origen.nunique()
        curva = [va.canal(d, f, fuera_exceso=True) for f in va.GRILLA_F]
        a_c = min(curva, key=lambda a: abs(int(a.sum()) - total))
        a_m = va.emparejar(d, a_c)
        ini = d.inicio.values == 1
        cortes = {
            "endemicidad (P75 objetivo)": d.p75_objetivo,
            "cercanía al umbral (casos/P75)": d.casos_t / (d.p75_objetivo + 1),
        }
        for nombre, x in cortes.items():
            g = pd.qcut(x.rank(method="first"), 3, labels=["bajo", "medio", "alto"])
            for t in ("bajo", "medio", "alto"):
                s = (g == t).values
                filas.append(
                    {
                        "receta": receta,
                        "horizonte": h,
                        "corte": nombre,
                        "tercio": t,
                        "inicios": int((ini & s).sum()),
                        "canal": int((a_c * ini * s).sum()),
                        "modelo": int((a_m * ini * s).sum()),
                    }
                )
out = pd.DataFrame(filas)
out["diferencia"] = out.modelo - out.canal
out.to_csv(carpeta / "lectura_tipo.csv", index=False)
print(out.to_string())
print(np.nan if out.empty else "")
