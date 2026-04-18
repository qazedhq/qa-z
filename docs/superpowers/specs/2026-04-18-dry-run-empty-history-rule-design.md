# Dry-Run Empty-History Rule Design

Date: 2026-04-18

## Context

The dry-run empty-history path is now operator-visible:

- `verdict`: `attention_required`
- `verdict_reason`: `no_recorded_attempts`
- `history_signals`: `["no_recorded_attempts"]`
- `recommended_action_ids`: `["ingest_executor_result"]`
- `next_recommendation`: `ingest executor result before relying on dry-run safety evidence`

However, the rule-level summary still reports all existing rules as clear for
empty history. That means an operator can see an attention verdict with
`attention_rule_count: 0`. The same class of mismatch was just removed for
repeated no-op history; empty history should now receive an explicit rule bucket
as well.

## Goal

Add an explicit dry-run rule for recorded executor history so empty sessions have
a rule-level attention signal instead of relying only on top-level verdict and
recommended actions.

## Non-Goals

- Do not add live executor behavior.
- Do not change the `ingest_executor_result` action id.
- Do not change empty history from `attention_required` to `blocked`.
- Do not hide or special-case materialized empty history.
- Do not reuse unrelated rules such as `retry_boundary_is_manual` for an
  empty-history condition.

## Design

Add a new first-class dry-run rule in
`src/qa_z/executor_dry_run_logic.py`:

- `id`: `executor_history_recorded`
- `status`: `attention` when `no_recorded_attempts` is present, otherwise
  `clear`
- clear summary: `Executor history contains at least one recorded attempt.`
- attention summary: `No executor attempts are recorded; ingest a result before relying on dry-run safety evidence.`

This increases the dry-run rule count from 6 to 7 for every dry-run summary.
Non-empty histories gain one additional clear rule. Empty histories gain one
attention rule while the existing six rules remain clear.

Expected count changes:

- clear completed: `clear 7`, `attention 0`, `blocked 0`
- empty history: `clear 6`, `attention 1`, `blocked 0`
- one attention signal: previous clear count + 1
- blocked-only signal: previous clear count + 1
- mixed attention/blocked signal: previous clear count + 1

## Benchmark Coverage

Update all committed executor dry-run fixtures because the total rule count is
part of the expected contract. The key pinned fixture is
`executor_dry_run_empty_history_operator_actions`, which should now include:

- `attention_rule_ids`: `["executor_history_recorded"]`
- `attention_rule_count`: `1`
- `clear_rule_count`: `6`
- `blocked_rule_count`: `0`

All non-empty dry-run fixtures should keep their existing attention/blocked ids
and counts, but increase `clear_rule_count` by one.

## Documentation

Update current-truth surfaces to mention that empty-history/no-recorded-attempts
now has an explicit rule-level attention bucket:

- `README.md`
- `docs/benchmarking.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

## Test Strategy

1. Add a failing pure-logic assertion that empty history marks
   `executor_history_recorded` as attention.
2. Add the new dry-run rule and update logic count assertions.
3. Add failing benchmark/current-truth assertions for the rule id and docs.
4. Update all dry-run fixture count expectations.
5. Run the empty-history fixture benchmark, focused tests, full pytest, and full
   benchmark.
