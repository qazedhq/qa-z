# Repair Session Action Context Bridge Inputs Design

## Purpose

QA-Z autonomy can prepare a local `repair_session` action when verification
evidence identifies a baseline run. The repair-session action already records
the session, handoff, and validation commands, but it does not preserve the
selected task evidence paths that explain why the session was created.

Executor bridge packaging then copies the loop outcome, session, handoff, and
safety package into `.qa-z/executor/<bridge-id>/inputs/`, but it has no
bridge-local copy of action-specific context paths. This leaves an external
executor with enough repair mechanics but a thinner evidence trail.

This pass keeps the existing live-free boundary while carrying repair-session
action context into the bridge package as copied local evidence inputs.

## Scope

- Add selected task evidence `context_paths` to autonomy-created
  `repair_session` actions.
- Copy existing file context paths from the selected `repair_session` action
  into executor bridge `inputs/context/`.
- Record copied context input metadata in `bridge.json` without changing the
  existing schema version.
- Mention the copied context inputs in executor guides.
- Keep missing or non-file context paths non-fatal and record them as skipped
  context paths.
- Keep manually-created `--from-session` bridges unchanged except for an empty
  context input field.

## Behavior

When a selected verification regression task carries evidence such as:

```json
{
  "evidence": [
    {"path": ".qa-z/runs/candidate/verify/summary.json"},
    {"path": ".qa-z/runs/candidate/verify/compare.json"}
  ]
}
```

the prepared repair-session action should include:

```json
{
  "type": "repair_session",
  "context_paths": [
    ".qa-z/runs/candidate/verify/compare.json",
    ".qa-z/runs/candidate/verify/summary.json"
  ]
}
```

The bridge manifest should then include bridge-local copies:

```json
{
  "inputs": {
    "action_context": [
      {
        "source_path": ".qa-z/runs/candidate/verify/compare.json",
        "copied_path": ".qa-z/executor/bridge-one/inputs/context/001-compare.json"
      }
    ],
    "action_context_missing": []
  }
}
```

The copy names are deterministic and include an ordinal plus the source file
name. If two source files share a name, the ordinal still keeps the copied
paths unique.

## Non-Goals

- Do not package directories or arbitrary external absolute paths.
- Do not make context path copying a hard failure for otherwise valid bridge
  packages.
- Do not add live Codex or Claude calls, background queues, scheduling,
  commits, pushes, or GitHub comments.
- Do not change repair-session verification or executor-result ingest
  semantics.

## Test Strategy

- Add an autonomy regression test proving `repair_session` actions include
  selected task evidence `context_paths`.
- Add an executor bridge regression test proving loop-sourced bridges copy
  `repair_session` action context files into `inputs/context/` and record them
  in `bridge.json`.
- Add guide assertions so the human bridge guide points at copied action
  context inputs.
- Run focused tests before and after implementation, then the full alpha gate
  suite.

## Documentation

Update README, artifact schema, current-state analysis, roadmap, commit plan,
and current-truth assertions so alpha status documents the new bridge-local
action context inputs without claiming live executor automation.
