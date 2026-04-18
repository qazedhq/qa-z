# P75-P78 Loop Plan Selection Residue Design

## Goal

Align persisted loop plans with the richer operator-facing selection surfaces so
saved planning artifacts keep the same selection-diversity residue visible on
stdout and status commands.

## Problem

After recent operator-surface work, `qa-z select-next` and `qa-z autonomy
status` preserve selection score and penalty residue, but `loop_plan.md`
remains shallower. That means the saved plan can lose the exact diversity
signals that influenced task ordering.

## Scope

- Mirror `selection_priority_score` in self-improvement and autonomy loop-plan
  renderers when present.
- Mirror `selection_penalty` and `selection_penalty_reasons` when present.
- Keep the plan artifacts human-oriented and additive.

## Non-Goals

- No scoring changes.
- No new loop artifacts.
- No executor or bridge behavior changes.

## Validation

- Focused loop-plan rendering tests first.
- README/schema/current-truth sync.
- Full repository validation afterwards.
