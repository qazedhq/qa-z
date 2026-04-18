# Worktree Area Action Hints Design

## Purpose

Dirty-worktree self-inspection evidence now includes deterministic area counts,
such as `areas=benchmark:271, docs:160, source:42`. The current `action:` hint
for `reduce_integration_risk` still stays generic, so an operator sees the
dominant areas in evidence but must translate that into the first move manually.

This pass makes the existing action hint area-aware when area evidence exists.

## Scope

- Parse the existing `areas=` segment from backlog evidence summaries.
- For `reduce_integration_risk`, mention the top one or two dirty areas in the
  first action hint.
- Keep the fallback action hint unchanged when area evidence is absent.
- Keep JSON artifact shape, scoring, candidate ids, validation commands, and
  command names unchanged.

## Behavior

Given evidence:

```text
modified=31; untracked=488; staged=0; areas=benchmark:271, docs:160, source:42
```

The action hint becomes:

```text
triage benchmark and docs changes first, separate generated artifacts, then rerun self-inspection
```

If only one area is present:

```text
triage docs changes first, separate generated artifacts, then rerun self-inspection
```

If no `areas=` segment is present, the existing action remains:

```text
inspect the dirty worktree and separate generated artifacts, then rerun self-inspection
```

## Parser Rules

- Read only evidence entries on the selected/backlog item.
- Use the first `areas=` segment found in an evidence summary.
- Split comma-separated `area:count` pairs.
- Ignore malformed or empty pairs.
- Preserve the area order already rendered by `worktree_area_summary()`, which
  is count-descending and then name-sorted.
- Limit action hints to two areas for readability.

## Non-Goals

- Do not execute `git status`.
- Do not mutate, stage, commit, delete, or move files.
- Do not add a new CLI command or JSON field.
- Do not change non-worktree recommendations.

## Test Strategy

- Unit-test area extraction from evidence summaries.
- Unit-test `selected_task_action_hint()` for two-area, one-area, and no-area
  worktree evidence.
- Extend the existing CLI renderer tests to expect the area-aware action string
  when their fixture evidence includes `areas=`.

## Documentation

Update README, artifact schema, and reports to state that dirty-worktree action
hints now use existing area evidence when present.
