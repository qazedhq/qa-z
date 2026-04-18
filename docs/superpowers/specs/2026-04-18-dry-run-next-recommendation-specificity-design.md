# Dry-Run Next-Recommendation Specificity Design

Date: 2026-04-18

## Context

Executor dry-run summaries now carry operator summaries and recommended action
objects. Several high-value actions are already specific:

- `review_validation_conflict`
- `require_no_op_explanation`
- `inspect_no_op_pattern`

The top-level `next_recommendation` is still generic for some of those attention
signals. For validation conflicts, missing no-op explanations, and repeated
no-op history, the summary can currently say `inspect executor attempt history
before another retry` even while the recommended action list gives a sharper
instruction.

That is a small operator-diagnostics gap. The machine-readable actions are
correct, but the most visible one-line next step should match the same priority
model.

## Goal

Make dry-run `next_recommendation` action-aligned for validation conflicts,
missing no-op explanations, and repeated no-op attempts, then pin the behavior
with unit tests and benchmark fixtures.

## Non-Goals

- Do not add live executor behavior.
- Do not add new dry-run rules, verdicts, or action ids.
- Do not change rule-status counts.
- Do not change blocked verdict priority for scope validation or incomplete
  verification.
- Do not introduce hidden network dependencies or agent-specific logic.

## Design

Extend `next_recommendation()` in `src/qa_z/executor_dry_run_logic.py` so it
uses the same signal priority as `operator_summary()` and
`recommended_actions()` after blocked conditions:

1. `scope_validation_failed` keeps `inspect executor scope drift before another attempt`
2. `completed_verify_blocked` keeps `resolve verification blocking evidence before another completed attempt`
3. `validation_conflict` becomes `review executor validation conflict before another retry`
4. `missing_no_op_explanation` becomes `require no-op explanation before accepting executor result`
5. `repeated_partial_attempts` keeps `inspect repeated partial attempts before another retry`
6. `repeated_rejected_attempts` keeps `inspect repeated rejected executor results before another retry`
7. `repeated_no_op_attempts` becomes `inspect repeated no-op outcomes before another retry`
8. `no_recorded_attempts` keeps `ingest executor result before relying on dry-run safety evidence`

Existing mixed blocked histories remain blocked by verification before secondary
attention signals, so this change does not reorder blocked safety decisions.

## Benchmark Coverage

Update the existing fixtures whose current top-level recommendation is too
generic:

- `executor_dry_run_validation_noop_operator_actions`
- `executor_dry_run_repeated_noop_operator_actions`

Add one missing focused fixture:

- `executor_dry_run_missing_noop_explanation_operator_actions`

The new fixture seeds one accepted no-op attempt with
`no_op_without_explanation`. Expected output:

- `verdict`: `attention_required`
- `verdict_reason`: `no_op_explanation_missing`
- `history_signals`: `["missing_no_op_explanation"]`
- `expected_recommendation`: `require no-op explanation before accepting executor result`
- `operator_summary`: `A no-op style executor result needs an explanation before acceptance.`
- `recommended_action_ids`: `["require_no_op_explanation"]`
- rule counts: clear `5`, attention `1`, blocked `0`

## Documentation

Update current-truth surfaces to say that dry-run operator diagnostics now pin
action-aligned next recommendations, including validation-conflict,
missing-no-op, and repeated-no-op paths:

- `README.md`
- `docs/benchmarking.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

## Test Strategy

1. Add failing pure-logic tests for the new recommendation strings.
2. Add failing benchmark corpus/current-truth assertions for the new missing
   no-op fixture.
3. Update `next_recommendation()` minimally.
4. Add the new fixture and update existing expected recommendations.
5. Update docs.
6. Run focused tests, the new fixture benchmark, full pytest, and full benchmark.
