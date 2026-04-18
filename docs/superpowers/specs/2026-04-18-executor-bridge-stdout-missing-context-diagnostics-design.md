# Executor Bridge Stdout Missing Context Diagnostics Design

## Purpose

Executor bridge packaging already records copied action context under
`inputs.action_context` and skipped optional context paths under
`inputs.action_context_missing`. The executor-facing guides also call out
missing action context, but the default human `qa-z executor-bridge` stdout only
prints bridge, return-contract, safety, and verification pointers.

That leaves operators with a small visibility gap: they can create a bridge that
quietly skipped optional context inputs, then only notice after opening
`bridge.json` or an executor guide. This pass keeps the manifest unchanged and
adds the same diagnostic to the first human CLI surface.

## Scope

- Show copied action-context input count in human executor-bridge stdout when
  action context was copied.
- Show skipped/missing action-context input count and paths in human
  executor-bridge stdout when optional context paths were missing.
- Preserve current JSON output exactly; `--json` remains the machine-readable
  manifest.
- Keep missing action context non-fatal because these paths are optional
  supporting evidence, not required bridge inputs.
- Keep executor guides, Codex docs, Claude docs, and bridge manifests aligned
  with the existing behavior.

## Behavior

For a bridge with one copied context file and one missing optional context file,
human stdout should include lines equivalent to:

```text
Action context inputs: 1
Missing action context: 1 (.qa-z/runs/candidate/verify/missing-context.json)
```

The copied count gives a fast package-health check. The missing line names the
skipped source path so an operator can decide whether to regenerate evidence,
continue without it, or inspect the loop outcome.

For bridges without action context, stdout remains focused on the existing
return pointers and safety package details.

## Non-Goals

- Do not change `bridge.json` schema or add a new schema version.
- Do not make missing optional context a bridge creation failure.
- Do not add live executor calls, retries, scheduling, commits, pushes, or
  GitHub comments.
- Do not change executor-result ingest or repair-session verification
  semantics.

## Test Strategy

- Add a CLI stdout regression test that mutates a loop-prepared repair-session
  action to include one present context file and one missing context file.
- Assert the human stdout reports copied action-context input count.
- Assert the human stdout reports missing action-context count and skipped path.
- Run focused executor-bridge/current-truth tests, then the full alpha gate
  suite.

## Documentation

Update README and current-state notes so the public truth says human
executor-bridge output includes action-context package health and missing-context
diagnostics without claiming live executor automation.
