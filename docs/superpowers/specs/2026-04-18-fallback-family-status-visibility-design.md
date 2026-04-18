# Fallback Family Status Visibility Design

## Purpose

QA-Z already records `selected_fallback_families` in autonomy outcomes and loop
history. Self-inspection can then promote repeated fallback-family reuse into an
`autonomy_selection_gap`. The latest status and saved loop plan still make an
operator infer that family context from individual selected tasks and penalty
reasons.

This pass surfaces the recorded selected fallback families directly in autonomy
status and loop plans.

## Scope

- Reuse the existing `selected_fallback_families` list from `outcome.json`.
- Add `latest_selected_fallback_families` to `qa-z autonomy status --json`.
- Print selected fallback families in human `qa-z autonomy status` output when
  present.
- Print selected fallback families in saved autonomy loop plans when present.
- Keep scoring, selection, fallback penalties, backlog candidate generation, and
  action packet mapping unchanged.

## Behavior

Autonomy status JSON gains an additive field:

```json
{
  "latest_selected_fallback_families": ["cleanup"]
}
```

Human status gains:

```text
Selected fallback families: cleanup
```

Saved loop plans gain:

```text
- Selected fallback families: `cleanup`
```

When no selected fallback families are recorded, the fields stay empty or the
human line is omitted.

## Non-Goals

- Do not change the fallback-family penalty algorithm.
- Do not add new fallback families.
- Do not alter backlog priority scores or selected task ordering.
- Do not introduce a live executor, remote orchestration, or code editing loop.
- Do not change existing outcome or history field names.

## Test Strategy

- Add a status JSON regression assertion that `load_autonomy_status()` exposes
  the latest outcome fallback families.
- Add a human status rendering test for the new fallback-family line.
- Add a loop-plan rendering test for the new fallback-family line.
- Run focused autonomy and current-truth tests, then the full alpha gate suite.

## Documentation

Update README, artifact schema notes, current-state analysis, roadmap, commit
plan, and current-truth assertions to say autonomy status and loop plans mirror
selected fallback families for repeated-selection diagnostics.
