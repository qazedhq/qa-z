# Legacy Benchmark Snapshot Fallback Design

## Context

Benchmark summaries now write a compact `snapshot` field such as
`50/50 fixtures, overall_rate 1.0`. Self-inspection preserves that field in
benchmark-gap candidate evidence so backlog, selected-task, and loop-plan
surfaces can show the failed fixture together with the overall benchmark state.

Older generated summaries can still exist without the `snapshot` field. Those
artifacts already carry `fixtures_passed`, `fixtures_total`, and `overall_rate`,
but the current self-inspection helper drops the compact benchmark state when
`snapshot` is absent.

## Goal

When self-inspection reads a legacy benchmark summary without `snapshot`, it
should synthesize the same compact snapshot text from the legacy numeric fields:

```text
<fixtures_passed>/<fixtures_total> fixtures, overall_rate <overall_rate>
```

## Design

`benchmark_summary_snapshot` remains the only formatting point for compact
benchmark summary evidence.

The helper will:

1. Return the explicit `snapshot` string when present and non-empty.
2. Otherwise, if `fixtures_passed`, `fixtures_total`, and `overall_rate` are
   all present, return the synthesized compact text.
3. Return an empty string if the summary lacks enough data.

This keeps the backlog schema unchanged and only improves the compact evidence
summary attached to existing benchmark-gap candidates.

## Testing

- Add a legacy benchmark summary fixture by removing `snapshot` from the
  existing self-inspection benchmark summary fixture.
- Run self-inspection.
- Assert the benchmark-gap evidence still includes
  `snapshot=1/2 fixtures, overall_rate 0.5`.
- Keep the existing test that proves explicit `snapshot` values are preserved.

## Non-Goals

- Do not change benchmark execution or generated summary schema.
- Do not infer snapshots for unrelated artifact kinds.
- Do not create benchmark candidates for passing summaries.
- Do not commit generated benchmark result artifacts.
