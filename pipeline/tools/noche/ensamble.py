"""Ensamble de rangos sobre las predicciones del retroanálisis (tandas 14 y 23).

Promedio de rangos percentiles dentro de cada mes de origen, sin pesos. Escribe el ensamble
como una receta más (predicciones_ens_<a>+<b>.csv) para compararlo con comparar.py.
Uso: python tools/noche/ensamble.py <carpeta> <receta_a> <receta_b> [<receta_b2> ...]
"""

import sys
from pathlib import Path

import pandas as pd

carpeta = Path(sys.argv[1])
receta_a, otras = sys.argv[2], sys.argv[3:]
preds = pd.concat(
    [pd.read_csv(f, dtype={"municipality_code": str}) for f in carpeta.glob("predicciones*.csv")],
    ignore_index=True,
).drop_duplicates(["receta", "municipality_code", "origin_period", "horizon"])
claves = ["municipality_code", "origin_period", "target_period", "horizon"]
for b in otras:
    partes = []
    for h in sorted(preds.horizon.unique()):
        a = preds[(preds.receta == receta_a) & (preds.horizon == h)]
        o = preds[(preds.receta == b) & (preds.horizon == h)]
        m = a.merge(o[claves + ["raw_probability"]], on=claves, suffixes=("", "_b"))
        assert len(m) == len(a) == len(o), f"{receta_a} y {b} no tienen las mismas filas"
        ra = m.groupby("origin_period").raw_probability.rank(pct=True)
        rb = m.groupby("origin_period").raw_probability_b.rank(pct=True)
        etiqueta = f"ens_{receta_a}+{b}"
        partes.append(
            m[a.columns].assign(raw_probability=(ra + rb) / 2, candidate=etiqueta, receta=etiqueta)
        )
    pd.concat(partes).to_csv(carpeta / f"predicciones_ens_{receta_a}+{b}.csv", index=False)
    print("escrito", etiqueta)
