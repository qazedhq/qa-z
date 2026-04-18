# QA-Z Pre-Live Executor Safety

QA-Z now freezes its pre-live executor boundary as one explicit local package before any live executor integration is considered.

This is not a live runtime. It is not a scheduler. It is not an auto-edit path.

The package exists so repair sessions, executor bridges, executor-result ingest, and public docs can point at the same rule set instead of carrying scattered policy prose.

## Package

Each `qa-z repair-session start` writes:

```text
.qa-z/sessions/<session-id>/executor_safety.json
.qa-z/sessions/<session-id>/executor_safety.md
```

Each `qa-z executor-bridge` copies those artifacts into:

```text
.qa-z/executor/<bridge-id>/inputs/executor_safety.json
.qa-z/executor/<bridge-id>/inputs/executor_safety.md
```

The JSON artifact is the machine-readable source of truth for the executor safety rule catalog. The Markdown artifact is the human-facing companion.

Bridge manifests and executor-facing guides summarize the copied package with ordered rule ids and a safety rule count so operators can confirm the package still carries the complete frozen set without recounting the JSON by hand.

## Frozen Rules

The current package id is `pre_live_executor_safety_v1`.

The executor safety rule catalog is the six-rule frozen pre-live set:

The frozen rules are:

1. `no_op_requires_explanation`
   No-op and not-applicable outcomes require an explicit explanation and cannot be treated as silent success.
2. `retry_boundary_is_manual`
   QA-Z does not auto-retry, auto-redispatch, or silently replay an external executor after rejected, partial, or failed outcomes.
3. `mutation_scope_limited`
   External edits must stay within the selected repair-session and bridge scope.
4. `unrelated_refactors_prohibited`
   External executors must not broaden scope or bundle unrelated refactors with the requested repair.
5. `verification_required_for_completed`
   A `completed` result is not merge-ready until deterministic QA-Z verification has passed or approved evidence has been attached.
6. `outcome_classification_must_be_honest`
   Executor outcomes must be classified honestly as `completed`, `partial`, `failed`, `no_op`, or `not_applicable`.

## Example Shape

```json
{
  "kind": "qa_z.executor_safety",
  "schema_version": 1,
  "package_id": "pre_live_executor_safety_v1",
  "status": "pre_live_only",
  "summary": "Freeze local executor safety policy before any live executor integration is attempted.",
  "rules": [
    {
      "id": "verification_required_for_completed",
      "category": "verification_gate",
      "requirement": "A completed result is not merge-ready until deterministic QA-Z verification has passed or attached approved evidence.",
      "enforced_by": [
        "repair-session verify flow",
        "executor-result verify-resume gating"
      ]
    }
  ],
  "non_goals": [
    "no live Codex or Claude API execution from QA-Z",
    "no remote orchestration, queues, schedulers, or daemons",
    "no automatic code editing, commit, push, or GitHub bot behavior"
  ]
}
```

## Enforcement Relationship

The package is not a second verification engine. It documents where current enforcement already lives:

- repair-session and bridge artifacts for operator guidance
- repair handoff scope and bridge inputs for mutation boundaries
- executor-result ingest for freshness, provenance, no-op, and scope checks
- executor-result dry-run for live-free history-aware safety audits
- deterministic verification for completion

## Live-Free Dry-Run

QA-Z now has an explicit local audit surface for this package:

```bash
python -m qa_z executor-result dry-run --session .qa-z/sessions/<session-id>
```

The command reads the owning session's recorded executor-result history, evaluates it against the frozen rules above, and writes `executor_results/dry_run_summary.json` plus `executor_results/dry_run_report.md` under the same session.

The dry-run rule catalog extends the frozen safety package with the dry-run-only `executor_history_recorded` rule. That extra rule checks whether a session has recorded executor-result history before operators rely on dry-run safety evidence; it does not change the frozen executor safety package itself.

It is still live-free:

- no external executor invocation
- no auto-retry or redispatch
- no code mutation
- no branch, commit, push, or GitHub action

## What This Does Not Mean

This package does not mean QA-Z now performs live execution.

It does not add:

- live Codex or Claude API calls
- automatic code editing
- remote orchestration, queues, schedulers, or daemons
- automatic retries or redispatch
- commits, pushes, branches, or GitHub bot actions

## Remaining Future Work

Future work can broaden benchmark coverage around the dry-run surface, add richer operator diagnostics on top of the current rule outputs, and refine longer multi-result policy narratives without changing the frozen safety baseline. Any live executor proposal should point back to this package instead of inventing a new safety baseline.
