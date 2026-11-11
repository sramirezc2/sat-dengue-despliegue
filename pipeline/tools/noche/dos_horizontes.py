"""Inicios de T+1 avisados a uno o a dos meses, al 10 % en cada horizonte (tanda 37).

Uso: python tools/noche/dos_horizontes.py <carpeta> <receta> [...]
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
carpeta = Path(sys.argv[1])
preds = pd.concat(
    [pd.read_csv(f, dtype={"municipality_code": str}) for f in carpeta.glob("predicciones*.csv")],
    ignore_index=True,
).drop_duplicates(["receta", "municipality_code", "origin_period", "horizon"])


def alertas(receta, h):
    """Filas evaluadas con alerta del canal y del modelo, por mes objetivo."""
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
    d["canal"], d["modelo"], d["objetivo_mes"] = a_c, va.emparejar(d, a_c), d.origen + h
    return d


filas = []
for receta in sys.argv[2:]:
    d1, d2 = alertas(receta, 1), alertas(receta, 2)
    m = d1[d1.inicio == 1][["municipio", "objetivo_mes", "canal", "modelo"]].merge(
        d2[["municipio", "objetivo_mes", "canal", "modelo"]],
        on=["municipio", "objetivo_mes"],
        how="left",
        suffixes=("_1", "_2"),
    ).fillna(0)
    for quien in ("canal", "modelo"):
        a1, a2 = m[f"{quien}_1"] == 1, m[f"{quien}_2"] == 1
        filas.append(
            {
                "receta": receta,
                "metodo": quien,
                "inicios": len(m),
                "a_un_mes": int(a1.sum()),
                "a_dos_meses": int(a2.sum()),
                "cualquiera": int((a1 | a2).sum()),
                "solo_a_dos": int((a2 & ~a1).sum()),
            }
        )
out = pd.DataFrame(filas)
out.to_csv(carpeta / "dos_horizontes.csv", index=False)
print(out.to_string())
