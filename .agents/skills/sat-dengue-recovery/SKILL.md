---
name: sat-dengue-recovery
description: Diagnose a failed, blocked, killed, interrupted, or incomplete SAT DENGUE execution and propose the smallest evidence-preserving recovery.
---

# SAT DENGUE Recovery

Diagnose before changing state. Preserve failed history and determine whether recovery is safe or a new experiment identity is required. Read the [operations recovery guide](../../../docs/operations/pipeline-operations.md), [factory manual](../../../docs/experiments/manual_pipeline.md), [experiment evidence design](../../../docs/decisions/experiment-management.md), and [security review](../../../docs/security/security-review.md).

## Triggers and inputs

Use for interrupted downloads, incorrect hashes, failed private access, altered recipes, missing approval, abandoned-looking locks, partial evidence, MLflow failures, memory exhaustion, Colab disconnects, encoding/path/platform differences, or `BLOCKED`, `FAILED`, and `KILLED` executions.

Require the experiment and execution IDs when available, observed terminal/state, failing stage, aggregate receipt/inventory, relevant logs with secrets removed, current process/lock facts, and platform/resource context. Do not request secret values or private paths in the response.

## Process

1. Inspect state, receipts, inventories, locks, processes, filesystem metadata, and aggregate logs without modifying them.
2. Locate the failed stage and separate a confirmed cause from hypotheses and missing evidence.
3. Preserve existing receipts, aggregate logs, incomplete packages, inventories, caches, and MLflow store. A failure remains visible.
4. Decide whether the issue is transport/environmental and recoverable before training, or whether any retry would be another scientific execution requiring a new identity.
5. Propose the smallest bounded action and its rollback/check. Do not apply deletion, unlock, state transition, retry, or evidence repair without explicit authorization for that concrete action.
6. If training must repeat, hand off to `$sat-dengue-experiment` in `repeat` mode with a new ID, frozen recipe as appropriate, fresh review, and approval.
7. Use `$sat-dengue-verification` to define the checks that demonstrate recovery.

An apparent stale lock is not proof that no writer exists. An incomplete inventory is not a successful execution. Re-running with the same ID is not a continuation.

## Prohibitions and stop conditions

Never automatically delete locks, evidence, caches, stores, or directories; reset registry state; reuse a closed/executed ID; print secrets; download private data; hide a failed attempt; use `git reset --hard`; force push; or run destructive commands. Stop when ownership/process state is ambiguous, evidence could be overwritten, approval is missing, hashes or identity disagree, or the proposed recovery changes scientific scope.

## Output

Return a diagnostic with observed state, failed stage, confirmed cause or ranked hypotheses, evidence preserved, risk, recommended minimal action, specific approval required, whether a new experiment ID is mandatory, and the verification criterion. Do not claim recovery until those checks pass.
