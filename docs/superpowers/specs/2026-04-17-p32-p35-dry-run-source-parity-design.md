# P32-P35 Dry-Run Source Parity Design

## Goal

Carry dry-run provenance all the way down to the materialized dry-run artifact,
surface it in human-facing repair-session status output, and lock it into the
benchmark corpus with additive expectations.

## Scope

Included:

- `summary_source: materialized` on persisted dry-run summaries
- human `repair-session status` output parity for dry-run source
- additive benchmark expectation support for dry-run provenance
- fixture and regression coverage for the new parity

Excluded:

- benchmark category redesign
- new executor-result workflows
- live execution or retry scheduling

## Design

The current system preserves dry-run provenance on session and publish surfaces,
but the persisted `executor_results/dry_run_summary.json` artifact itself does
not currently self-identify as materialized. That leaves one awkward gap:
downstream consumers must infer provenance from context instead of reading it
directly.

This pass closes that gap by adding an additive `summary_source` field to the
materialized dry-run artifact with the value `materialized`. The existing
history-only fallback already stamps `history_fallback` in memory, so this makes
both sides of the provenance split explicit without changing verdict logic.

Once the artifact is self-describing, the human `repair-session status` output
can show the same source value that JSON and Markdown already preserve
elsewhere. That keeps operator-facing inspection aligned with machine-facing
surfaces.

Finally, the benchmark runner already supports `expect_executor_dry_run`. This
pass extends it additively with an `expected_source` alias that maps to
`summary_source`, then updates one seeded executor dry-run fixture so the corpus
guards the new provenance behavior.
