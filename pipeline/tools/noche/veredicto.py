"""Veredicto de la sección 0: canal condicionado contra el modelo, a presupuesto fijo.

Para cada horizonte y presupuesto (5, 10 y 20 % de los 76 municipios por mes, sección 0.1) se toma la fracción f
del canal condicionado cuyo número de alertas queda más cerca del presupuesto, y el modelo emite
las mismas alertas por mes de origen. Se reporta la diferencia de inicios en puntos, con dos IC
95 %: bootstrap por municipio (el de validar_candidato) y por bloques de mes de origen (el del
contrato), y la diferencia de carga de falsas alertas por 100 municipio-mes con su IC por mes.
A: IC excluye el cero. Barra 0.3: al menos 5 pp con la cota inferior sobre cero. C: carga no
supera en más de 5 a la del canal, ni su cota superior.
Uso: python tools/noche/veredicto.py <carpeta> <receta> [...]
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
rng = np.random.default_rng(42)


def boot(d, x, grupo, n=2000):
    """IC 95 % de la suma de x remuestreando bloques del grupo."""
    s = pd.Series(x, index=d.index).groupby(d[grupo]).sum().values
    b = rng.choice(s, size=(n, len(s)), replace=True).sum(axis=1)
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


filas = []
for receta in sys.argv[2:]:
    for h in (1, 2):
        q = preds[(preds.receta == receta) & (preds.horizon == h)].drop(columns="receta")
        df = va.desde_pipeline(table, q, str(q.candidate.iloc[0]), h)
        anios = tuple(sorted(int(a) for a in df.anio_objetivo.unique() if a < 2025))
        d = va.validar_entrada(df, anios)
        d = d[d.anio_objetivo.isin(anios)].reset_index(drop=True)
        n, ini = len(d), (d.inicio.values == 1)
        # Sección 0.1: el presupuesto es una fracción de los 76 municipios de cada mes,
        # no de las filas elegibles (las que no están en exceso).
        meses = d.origen.nunique()
        total = 76 * meses
        curva = [(f, va.canal(d, f, fuera_exceso=True)) for f in va.GRILLA_F]
        for frac in (0.05, 0.10, 0.20):
            f, a_c = min(curva, key=lambda t: abs(int(t[1].sum()) - frac * total))
            a_m = va.emparejar(d, a_c)
            mc, mm = va.metricas(a_c, d), va.metricas(a_m, d)
            dif = (a_m - a_c) * ini
            fa = (a_m - a_c) * (~ini) * 100 / n
            lo_m, hi_m = boot(d, dif, "municipio")
            lo_o, hi_o = boot(d, dif, "origen")
            lo_c, hi_c = boot(d, fa, "origen")
            I = mc["inicios"]
            dpp, lopp = 100 * dif.sum() / I, 100 * lo_o / I
            dcarga = mm["carga_100mm"] - mc["carga_100mm"]
            filas.append(
                {
                    "receta": receta,
                    "horizonte": h,
                    "presupuesto": frac,
                    "f": f,
                    "objetivo": round(frac * total),
                    "alertas": int(a_c.sum()),
                    "alertas_mes": round(a_c.sum() / meses, 1),
                    "fraccion_real": round(a_c.sum() / total, 3),
                    "filas_evaluadas": n,
                    "inicios": I,
                    "canal": mc["inicios_detectados"],
                    "modelo": mm["inicios_detectados"],
                    "dif_pp": round(dpp, 1),
                    "ic_mun_pp": f"{100 * lo_m / I:.1f} a {100 * hi_m / I:.1f}",
                    "ic_mes_pp": f"{lopp:.1f} a {100 * hi_o / I:.1f}",
                    "dif_carga": round(dcarga, 2),
                    "ic_carga": f"{lo_c:.2f} a {hi_c:.2f}",
                    "A": "CUMPLE" if lo_o > 0 else "NO",
                    "barra_5pp": "CUMPLE" if dpp >= 5 and lo_o > 0 else "NO",
                    "C": "CUMPLE" if dcarga <= 5 and hi_c <= 5 else "NO",
                }
            )
out = pd.DataFrame(filas)
out.to_csv(carpeta / "veredicto.csv", index=False)
print(out.to_string())
