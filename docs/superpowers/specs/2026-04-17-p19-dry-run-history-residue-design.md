# P19 Dry-Run History Residue Design

## Goal

Preserve multi-result dry-run residue in completed repair-session surfaces so operator-facing artifacts do not collapse rich session history down to only a verdict and reason.

## Scope

Included:

- repair-session `summary.json` fields for dry-run attempt count and history signals
- repair-session `outcome.md` rendering of those residue fields
- publish-summary and GitHub-summary rendering of the same residue
- focused repair-session and GitHub summary tests

Excluded:

- new retry scheduling
- live executor calls
- new executor-result storage formats

## Design

QA-Z already writes `evaluated_attempt_count` and `history_signals` into
`executor_results/dry_run_summary.json`. The remaining gap is that completed
session surfaces only preserve `executor_dry_run_verdict` and
`executor_dry_run_reason`.

P19 closes that gap additively:

- copy `evaluated_attempt_count` into
  `executor_dry_run_attempt_count`
- copy `history_signals` into
  `executor_dry_run_history_signals`
- render both fields in `outcome.md`
- surface both fields in publish-ready repair summaries and GitHub job summaries

This keeps the artifact model deterministic while making repeated partial,
rejected, or verify-blocked histories visible after verification completes.
