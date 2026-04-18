# P51-P54 Action Packet Clarity Design

## Goal

Make autonomy action packets for worktree, commit-isolation, and integration backlog items point at the right local evidence instead of collapsing into one generic follow-up.

## Why now

Recent self-inspection cleanup removed stale runtime-artifact noise and stale backlog residue. The top selected work now clusters around `worktree_risk`, `commit_isolation_gap`, and `integration_gap`, but the prepared actions for those categories still look too generic to drive a realistic next step.

## Scope

- keep existing action types stable where possible
- specialize commands and next recommendations by deterministic recommendation id
- attach compact context paths derived from task evidence
- render the richer action packets in loop-plan docs and schema docs

## Non-goals

- no live execution
- no automatic git staging or commit splitting
- no new autonomy state machine
- no broad contract redesign

## Intended result

Selected cleanup and integration tasks stay deterministic, but now hand an external operator or executor a more concrete packet: what to inspect, which local reports matter, and which stable commands to rerun after the cleanup work.
