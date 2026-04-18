# P27-P30 Dry-Run Provenance Continuation Design

## Goal

Extend the dry-run history residue work so session publish and GitHub summary
surfaces preserve where their executor safety signal came from and keep that
signal visible even when session `summary.json` is missing.

## Scope

Included:

- additive `executor_dry_run_source` propagation
- session publish fallback that still loads dry-run residue from history
- GitHub summary rendering for the same additive provenance
- focused regression tests for materialized and synthesized dry-run paths
- artifact-schema and milestone docs updates

Excluded:

- schema version bumps
- benchmark contract redesign
- new live executor behavior
- retry policy changes or backlog reprioritization

## Design

P21 through P26 made history-only dry-run synthesis available in repair-session
status, session verification summaries, publish summaries, and explicit
verify-artifact fallback. The remaining gap is provenance continuity: callers
can often recover a dry-run verdict, but they cannot always tell whether it came
from `executor_results/dry_run_summary.json` or an in-memory synthesis from
`executor_results/history.json`. Another gap remains when session
`summary.json` is absent: publish surfaces already recover verification data
from `verify/`, but dry-run residue currently falls away.

This pass keeps the current artifact contracts intact and adds a single narrow
field, `executor_dry_run_source`, on session-oriented summary surfaces. Allowed
values are `materialized` and `history_fallback`. Repair-session logic already
knows which path it used, so publish and GitHub summary layers can reuse that
answer instead of inventing parallel logic.

When `load_session_publish_summary()` falls back from missing `summary.json` to
`verify/` artifacts, it should still call the existing dry-run loader and
populate dry-run verdict, reason, attempt count, history signals, and source.
That keeps operator-facing summaries honest about both the verification outcome
and the executor safety residue that survived the missing session summary.

Rendering stays compact: one extra line for dry-run source is enough. The
verification headline and recommendation stay unchanged so this remains an
additive transparency pass rather than a behavior redesign.
