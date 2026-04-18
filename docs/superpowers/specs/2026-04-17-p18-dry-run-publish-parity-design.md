# P18 Dry-Run Publish Parity Design

## Goal

Surface repair-session dry-run safety context in GitHub-style publish summaries so operator-facing CI output carries the same executor safety signal already available in session summaries.

## Scope

Included:

- session publish summary fields for dry-run verdict and reason
- GitHub summary rendering of that dry-run context
- focused publish tests

Excluded:

- GitHub API calls
- new reporting commands
- live executor work

## Design

When a repair session summary contains:

- `executor_dry_run_verdict`
- `executor_dry_run_reason`

the session publish summary should preserve them and the GitHub summary renderer should add compact lines under the repair session section.
