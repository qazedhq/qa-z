# P55-P58 Autonomy Status Action Visibility Design

## Goal

Expose the latest prepared autonomy actions through `qa-z autonomy status` so operators can see the current next-step packet without opening `outcome.json`.

## Why now

The latest loop outcome already carries richer recommendation-aware action packets with `commands` and `context_paths`, but the status surface still only shows selected task ids and backlog top items. That makes the most operator-relevant part of the loop harder to see than it should be.

## Scope

- add additive status fields for the latest prepared actions and next recommendations
- render those fields in the plain-text `autonomy status` output
- preserve the existing autonomy outcome shape and action packet types
- document the new status visibility exactly

## Non-goals

- no new autonomy state machine
- no live execution
- no automatic repair or git operations
- no broad report redesign

## Intended result

`qa-z autonomy status` becomes a practical operator summary: latest state, latest selected tasks, latest prepared actions, compact next recommendations, and the key local report paths to inspect next.
