# P23 Self-Inspection Fallback Design

## Goal

Make self-inspection and backlog synthesis reuse the same history-only dry-run
fallback that repair-session and publish surfaces already use.

## Scope

Included:

- synthetic dry-run summary reuse inside executor-history candidate discovery
- additive evidence labeling for fallback-derived dry-run summaries
- focused self-inspection regression coverage
- README and milestone status updates

Excluded:

- changes to backlog scoring weights
- benchmark fixture changes
- automatic materialization of dry-run artifacts

## Design

P21 and P22 made history-only dry-run residue visible in repair-session and
publish surfaces, but self-inspection still treated sessions without
`dry_run_summary.json` as weaker evidence. P23 closes that gap by synthesizing
the same dry-run summary in memory during candidate discovery, then carrying it
into evidence summaries and signals. When the fallback path is used, evidence is
labeled as a fallback instead of pretending a real `dry_run_summary.json` file
exists.
