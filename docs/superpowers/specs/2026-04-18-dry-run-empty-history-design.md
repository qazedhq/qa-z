# Dry-Run Empty-History Design

Date: 2026-04-18

## Context

The dry-run logic already recognizes sessions with no recorded executor attempts
as `no_recorded_attempts`. It also emits an `ingest_executor_result` recommended
action. However, the top-level `next_recommendation` still falls through to the
generic retry-review text, and the committed benchmark corpus does not exercise
the empty-history path.

That leaves a small operator-clarity gap: a session with no executor-result
history should tell the operator to ingest a result before relying on dry-run
safety evidence, not imply there is retry history to inspect.

## Goal

Make empty executor-result history produce a precise deterministic next
recommendation and pin that behavior in the benchmark corpus.

## Non-Goals

- Do not add live execution.
- Do not add a new dry-run verdict.
- Do not change the `ingest_executor_result` recommended action id.
- Do not turn missing history into a failure. A missing history artifact should
  still be materialized as empty history by the existing dry-run path.

## Design

Update `next_recommendation()` in `src/qa_z/executor_dry_run_logic.py` so
`no_recorded_attempts` maps to:

`ingest executor result before relying on dry-run safety evidence`

Then add `executor_dry_run_empty_history_operator_actions`, a benchmark fixture
with a repair session manifest but no pre-seeded executor-result attempts. The
dry-run command should materialize an empty history artifact and produce:

- `verdict`: `attention_required`
- `verdict_reason`: `no_recorded_attempts`
- `history_signals`: `["no_recorded_attempts"]`
- `evaluated_attempt_count`: `0`
- `operator_summary`: `No executor attempts are recorded for this session.`
- `recommended_action_ids`: `["ingest_executor_result"]`
- `expected_recommendation`: `ingest executor result before relying on dry-run safety evidence`

Rule counts remain all clear because there are no failed safety-rule signals:

- clear: 6
- attention: 0
- blocked: 0

## Documentation

Update current-truth surfaces to mention that the dry-run corpus now covers the
empty-history/no-recorded-attempts operator path:

- `README.md`
- `docs/benchmarking.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

## Test Strategy

1. Add a failing unit assertion for the empty-history `next_recommendation`.
2. Add failing benchmark corpus/current-truth assertions for the new fixture.
3. Update production logic minimally.
4. Add the fixture.
5. Run the new fixture, focused dry-run tests, full pytest, and full benchmark.
