# P67-P70 Select-Next Stdout And Runtime Clarity Design

## Goal

Make the operator-facing planning surfaces easier to read without changing the
underlying backlog, selection, or autonomy artifact contracts.

## Why Now

`qa-z select-next --json` already preserves rich selected-task context, but the
plain-text CLI only reports file paths and count. Meanwhile `qa-z autonomy`
shows `Runtime: 1/0 seconds` when no minimum runtime budget is configured,
which is technically accurate but awkward for operators.

## Scope

- Add a human stdout renderer for `qa-z select-next`.
- Mirror the latest selected task title, recommendation, compact evidence
  summary, selection score, and optional selection-penalty reasons.
- Replace the `elapsed/0 seconds` wording on autonomy human output with an
  explicit `no minimum budget` phrase when the runtime target is zero.
- Keep JSON artifacts and machine-readable schemas additive and unchanged.

## Non-Goals

- No changes to selection scoring or backlog prioritization.
- No new artifact files.
- No new executor, automation, or remote orchestration behavior.

## Validation

- Focused CLI and autonomy rendering tests first.
- Full `ruff`, `mypy`, `pytest`, and `qa_z benchmark --json` after the change.
