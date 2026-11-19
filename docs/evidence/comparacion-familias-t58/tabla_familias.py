"""Une las salidas de veredicto_anios.py por periodo y resume el rango de XGBoost entre semillas.

Uso: python tabla_familias.py <carpeta con v_completo.csv, v_seleccion.csv, v_reserva.csv>
"""
import sys
from pathlib import Path

import pandas as pd

c = Path(sys.argv[1])
periodos = {"completo": "2018-2024", "seleccion": "2018-2022", "reserva": "2023-2024"}
t = pd.concat([pd.read_csv(c / f"v_{k}.csv").assign(periodo=v) for k, v in periodos.items()])
t["familia"] = t.receta.str.replace(r"_s\d+$", "", regex=True)
t["semilla"] = t.receta.str.extract(r"_s(\d+)$")[0]
t["ic_mes_inf"] = t.ic_mes_pp.str.split(" a ").str[0].astype(float)
cols = ["periodo", "horizonte", "familia", "semilla", "receta", "presupuesto", "f", "objetivo", "alertas",
        "alertas_mes", "filas_evaluadas", "inicios", "canal", "modelo", "dif_pp", "ic_mes_pp", "dif_carga",
        "ic_carga", "A", "barra_5pp", "C"]
t[cols].to_csv(c / "comparacion_familias.csv", index=False)
g = t.groupby(["periodo", "horizonte", "familia"], sort=False)
r = g.agg(semillas=("receta", "size"), inicios=("inicios", "first"), canal=("canal", "first"),
          alertas=("alertas", "first"), modelo_min=("modelo", "min"), modelo_max=("modelo", "max"),
          dif_pp_min=("dif_pp", "min"), dif_pp_max=("dif_pp", "max"),
          ic_inf_min=("ic_mes_inf", "min"), ic_inf_max=("ic_mes_inf", "max"),
          cumplen_barra=("barra_5pp", lambda s: int((s == "CUMPLE").sum()))).reset_index()
r.to_csv(c / "rango_por_familia.csv", index=False)
print(r.to_string())
