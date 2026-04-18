# Benchmark Snapshot Artifact Decision Design

## Purpose

Alpha closure still depends on separating source changes, committed benchmark
fixtures, local generated outputs, and intentionally frozen evidence. QA-Z
already treats `benchmarks/results/` as generated runtime output, but ad hoc
benchmark snapshot directories such as `benchmarks/results-p12-*` can appear as
ordinary benchmark paths in dirty-worktree summaries.

This pass classifies `benchmarks/results-*` sibling snapshots as generated
runtime artifacts and makes the operator action hint name the remaining decision:
keep them local or intentionally freeze them with context.

## Scope

- Treat `benchmarks/results-*` paths as runtime/generated artifact paths.
- Keep normal benchmark fixtures under `benchmarks/fixtures/**` classified as
  benchmark work, not runtime artifacts.
- Reuse the existing runtime-artifact cleanup and dirty-worktree evidence
  surfaces.
- Add a deterministic action hint for `triage_and_isolate_changes` that tells
  operators to decide local-only versus intentional frozen evidence before source
  integration.
- Keep JSON artifact shapes, recommendation ids, scores, command names, and live
  execution boundaries unchanged.

## Behavior

Runtime artifact detection before:

```text
benchmarks/results-p12-dry-run/report.md -> benchmark
```

Runtime artifact detection after:

```text
benchmarks/results-p12-dry-run/report.md -> runtime_artifact
```

Action hint for deferred/generated cleanup work:

```text
decide whether generated artifacts stay local-only or become intentional frozen evidence, separate them from source changes, then rerun self-inspection
```

## Non-Goals

- Do not delete generated artifacts.
- Do not commit frozen evidence or decide which snapshots should be kept.
- Do not add a new command, artifact field, or backlog category.
- Do not broaden benchmark fixture semantics.
- Do not stage, commit, push, or post GitHub comments.

## Test Strategy

- Add unit tests proving `benchmarks/results-*` paths are runtime artifacts while
  `benchmarks/fixtures/**` paths remain benchmark work.
- Add an action-hint test for `triage_and_isolate_changes`.
- Run focused self-improvement, CLI, and current-truth tests.
- Run the full alpha closure gate suite.

## Documentation

Update README, artifact schema notes, current-state analysis, next roadmap, and
worktree commit plan to state that benchmark snapshot directories are treated as
generated artifacts unless intentionally frozen with context.
