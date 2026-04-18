# FastAPI Demo Deterministic Boundary Design

## Context

`examples/fastapi-demo` is the runnable Python example. It is intentionally
dependency-light: the service exposes pure functions, works without installing a
web server, and optionally creates a `FastAPI` app only when `fastapi` is
available. Its standard and failing configs exercise deterministic Python fast
checks plus review and repair-prompt artifacts. Both configs keep
`checks.deep` empty.

The example README already says the failing run is intentional and provides
deterministic evidence. It does not yet explicitly pin the same live-free and
fast-only boundary now used by the TypeScript demo and workflow template docs.

## Goal

Pin the FastAPI-shaped example as a dependency-light deterministic fast and
repair-prompt demo, not a mandatory web-server, deep automation, live executor,
or repair-session workflow.

## Non-Goals

- Do not change the example app code.
- Do not add FastAPI as a required dependency.
- Do not add deep checks to the example configs.
- Do not add repair-session, executor-bridge, executor-result, live agents,
  commits, pushes, or GitHub bot behavior to the example.
- Do not change the existing passing or failing example flows.

## Design

### Example README Boundary

`examples/fastapi-demo/README.md` should explicitly state:

- it is dependency-light
- it works without installing a web server
- it is a deterministic fast and repair-prompt demo
- it does not configure deep checks
- it does not call live agents
- it does not run `repair-session`, `executor-bridge`, or `executor-result`

The existing passing and failing command blocks should remain unchanged because
they already match the example contract.

### Tests

Extend `tests/test_examples.py` with a focused README/config guard:

- parse `qa-z.yaml`
- parse `qa-z.failing.yaml`
- assert the standard fast check ids remain `py_lint`, `py_format`, `py_test`
- assert the failing fast check ids include `py_test_bug_demo`
- assert both configs keep `checks.deep` empty
- assert the README contains the dependency-light, no-web-server, deterministic,
  no-deep, no-live-agent, and no-executor/reair-session boundary language

The first run should fail before the README text is updated.

### Reports

Update `docs/reports/current-state-analysis.md` and
`docs/reports/next-improvement-roadmap.md` so report/template/example sync now
records the FastAPI demo deterministic boundary sync pass. Add a current-truth
test so stale reports cannot treat this as unlanded.

## Success Criteria

- The focused example/current-truth tests fail before docs are updated.
- `examples/fastapi-demo/README.md` states the deterministic fast/repair-prompt
  boundary.
- Reports record the FastAPI demo deterministic boundary sync pass.
- Focused tests pass.
- Full pytest passes.
- Benchmark still passes.
