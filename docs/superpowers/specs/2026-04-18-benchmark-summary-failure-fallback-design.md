# Benchmark Summary Failure Fallback Design

## Context

Self-inspection promotes failed benchmark summaries into benchmark-gap backlog
candidates. Current summaries normally include per-fixture records or a
`failed_fixtures` list, so QA-Z can name the failed fixture in the backlog item.

Legacy or partially preserved benchmark summaries may only contain aggregate
failure fields such as `fixtures_failed`, `fixtures_passed`, `fixtures_total`,
and `overall_rate`. When the aggregate failure count is positive but fixture
details are absent, self-inspection currently has evidence that the benchmark
failed but no fixture name to turn into a candidate.

## Goal

Do not silently drop aggregate benchmark failures. If a benchmark summary reports
one or more failed fixtures but contains neither failed fixture records nor a
usable `failed_fixtures` list, self-inspection should create one summary-level
benchmark-gap candidate.

## Design

`discover_benchmark_candidates` will keep its current detailed behavior first:

1. Prefer failed entries from the `fixtures` list.
2. Fall back to names from `failed_fixtures`.
3. If neither path yields a candidate while `fixtures_failed` is positive,
   create a summary-level candidate with fixture name `summary`.

The fallback evidence summary will include the existing compact snapshot when
available or synthesizable, plus a direct aggregate failure note:

```text
snapshot=1/2 fixtures, overall_rate 0.5; fixture=summary; failures=benchmark summary reports 1 failed fixture without fixture details
```

This preserves the existing `benchmark_gap-*` id shape, category, signals, and
`add_benchmark_fixture` recommendation. No schema fields or command names
change.

## Testing

- Seed a benchmark summary with `fixtures_failed > 0`.
- Remove both `fixtures` and `failed_fixtures`.
- Run self-inspection.
- Assert a `benchmark_gap-summary` item exists.
- Assert its evidence includes the synthesized or explicit snapshot and the
  aggregate failure count.

## Non-Goals

- Do not invent fixture names when the summary does not contain them.
- Do not create summary-level candidates when detailed fixture candidates were
  already created.
- Do not change benchmark execution, result comparison, or generated artifact
  schema.
