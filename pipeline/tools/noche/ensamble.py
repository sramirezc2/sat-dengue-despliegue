"""Ensamble de rangos sobre predicciones.csv del retroanálisis (tanda 14, línea V).

Promedio de rangos percentiles dentro de cada mes de origen, sin pesos. Se evalúa con
validar_candidato, igual que cualquier receta, sobre las mismas filas.
Uso: python tools/noche/ensamble.py <carpeta_salida> <receta_a> <receta_b> [<receta_b2> ...]
Con varias recetas b (semillas), un ensamble por cada una.
"""

import glob
import hashlib
import os
import sys
from pathlib import Path

import pandas as pd

from sat_dengue_pipeline.evaluation.validacion_anual import validar_candidato
from sat_dengue_pipeline.raw.serialization import CanonicalArtifact, load_canonical

carpeta = Path(sys.argv[1])
receta_a, otras = sys.argv[2], sys.argv[3:]
panel = os.environ.get("PANEL_DIR", "data/canonical-2007")
p = Path(sorted(glob.glob(panel + "/**/canonical.json", recursive=True))[-1])
table, _ = load_canonical(
    CanonicalArtifact(p, p.parent.name, hashlib.sha256(p.read_bytes()).hexdigest())
)
table = table[table.department_code.isin(["50", "73"])].reset_index(drop=True)
preds = pd.read_csv(carpeta / "predicciones.csv", dtype={"municipality_code": str})
claves = ["municipality_code", "origin_period", "target_period", "horizon"]
salida = []
for b in otras:
    for h in sorted(preds.horizon.unique()):
        a = preds[(preds.receta == receta_a) & (preds.horizon == h)]
        o = preds[(preds.receta == b) & (preds.horizon == h)]
        m = a.merge(o[claves + ["raw_probability"]], on=claves, suffixes=("", "_b"))
        assert len(m) == len(a) == len(o), "Las dos recetas no tienen las mismas filas"
        ra = m.groupby("origin_period").raw_probability.rank(pct=True)
        rb = m.groupby("origin_period").raw_probability_b.rank(pct=True)
        ens = m[a.columns].assign(raw_probability=(ra + rb) / 2, candidate="ensamble")
        resumen, anio, _ = validar_candidato(
            table, ens.drop(columns="receta"), {"candidato": "ensamble", "horizonte": int(h)}
        )
        etiqueta = f"ens_{receta_a}+{b}"
        salida.append(resumen.assign(horizonte=h, receta=etiqueta))
        anio.assign(horizonte=h, receta=etiqueta).to_csv(
            carpeta / f"por_anio_{etiqueta}_h{h}.csv", index=False
        )
pd.concat(salida).to_csv(carpeta / "resumen_ensambles.csv", index=False)
print(pd.concat(salida).to_string())
