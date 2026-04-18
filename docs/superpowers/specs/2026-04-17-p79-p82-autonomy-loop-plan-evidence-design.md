# P79-P82 Autonomy Loop Plan Evidence Design

## Goal

Keep persisted autonomy loop plans self-contained by mirroring selected-task
evidence alongside the score and penalty residue that already survived earlier
selection-surface work.

## Problem

`qa-z autonomy status` and `selected_tasks.json` preserve the selected task's
evidence, but the saved `loop_plan.md` still dropped that context. Operators
could see which task won, but not why, unless they reopened the JSON artifact.

## Scope

- Mirror selected-task evidence entries into autonomy `loop_plan.md`.
- Keep the existing Markdown plan shape and additive residue fields.
- Sync README, artifact schema, roadmap notes, and current-truth tests.

## Non-Goals

- No scoring changes.
- No new autonomy artifacts.
- No executor, bridge, or backlog-selection behavior changes.

## Validation

- Add a focused failing test for autonomy loop-plan evidence rendering.
- Re-run focused autonomy/current-truth coverage.
- Re-run repository formatting, lint, typecheck, pytest, and benchmark gates.
