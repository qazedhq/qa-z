# P22 CLI Fallback Parity Design

## Goal

Pin history-only dry-run fallback behavior on the actual human-facing CLI
surfaces, not just the internal repair-session and publish helpers.

## Scope

Included:

- `repair-session status` parity coverage when only executor history exists
- `github-summary` parity coverage for the same case
- milestone/status docs

Excluded:

- new CLI flags
- benchmark corpus changes
- live executor work

## Design

P21 made the fallback available to repair-session and publish internals. P22
locks that behavior onto the real CLI entry points by adding focused regression
tests that exercise:

- `qa-z repair-session status`
- `qa-z github-summary`

Both tests create session-local executor history without
`dry_run_summary.json`, then assert that the rendered output still shows the
derived dry-run verdict, reason, attempt count, and history signal residue.
