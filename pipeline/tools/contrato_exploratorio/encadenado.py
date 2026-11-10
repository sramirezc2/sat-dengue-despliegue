"""Idea de Mauro: un modelo alimenta al otro, evaluado con el contrato.

En T+2 se combina el puntaje del modelo T+2 con el del modelo T+1 emitido en el mismo mes de origen
(ambos disponibles al cierre de T; sin fuga), con el mismo canal condicionado y presupuesto, en las
cuatro cohortes combinadas con bootstrap por bloques de mes. Variantes: solo T+2, solo puntaje T+1,
promedio de rangos y máximo de rangos.
Uso: python encadenado.py <carpeta_runs> <prefijo_receta>
"""

import glob
import hashlib
import json
import sys
from pathlib import Path

import contrato_local as ct
import numpy as np
import pandas as pd

from sat_dengue_pipeline.raw.serialization import CanonicalArtifact, load_canonical

carpeta, receta = Path(sys.argv[1]), sys.argv[2]
p = Path(sorted(glob.glob("data/retro-real/provisional/*/canonical.json"))[-1])
table, _ = load_canonical(
    CanonicalArtifact(p, p.parent.name, hashlib.sha256(p.read_bytes()).hexdigest())
)
table = table[table.department_code.isin(["50", "73"])].reset_index(drop=True)
P = ct.PARAMETROS_DEFECTO
filas = {k: [] for k in ("solo T+2", "solo puntaje T+1", "promedio de rangos", "maximo de rangos")}
for s in range(4):
    f = carpeta / f"{receta}_s{s}.json"
    if not f.exists():
        continue
    r = json.load(open(f, encoding="utf-8"))
    k2 = pd.DataFrame(
        {c: r["2"]["scores"][c] for c in ("municipality_code", "origin_period", "target_period")}
    ).assign(s2=r["2"]["scores"]["raw"])
    k1 = pd.DataFrame(
        {c: r["1"]["scores"][c] for c in ("municipality_code", "origin_period")}
    ).assign(s1=r["1"]["scores"]["raw"])
    m = k2.merge(k1, on=["municipality_code", "origin_period"], how="left")
    cobertura = m.s1.notna().mean()
    m["s1"] = m.s1.fillna(m.s1.min() if m.s1.notna().any() else 0.0)
    r2 = m.groupby("origin_period").s2.rank(pct=True)
    r1 = m.groupby("origin_period").s1.rank(pct=True)
    combos = {
        "solo T+2": m.s2.values,
        "solo puntaje T+1": m.s1.values,
        "promedio de rangos": ((r2 + r1) / 2).values,
        "maximo de rangos": np.maximum(r2, r1).values,
    }
    dk = pd.DataFrame(r["2"]["dev_keys"])
    keys = m[["municipality_code", "origin_period", "target_period"]]
    ev0 = ct.filas(keys, table, 2)
    dev = ct.filas(dk, table, 2)
    dev = dev[dev.evaluable].reset_index(drop=True)
    fcanal = ct.elegir_f(dev, P["grilla_f"])
    for nombre, sc in combos.items():
        ev = ev0.assign(score=sc)
        ev = ev[ev.evaluable].reset_index(drop=True)
        canal = ct._canal(ev, fcanal)
        kk = pd.Series(canal).groupby(ev.origen).transform("sum").values
        ev["a_c"] = canal
        ev["a_m"] = ct._top_k_por_mes(ev, ev.score.values, kk)
        filas[nombre].append(ev)
    print(f"cohorte s{s}: cobertura del puntaje T+1 en filas T+2 = {cobertura:.1%}", flush=True)
for nombre, partes in filas.items():
    if not partes:
        continue
    ev = pd.concat(partes, ignore_index=True)
    mm, mc = ct._medidas(ev.a_m.values, ev), ct._medidas(ev.a_c.values, ev)
    mp = ct._medidas((ev.exceso_t.values == 1).astype(int), ev)
    ic = ct._bootstrap(ev, ev.a_m.values, ev.a_c.values, 2000, 42, 0.95)
    v = ct._veredicto(mm, mc, mp, ic, P)
    print(
        f"T+2 {receta} [{nombre}]: canal {mc['detectados']} vs {mm['detectados']} de {mm['inicios']} | dS {v['delta_sensibilidad_pp']:.1f} "  # noqa: E501
        f"IC {[round(x, 1) for x in v['ic_delta_sensibilidad_pp']]} | dB {v['delta_carga_100mm']:.2f} -> {v['veredicto']}",  # noqa: E501
        flush=True,
    )
