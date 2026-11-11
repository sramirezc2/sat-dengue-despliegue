"""Tabla Markdown de una comparación emparejada (salida de comparar.py), para las tandas.

Uso: python tools/noche/tabla_md.py <carpeta> <referencia> [receta ...]
"""

import sys
from pathlib import Path

import pandas as pd

carpeta, ref = Path(sys.argv[1]), sys.argv[2]
c = pd.read_csv(carpeta / f"comparacion_vs_{ref}.csv")
a = pd.read_csv(carpeta / f"comparacion_anual_vs_{ref}.csv")
if sys.argv[3:]:
    c, a = c[c.receta.isin(sys.argv[3:])], a[a.receta.isin(sys.argv[3:])]
nombres = {"canal_fuera_exceso": "condicionado", "0.05": "5 %", "0.1": "10 %", "0.2": "20 %"}
for h, g in c.groupby("horizonte"):
    ini = int(g.inicios.iloc[0])
    print(
        f"\n| T+{h}, {ini} inicios | Presupuesto | Alertas | Referencia | Receta "
        "| Diferencia (IC 95 %) | pp | Carga ref → receta | Años a favor |"
    )
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for _, r in g.iterrows():
        anios = ""
        if r.presupuesto == "canal_fuera_exceso":
            q = a[(a.horizonte == h) & (a.receta == r.receta)]
            anios = f"{int((q.receta_det > q.ref).sum())}+ / {int((q.receta_det < q.ref).sum())}−"
        p = nombres.get(str(r.presupuesto), str(r.presupuesto))
        print(
            f"| {r.receta} | {p} | {int(r.alertas)} | {int(r.ref_detectados)} | "
            f"{int(r.receta_detectados)} | {int(r.diferencia):+d} "
            f"({r.ic95_lo:.0f} a {r.ic95_hi:.0f}) | "
            f"{r.dif_pp:+.1f} | {r.ref_carga_100mm:.2f} → {r.receta_carga_100mm:.2f} | {anios} |"
        )
