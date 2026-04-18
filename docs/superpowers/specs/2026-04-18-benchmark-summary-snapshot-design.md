# Benchmark Summary Snapshot Design

## Context

The alpha closure evidence now depends on a compact benchmark phrase such as
`50/50 fixtures, overall_rate 1.0`. That phrase is currently written by humans in
reports, while the benchmark summary only exposes the separate
`fixtures_passed`, `fixtures_total`, and `overall_rate` fields.

## Goal

Add one deterministic `snapshot` field to benchmark summaries so reports,
operator notes, and alpha closure docs can quote the same machine-produced
string.

## Design

`qa_z.benchmark` will format the compact snapshot while building the benchmark
summary. The value will use the existing aggregate fields and the exact shape:

```text
<fixtures_passed>/<fixtures_total> fixtures, overall_rate <overall_rate>
```

For example, a full green corpus with 50 fixtures reports
`50/50 fixtures, overall_rate 1.0`. A selected two-fixture run with one pass
reports `1/2 fixtures, overall_rate 0.5`.

The field is additive to the existing schema version. Existing consumers can
continue reading the numeric fields. Human `report.md` output will include the
same snapshot near the top so the Markdown companion mirrors `summary.json`.

## Testing

- Unit tests pin the new summary field for a mixed pass/fail corpus.
- Unit tests pin that the human report renders the same snapshot.
- Current-truth tests pin that the alpha closure report references the benchmark
  summary snapshot field rather than only a hand-written count.

## Non-Goals

- Do not change fixture discovery, result comparison, or exit-code behavior.
- Do not add live executor benchmarking.
- Do not commit generated `benchmarks/results/**` artifacts.
