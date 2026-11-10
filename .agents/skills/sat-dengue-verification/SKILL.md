---
name: sat-dengue-verification
description: Select and run the SAT DENGUE validation gates before completion, experiment closure, commit preparation, or a proposed push, without publishing changes.
---

# SAT DENGUE Verification

Verify the changed surface and report evidence before work is declared complete or ready for commit/push. Read [AGENTS.md](../../../AGENTS.md), the [operations guide](../../../docs/operations/pipeline-operations.md), and [plan.md](../../../plan.md). Verification never authorizes a push or merge.

## Inputs

Require the target claim (for example experiment closure or changes ready for push), the diff/base revision, changed files, and any task-specific protected baseline. Inspect current Git status before selecting gates. Do not assume that a previous HEAD's CI validates the current one.

## Gate selection

Run focused checks while iterating, then the accumulated gate when preparing delivery across components:

```sh
uv lock --check --project pipeline
uv sync --locked --project pipeline
uv run --directory pipeline ruff check .
uv run --directory pipeline pytest
(cd app/api && python -m pytest)
(cd app/dashboard && bun install --frozen-lockfile)
(cd app/dashboard && bun run lint)
(cd app/dashboard && bun run test)
(cd app/dashboard && NITRO_PRESET=node_server bun run build)
uv run --directory pipeline python -m sat_dengue_pipeline.experiment_management validate
uv run --directory pipeline python tools/check_experiment_preservation.py
git diff --check origin/main...HEAD
git status --short
```

Add checks when their surface is relevant: Pydantic/Zod consumers, Markdown links, new file sizes, secret-pattern candidates without printing values, notebooks, protected SHA-256 files, append-only evidence, N=3 identity, all 22 published JSON, import/write boundaries, Windows checkout behavior, and PR/check status.

Documentation-only work may use proportional structural/link tests before the accumulated gate. Code, configuration, evidence, operational documentation, experiment closure, or delivery claims require the repository gates specified by the current task. A partial run never substitutes for an explicitly required accumulated gate.

## Rules

- Report every required command, outcome, warning, and justified omission.
- Distinguish new failures from pre-existing warnings; never hide either.
- Do not declare success while a required gate fails or remains unknown.
- Do not fix a failure outside the authorized scope. Report it and stop.
- Do not print candidate secret values, read private raw data for hygiene checks, or mutate protected evidence.
- Do not push, merge, force push, publish, approve science, or select a champion.

## Stop conditions and output

Return `FAIL` for a failed required gate, `BLOCKED` when a required environment/approval/evidence source is unavailable, or `PASS` only when all selected required gates succeed. Include the inspected revision/diff, commands and results, warnings, omissions with reasons, preservation checks, external checks distinguished from local checks, and the next safe action.
