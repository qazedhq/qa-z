# Executor Bridge Action Context Benchmark Design

## Purpose

Executor bridge packages now copy prepared repair-session action
`context_paths` into bridge-local `inputs/context/` files. Unit tests pin that
behavior, but the committed benchmark corpus does not yet prove it. That leaves
the alpha evidence set thinner than the implementation surface.

This pass adds a deterministic benchmark fixture for loop-sourced executor
bridges with action context inputs.

## Scope

- Add an `expect_executor_bridge` expectation section to benchmark contracts.
- Add a `run.executor_bridge` fixture path that creates a repair session,
  writes a minimal loop outcome with a `repair_session` action and
  `context_paths`, packages a bridge from that loop, and summarizes the bridge
  manifest.
- Add a committed fixture that first runs local verification to materialize
  `.qa-z/runs/candidate/verify/summary.json`, then verifies that the bridge
  copies that file into `inputs/context/`.
- Count executor-bridge expectations as artifact coverage.
- Update benchmark and current-truth documentation to mention the new fixture.

## Behavior

A fixture can declare:

```json
{
  "run": {
    "verify": {
      "baseline_run": ".qa-z/runs/baseline",
      "candidate_run": ".qa-z/runs/candidate"
    },
    "executor_bridge": {
      "baseline_run": ".qa-z/runs/baseline",
      "session_id": "session-bridge-context",
      "bridge_id": "bridge-context",
      "loop_id": "loop-bridge-context",
      "context_paths": [".qa-z/runs/candidate/verify/summary.json"]
    }
  },
  "expect_executor_bridge": {
    "action_context_count": 1,
    "action_context_paths": [".qa-z/runs/candidate/verify/summary.json"],
    "action_context_copied_paths": [
      ".qa-z/executor/bridge-context/inputs/context/001-summary.json"
    ],
    "action_context_missing_count": 0,
    "action_context_files_exist": true,
    "guide_mentions_action_context": true
  }
}
```

The benchmark runner executes `verify` before `executor_bridge`, so the context
file exists when bridge packaging runs.

## Non-Goals

- Do not add live executor execution or executor-result ingest to this fixture.
- Do not benchmark missing context paths in this pass.
- Do not change the executor bridge schema version.
- Do not make benchmark fixtures depend on live Semgrep, TypeScript, or Python
  tool installations.

## Test Strategy

- Add a unit test proving `expect_executor_bridge` participates in
  `compare_expected()`.
- Add a committed-corpus assertion for
  `executor_bridge_action_context_inputs`.
- Add the fixture and run it first as a selected benchmark to confirm the
  missing runner support.
- Implement the minimal runner support and rerun the selected fixture.
- Run focused benchmark/current-truth tests, then the full alpha gate.

## Documentation

Update `docs/benchmarking.md`, README, current-state analysis, roadmap,
worktree commit plan, and current-truth tests with the new fixture name and the
new full benchmark count.
