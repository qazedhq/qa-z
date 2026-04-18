# Dry-Run Fixture Operator Parity Design

Date: 2026-04-18

## Context

`qa-z executor-result dry-run` now emits deterministic operator diagnostics:
`operator_summary`, `recommended_action_ids`, and
`recommended_action_summaries`. Newer dry-run benchmark fixtures pin those
fields, but the original committed dry-run fixtures still mostly assert verdict
and rule-count behavior.

That leaves a narrow regression gap: the benchmark can continue passing if the
operator guidance for clear, repeated-partial, or completed-but-blocked history
drifts while the verdict stays the same.

## Goal

Every committed `executor_dry_run_*` benchmark fixture should pin the operator
summary and recommended action residue that matters to an operator. Future
dry-run fixtures should fail review tests if they omit that residue.

## Non-Goals

- Do not change dry-run production logic.
- Do not add live executor calls, retries, queues, or model orchestration.
- Do not broaden the benchmark corpus with another fixture in this pass.
- Do not make benchmark expectations brittle by copying full reports.

## Design

Add a corpus invariant test in `tests/test_benchmark.py` that discovers all
committed fixtures under `benchmarks/fixtures/` and requires every fixture whose
name starts with `executor_dry_run_` to include non-empty values for:

- `operator_summary`
- `recommended_action_ids`
- `recommended_action_summaries`

Backfill the missing expected fields into the older dry-run fixtures:

- `executor_dry_run_clear_verified_completed`
  - summary: `Executor history is clear under the pre-live safety rules.`
  - action id: `continue_standard_verification`
- `executor_dry_run_repeated_partial_attention`
  - summary: `Repeated partial executor attempts need manual review before another retry.`
  - action id: `inspect_partial_attempts`
- `executor_dry_run_completed_verify_blocked`
  - summary: `A completed executor attempt is still blocked by verification evidence.`
  - action ids: `resolve_verification_blockers`, `review_validation_conflict`

Keep list comparisons subset-based as they are today, but make the fixture
expectations explicit enough that these specific actions cannot disappear
silently.

## Documentation

Update the current-truth surfaces that already describe benchmark and operator
diagnostic density:

- `README.md`
- `docs/benchmarking.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

The docs should say the committed dry-run corpus pins operator summary and
recommended action residue across all committed dry-run fixtures, not only the
newer operator-action fixtures.

## Test Strategy

1. Add the corpus invariant test first and run it before backfilling fixtures.
   It should fail on the older dry-run fixtures.
2. Backfill the expected fixture fields and rerun the focused test.
3. Update current-truth tests so docs must mention full dry-run operator parity.
4. Run the dry-run benchmark fixtures sequentially. Do not run multiple
   benchmark commands in parallel against the same default results directory on
   Windows because the benchmark work-directory reset is shared.
5. Run the full repository tests and full benchmark.
