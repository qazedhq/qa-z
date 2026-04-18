# Dry-Run Repeated No-Op Rule Alignment Design

Date: 2026-04-18

## Context

The live-free executor dry-run already recognizes repeated no-op attempts as a
history-level attention signal:

- `history_signals`: `["repeated_no_op_attempts"]`
- `verdict`: `attention_required`
- `verdict_reason`: `manual_retry_review_required`
- `recommended_action_ids`: `["inspect_no_op_pattern"]`
- `next_recommendation`: `inspect repeated no-op outcomes before another retry`

However, the rule-level summary still reports all rules as clear for this case.
That creates an operator-diagnostics mismatch: the top-level verdict asks for
attention, but `rule_status_counts` can show `attention: 0`.

## Goal

Make repeated no-op attempts mark the existing `retry_boundary_is_manual` rule
as attention, so verdicts, actions, next recommendations, and rule counts tell
the same story.

## Non-Goals

- Do not add a new dry-run rule id.
- Do not change the `inspect_no_op_pattern` action id.
- Do not change clear, blocked, scope-validation, missing no-op explanation, or
  completed-verification-blocked behavior.
- Do not add live execution, retries, queues, or code mutation.

## Design

Extend the `retry_boundary_is_manual` rule in
`src/qa_z/executor_dry_run_logic.py` so it treats
`repeated_no_op_attempts` the same way as repeated partial and repeated rejected
attempts:

- status becomes `attention`
- summary remains `Repeated attempts need explicit manual review before another retry.`

This keeps the existing rule vocabulary and avoids adding a second overlapping
rule for retry pressure. The repeated no-op fixture should then report:

- `attention_rule_ids`: `["retry_boundary_is_manual"]`
- `attention_rule_count`: `1`
- `clear_rule_count`: `5`
- `blocked_rule_count`: `0`

The top-level verdict, verdict reason, history signals, operator summary,
recommended action, and next recommendation remain unchanged.

## Documentation

Update current-truth surfaces to mention that repeated no-op histories now align
their attention verdict with a rule-level attention bucket:

- `README.md`
- `docs/benchmarking.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

## Test Strategy

1. Add failing logic assertions for repeated no-op rule counts and rule ids.
2. Update `evaluate_rules()` minimally.
3. Update the repeated no-op benchmark fixture expected values.
4. Add current-truth assertions and update docs.
5. Run the repeated no-op fixture benchmark, focused tests, full pytest, and
   full benchmark.
