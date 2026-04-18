# Executor Bridge Stdout Benchmark Parity Design

## Purpose

Human `qa-z executor-bridge` stdout now reports action-context package health and
missing action-context diagnostics. Unit tests pin that CLI behavior, and bridge
fixtures already pin manifest and guide diagnostics. The benchmark corpus,
however, still summarizes only the manifest and guide text for executor bridge
fixtures, so stdout diagnostic drift would not appear in benchmark results.

This pass extends the existing executor-bridge benchmark summary to treat the
human stdout rendering as first-class observed evidence.

## Scope

- Reuse `render_bridge_stdout(manifest)` inside the benchmark executor-bridge
  summarizer.
- Record whether stdout mentions the copied action-context count when copied
  paths exist.
- Record whether stdout mentions missing action context when skipped optional
  context paths exist.
- Pin those fields in the two existing executor bridge action-context fixtures.
- Keep fixture count unchanged and avoid adding a new bridge schema field.

## Behavior

For `executor_bridge_action_context_inputs`, benchmark actual output should
include:

```json
{
  "stdout_mentions_action_context": true
}
```

For `executor_bridge_missing_action_context_inputs`, benchmark actual output
should include:

```json
{
  "stdout_mentions_action_context": true,
  "stdout_mentions_missing_action_context": true
}
```

The copied-context check should require the exact count line because stdout is a
compact human surface and does not list copied context paths. The
missing-context check should require both the human heading text and each
missing path so a count-only line does not accidentally pass.

## Non-Goals

- Do not add new fixtures; use the existing bridge action-context fixtures.
- Do not change `bridge.json`, executor guides, or CLI JSON output.
- Do not introduce live executor calls, network dependencies, scheduling,
  commits, pushes, or GitHub comments.

## Test Strategy

- Update expected fixture contracts first so the selected benchmark fixture
  fails while the benchmark summarizer lacks stdout fields.
- Add corpus assertions that the committed bridge fixtures require stdout
  diagnostic parity.
- Implement the summarizer fields and rerun the selected bridge fixture.
- Run focused benchmark/current-truth tests, then the full alpha gate suite.

## Documentation

Update README, benchmarking docs, roadmap/current-state notes, worktree commit
plan, and current-truth assertions to say benchmark executor-bridge fixtures pin
human stdout diagnostics as well as manifest and guide diagnostics.
