# Executor Operator Diagnostics Design

Date: 2026-04-17

## Goal

Make `executor-result dry-run` more useful to a human operator without adding
live execution, retries, scheduling, or model calls.

The dry-run already records verdicts, reasons, history signals, rule counts, and
rule evaluations. The missing layer is an explicit operator translation:

- what the dry-run means in one readable sentence
- which deterministic next actions should be inspected first
- whether the diagnostic came from a materialized dry-run summary or synthesized
  session history

## Non-Goals

- no automatic executor retry
- no remote orchestration
- no code mutation
- no LLM-only judgment
- no replacement of existing `verdict`, `verdict_reason`, `history_signals`, or
  `next_recommendation`

## Additive Summary Fields

`executor_results/dry_run_summary.json` gains two additive fields:

- `operator_summary`: stable one-sentence human diagnostic
- `recommended_actions`: ordered list of action objects

Each action object contains:

- `id`: stable machine-readable action id
- `summary`: human-readable operator action

The fields are generated from the same deterministic `history_signals` already
used for verdict and rule evaluation.

## Mapping

Signals map to actions in priority order:

- `scope_validation_failed` -> `inspect_scope_drift`
- `completed_verify_blocked` -> `resolve_verification_blockers`
- `validation_conflict` -> `review_validation_conflict`
- `missing_no_op_explanation` -> `require_no_op_explanation`
- `repeated_partial_attempts` -> `inspect_partial_attempts`
- `repeated_rejected_attempts` -> `inspect_rejected_results`
- `repeated_no_op_attempts` -> `inspect_no_op_pattern`
- `no_recorded_attempts` -> `ingest_executor_result`

When no signal is present, the dry-run records:

- `continue_standard_verification`

## Surfaces

The diagnostic fields should be visible in:

- JSON dry-run summaries
- Markdown dry-run reports
- human `executor-result dry-run` stdout
- `repair-session status` human and JSON output
- completed repair-session `summary.json`
- completed repair-session `outcome.md`
- verification publish summaries used by `github-summary`

## Acceptance Criteria

- existing dry-run verdict behavior remains unchanged
- new fields are present on materialized and history-fallback dry-run summaries
- materialized summaries missing the new fields remain loadable
- publish/session surfaces preserve the operator summary and recommended actions
- docs explain that the diagnostics are local, deterministic, and live-free
- targeted tests, full pytest, and benchmark corpus pass
