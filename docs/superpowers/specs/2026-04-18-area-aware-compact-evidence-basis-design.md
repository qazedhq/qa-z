# Area-Aware Compact Evidence Basis Design

## Purpose

Commit-isolation tasks now reuse dirty-worktree area evidence for their
operator-facing action hints. The compact evidence summary still prioritizes the
alpha closure readiness snapshot, which is useful as the primary gate reference
but hides why the action hint names benchmark, docs, source, or test areas.

This pass keeps the closure snapshot as the primary compact evidence while
adding a short `action basis:` suffix when a secondary evidence entry carries
`areas=`.

## Scope

- Keep `compact_evidence_priority()` unchanged so alpha closure readiness
  snapshots remain the primary one-line evidence.
- Add a small helper that finds the first area-bearing evidence summary when the
  primary compact summary does not already include `areas=`.
- Append that secondary summary as `action basis: <source>: <summary>` on human
  compact evidence surfaces.
- Keep backlog JSON shape, selected task JSON shape, scoring, recommendations,
  validation hints, and action hints unchanged.

## Behavior

Compact commit-isolation evidence before:

```text
worktree_commit_plan: alpha closure readiness snapshot pins full gate pass and commit-split action
```

Compact commit-isolation evidence after:

```text
worktree_commit_plan: alpha closure readiness snapshot pins full gate pass and commit-split action; action basis: git_status: dirty worktree still spans modified=3; untracked=1; areas=docs:2, source:1
```

If the primary compact evidence already includes `areas=`, the summary is left
unchanged to avoid duplicate area residue.

## Non-Goals

- Do not add new artifact fields.
- Do not change backlog selection, scoring, fallback rotation, or action hints.
- Do not broaden live execution or introduce network calls.
- Do not replace the alpha closure snapshot priority for commit-isolation items.
- Do not stage, commit, delete, or move files.

## Test Strategy

- Add a direct compact evidence test that uses an alpha closure primary entry
  plus a `git_status` area entry and expects the `action basis:` suffix.
- Add a direct compact evidence test proving area-bearing primary evidence is
  not duplicated.
- Run focused self-improvement, CLI, and current-truth tests.
- Run the full alpha closure gate suite.

## Documentation

Update README, artifact schema notes, and current reports to explain that compact
human evidence can append an `action basis:` suffix when action guidance depends
on secondary area evidence.
