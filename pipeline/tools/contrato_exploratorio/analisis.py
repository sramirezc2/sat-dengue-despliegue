"""Consolida las corridas del contrato (contrato_runs/*.json).

1) Tabla de todas las corridas.
2) Evidencia acumulada por receta con varios años de evaluación (desplazamientos 0-4): se
reconstruyen las
   alertas fila a fila con las funciones del contrato (f de cada cohorte, mismo presupuesto) y
   se aplica el
   bootstrap emparejado por bloques de mes objetivo sobre el conjunto.
3) Ensamble de rangos logística + XGBoost (desplazamiento 0).
4) Inicios sostenidos frente a picos de un mes, y sensibilidad del veredicto a la meta (5, 7,5 y
10 pp).
Uso: python analisis_contrato.py <carpeta_runs> <salida.json>
"""

import glob
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.evaluation import contrato as ct
from sat_dengue_pipeline.raw.serialization import CanonicalArtifact, load_canonical

carpeta, salida = Path(sys.argv[1]), Path(sys.argv[2])
p = Path(
    sorted(
        glob.glob(
            os.environ.get("PANEL_DIR", "data/retro-real") + "/**/canonical.json", recursive=True
        )
    )[-1]
)
table, _ = load_canonical(
    CanonicalArtifact(p, p.parent.name, hashlib.sha256(p.read_bytes()).hexdigest())
)
table = table[table.department_code.isin(["50", "73"])].reset_index(drop=True)
exc = ct._exceso(table)
P = ct.PARAMETROS_DEFECTO
runs = {}
for f in sorted(carpeta.glob("*.json")):
    runs[f.stem] = json.load(open(f, encoding="utf-8"))
resumen = []
for n, r in runs.items():
    for h in ("1", "2"):
        c = r[h]["contract"]
        v = c["veredictos"]["candidato"]
        m = c["medidas"]
        resumen.append(
            {
                "corrida": n,
                "receta": n.rsplit("_s", 1)[0],
                "desplazamiento": r["desplazamiento"],
                "h": int(h),
                "evaluacion": r["evaluacion"][h]["start"][:4],
                "inicios": m["candidato"]["inicios"],
                "canal": m["canal_condicionado"]["detectados"],
                "modelo": m["candidato"]["detectados"],
                "dS_pp": round(v.get("delta_sensibilidad_pp", np.nan), 1),
                "ic_dS": [round(x, 1) for x in v.get("ic_delta_sensibilidad_pp", [np.nan, np.nan])],
                "dB": round(v.get("delta_carga_100mm", np.nan), 2),
                "veredicto": c["veredicto"],
                "controles_ok": c["controles_negativos_validos"],
            }
        )
R = pd.DataFrame(resumen).sort_values(["h", "receta", "desplazamiento"])
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 200)
print("== 1) Todas las corridas")
print(R.to_string(index=False))


def filas_alertas(r, h, score=None, mult=1.0):
    """Reconstruye filas evaluables con alertas del canal condicionado y del candidato (mismo presupuesto)."""  # noqa: E501
    s = r[h]["scores"]
    k = pd.DataFrame({c: s[c] for c in ("municipality_code", "origin_period", "target_period")})
    dk = pd.DataFrame(r[h]["dev_keys"])
    ev = ct.filas(k, table, int(h)).assign(
        score=np.asarray(score if score is not None else s["raw"], float)
    )
    dev = ct.filas(dk, table, int(h))
    ev, dev = ev[ev.evaluable].reset_index(drop=True), dev[dev.evaluable].reset_index(drop=True)
    f = ct.elegir_f(dev, P["grilla_f"])
    canal = ct._canal(ev, f)
    kk = pd.Series(canal).groupby(ev.origen).transform("sum").values
    ev["a_c"] = canal
    ev["a_m"] = ct._top_k_por_mes(ev, ev.score.values, np.round(kk * mult))
    prev = [add_months(t, 1) for t in ev.objetivo]
    ev["sostenido"] = exc.reindex(pd.MultiIndex.from_arrays([ev.municipio, prev])).values
    return ev


def veredicto(ev, meta=10.0, reps=2000):
    """Veredicto del contrato sobre un conjunto de filas (puede combinar cohortes)."""
    mm, mc = ct._medidas(ev.a_m.values, ev), ct._medidas(ev.a_c.values, ev)
    mp = ct._medidas((ev.exceso_t.values == 1).astype(int), ev)
    ic = ct._bootstrap(ev, ev.a_m.values, ev.a_c.values, reps, P["semilla"], P["nivel"])
    return ct._veredicto(mm, mc, mp, ic, {**P, "ganancia_minima_pp": meta}), mm, mc


out = {
    "resumen": resumen,
    "acumulado": {},
    "ensamble": {},
    "sostenidos": {},
    "metas": {},
    "presupuesto": {},
    "heterogeneidad": {},
    "modelo_vs_modelo": {},
}
print("\n== 2) Evidencia acumulada por receta (todas las cohortes de evaluación disponibles)")
for receta in sorted(set(R.receta)):
    for h in ("1", "2"):
        cs = [n for n in runs if n.rsplit("_s", 1)[0] == receta]
        if len(cs) < 2:
            continue
        ev = pd.concat([filas_alertas(runs[n], h).assign(cohorte=n) for n in cs], ignore_index=True)
        v, mm, mc = veredicto(ev)
        anios = sorted({runs[n]["evaluacion"][h]["start"][:4] for n in cs})
        out["acumulado"][f"{receta} T+{h}"] = {
            "anios": anios,
            "inicios": mm["inicios"],
            "canal": mc["detectados"],
            "modelo": mm["detectados"],
            **v,
        }
        print(
            f"{receta} T+{h} años {anios}: I={mm['inicios']} canal {mc['detectados']} vs {mm['detectados']} | "  # noqa: E501
            f"dS {v['delta_sensibilidad_pp']:.1f} IC {[round(x, 1) for x in v['ic_delta_sensibilidad_pp']]} | "  # noqa: E501
            f"dB {v['delta_carga_100mm']:.2f} IC {[round(x, 2) for x in v['ic_delta_carga_100mm']]} -> {v['veredicto']}",  # noqa: E501
            flush=True,
        )
        for meta in (5.0, 7.5, 10.0):
            out["metas"][f"{receta} T+{h} meta {meta}"] = veredicto(ev, meta)[0]["veredicto"]
        print(
            "   con meta 5 / 7,5 / 10 pp:",
            [out["metas"][f"{receta} T+{h} meta {m}"] for m in (5.0, 7.5, 10.0)],
        )
        ini = ev.inicio.values == 1
        for nombre, mask in (
            ("sostenidos", ini & (ev.sostenido.values == 1)),
            ("picos de un mes", ini & (ev.sostenido.values == 0)),
        ):
            out["sostenidos"][f"{receta} T+{h} {nombre}"] = {
                "inicios": int(mask.sum()),
                "canal": int(ev.a_c.values[mask].sum()),
                "modelo": int(ev.a_m.values[mask].sum()),
            }
            print(
                f"   {nombre}: {int(mask.sum())} | canal {int(ev.a_c.values[mask].sum())} vs modelo {int(ev.a_m.values[mask].sum())}"  # noqa: E501
            )
print("\n== 3) Ensamble de rangos logística + XGBoost (cada cohorte disponible en ambos)")
for s in range(7):
    a, b = runs.get(f"log_sinclima_C1_s{s}"), runs.get(f"xgb_300d4_conclima_s{s}")
    if not (a and b):
        continue
    for h in ("1", "2"):
        ka = pd.DataFrame(
            {c: a[h]["scores"][c] for c in ("municipality_code", "origin_period", "target_period")}
        ).assign(sa=a[h]["scores"]["raw"])
        kb = pd.DataFrame(
            {c: b[h]["scores"][c] for c in ("municipality_code", "origin_period", "target_period")}
        ).assign(sb=b[h]["scores"]["raw"])
        e = ka.merge(kb, on=["municipality_code", "origin_period", "target_period"], how="inner")
        if len(e) != len(ka):
            print(f"   s{s} T+{h}: claves distintas, se omite")
            continue
        e["s"] = (
            e.groupby("origin_period").sa.rank(pct=True)
            + e.groupby("origin_period").sb.rank(pct=True)
        ) / 2
        r2 = {
            h: {
                "scores": {
                    **{
                        c: e[c].tolist()
                        for c in ("municipality_code", "origin_period", "target_period")
                    },
                    "raw": e.s.tolist(),
                },
                "dev_keys": a[h]["dev_keys"],
            }
        }
        ev = filas_alertas(r2, h)
        v, mm, mc = veredicto(ev)
        out["ensamble"][f"s{s} T+{h}"] = {
            "canal": mc["detectados"],
            "modelo": mm["detectados"],
            "inicios": mm["inicios"],
            **v,
        }
        print(
            f"   eval {a['evaluacion'][h]['start'][:4]} T+{h}: canal {mc['detectados']} vs ensamble {mm['detectados']} de {mm['inicios']} | "  # noqa: E501
            f"dS {v['delta_sensibilidad_pp']:.1f} IC {[round(x, 1) for x in v['ic_delta_sensibilidad_pp']]} -> {v['veredicto']}",  # noqa: E501
            flush=True,
        )

print(
    "\n== 5) Sensibilidad al presupuesto (alertas del modelo = m x alertas del canal), acumulado por receta"  # noqa: E501
)
for receta in ("log_sinclima_C1", "xgb_300d4_conclima", "log_minima"):
    for h in ("1", "2"):
        cs = [n for n in runs if n.rsplit("_s", 1)[0] == receta]
        if len(cs) < 2:
            continue
        for mult in (0.5, 1.0, 1.1, 1.2, 1.3, 1.5, 2.0):
            ev = pd.concat([filas_alertas(runs[n], h, mult=mult) for n in cs], ignore_index=True)
            mm, mc = ct._medidas(ev.a_m.values, ev), ct._medidas(ev.a_c.values, ev)
            out["presupuesto"][f"{receta} T+{h} x{mult}"] = {
                "S_modelo": mm["sensibilidad"],
                "S_canal": mc["sensibilidad"],
                "B_modelo": mm["carga_100mm"],
                "B_canal": mc["carga_100mm"],
            }
            print(
                f"{receta} T+{h} x{mult}: S modelo {100 * mm['sensibilidad']:.1f} % (canal {100 * mc['sensibilidad']:.1f} %) | "  # noqa: E501
                f"B modelo {mm['carga_100mm']:.2f} (canal {mc['carga_100mm']:.2f})",
                flush=True,
            )
print("\n== 6) Heterogeneidad acumulada por departamento y año (logística sin clima y XGBoost)")
for receta in ("log_sinclima_C1", "xgb_300d4_conclima"):
    for h in ("1", "2"):
        cs = [n for n in runs if n.rsplit("_s", 1)[0] == receta]
        if len(cs) < 2:
            continue
        ev = pd.concat([filas_alertas(runs[n], h) for n in cs], ignore_index=True)
        ev["anio"] = ev.objetivo.str[:4]
        for col in ("departamento", "anio"):
            for val, g in ev.groupby(col):
                d = {
                    "inicios": int(g.inicio.sum()),
                    "canal": int((g.a_c * g.inicio).sum()),
                    "modelo": int((g.a_m * g.inicio).sum()),
                }
                out["heterogeneidad"][f"{receta} T+{h} {col}={val}"] = d
        if True:
            print(
                f"{receta} T+{h}:",
                {
                    f"{c}={v}": (
                        int((g.a_m * g.inicio).sum()),
                        int((g.a_c * g.inicio).sum()),
                        int(g.inicio.sum()),
                    )
                    for c in ("departamento", "anio")
                    for v, g in ev.groupby(c)
                },
                flush=True,
            )
print("\n== 7) Logística vs XGBoost, emparejado (mismas cohortes, mismo presupuesto)")
for h in ("1", "2"):
    filas_l, filas_x = [], []
    for s in range(7):
        a, b = runs.get(f"log_sinclima_C1_s{s}"), runs.get(f"xgb_300d4_conclima_s{s}")
        if a and b:
            filas_l.append(filas_alertas(a, h))
            filas_x.append(filas_alertas(b, h))
    if not filas_l:
        continue
    L, X = pd.concat(filas_l, ignore_index=True), pd.concat(filas_x, ignore_index=True)
    if len(L) == len(X) and (L.municipio.values == X.municipio.values).all():
        ic = ct._bootstrap(L, L.a_m.values, X.a_m.values, 2000, 42, 0.95)
        dS = 100 * ((L.a_m * L.inicio).sum() - (X.a_m * X.inicio).sum()) / L.inicio.sum()
        out["modelo_vs_modelo"][f"T+{h}"] = {"dS_pp": dS, "ic": [ic[0], ic[1]]}
        print(
            f"T+{h}: logística - XGBoost = {dS:.1f} pp (IC {ic[0]:.1f} a {ic[1]:.1f})", flush=True
        )

print(
    "\n" + "== 8) Presupuesto elegido en 2021-2022 (desarrollo) y evaluado congelado en 2023-2024"
)
for receta in ("log_sinclima_C1", "log_minima", "xgb_300d4_conclima"):
    for h in ("1", "2"):
        dev_c = [f"{receta}_s{s}" for s in (2, 3) if f"{receta}_s{s}" in runs]
        ev_c = [f"{receta}_s{s}" for s in (0, 1) if f"{receta}_s{s}" in runs]
        if len(dev_c) < 2 or len(ev_c) < 2:
            continue
        mejor = None
        for mult in (1.0, 1.1, 1.2, 1.3, 1.5):
            d = pd.concat([filas_alertas(runs[n], h, mult=mult) for n in dev_c], ignore_index=True)
            mm, mc = ct._medidas(d.a_m.values, d), ct._medidas(d.a_c.values, d)
            dS, dB = (
                100 * (mm["sensibilidad"] - mc["sensibilidad"]),
                mm["carga_100mm"] - mc["carga_100mm"],
            )
            if dB <= 5 and (mejor is None or dS > mejor[1]):
                mejor = (mult, dS, dB)
        mult = mejor[0]
        e = pd.concat([filas_alertas(runs[n], h, mult=mult) for n in ev_c], ignore_index=True)
        v, mm, mc = veredicto(e)
        out.setdefault("presupuesto_elegido", {})[f"{receta} T+{h}"] = {
            "mult": mult,
            "dev_dS": mejor[1],
            "dev_dB": mejor[2],
            **v,
        }
        print(
            f"{receta} T+{h}: m={mult} (desarrollo dS {mejor[1]:.1f}, dB {mejor[2]:.2f}) -> 2023-24: canal {mc['detectados']} vs {mm['detectados']} de {mm['inicios']} | "  # noqa: E501
            f"dS {v['delta_sensibilidad_pp']:.1f} IC {[round(x, 1) for x in v['ic_delta_sensibilidad_pp']]} | dB {v['delta_carga_100mm']:.2f} IC {[round(x, 2) for x in v['ic_delta_carga_100mm']]} -> {v['veredicto']}",  # noqa: E501
            flush=True,
        )
json.dump(out, open(salida, "w", encoding="utf-8"), default=float, ensure_ascii=False, indent=1)
R.to_csv(salida.with_suffix(".csv"), index=False)
