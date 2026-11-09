---
name: sat-dengue-experiment
description: Operate the registered SAT DENGUE experiment lifecycle when preparing, registering, running, repeating, concluding, listing, or comparing an experiment.
---

# SAT DENGUE Experiment

Operate one registered experiment without rewriting its recipe, identity, or history. Read the [factory manual](../../../docs/experiments/manual_pipeline.md) and the [scientific contract](../../../docs/experiments/contrato.md) before acting, then use the real `experiment_management` and Kedro `experiment_run` interfaces documented there. If the contract remains a proposal, do not treat its unresolved decisions as approved.

## Modes

Choose the mode from the request:

- `prepare`: draft a new hypothesis, specification, closed configuration, and hashes.
- `register`: validate a new identity and add its proposal through the registry CLI.
- `run`: execute an already `APPROVED` identity once.
- `conclude`: prepare conclusions from complete aggregate evidence and request the human scientific decision needed for closure.
- `compare`: list or compare registered aggregate results without ranking or selecting a champion.
- `repeat`: prepare a new identity with an equivalent predeclared recipe; never reuse the prior ID.

## Inputs

Require the requested mode and experiment ID. Depending on the mode, also require the hypothesis and reference experiment, approved raw manifest, protocol, configuration, declared hashes, registry state, execution inventory, and proposed scientific result. Treat missing identity, approval, evidence, or decision context as a stop condition rather than filling it in.

Check [plan.md](../../../plan.md) for the current task authority, but do not update task state during ordinary experiment operation. Use [experiment management](../../../docs/decisions/experiment-management.md) for state, evidence, and identity invariants.

## Process

1. Inspect the registry and relevant files without changing closed entries or evidence.
2. Confirm the ID is new for `prepare`, `register`, and `repeat`; an executed ID is never reusable.
3. Keep hypothesis, protocol, executable configuration, and generated evidence distinct. Verify SHA-256 identities before registration or execution.
4. Confirm all learning ends before 2025 and the approved manifest and five temporal roles remain valid.
5. For a scientific claim, verify that the specification declares how it will
   satisfy the contract's common cohort, primary comparator, operating point,
   metrics, uncertainty and verdict. Stop if a required contract decision is
   still unapproved.
6. In `prepare`, create only a proposal and run structural validation. Stop before approval or execution.
7. In `register`, use the documented registry command; never edit registry state to bypass validation.
8. In `run`, require exact hashes and `APPROVED`; use only implemented model, preparation, and pipeline options. A successful computation remains pending human conclusions.
9. In `conclude`, verify the inventory and correspondence among registry, recipe, evidence, conclusions and the applicable scientific contract. A human assigns `POSITIVE`, `NEGATIVE` or `INCONCLUSIVE` and authorizes the transition.
10. In `compare`, report comparability limits and aggregate provenance. Do not infer superiority from unlike cohorts or recipes.
11. In `repeat`, create a new ID, approval, execution, and evidence package even when the recipe is byte-equivalent.

Preserve append-only evidence and prior failed terminals. Fixtures such as EXP001 and EXP002 demonstrate infrastructure only and are not scientific evidence.

## Human decisions and permissions

Never approve a recipe, decide scientific meaning, select a champion, publish results, access a secret, push, merge, delete, or overwrite on behalf of a person. Ask for the specific missing approval immediately before the action that needs it. `plan.md` remains the task-state authority.

## Stop conditions

Stop closed if the ID exists, approval is absent, a hash differs, 2025 enters learning, the approved manifest is absent, an option is not implemented, evidence is incomplete, a human scientific judgment is required, or an execution would be overwritten. For a failed or interrupted attempt, hand off to `$sat-dengue-recovery` before proposing another identity.

## Validation and output

Run the proportional registry/configuration checks from the manual and use `$sat-dengue-verification` before declaring changes ready. Return a structured summary with:

- mode and action performed;
- experiment ID and prior/new state;
- files created or modified;
- validations and aggregate evidence;
- pending human decisions;
- next safe action.
