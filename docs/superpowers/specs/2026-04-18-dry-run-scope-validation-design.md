# Dry-Run Scope-Validation Design

Date: 2026-04-18

## Context

The dry-run logic already recognizes executor-result attempts whose provenance
failed with `scope_validation_failed`. That path blocks the
`mutation_scope_limited` rule, returns the `scope_validation_failed` verdict
reason, and guides operators through the `inspect_scope_drift` action.

However, the committed benchmark corpus does not yet exercise this path. That
leaves a small but important safety gap: scope drift is a core external
executor risk, and its operator guidance should be protected by executable
current-truth evidence instead of only unit-level assertions.

## Goal

Add a committed dry-run benchmark fixture that pins scope-validation failures
to a blocked verdict and preserves the scope-drift operator action.

## Non-Goals

- Do not add live executor behavior.
- Do not add new dry-run rules or verdicts.
- Do not change the existing `inspect_scope_drift` action id.
- Do not broaden mutation-scope validation beyond the existing executor-result
  history signal.
- Do not introduce network dependencies or agent-specific logic.

## Design

Add `executor_dry_run_scope_validation_operator_actions`, a seeded benchmark
fixture with one recorded executor-result attempt:

- `provenance_reason`: `scope_validation_failed`
- `provenance_status`: `failed`
- `validation_status`: `failed`
- `ingest_status`: `rejected_invalid`
- `result_status`: `partial`

The dry-run output should preserve the existing deterministic behavior:

- `verdict`: `blocked`
- `verdict_reason`: `scope_validation_failed`
- `history_signals`: `["scope_validation_failed"]`
- `evaluated_attempt_count`: `1`
- `operator_summary`: `Executor history is blocked by scope validation; inspect handoff scope before another attempt.`
- `recommended_action_ids`: `["inspect_scope_drift"]`
- `expected_recommendation`: `inspect executor scope drift before another attempt`
- `blocked_rule_ids`: `["mutation_scope_limited"]`

Rule counts should show that only mutation-scope safety is blocked:

- clear: 5
- attention: 0
- blocked: 1

## Documentation

Update current-truth surfaces to mention that the dry-run corpus covers
scope-validation drift and the corresponding operator action:

- `README.md`
- `docs/benchmarking.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

## Test Strategy

1. Add a failing benchmark corpus assertion for the new fixture and action id.
2. Add the seeded benchmark fixture.
3. Add a current-truth assertion that docs mention the fixture.
4. Update docs.
5. Run the new fixture, focused tests, full pytest, and full benchmark.
