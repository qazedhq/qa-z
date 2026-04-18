# Selected Task Action Hints Design

Date: 2026-04-18

## Purpose

`qa-z select-next` already chooses evidence-backed backlog items and now shows
compact closure-aware evidence. The remaining operator gap is that the plain
output and saved loop plan still require the reader to translate internal
recommendation ids such as `isolate_foundation_commit` into the first practical
action.

This pass adds deterministic selected-task action hints to the existing human
surfaces. It does not change selection scoring, start live execution, edit code,
or add orchestration.

## Scope

- Add a small helper that maps selected backlog items to one readable action
  hint.
- Render the hint in human `qa-z select-next` output.
- Render the same hint in `.qa-z/loops/latest/loop_plan.md`.
- Keep `--json` output stable; selected task artifacts continue to carry the
  original backlog item shape.
- Cover closure-oriented recommendations, especially
  `reduce_integration_risk`, `isolate_foundation_commit`, and
  `audit_worktree_integration`.

## Non-Goals

- No live Codex, Claude, or remote executor calls.
- No staging, committing, pushing, or GitHub posting.
- No automatic commit splitting.
- No change to backlog scoring or loop-history penalty behavior.
- No new schema-required field in `selected_tasks.json`.

## Behavior

For each selected task, QA-Z derives one action hint from the `recommendation`
field. Known closure recommendations get specific wording:

- `reduce_integration_risk`: inspect the dirty worktree and separate generated
  artifacts before rerunning self-inspection.
- `isolate_foundation_commit`: follow
  `docs/reports/worktree-commit-plan.md` to split the foundation commit before
  rerunning self-inspection.
- `audit_worktree_integration`: inspect current-state, triage, and commit-plan
  reports before rerunning self-inspection.

Unknown recommendations fall back to a deterministic readable form:
`turn <recommendation id> into a scoped repair plan`.

## Test Strategy

- Add a focused unit test for the action hint helper.
- Add a CLI rendering test proving `qa-z select-next` human output includes the
  action hint.
- Add a loop-plan rendering test proving the saved plan includes the same hint.
- Run focused tests first, then the full repository gates.

## Documentation

Update the report and README/schema wording only where it describes human
`select-next` and loop-plan operator context. The docs must continue to state
that QA-Z plans work only and does not perform live repair.
