"""Corrida exploratoria con el motor de la fábrica (cinco roles) y el contrato, sobre datos reales.

No pasa por el registro: no produce evidencia ni cambia estados.
Uso: python corrida.py <receta.yml> <desplazamiento_años> <salida.json>
  receta.yml: bloques candidate/preparation/predictors/seed (como conf/retroanalisis/*.yml)
  desplazamiento: 0 = roles de EXP001 (evaluación 2024); 1 = todo 12 meses antes (evaluación
  2023); ...
Guarda además las probabilidades de evaluación por clave, para ensambles posteriores.
"""

import copy
import glob
import hashlib
import json
import sys
from pathlib import Path

import yaml

from sat_dengue_pipeline.domain.calendar import add_months
from sat_dengue_pipeline.evaluation.contrato import PARAMETROS_DEFECTO
from sat_dengue_pipeline.factory import engine
from sat_dengue_pipeline.factory.rolling_protocol import filtrar_poblacion
from sat_dengue_pipeline.raw.serialization import CanonicalArtifact, load_canonical

receta, shift, salida = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3])
base = yaml.safe_load(open("conf/experiments/EXP001.yml", encoding="utf-8"))
rec = yaml.safe_load(open(receta, encoding="utf-8"))
cfg = copy.deepcopy(base)
for k in ("predictors", "preparation", "candidate"):
    cfg[k] = copy.deepcopy(rec[k])
cfg["seed"] = rec.get("seed", base["seed"])
cfg["calibration"]["parameters"]["random_state"] = cfg["seed"]
for h, roles in cfg["roles_by_horizon"].items():
    for r in roles.values():
        r["start"], r["end"] = (
            add_months(r["start"], -12 * shift),
            add_months(r["end"], -12 * shift),
        )
    # Variables completas (canal de 5 años) desde objetivos 2016-08: se recorta train y se declara su soporte real.  # noqa: E501
    tr = roles["train"]
    if tr["start"] < "2016-08":
        tr["start"] = "2016-08"
        n = (int(tr["end"][:4]) - 2016) * 12 + int(tr["end"][5:]) - 8 + 1
        if n < 12:
            raise SystemExit(f"Cohorte no factible: train de {n} meses")
        tr["support"]["months"] = n
cfg["population"] = {"department_codes": ["50", "73"]}
cfg["contract"] = dict(PARAMETROS_DEFECTO)
p = Path(sorted(glob.glob("data/retro-real/provisional/*/canonical.json"))[-1])
art = CanonicalArtifact(p, p.parent.name, hashlib.sha256(p.read_bytes()).hexdigest())
table, schema = load_canonical(art)
table = filtrar_poblacion(table, cfg)
run = engine.FactoryRun(
    None,
    cfg,
    Path(f"data/contrato-tmp-{salida.stem}"),
    {},
    artifact=art,
    table=table,
    schema=schema,
    audit={},
)
for fn in (engine.prepare, engine.preflight, engine.fit, engine.predict, engine.evaluate):
    fn(run)
out = {
    "receta": receta,
    "desplazamiento": shift,
    "evaluacion": {h: cfg["roles_by_horizon"][h]["evaluation"] for h in cfg["roles_by_horizon"]},
}
for h, r in run.results.items():
    pred = run.predictions[int(h)]
    out[h] = {
        "contract": r["contract"],
        "threshold": r["threshold"],
        "scores": {
            "municipality_code": pred.keys.municipality_code.tolist(),
            "origin_period": pred.keys.origin_period.tolist(),
            "target_period": pred.keys.target_period.tolist(),
            "raw": pred.raw_probability.astype(float).tolist(),
        },
        "dev_keys": {
            c: run.batches[int(h)]["threshold_selection"].keys[c].tolist()
            for c in ("municipality_code", "origin_period", "target_period")
        },
    }
    out[h]["model_sha256"] = run.fitted[int(h)].model.adapter.model_sha256()
json.dump(out, open(salida, "w", encoding="utf-8"), default=float, ensure_ascii=False)
for h in sorted(k for k in out if k.isdigit()):
    c = out[h]["contract"]
    v = c["veredictos"]["candidato"]
    m = c["medidas"]
    print(
        f"{Path(receta).stem} shift{shift} T+{h} eval {out['evaluacion'][h]['start']}..{out['evaluacion'][h]['end']}: "  # noqa: E501
        f"I={m['candidato']['inicios']} canal {m['canal_condicionado']['detectados']} vs {m['candidato']['detectados']} "  # noqa: E501
        f"dS {v.get('delta_sensibilidad_pp', float('nan')):.1f} IC {[round(x, 1) for x in v.get('ic_delta_sensibilidad_pp', [])]} "  # noqa: E501
        f"dB {v.get('delta_carga_100mm', float('nan')):.2f} -> {c['veredicto']}",
        flush=True,
    )
