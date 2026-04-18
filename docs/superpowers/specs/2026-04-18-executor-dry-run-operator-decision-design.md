# Executor Dry-Run Operator Decision Design

## Goal

Add a stable top-level `operator_decision` field to executor-result dry-run diagnostics so operators can see the primary action id without parsing `recommended_actions`.

## Current Evidence

Executor-result dry-run summaries already expose:

- `verdict`
- `verdict_reason`
- `history_signals`
- `operator_summary`
- `recommended_actions`
- `next_recommendation`
- rule status counts and rule evaluations

That is enough for detailed diagnostics, but the primary operator decision is only implicit as the first recommended action. This makes downstream surfaces repeat action summaries without a compact machine-readable decision id.

## Design

Add `operator_decision` as an additive field on dry-run summaries.

The value will be the primary recommended action id for the dominant signal:

- `inspect_scope_drift` for scope validation failures
- `resolve_verification_blockers` for completed attempts that are not verification-clean
- `review_validation_conflict` for validation or classification conflicts
- `require_no_op_explanation` for missing no-op or not-applicable explanations
- `inspect_partial_attempts` for repeated partial attempts
- `inspect_rejected_results` for repeated rejected attempts
- `inspect_no_op_pattern` for repeated no-op attempts
- `ingest_executor_result` for empty recorded history
- `continue_standard_verification` for clear history
- `inspect_executor_history` for unknown attention states

Carry the field through:

- materialized `dry_run_summary.json`
- human `dry_run_report.md`
- `qa-z executor-result dry-run` stdout
- repair-session status JSON/stdout
- repair-session completed summary/outcome Markdown
- publish/GitHub summary surfaces through `SessionPublishSummary`
- benchmark dry-run actual summaries and committed dry-run fixture expectations

## Non-Goals

- Do not change verdict semantics.
- Do not add live executor retries, scheduling, or orchestration.
- Do not remove or rename `recommended_actions`.
- Do not change the dry-run rule catalog.

## Acceptance

Focused tests should fail before implementation because `operator_decision` is missing, then pass after the additive field and docs are synced. Full `python -m pytest` and `python -m qa_z benchmark --json` must remain green.
