# Executor Bridge Missing Action Context Diagnostics Design

## Purpose

Executor bridge packages already record missing prepared-action `context_paths`
under `inputs.action_context_missing`. The bridge guides, however, only render
copied context inputs. That means an external operator can miss the fact that a
selected task tried to pass additional evidence but the file was not available
when the bridge package was created.

This pass makes missing action-context evidence visible in executor-facing
guides and pins that behavior in the benchmark corpus.

## Scope

- Render missing action-context paths in `executor_guide.md`, `codex.md`, and
  `claude.md` when `inputs.action_context_missing` is non-empty.
- Keep missing context paths non-fatal. Required bridge inputs still fail fast;
  optional prepared-action context remains diagnostic residue.
- Extend the benchmark executor-bridge summary with a
  `guide_mentions_missing_action_context` boolean.
- Add a committed fixture that includes one copied context path and one missing
  context path, then expects both manifest residue and guide visibility.
- Update README, benchmark docs, current-state reports, roadmap, closure
  snapshot counts, and current-truth tests.

## Behavior

Given a prepared loop action with:

```json
{
  "context_paths": [
    ".qa-z/runs/candidate/verify/summary.json",
    ".qa-z/runs/candidate/verify/missing-context.json"
  ]
}
```

the bridge should:

- copy the existing summary to `inputs/context/001-summary.json`
- record `.qa-z/runs/candidate/verify/missing-context.json` under
  `inputs.action_context_missing`
- render an "Action context missing" section in all bridge guides
- keep bridge creation successful

## Non-Goals

- Do not make missing action context fatal.
- Do not change the executor bridge schema version.
- Do not add live executor execution, retries, queues, or code mutation.
- Do not change autonomy action selection. This is packaging diagnostics only.

## Testing

- Add a focused executor-bridge unit test that mutates a prepared loop outcome
  to include an existing and a missing context path, then asserts manifest and
  guide behavior.
- Add a benchmark comparison test for
  `guide_mentions_missing_action_context`.
- Add a committed benchmark fixture named
  `executor_bridge_missing_action_context_inputs`.
- Run the selected fixture, focused tests, and full alpha gates.
