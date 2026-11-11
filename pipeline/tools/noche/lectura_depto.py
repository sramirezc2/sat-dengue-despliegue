"""Inicios detectados por departamento: canal condicionado contra cada receta (tanda 25).

Mismo presupuesto por mes de origen que validar_candidato (el del canal condicionado).
Uso: python tools/noche/lectura_depto.py <carpeta> [receta ...]
"""

import hashlib
import os
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
recetas = sys.argv[2:] or list(preds.receta.unique())
filas = []
for h in (1, 2):
    historia = va.historia_desde_panel(table, h)
    for r in recetas:
        q = preds[(preds.receta == r) & (preds.horizon == h)].drop(columns="receta")
        df = va.desde_pipeline(table, q, str(q.candidate.iloc[0]), h)
        anios = tuple(sorted(int(a) for a in df.anio_objetivo.unique() if a < 2025))
        big = va.lineas_base_por_anio(va.validar_entrada(df, anios), anios, historia)
        a_m = np.zeros(len(big), int)
        if os.environ.get("PRESUPUESTO"):
            # Presupuesto de la sección 0: fracción de 76 municipios por mes, f fija.
            total = float(os.environ["PRESUPUESTO"]) * 76 * big.origen.nunique()
            big["canal_fuera_exceso"] = min(
                (va.canal(big, f, fuera_exceso=True) for f in va.GRILLA_F),
                key=lambda a: abs(int(a.sum()) - total),
            )
            a_m = va.emparejar(big, big["canal_fuera_exceso"].values)
        else:
            for _, g in big.groupby("anio_objetivo"):
                a_m[g.index.values] = va.emparejar(g, g["canal_fuera_exceso"].values)
        ini = big.inicio.values == 1
        dep = big.municipio.astype(str).str[:2]
        for d in ("50", "73"):
            s = (dep == d).values
            filas.append(
                {
                    "horizonte": h,
                    "receta": r,
                    "departamento": {"50": "Meta", "73": "Tolima"}[d],
                    "inicios": int((ini & s).sum()),
                    "canal": int((big.canal_fuera_exceso.values * ini * s).sum()),
                    "receta_det": int((a_m * ini * s).sum()),
                }
            )
out = pd.DataFrame(filas)
out["diferencia"] = out.receta_det - out.canal
out.to_csv(carpeta / f"lectura_departamento{os.environ.get('PRESUPUESTO', '')}.csv", index=False)
print(out.to_string())
