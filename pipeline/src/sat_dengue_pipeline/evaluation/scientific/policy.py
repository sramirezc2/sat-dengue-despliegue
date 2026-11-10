"""Canal y presupuesto congelados con desarrollo; emisión sin etiquetas futuras."""

from typing import Any

import numpy as np
import pandas as pd

from sat_dengue_pipeline.domain.canonical import KEYS
from sat_dengue_pipeline.experiments.rolling import stable_digest


def origin_context(table: pd.DataFrame, keys: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Enlazar solo valores disponibles en T con las claves previamente guardadas.

    Args:
        table: Canónico certificado, nunca una tabla de etiquetas.
        keys: Claves validadas por TemporalPolicy y preflight_roles.
        horizon: Horizonte cuyo P75 H5 ya construyó el productor canónico.

    Returns:
        Contexto de emisión sin estado de T+1 ni resultados del objetivo.
    """
    origins = keys[["municipality_code", "origin_period"]].rename(
        columns={"origin_period": "year_month"}
    )
    selected = table.set_index(KEYS).loc[pd.MultiIndex.from_frame(origins)].reset_index()
    context = keys.copy()
    context["cases_at_origin"] = selected.dengue_notifications_count.to_numpy(
        dtype=float, na_value=np.nan
    )
    context["target_p75_at_origin"] = selected[f"p75_h5_t{horizon}"].to_numpy(
        dtype=float, na_value=np.nan
    )
    context["excess_at_origin"] = selected.zona_canal_t.eq("EXCESO").to_numpy(dtype=bool)
    context["department_code"] = selected.department_code.astype(str).to_numpy()
    if context[["cases_at_origin", "target_p75_at_origin"]].isna().any().any():
        raise ValueError("Contexto del comparador ausente: no reducir soporte por método")
    return context


def cap_alerts(
    context: pd.DataFrame, score: np.ndarray, eligible: np.ndarray, rate: float
) -> np.ndarray:
    """Aplicar cupo mensual floor(rate*N), con empates por código y sin consultar y.

    Args:
        context: Población común y calendario del punto de operación.
        score: Ordenamiento congelado disponible en T.
        eligible: Decisión antes del cupo, basada exclusivamente en información en T.
        rate: Fracción comprometida en la receta antes de ver evaluación.

    Returns:
        Máscara binaria; nunca excede el cupo de cada mes objetivo.
    """
    score = np.asarray(score, dtype=float)
    eligible = np.asarray(eligible, dtype=bool)
    if (
        len(score) != len(context)
        or len(eligible) != len(context)
        or not np.isfinite(score).all()
        or not 0 <= rate <= 1
    ):
        raise ValueError("Presupuesto/score/desalineación inválidos")
    result = np.zeros(len(context), dtype=bool)
    for _, positions in context.groupby(
        ["target_period", "department_code"], sort=True
    ).indices.items():
        quota = int(np.floor(rate * len(positions)))
        allowed = [p for p in positions if eligible[p]]
        ordered = sorted(allowed, key=lambda p: (-score[p], context.iloc[p].municipality_code))
        result[ordered[:quota]] = True
    return result


def channel_score(context: pd.DataFrame, fraction: float) -> np.ndarray:
    """Priorizar el cupo por exceso absoluto sobre el umbral, incluso con P75=0.

    Args:
        context: Casos en T y P75 del objetivo disponibles al emitir.
        fraction: Fracción del canal; 1 para C0 o la congelada para el condicionado.

    Returns:
        Casos(T) menos fracción por P75; la elegibilidad se determina por separado.
    """
    return (
        context.cases_at_origin.to_numpy(dtype=float)
        - fraction * context.target_p75_at_origin.to_numpy(dtype=float)
    )


def channel_ranking_score(context: pd.DataFrame) -> np.ndarray:
    """Conservar el score de razón para AP/AUROC, separado de la prioridad del cupo."""
    cases = context.cases_at_origin.to_numpy(dtype=float)
    p75 = context.target_p75_at_origin.to_numpy(dtype=float)
    ratio = np.divide(cases, p75, out=np.zeros(len(cases)), where=p75 > 0)
    # Una transformación monótona finita permite ordenar sin cambiar la regla de alerta.
    score = ratio / (1 + ratio)
    score[(p75 == 0) & (cases > 0)] = 1.0
    return score


def channel_decision(context: pd.DataFrame, fraction: float) -> np.ndarray:
    """Regla estricta casos(T)>f*P75(T+h); la cohorte ya fijó la compuerta en T."""
    return (context.cases_at_origin > fraction * context.target_p75_at_origin).to_numpy(dtype=bool)


def freeze_policy(run: Any) -> None:
    """Elegir fracción del canal solo en threshold_selection y firmar el compromiso.

    Args:
        run: Corrida ya ajustada; no se accede a evaluation.read_y ni a su contexto.
    """
    science = run.config["scientific_evaluation"]
    for h in run.config["horizons"]:
        rate = science["budget_rate_by_horizon"][str(h)]
        grid = science["channel_fraction_grid"][str(h)]
        context = run.scientific_contexts[(h, "threshold_selection")]
        y = run.batches[h]["threshold_selection"].read_y().to_numpy(dtype=int)
        chosen = None
        diagnostics = []
        if rate is not None and grid is not None:
            for fraction in grid:
                decision = cap_alerts(
                    context,
                    channel_score(context, fraction),
                    channel_decision(context, fraction),
                    rate,
                )
                tp, alerts, positives = (
                    int((decision & (y == 1)).sum()),
                    int(decision.sum()),
                    int((y == 1).sum()),
                )
                f1 = 2 * tp / (alerts + positives) if alerts + positives else 0.0
                diagnostics.append({"fraction": fraction, "f1": f1, "alerts": alerts})
            chosen = max(diagnostics, key=lambda r: (r["f1"], -r["alerts"], r["fraction"]))[
                "fraction"
            ]
        payload = {
            "budget_rate": rate,
            "budget_rule": science["budget_rule"],
            "channel_fraction": chosen,
            "channel_selection": science["channel_selection"],
            "selection_grid": diagnostics,
            "selection_keys_digest": stable_digest(
                run.batches[h]["threshold_selection"].keys.to_dict("records")
            ),
            "model_frozen_digest": run.fitted[h].decisions.digest,
            "available_period": run.fitted[h].decisions.available_period,
            "status": "FROZEN" if chosen is not None else "PENDING_RECIPE_POLICY",
        }
        run.scientific_policies[h] = {**payload, "sha256": stable_digest(payload)}
