# Generated Artifact Action Basis Design

## Purpose

Deferred cleanup tasks now tell operators to decide whether generated artifacts
stay local-only or become intentional frozen evidence. The compact evidence line
can still lead with a report summary, so the generated artifact evidence that
explains the action may require opening the JSON artifact.

This pass appends a short `action basis:` suffix when a deferred cleanup task has
secondary `generated_outputs` or `runtime_artifacts` evidence.

## Scope

- Keep compact evidence priority unchanged.
- Keep backlog and selected-task JSON shapes unchanged.
- Reuse the existing `action basis:` suffix pattern from area-aware
  commit-isolation evidence.
- Append generated/runtime action basis only for
  `triage_and_isolate_changes` tasks.
- Avoid duplicating basis text when the primary compact evidence already carries
  generated/runtime artifact evidence.

## Behavior

Compact evidence before:

```text
current_state: report calls out deferred cleanup work or generated outputs to isolate
```

Compact evidence after:

```text
current_state: report calls out deferred cleanup work or generated outputs to isolate; action basis: generated_outputs: generated benchmark outputs still present: benchmarks/results/report.md, benchmarks/results/summary.json
```

If the primary compact evidence is already `generated_outputs` or
`runtime_artifacts`, the suffix is not added.

## Non-Goals

- Do not change scoring, selection, candidate ids, or recommendation ids.
- Do not add a new artifact field.
- Do not delete, move, stage, commit, or freeze generated artifacts.
- Do not alter the alpha closure live-free boundary.

## Test Strategy

- Add a direct compact evidence test for a deferred cleanup item with primary
  report evidence plus secondary `generated_outputs` evidence.
- Add a direct test proving no duplicate suffix is added when generated evidence
  is already primary.
- Run focused self-improvement, CLI, and current-truth tests.
- Run full alpha closure gates.

## Documentation

Update README, artifact schema notes, current-state analysis, roadmap, and commit
plan to explain that generated cleanup compact evidence can show an `action
basis:` suffix with the concrete generated/runtime artifact evidence.
