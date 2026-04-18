# P21 History Residue Fallback Design

## Goal

Preserve dry-run safety residue for repair-session and publish surfaces even when
`executor_results/dry_run_summary.json` has not been materialized yet.

## Scope

Included:

- deterministic fallback synthesis from `executor_results/history.json`
- repair-session verification and outcome surfaces using that fallback
- publish-summary and GitHub-summary use of the same fallback
- focused tests and current-truth docs

Excluded:

- writing fallback summaries back to disk automatically
- live executor calls
- retry scheduling or orchestration

## Design

QA-Z already stores enough structured attempt history to reconstruct the same
verdict and residue carried by a dry-run summary. P21 extracts the pure dry-run
logic into a shared helper so:

- `qa-z executor-result dry-run` keeps using the same deterministic logic
- repair-session verification can synthesize dry-run context from history when
  no summary file exists
- publish surfaces can do the same without weakening contracts or inventing a
  second verdict model

The fallback stays additive and in-memory: it enriches session and publish
surfaces without silently creating new dry-run artifacts.
