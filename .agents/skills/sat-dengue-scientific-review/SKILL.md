---
name: sat-dengue-scientific-review
description: Review a SAT DENGUE recipe before approval or its conclusions after a run for temporal leakage, comparability, metric validity, and scientific support.
---

# SAT DENGUE Scientific Review

Audit whether a predeclared design or completed run can validly answer its hypothesis. This skill reviews; it does not operate training or replace `$sat-dengue-experiment`.

Read the [scientific contract](../../../docs/experiments/contrato.md), [factory manual](../../../docs/experiments/manual_pipeline.md), [temporal contracts](../../../docs/decisions/temporal-experiments.md), [paired evaluation rules](../../../docs/decisions/paired-evaluation.md), and the prior [independent review](../../../docs/reviews/scientific-review.md). Check [plan.md](../../../plan.md) for task authority without changing it during an ordinary review. A proposed contract or unresolved threshold is not an approval.

## Modes and inputs

- `pre-approval`: require the hypothesis, reference experiment, specification, configuration, manifest identity, declared hashes, comparison plan, and approval criteria.
- `post-run`: additionally require the immutable registry entry, complete execution inventory, aggregate metrics/supports, conclusions, code/data identities, and declared limitations.

If the requested mode or required evidence is missing, return `NOT_VERIFIED` findings and stop before an approval recommendation.

## Review method

1. Identify the exact hypothesis and the single predeclared change from the reference.
2. Check population, geography, periods, horizons, reference experiment, and whether data/code/cohorts support the proposed comparison.
3. Verify the five temporal roles, label availability, reporting delay, embargo, and the complete exclusion of 2025 from learning, calibration, threshold selection, and presented independent evaluation.
4. Review predictors, preparation, seeds, hyperparameters, calibration, threshold policy, FAR constraint, metrics, baselines, supports, and denominators.
5. Check the recipe against every applicable validity and decision rule in the
   scientific contract. Distinguish a technical factory result from exploratory
   or confirmatory evidence and identify any contract capability not yet
   implemented.
6. For `pre-approval`, flag any choice that remains data-dependent or was selected after observing evaluation.
7. For `post-run`, match conclusions to the registry, frozen recipe, inventory, aggregate evidence, support, limitations and contract verdict. Separate demonstrated, adapted, partial, and unverified claims.
8. Classify each finding by severity and cite a concrete file, field, receipt, test, or aggregate result.

Do not treat synthetic fixtures as scientific evidence. Do not silently repair the design, retrain, tune after evaluation, change a recipe to improve results, approve for the team, or infer a champion. `PARTIAL` and `NOT_VERIFIED` remain explicit limitations.

For independence, recommend a different chat or reviewer from the one that prepared or ran the experiment when the decision requires independent scientific review.

## Stop conditions

Return `BLOCKED` for temporal leakage, changed post-evaluation recipes, corrupt or mismatched evidence, incomparable claims presented as causal/equivalent, unsupported scientific conclusions, or a missing decision that only a human reviewer can make. Do not operate the experiment while blocked.

## Output

Return `APPROVED`, `APPROVED_WITH_LIMITATIONS`, or `BLOCKED`. Include scope and mode, evidence reviewed, findings with severity/evidence/action, limitations, claims that remain unverified, required human decisions, and the next safe action. The status is a review recommendation; it is not a registry approval or permission to run, publish, push, or merge.
