# P36-P39 Self-Inspection Dry-Run Provenance Design

## Goal

Keep executor dry-run provenance visible inside self-inspection evidence, not just in repair-session and publish surfaces.

## Why now

P32-P35 made materialized dry-run artifacts self-describing and pinned that provenance in benchmark contracts. Self-inspection still consumed the same residue, but its evidence summaries did not explicitly say whether a dry-run signal came from `dry_run_summary.json` or synthesized history.

That made backlog review slightly weaker than the surrounding surfaces.

## Scope

- preserve `summary_source` when self-inspection loads a materialized dry-run summary
- mark synthesized self-inspection dry-run summaries as `history_fallback`
- include provenance in self-inspection evidence summaries
- update docs/tests so the public description matches the actual behavior

## Non-goals

- no new backlog categories
- no score recalibration
- no live executor behavior
- no benchmark contract redesign

## Implementation notes

1. Backfill `summary_source: materialized` in `load_executor_dry_run_summary()` so older persisted artifacts still read consistently during self-inspection.
2. Wrap synthesized dry-run summaries with `summary_source: history_fallback`.
3. Extend compact evidence summaries with `source=<provenance>`.
4. Prove the change with focused self-inspection tests plus current-truth docs coverage.
