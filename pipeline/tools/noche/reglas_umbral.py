"""Reglas desplegables: umbral del canal y del modelo fijados con el año anterior (tanda 41).

Uso: python tools/noche/reglas_umbral.py <carpeta> <receta> [...]
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
        ini = d.inicio.values == 1
        for y in anios[1:]:
            prev, cur = d[d.anio_objetivo == y - 1], d[d.anio_objetivo == y]
            objetivo = 0.10 * 76 * prev.origen.nunique()
            f = min(va.GRILLA_F, key=lambda f: abs(int(va.canal(prev, f, True).sum()) - objetivo))
            k = int(round(objetivo))
            umbral = np.sort(prev.score.values)[::-1][min(k, len(prev)) - 1]
            a_c = va.canal(cur, f, fuera_exceso=True)
            a_m = (cur.score.values >= umbral).astype(int)
            i = cur.index.values
            for metodo, a in (("canal", a_c), ("modelo", a_m)):
                m = va.metricas(a, cur)
                filas.append(
                    {
                        "receta": receta,
                        "horizonte": h,
                        "anio": y,
                        "metodo": metodo,
                        "alertas": int(a.sum()),
                        "inicios": int(ini[i].sum()),
                        "detectados": m["inicios_detectados"],
                        "falsas": m["falsas"],
                    }
                )
out = pd.DataFrame(filas)
out.to_csv(carpeta / "reglas_umbral.csv", index=False)
tot = out.groupby(["receta", "horizonte", "metodo"])[["alertas", "inicios", "detectados", "falsas"]].sum()
tot["falsas_por_acierto"] = (tot.falsas / tot.detectados).round(2)
print(tot.to_string())
