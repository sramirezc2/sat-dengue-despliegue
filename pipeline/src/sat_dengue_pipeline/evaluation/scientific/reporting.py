"""Proyección agregada de los modelos de la corrida; no es un ejecutor de experimentos."""

from collections import defaultdict
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd

from sat_dengue_pipeline.evaluation.metrics import metric_records
from sat_dengue_pipeline.experiments.roles import support_passes
from sat_dengue_pipeline.experiments.rolling import LINK, stable_digest
from sat_dengue_pipeline.raw.serialization import verify_artifact

from .policy import cap_alerts, channel_decision, channel_score
from .statistics import (
    historical_abc,
    method_counts,
    paired_intervals,
    probability_metrics,
    utility_verdict,
)

PROPOSED = "VEREDICTO_BAJO_CONTRATO_PROPUESTO"


def read_outcomes(run: Any) -> None:
    """Liberar y una vez después de ambas predicciones, conservando etiquetas ausentes."""
    if not all(run.prediction_complete.get(h, False) for h in run.config["horizons"]):
        raise ValueError("Etiquetas científicas antes de congelar todas las predicciones")
    for h in run.config["horizons"]:
        batch = run.batches[h]["evaluation"]
        y = batch.read_y()
        run.support[str(h)]["evaluation"].update(
            rows=len(y),
            n0=int(y.eq(0).sum()),
            n1=int(y.eq(1).sum()),
            missing_labels=int(y.isna().sum()),
            label_stage="after_freeze_and_predictions",
        )
        counts = run.support[str(h)]["evaluation"]
        counts["passed"] = support_passes(counts, run.plans[h], "evaluation")
    run.temporal["evaluation_reads_after_both_predictions"] = True


def emission_frame(run: Any, h: int) -> tuple[pd.DataFrame, dict[str, np.ndarray], bool]:
    """Enlazar salida del modelo ajustado y compromiso previo sin reajustar políticas."""
    output = run.predictions[h]
    policy = run.scientific_policies[h]
    if stable_digest({k: v for k, v in policy.items() if k != "sha256"}) != policy["sha256"]:
        raise ValueError("Compromiso de alertas alterado después del freeze")
    if (
        output.artifact_digest != policy["model_frozen_digest"]
        or run.fitted[h].model.adapter.model_sha256() != run.identities[str(h)]["model_json"]
    ):
        raise ValueError("La evaluación debe usar el modelo entrenado en esta corrida")
    frame = run.scientific_contexts[(h, "evaluation")].copy()
    if not frame[LINK].equals(output.keys[LINK]):
        raise ValueError("Contexto y predicciones de distintas observaciones")
    frame["candidate_probability"] = output.probability.to_numpy(dtype=float)
    outcome = run.scientific_outcomes[(h, "evaluation")]
    origins = frame[["municipality_code", "origin_period"]].rename(
        columns={"origin_period": "year_month"}
    )
    if not origins.equals(outcome[["municipality_code", "year_month"]]):
        raise ValueError("Desenlaces desalineados de las predicciones")
    # Se adjuntan solo aquí; las funciones de emisión reciben el contexto de T.
    frame["onset"] = outcome[f"y_t{h}"].to_numpy()
    frame["excess_target"] = outcome.excess_target.to_numpy()
    raw = output.decision.to_numpy(dtype=bool)
    c0 = channel_decision(frame, 1.0)
    persistence = frame.excess_at_origin.to_numpy(dtype=bool)
    rate = policy["budget_rate"]
    defined = policy["status"] == "FROZEN"
    decisions = {"candidate": raw, "channel_C0": c0, "persistence": persistence}
    if defined:
        decisions["candidate"] = cap_alerts(
            frame, frame.candidate_probability.to_numpy(), raw, rate
        )
        decisions["channel_conditioned"] = cap_alerts(
            frame, channel_score(frame), channel_decision(frame, policy["channel_fraction"]), rate
        )
        random_score = np.array(
            [
                int(stable_digest({"seed": 42, "key": list(key)})[:13], 16) / 16**13
                for key in frame[LINK].itertuples(index=False, name=None)
            ]
        )
        decisions["random_ranking"] = cap_alerts(
            frame, random_score, np.ones(len(frame), dtype=bool), rate
        )
        decisions["alert_everything"] = np.ones(len(frame), dtype=bool)
        decisions["inflated_channel"] = (
            decisions["channel_conditioned"] | decisions["random_ranking"]
        )
    return frame, decisions, defined


def budget_ok(frame: pd.DataFrame, decision: np.ndarray, rate: float) -> bool:
    """Comprobar el cupo original; no recalcularlo según etiquetas conocidas."""
    for _, positions in frame.groupby(["target_period", "department_code"]).indices.items():
        if int(decision[positions].sum()) > int(np.floor(rate * len(positions))):
            return False
    return True


def cells(frame: pd.DataFrame) -> list[tuple[str, str, np.ndarray]]:
    """Desglosar años y territorios como vistas no sumables entre sí."""
    territories = [
        ("national", np.ones(len(frame), dtype=bool)),
        ("primary_meta_tolima", frame.department_code.isin(["50", "73"]).to_numpy()),
    ]
    territories += [
        (f"department:{d}", frame.department_code.eq(d).to_numpy())
        for d in sorted(frame.department_code.unique())
    ]
    years = [("all", np.ones(len(frame), dtype=bool))]
    years += [
        (year, frame.target_period.str[:4].eq(year).to_numpy())
        for year in sorted(frame.target_period.str[:4].unique())
    ]
    return [
        (territory, year, mask & year_mask)
        for territory, mask in territories
        for year, year_mask in years
        if (mask & year_mask).any()
    ]


def evaluate_cell(
    frame: pd.DataFrame, decisions: dict[str, np.ndarray], policy: dict
) -> dict[str, Any]:
    """Calcular las dos reglas en soporte común y mantener las limitaciones visibles."""
    known = frame.onset.notna().to_numpy() & frame.excess_target.notna().to_numpy()
    support = frame.loc[known].reset_index(drop=True)
    masked = {name: value[known] for name, value in decisions.items()}
    methods = {name: method_counts(support, value) for name, value in masked.items()}
    score_metrics = {"candidate": probability_metrics(support)}
    for name, decision in masked.items():
        if name == "candidate":
            continue
        score = (
            channel_score(support)
            if name in {"channel_C0", "channel_conditioned"}
            else decision.astype(float)
        )
        score_metrics[name] = metric_records(
            support.onset.reset_index(drop=True).astype("Int64"),
            pd.Series(score, dtype=float),
            None,
            probabilistic=False,
        )[:3]
    abc = historical_abc(methods)
    missing_predictions = int(
        (~np.isfinite(frame.candidate_probability.to_numpy(dtype=float))).sum()
    )
    intervals, controls = {}, {}
    defined = policy["status"] == "FROZEN"
    verdict = "NO_EVALUABLE"
    if defined:
        for reference in ("channel_conditioned", "channel_C0", "persistence"):
            intervals[reference] = paired_intervals(support, masked, reference=reference)
        for name in ("random_ranking", "alert_everything", "inflated_channel", "persistence"):
            ci = paired_intervals(support, masked, candidate=name)
            controls[name] = utility_verdict(
                methods,
                ci,
                candidate=name,
                budget_respected=budget_ok(frame, decisions[name], policy["budget_rate"]),
            )
        verdict = utility_verdict(
            methods,
            intervals["channel_conditioned"],
            budget_respected=budget_ok(frame, decisions["candidate"], policy["budget_rate"]),
            missing_predictions=missing_predictions,
        )
        if "CUMPLE" in controls.values():
            verdict = "INVALIDO"
    if missing_predictions:
        abc["status"] = "INVALIDO"
        verdict = "INVALIDO"
    return {
        "kind": "cell",
        "label": PROPOSED,
        "contract_status": "PROPUESTA_PARA_APROBACION",
        "prediction_rows": len(frame),
        "missing_labels": int((~known).sum()),
        "missing_predictions": missing_predictions,
        "paired_keys_digest": stable_digest(support[LINK].to_dict("records")),
        "emission_keys_digest": stable_digest(frame[LINK].to_dict("records")),
        "months": int(support.target_period.nunique()),
        "municipalities": int(support.municipality_code.nunique()),
        "methods": methods,
        "ABC_HISTORICA": abc,
        "intervals": intervals,
        "UTILIDAD_PROPUESTA": verdict,
        "negative_controls": controls,
        "score_metrics": score_metrics,
        "support_status": "SUFFICIENT"
        if methods["candidate"]["I"] >= 30
        else "INSUFFICIENT_30_ONSETS",
        "policy_status": policy["status"],
        "budget_rate": policy["budget_rate"],
        "budget_respected": budget_ok(frame, decisions["candidate"], policy["budget_rate"])
        if defined
        else None,
        "scientific_conclusion": "NOT_APPROVED",
        "operational_authorization": False,
    }


def summaries(records: list[dict], policy: dict) -> list[dict]:
    """Informar consistencia por semilla y distribución sin inventar su agregación científica."""
    by_seed: dict[tuple, list] = defaultdict(list)
    for record in records:
        if record["kind"] == "cell" and record["year"] == "all":
            key = tuple(
                record[name]
                for name in ("arm", "population", "reading", "horizon", "territory", "seed")
            )
            by_seed[key].append(record)
    result = []
    by_seeds: dict[tuple, list] = defaultdict(list)
    for key, group in sorted(by_seed.items()):
        usable = [r for r in group if r["support_status"] == "SUFFICIENT"]
        invalid = any(r["UTILIDAD_PROPUESTA"] == "INVALIDO" for r in group)
        votes = sum(
            r["UTILIDAD_PROPUESTA"] == "CUMPLE"
            and r["ABC_HISTORICA"]["status"] == "ABC_HISTORICA_CUMPLE"
            for r in usable
        )
        k = len(usable)
        required = k // 2 + 1
        status = (
            "INVALIDO"
            if invalid
            else "PENDING_CONSISTENCY_RULE"
            if policy["consistency_rule"] is None or policy["consistency_vote"] is None
            else "PENDING_RECIPE_POLICY"
            if any(r.get("policy_status", "FROZEN") != "FROZEN" for r in group)
            else "INSUFFICIENT_CUTS"
            if k < 3
            else "CUMPLE"
            if votes >= required
            else "NO_CUMPLE"
        )
        dims = dict(
            zip(("arm", "population", "reading", "horizon", "territory", "seed"), key, strict=True)
        )
        result.append(
            {
                "kind": "consistency",
                **dims,
                "label": PROPOSED,
                "planned_cuts": len(policy["cuts"]),
                "usable_cuts": k,
                "excluded_insufficient_support": len(group) - k,
                "votes": votes,
                "required_votes": required,
                "status": status,
            }
        )
        by_seeds[key[:-1]].append(
            {
                "seed": key[-1],
                "consistency": status,
                "cuts": [
                    {
                        "cut": r["cut"],
                        "TP": r["methods"]["candidate"]["TP"],
                        "delta_TP_C0": r["methods"]["candidate"]["TP"]
                        - r["methods"]["channel_C0"]["TP"],
                        "delta_TP_conditioned": (
                            r["methods"]["candidate"]["TP"]
                            - r["methods"]["channel_conditioned"]["TP"]
                        )
                        if "channel_conditioned" in r["methods"]
                        else None,
                        "paired_keys_digest": r["paired_keys_digest"],
                    }
                    for r in group
                ],
            }
        )
    for key, seed_rows in sorted(by_seeds.items()):
        distributions = []
        cuts = sorted({row["cut"] for seed in seed_rows for row in seed["cuts"]})
        for cut in cuts:
            samples = [
                {"seed": seed["seed"], **row}
                for seed in seed_rows
                for row in seed["cuts"]
                if row["cut"] == cut
            ]
            comparable = len({row["paired_keys_digest"] for row in samples}) == 1
            for metric in ("delta_TP_C0", "delta_TP_conditioned"):
                values = [row[metric] for row in samples if row[metric] is not None]
                distributions.append(
                    {
                        "cut": cut,
                        "metric": metric,
                        "values_by_seed": [
                            {"seed": row["seed"], "value": row[metric]} for row in samples
                        ],
                        "mean": float(np.mean(values)) if values and comparable else None,
                        "std": float(np.std(values, ddof=1))
                        if len(values) > 1 and comparable
                        else None,
                        "positive": sum(v > 0 for v in values),
                        "negative": sum(v < 0 for v in values),
                        "ties": sum(v == 0 for v in values),
                        "one_or_two_onset_check": "REPORTED_FIVE_SEEDS"
                        if len(values) >= 5 and comparable
                        else "NOT_VERIFIED",
                        "support_comparable": comparable,
                    }
                )
        # El contrato exige distribución de cinco semillas, pero no fija un operador
        # para convertirla en un único CUMPLE; ese tramo se detiene explícitamente.
        result.append(
            {
                "kind": "seed_stability",
                **dict(
                    zip(("arm", "population", "reading", "horizon", "territory"), key, strict=True)
                ),
                "label": PROPOSED,
                "seeds": seed_rows,
                "distributions": distributions,
                "five_seeds_check": "REPORTED" if len(seed_rows) >= 5 else "NOT_VERIFIED",
                "status": "PENDING_SEED_AGGREGATION_RULE",
                "scientific_conclusion": "NOT_APPROVED",
            }
        )
    return result


def evaluate_runs(runs: dict[str, Any], configuration: dict) -> tuple[list[dict], dict[str, Any]]:
    """Evaluar exclusivamente instancias entrenadas del lifecycle y agregar procedencia.

    Args:
        runs: Brazos/cortes/semillas producidos por el mismo flujo registrado.
        configuration: Receta y contrato fijados por hash antes de la adquisición.

    Returns:
        Registros agregados para el inventario habitual y métricas compactas de tracking.
    """
    records, retained = [], {}
    tracking = {str(h): {"metrics": {}, "label": PROPOSED} for h in configuration["horizons"]}
    verified_artifacts = set()
    for name, run in runs.items():
        artifact_key = (run.artifact.serialized_sha256, run.artifact.semantic_digest)
        if artifact_key not in verified_artifacts:
            verify_artifact(run.artifact)
            verified_artifacts.add(artifact_key)
        dimensions = run.config["scientific_dimensions"]
        records.append(
            {
                "kind": "variant",
                "id": name,
                **dimensions,
                "effective_configuration": {
                    k: v for k, v in run.config.items() if k != "scientific_evaluation"
                },
                "canonical": run.lineage["canonical"],
                "model_artifacts": run.identities,
                "support": run.support,
                "temporal": run.temporal,
                "label_reads": run.label_reads,
                "frozen_policies": {str(k): v for k, v in run.scientific_policies.items()},
            }
        )
        for h in run.config["horizons"]:
            frame, decisions, _ = emission_frame(run, h)
            policy = run.scientific_policies[h]
            retained[
                (
                    dimensions["cut"],
                    dimensions["seed"],
                    dimensions["reading"],
                    h,
                    dimensions["population"],
                    dimensions["arm"],
                )
            ] = (frame, decisions)
            for territory, year, mask in cells(frame):
                subframe = frame.loc[mask].reset_index(drop=True)
                subdecisions = {method: value[mask] for method, value in decisions.items()}
                record = evaluate_cell(subframe, subdecisions, policy)
                record["producer_support_passed"] = run.support[str(h)]["evaluation"]["passed"]
                if not record["producer_support_passed"]:
                    record["UTILIDAD_PROPUESTA"] = "NO_EVALUABLE"
                    record["support_status"] = "INSUFFICIENT_DECLARED_ROLE_SUPPORT"
                record.update(
                    **dimensions,
                    horizon=h,
                    territory=territory,
                    year=year,
                    model_sha256=run.identities[str(h)]["model_json"],
                    canonical_serialized_sha256=run.artifact.serialized_sha256,
                    policy_sha256=policy["sha256"],
                )
                records.append(record)
                if territory == "primary_meta_tolima" and year == "all":
                    for method, values in record["methods"].items():
                        tracking[str(h)]["metrics"][name + "." + method] = [
                            {"metric": metric, "value": values[metric]}
                            for metric in (
                                "onset_sensitivity",
                                "FAR_exceso",
                                "carga_FA_inicio_100mm",
                            )
                        ]
    common: dict[tuple, dict] = defaultdict(dict)
    for (cut, seed, reading, h, population, arm), pair in retained.items():
        if population == "common":
            common[(cut, seed, reading, h)][arm] = pair
    for dims, arms in common.items():
        for left, right in combinations(sorted(arms), 2):
            lf, ld = arms[left]
            rf, rd = arms[right]
            if not lf[LINK].equals(rf[LINK]) or not lf.onset.equals(rf.onset):
                raise ValueError("El aporte climático exige soporte común exacto en ambos brazos")
            for territory, year, mask in cells(lf):
                known = lf.onset.notna().to_numpy() & mask
                paired = {left: ld["candidate"][known], right: rd["candidate"][known]}
                records.append(
                    {
                        "kind": "paired_arm_difference",
                        "cut": dims[0],
                        "seed": dims[1],
                        "reading": dims[2],
                        "horizon": dims[3],
                        "left_arm": left,
                        "right_arm": right,
                        "territory": territory,
                        "year": year,
                        "population": "common",
                        "label": PROPOSED,
                        "paired_keys_digest": stable_digest(lf.loc[known, LINK].to_dict("records")),
                        "intervals": paired_intervals(
                            lf.loc[known].reset_index(drop=True),
                            paired,
                            candidate=left,
                            reference=right,
                        ),
                    }
                )
    records += summaries(records, configuration["scientific_evaluation"])
    return records, tracking
