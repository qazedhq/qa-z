# Benchmark Snapshot Schema Sync Design

## Context

Benchmark summaries now include a deterministic `snapshot` field, and generated
benchmark reports repeat it for alpha closure notes. The artifact schema
document still lists only the older numeric fields, so a reader can miss that
`snapshot` is part of the benchmark summary contract.

## Goal

Make the benchmark `snapshot` field visible in schema-level documentation and
pin that visibility with current-truth tests.

## Design

The benchmark summary schema stays additive and remains at schema version `1`.
The numeric fields remain the machine-readable source for calculations, while
`snapshot` is the compact, generated text for closure notes and human reports.

`docs/artifact-schema-v1.md` will list:

```text
snapshot: compact generated text such as `50/50 fixtures, overall_rate 1.0`
```

The documentation will also note that `report.md` repeats the value and that the
field is generated from `fixtures_passed`, `fixtures_total`, and `overall_rate`.

## Testing

- Add a schema stability test for the benchmark summary payload keys.
- Add a current-truth test that fails when artifact schema docs omit the
  `snapshot` field.
- Keep existing benchmark behavior unchanged.

## Non-Goals

- Do not change benchmark fixture comparison.
- Do not change benchmark exit codes.
- Do not increment the schema version for this additive field.
- Do not commit generated `benchmarks/results/**` artifacts.
