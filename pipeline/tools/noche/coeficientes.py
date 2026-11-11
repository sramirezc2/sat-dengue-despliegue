"""Coeficientes estandarizados de la logística en el último fold (tanda 39).

Reentrena la receta solo en el último origen evaluable de cada horizonte, con toda la
historia anterior, y lee los coeficientes por desviación estándar.
Uso: python tools/noche/coeficientes.py <receta.yml> [...]
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd
import yaml

from sat_dengue_pipeline.evaluation import retroanalisis as ra
from sat_dengue_pipeline.models import familias
from sat_dengue_pipeline.raw.serialization import CanonicalArtifact, load_canonical

CERT = "de49b11bad43c35983a098ead2faa149d4e744da4172432aecdaadd828c73158"
p = Path(f"data/noche_panel/{CERT}/canonical.json")
table, schema = load_canonical(
    CanonicalArtifact(p, CERT, hashlib.sha256(p.read_bytes()).hexdigest())
)
table = table[table.department_code.isin(["50", "73"])].reset_index(drop=True)
instancias = []
for clave, clase in list(familias.ADAPTERS.items()):

    def crear(*a, _c=clase, **k):
        """Construir el adaptador y guardar la instancia para leerla después."""
        obj = _c(*a, **k)
        instancias.append(obj)
        return obj

    ra.ADAPTERS[clave] = crear
filas = []
for ruta in sys.argv[1:]:
    config = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))
    for h in (1, 2):
        ultimo = {1: "2024-10", 2: "2024-09"}[h]
        preds, omit, _ = ra.predicciones_rolling(table, schema, config, h, ultimo, "2024-12", "2012-01")
        print(len(preds), omit[:1])
        coef = instancias[-1].coeficientes()
        for col, v in coef.items():
            filas.append({"receta": Path(ruta).stem, "horizonte": h, "columna": col, "coef": v})
out = pd.DataFrame(filas)
out.to_csv("data/noche/coeficientes.csv", index=False)
for (r, h), g in out.groupby(["receta", "horizonte"]):
    g = g.reindex(g.coef.abs().sort_values(ascending=False).index)
    print(r, f"T+{h}", "; ".join(f"{c} {v:+.2f}" for c, v in zip(g.columna[:12], g.coef[:12])))
