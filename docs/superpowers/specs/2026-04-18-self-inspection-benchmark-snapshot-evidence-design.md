# Self-Inspection Benchmark Snapshot Evidence Design

## Context

Benchmark summaries now expose a compact generated `snapshot` field, for
example `50/50 fixtures, overall_rate 1.0`. Self-inspection already turns failed
benchmark summaries into backlog candidates, but its candidate evidence only
mentions the failed fixture and individual failure text. The generated snapshot
does not travel into backlog, selected-task, or loop-plan evidence summaries.

## Goal

When a benchmark summary has a `snapshot`, self-inspection should preserve that
value in benchmark failure candidate evidence so operators see both the failed
fixture and the overall benchmark state from the same generated artifact.

## Design

`discover_benchmark_candidates` will read the compact snapshot from each
benchmark summary and pass it into `benchmark_candidate`.

`benchmark_candidate` will keep the existing fixture/failure summary, but prefix
it with:

```text
snapshot=<summary snapshot>
```

Example:

```text
snapshot=1/2 fixtures, overall_rate 0.5; fixture=py_type_error; failures=fast.failed_checks missing expected values: py_type
```

Older summaries without `snapshot` keep the previous evidence text unchanged.
No backlog schema fields change; this is a better compact summary over existing
evidence.

## Testing

- Seed a benchmark summary with `snapshot`.
- Run self-inspection.
- Assert the benchmark-gap candidate evidence includes the generated snapshot.
- Assert the compact backlog evidence summary exposes the same snapshot.

## Non-Goals

- Do not change benchmark execution or comparison behavior.
- Do not create new backlog categories or recommendations.
- Do not treat a passing benchmark summary as a backlog candidate.
- Do not commit generated `benchmarks/results/**` artifacts.
