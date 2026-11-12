"""Agregación propuesta con resultados artificiales; sin modelos ni datos científicos."""

import copy
from itertools import product

import pytest

from sat_dengue_pipeline.evaluation.scientific.reporting import summaries

SEEDS = [7, 13, 31, 53, 101]
POLICY = {
    "seeds": SEEDS,
    "cuts": [{"id": str(cut)} for cut in range(4)],
    "consistency_rule": "strict_majority_min_three",
    "consistency_vote": "both_rules_cumple",
}


def artificial_results() -> list[dict]:
    """Construir 3/4 votos por semilla: veinte cortes no equivalen a veinte cohortes."""
    return [
        {
            "kind": "cell",
            "year": "all",
            "cut": str(cut),
            "arm": "epi",
            "population": "native",
            "reading": "primary",
            "horizon": 1,
            "territory": "primary_meta_tolima",
            "seed": seed,
            "support_status": "SUFFICIENT",
            "policy_status": "FROZEN",
            "UTILIDAD_PROPUESTA": "CUMPLE" if cut < 3 else "NO_CUMPLE_POR_EFECTO",
            "ABC_HISTORICA": {"status": "ABC_HISTORICA_CUMPLE"},
            "methods": {
                "candidate": {"TP": 40},
                "channel_C0": {"TP": 30},
                "channel_conditioned": {"TP": 30},
            },
            "paired_keys_digest": f"paired-cut-{cut}",
        }
        for seed, cut in product(SEEDS, range(4))
    ]


def stability(rows: list[dict], policy: dict | None = None) -> dict:
    """Leer el resumen dentro de los mismos registros de la etapa final."""
    return next(r for r in summaries(rows, policy or POLICY) if r["kind"] == "seed_stability")


@pytest.mark.parametrize(
    "case,expected",
    [
        ("five_pass", "CUMPLE_BAJO_CONTRATO_APROBADO"),
        ("four_pass", "INCONCLUSO_POR_INESTABILIDAD"),
        ("missing_seed", "NO_EVALUABLE"),
        ("insufficient_support", "NO_EVALUABLE"),
        ("invalid_run", "INVALIDO"),
    ],
)
def test_five_required_seed_cases(case: str, expected: str) -> None:
    """La unanimidad exige cinco consistencias válidas, sin escoger la mejor semilla."""
    rows = artificial_results()
    original = copy.deepcopy(rows)
    if case == "missing_seed":
        rows = [r for r in rows if r["seed"] != 101]
    for row in rows:
        if row["seed"] == 101:
            if case == "four_pass":
                row["UTILIDAD_PROPUESTA"] = "NO_CUMPLE_POR_EFECTO"
            elif case == "insufficient_support":
                row["support_status"] = "INSUFFICIENT_30_ONSETS"
            elif case == "invalid_run":
                row["UTILIDAD_PROPUESTA"] = "INVALIDO"
    before = copy.deepcopy(rows)
    result = stability(rows)
    assert rows == before  # No reescribir los veredictos individuales.
    assert result["status"] == expected
    assert len(result["seeds"]) == 5
    assert [r["seed"] for r in result["seeds"]] == SEEDS
    assert all(
        s["B"]
        == {
            "status": "NO_EVALUABLE",
            "reason": "DEGENERATE_PRIMARY_COHORT",
            "required_for_verdict": False,
        }
        for s in result["seeds"]
    )
    assert result["scientific_conclusion"] == "NOT_APPROVED"
    assert result["contract_status"] == "APPROVED"
    assert result["team_approval_required"]
    assert all(r["consistency"] == "CUMPLE" for r in result["seeds"][:4])
    assert all(r["usable_cuts"] == 4 for r in result["seeds"][:4])
    assert all(r["votes"] == 3 and r["required_votes"] == 3 for r in result["seeds"][:4])
    if case == "missing_seed":
        assert result["seeds"][-1]["missing_run"]
        assert result["five_seeds_check"] == "NOT_VERIFIED"
    else:
        assert result["five_seeds_check"] == "REPORTED"
        assert result["seeds"][0]["cuts"][0]["TP"] == original[0]["methods"]["candidate"]["TP"]


@pytest.mark.parametrize(
    "fault", ["policy", "missing_policy", "consistency_rule", "denominator", "missing_cut"]
)
def test_missing_policy_or_evidence_prevents_success(fault: str) -> None:
    """Un voto faltante no se convierte en deterioro ni desaparece detrás de una mayoría."""
    rows, policy = artificial_results(), copy.deepcopy(POLICY)
    if fault == "policy":
        rows[-1]["policy_status"] = "PENDING_RECIPE_POLICY"
    elif fault == "missing_policy":
        rows[-1].pop("policy_status")
    elif fault == "consistency_rule":
        policy["consistency_rule"] = None
    elif fault == "denominator":
        rows[-1]["ABC_HISTORICA"]["status"] = "ABC_HISTORICA_NO_EVALUABLE"
    else:
        rows.pop()
    assert stability(rows, policy)["status"] == "NO_EVALUABLE"


def test_predeclared_small_cut_exclusion_keeps_two_of_three_rule() -> None:
    """Un corte pequeño predeclarado se excluye dentro de cada semilla, sin exigir 4/4."""
    rows = artificial_results()
    for row in rows:
        if row["cut"] == "0":
            row["support_status"] = "INSUFFICIENT_30_ONSETS"
            row["UTILIDAD_PROPUESTA"] = "NO_EVALUABLE"
    result = stability(rows)
    assert result["status"] == "CUMPLE_BAJO_CONTRATO_APROBADO"
    assert all(s["usable_cuts"] == 3 and s["votes"] == 2 for s in result["seeds"])


@pytest.mark.parametrize(
    "fault", ["duplicate_cut", "extra_seed", "different_seed", "unpaired", "invalid_small_cut"]
)
def test_inconsistent_evidence_is_invalid(fault: str) -> None:
    """No aceptar repeticiones, identidades ajenas o cohortes diferentes como cinco semillas."""
    rows = artificial_results()
    if fault == "duplicate_cut":
        rows.append(copy.deepcopy(rows[0]))
    elif fault == "extra_seed":
        rows.append({**rows[0], "seed": 999})
    elif fault == "different_seed":
        for row in rows:
            if row["seed"] == 101:
                row["seed"] = 999
    elif fault == "invalid_small_cut":
        rows[-1]["support_status"] = "INSUFFICIENT_30_ONSETS"
        rows[-1]["UTILIDAD_PROPUESTA"] = "INVALIDO"
    else:
        rows[-1]["paired_keys_digest"] = "different-population"
    assert stability(rows)["status"] == "INVALIDO"


def test_all_nonpassing_seeds_do_not_infer_an_effect_verdict() -> None:
    """La agregación solo mide estabilidad afirmativa, sin crear una prueba de efecto."""
    rows = artificial_results()
    for row in rows:
        row["UTILIDAD_PROPUESTA"] = "PRECISION_INSUFICIENTE"
    assert stability(rows)["status"] == "INCONCLUSO_POR_INESTABILIDAD"


def test_horizons_readings_populations_arms_and_territories_never_mix() -> None:
    """Perturbar cada vista por separado sin transferir votos de ninguna otra dimensión."""
    dimensions = [
        (arm, population, reading, horizon, territory)
        for arm, population, (reading, horizon), territory in product(
            ["epi", "climate"],
            ["native", "common"],
            [("primary", 1), ("primary", 2), ("secondary_t2", 2)],
            ["national", "primary_meta_tolima"],
        )
    ]
    names = ("arm", "population", "reading", "horizon", "territory")
    records = [
        {**row, **dict(zip(names, dims, strict=True))}
        for dims in dimensions
        for row in artificial_results()
    ]
    # Las vistas anuales se conservan, pero no son cortes extra de la consistencia.
    records += [{**row, "year": "2023"} for row in records]
    for target in dimensions:
        changed = copy.deepcopy(records)
        for row in changed:
            if tuple(row[n] for n in names) == target and row["seed"] == 101:
                row["UTILIDAD_PROPUESTA"] = "NO_CUMPLE_POR_EFECTO"
        results = [r for r in summaries(changed, POLICY) if r["kind"] == "seed_stability"]
        assert len(results) == len(dimensions)
        for result in results:
            expected = (
                "INCONCLUSO_POR_INESTABILIDAD"
                if tuple(result[n] for n in names) == target
                else "CUMPLE_BAJO_CONTRATO_APROBADO"
            )
            assert result["status"] == expected
            assert len(result["seeds"]) == 5
            assert all(s["usable_cuts"] == 4 for s in result["seeds"])


@pytest.mark.parametrize("failed_rule", [None, "ABC_HISTORICA", "UTILIDAD_PROPUESTA"])
def test_one_failed_rule_in_one_seed_prevents_unanimity(failed_rule: str | None) -> None:
    """Dos votos de cuatro no bastan; el tercero exige A/B/C y utilidad simultáneas."""
    rows = artificial_results()
    changed = next(r for r in rows if r["seed"] == 101 and r["cut"] == "2")
    if failed_rule == "ABC_HISTORICA":
        changed[failed_rule] = {
            "status": "ABC_HISTORICA_NO_CUMPLE",
            "conditions": {"B_superar_persistencia": False},
        }
    elif failed_rule == "UTILIDAD_PROPUESTA":
        changed[failed_rule] = "NO_CUMPLE_POR_EFECTO"
    result = stability(rows)
    last_seed = result["seeds"][-1]
    assert all(s["consistency"] == "CUMPLE" for s in result["seeds"][:-1])
    assert last_seed["required_votes"] == 3 and last_seed["usable_cuts"] == 4
    assert last_seed["votes"] == (3 if failed_rule is None else 2)
    assert last_seed["consistency"] == ("CUMPLE" if failed_rule is None else "NO_CUMPLE")
    cut = next(c for c in last_seed["cuts"] if c["cut"] == "2")
    assert cut["ABC_HISTORICA"] == changed["ABC_HISTORICA"]
    assert cut["UTILIDAD_PROPUESTA"] == changed["UTILIDAD_PROPUESTA"]
    assert result["status"] == (
        "CUMPLE_BAJO_CONTRATO_APROBADO" if failed_rule is None else "INCONCLUSO_POR_INESTABILIDAD"
    )
