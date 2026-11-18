"""Comprueba que las recetas comparten claves (municipio, origen, horizonte) y etiquetas evaluadas.

Uso (desde pipeline/, PYTHONPATH=src): python claves_etiquetas.py <predicciones.csv> <receta> [...]
Para cada receta y horizonte construye las filas evaluables con validacion_anual (igual que
veredicto.py) y calcula un SHA-256 de las claves y otro de claves + etiqueta de inicio.
"""
import hashlib
import sys
from pathlib import Path

import pandas as pd

from sat_dengue_pipeline.evaluation import validacion_anual as va
from sat_dengue_pipeline.raw.serialization import CanonicalArtifact, load_canonical

CERT = "de49b11bad43c35983a098ead2faa149d4e744da4172432aecdaadd828c73158"
p = Path(f"data/noche_panel/{CERT}/canonical.json")
table, _ = load_canonical(CanonicalArtifact(p, CERT, hashlib.sha256(p.read_bytes()).hexdigest()))
table = table[table.department_code.isin(["50", "73"])].reset_index(drop=True)
preds = pd.read_csv(sys.argv[1], dtype={"municipality_code": str})
filas = []
for receta in sys.argv[2:]:
    for h in (1, 2):
        q = preds[(preds.receta == receta) & (preds.horizon == h)].drop(columns="receta")
        crudas = q[["municipality_code", "origin_period"]].sort_values(["municipality_code", "origin_period"])
        df = va.desde_pipeline(table, q, str(q.candidate.iloc[0]), h)
        anios = tuple(sorted(int(a) for a in df.anio_objetivo.unique() if a < 2025))
        d = va.validar_entrada(df, anios).sort_values(["municipio", "origen"])
        k = d[["municipio", "origen"]].astype(str).to_csv(index=False).encode()
        ke = d[["municipio", "origen", "inicio"]].astype(str).to_csv(index=False).encode()
        filas.append({
            "receta": receta, "horizonte": h, "predicciones": len(q),
            "sha_claves_predicciones": hashlib.sha256(crudas.to_csv(index=False).encode()).hexdigest()[:16],
            "filas_evaluables": len(d), "inicios": int(d.inicio.sum()),
            "sha_claves_evaluables": hashlib.sha256(k).hexdigest()[:16],
            "sha_claves_y_etiquetas": hashlib.sha256(ke).hexdigest()[:16],
        })
out = pd.DataFrame(filas)
print(out.to_string())
for h, g in out.groupby("horizonte"):
    for c in ("sha_claves_predicciones", "sha_claves_evaluables", "sha_claves_y_etiquetas"):
        print(f"T+{h} {c}: {'IGUAL en todas' if g[c].nunique() == 1 else 'DISTINTO'}")
out.to_csv("comprobacion_claves_etiquetas.csv", index=False)
