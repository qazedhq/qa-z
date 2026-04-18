# Backlog Action Hints Design

Date: 2026-04-18

## Purpose

`qa-z select-next` now shows deterministic action hints for selected tasks. The
plain `qa-z backlog` view still shows active items with title, status, priority,
recommendation, and compact evidence only. That leaves operators translating the
same recommendation ids before they have even selected work.

This pass extends the existing action hint helper to the plain backlog view so
active backlog review and selected-task review speak the same operator language.

## Scope

- Render one `action:` line for each open, selected, or in-progress item in
  plain `qa-z backlog` output.
- Reuse `selected_task_action_hint()` so wording stays aligned with
  `qa-z select-next` and loop plans.
- Keep `qa-z backlog --json` unchanged.
- Keep closed history collapsed to a count in plain output.
- Preserve the live-free boundary: this only explains work; it does not execute,
  stage, commit, push, schedule, or call a model.

## Non-Goals

- No new backlog schema field.
- No change to backlog scoring, selection penalties, or closure logic.
- No autonomy packet changes.
- No live executor integration or automatic commit splitting.

## Behavior

Plain backlog output for an active item becomes:

```text
- worktree_risk-dirty-worktree: Reduce dirty worktree integration risk
  status: open | priority: 65 | recommendation: reduce_integration_risk
  action: inspect the dirty worktree and separate generated artifacts, then rerun self-inspection
  evidence: git_status: modified=25; untracked=346; staged=0
```

Unknown recommendations use the existing generic action hint:
`turn <recommendation id> into a scoped repair plan`.

## Test Strategy

- Extend the existing backlog plain-output test to assert the action line.
- Verify the test fails before rendering changes.
- Implement the minimal renderer change.
- Run focused CLI tests, then the full alpha gate checklist.

## Documentation

Update README and artifact schema wording where they describe plain backlog
output. Update current reports to note that active backlog review now carries the
same deterministic action hint as selected-task review.
