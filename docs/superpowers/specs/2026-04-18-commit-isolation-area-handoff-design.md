# Commit Isolation Area Handoff Design

## Purpose

QA-Z now summarizes dirty-worktree areas for the primary worktree-risk item and
uses those areas in the matching action hint. The adjacent commit-isolation item
still says the dirty worktree spans modified/untracked counts, but it does not
carry the same area distribution or use it in its action guidance.

This pass threads the same deterministic area evidence into the
`commit_isolation_gap-foundation-order` candidate so foundation-commit splitting
can start from the same benchmark/docs/source/test distribution visible on the
worktree-risk candidate.

## Scope

- Add `areas=` to the commit-isolation candidate's existing `git_status`
  evidence when dirty paths are present.
- Make `isolate_foundation_commit` action hints mention the top one or two dirty
  areas when area evidence exists.
- Keep the existing fallback action unchanged when area evidence is absent.
- Reuse the existing `worktree_area_summary()`, `worktree_action_areas()`, and
  `join_action_areas()` helpers.
- Keep candidate ids, scoring, JSON schema fields, validation commands, and live
  execution boundaries unchanged.

## Behavior

Commit-isolation evidence before:

```text
dirty worktree still spans modified=3; untracked=1
```

Commit-isolation evidence after:

```text
dirty worktree still spans modified=3; untracked=1; areas=docs:2, source:1
```

Action hint with area evidence:

```text
follow docs/reports/worktree-commit-plan.md and isolate docs and source changes into the foundation split, then rerun self-inspection
```

Action hint without area evidence remains:

```text
follow docs/reports/worktree-commit-plan.md to split the foundation commit, then rerun self-inspection
```

## Non-Goals

- Do not change selected-task scoring or fallback-family behavior.
- Do not add a new command, JSON field, or artifact kind.
- Do not execute, stage, commit, delete, or move files.
- Do not replace the closure-aware commit-plan evidence priority.

## Test Strategy

- Extend the existing commit-isolation self-inspection test so its `git_status`
  evidence includes `areas=`.
- Add direct action-hint tests for `isolate_foundation_commit` with and without
  area evidence.
- Run focused self-improvement tests, then the full gate suite.

## Documentation

Update README, artifact schema, and current reports to say commit-isolation
handoff now reuses dirty area evidence when available while preserving the
existing schema and live-free boundary.
