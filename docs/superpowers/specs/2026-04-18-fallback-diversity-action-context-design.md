# Fallback Diversity Action Context Design

## Purpose

QA-Z can detect repeated fallback-family reuse and promote it as an
`autonomy_selection_gap` with recommendation `improve_fallback_diversity`.
Status and loop plans now show selected fallback families, but the prepared
`loop_health_plan` action still lacks the evidence path that explains why the
operator should inspect loop history.

This pass makes loop-health prepared actions carry their selected task evidence
paths through `context_paths`.

## Scope

- Reuse `task_context_paths()` for `backlog_reseeding_gap` and
  `autonomy_selection_gap` action packets.
- Keep the existing `loop_health_plan` action type.
- Keep commands and recommendation ids unchanged.
- Preserve selection scoring, penalty behavior, fallback-family detection, and
  backlog generation unchanged.
- Keep `context_paths` additive and omit the field when there are no non-root
  evidence paths.

## Behavior

For a repeated fallback-family task:

```json
{
  "category": "autonomy_selection_gap",
  "recommendation": "improve_fallback_diversity",
  "evidence": [
    {
      "path": ".qa-z/loops/history.jsonl",
      "source": "loop_history"
    }
  ]
}
```

The prepared action becomes:

```json
{
  "type": "loop_health_plan",
  "context_paths": [".qa-z/loops/history.jsonl"]
}
```

Existing loop plan and status renderers already display action
`context_paths`, so no new rendering contract is needed.

## Non-Goals

- Do not change fallback-family scoring or introduce cooldown logic.
- Do not add new fallback-family categories.
- Do not alter selected task ordering.
- Do not add live executor behavior, code mutation, queueing, or remote
  orchestration.

## Test Strategy

- Add an `action_for_task()` regression test for
  `autonomy_selection_gap`/`improve_fallback_diversity`.
- Assert the action remains `loop_health_plan`, keeps the existing commands,
  and includes `.qa-z/loops/history.jsonl` in `context_paths`.
- Run that test before implementation to confirm the missing context.
- Run focused autonomy/current-truth tests and then the full alpha gate suite.

## Documentation

Update README, artifact schema notes, current-state analysis, roadmap, commit
plan, and current-truth assertions to say loop-health prepared actions carry
evidence `context_paths` for fallback diversity diagnostics.
