# Generated Cleanup Action Context Design

## Purpose

Deferred cleanup tasks now explain generated/runtime artifact evidence in human
compact summaries. The matching autonomy prepared action can still hand an
operator only the triage and commit-plan reports, leaving the generated versus
frozen evidence policy one hop away.

This pass makes `triage_and_isolate_changes` prepared action packets carry the
generated evidence policy as an additive context path.

## Scope

- Keep the existing `integration_cleanup_plan` action type.
- Keep the `triage_and_isolate_changes` recommendation id unchanged.
- Add `docs/generated-vs-frozen-evidence-policy.md` to the recommendation-aware
  `context_paths` for deferred cleanup triage.
- Preserve deterministic sorted path output from `merge_context_paths()`.
- Keep human compact summaries and scoring unchanged.

## Behavior

Before, a deferred cleanup action could carry:

```json
{
  "context_paths": [
    "docs/reports/worktree-commit-plan.md",
    "docs/reports/worktree-triage.md"
  ]
}
```

After, the same action also carries:

```json
{
  "context_paths": [
    "docs/generated-vs-frozen-evidence-policy.md",
    "docs/reports/worktree-commit-plan.md",
    "docs/reports/worktree-triage.md"
  ]
}
```

If task evidence includes a report path, the normal evidence-path merge still
adds it. The policy path is recommendation-driven context rather than new
evidence.

## Non-Goals

- Do not delete, move, stage, commit, or freeze generated benchmark outputs.
- Do not change backlog scoring, selection, closure, or action packet commands.
- Do not add a live executor or remote orchestration path.
- Do not introduce a new artifact schema version.

## Test Strategy

- Add an autonomy action mapping test for `triage_and_isolate_changes` that
  asserts the generated evidence policy appears in `context_paths`.
- Run that test before implementation to confirm the missing context is real.
- Run focused autonomy/current-truth tests after implementation.
- Run full alpha closure gates.

## Documentation

Update README, artifact schema notes, current-state analysis, roadmap, commit
plan, and current-truth assertions so the live-free handoff boundary says
deferred cleanup packets carry generated/frozen policy context.
