# P15 Dry-Run Priority Calibration Design

## Goal

Make blocked dry-run safety findings rank above lighter attention-only history friction so autonomy and manual backlog review both treat executor safety blockers with the right urgency.

## Scope

Included:

- explicit dry-run severity signals on history-derived backlog candidates
- deterministic score bonuses for blocked versus attention dry-run states
- tests proving blocked dry-run work outranks lighter no-op or partial attention

Excluded:

- new backlog categories
- retry scheduling
- live executor work
- benchmark redesign

## Design

### 1. Candidate Signals

When executor-history candidates are derived with dry-run evidence:

- blocked dry-run verdicts should add `executor_dry_run_blocked`
- attention dry-run verdicts should add `executor_dry_run_attention`

These signals are additive. Existing category signals stay intact.

### 2. Score Bonuses

Extend `score_candidate()` with small deterministic bonuses:

- `executor_dry_run_blocked` -> `+2`
- `executor_dry_run_attention` -> `+1`

This keeps the existing formula intact while letting blocked safety issues outrank softer friction.

### 3. Expected Outcome

After P15:

- blocked dry-run workflow gaps rise naturally in the queue
- no-op and partial attention still remain visible, but lower
- autonomy selection gets a cleaner urgency gradient without adding a new policy engine
