# TypeScript Demo Live-Free Boundary Design

## Context

The repository now has a runnable `examples/typescript-demo` and a separate
`examples/nextjs-demo` placeholder. The TypeScript demo is intentionally small:
it exercises the landed TypeScript fast gate with ESLint, `tsc --noEmit`, and
Vitest. Its `qa-z.yaml` keeps `checks.deep` empty.

The main docs and reports already say TypeScript fast checks are landed while
TypeScript-specific deep automation, live executor calls, remote orchestration,
and automatic repair remain out of scope for the alpha baseline. The example
README should say the same thing so users do not infer that the TypeScript demo
is also a Next.js example, a TypeScript deep QA example, or a live executor
workflow.

## Goal

Pin the TypeScript demo as a runnable fast-only, live-free example.

## Non-Goals

- Do not add new TypeScript checks.
- Do not make the Next.js placeholder runnable.
- Do not add TypeScript-specific deep automation.
- Do not add executor-bridge, executor-result, live agent, queue, scheduler,
  commit, push, or GitHub bot behavior to the example.
- Do not change the example source or package behavior.

## Design

### Example README Boundary

`examples/typescript-demo/README.md` should explicitly state:

- it is a runnable TypeScript fast gate demo
- it is a fast-only demo
- it is not a Next.js demo
- it does not configure TypeScript-specific deep automation
- it does not call live agents
- it does not run `executor-bridge` or `executor-result`

The README should continue to show the existing `npm install`, `qa-z plan`, and
`qa-z fast --selection smart` commands. It should avoid adding `qa-z deep` to
the command block because the demo's config intentionally leaves `checks.deep`
empty.

### Tests

Extend `tests/test_examples.py` with a focused README/config guard:

- parse `examples/typescript-demo/qa-z.yaml`
- assert the configured fast check ids remain `ts_lint`, `ts_type`, `ts_test`
- assert `checks.deep` remains empty
- assert the README includes the fast-only, not-Next.js, no-TypeScript-deep, and
  no-live-executor boundary language

This should fail before the README text is updated.

### Reports

Update `docs/reports/current-state-analysis.md` and
`docs/reports/next-improvement-roadmap.md` to record the TypeScript demo
live-free boundary sync pass under the report/template/example sync lane. Add a
current-truth test so reports do not drift back into treating example sync as
unlanded.

## Success Criteria

- The focused example/current-truth tests fail before docs are updated.
- `examples/typescript-demo/README.md` says the demo is fast-only and live-free.
- Reports record the TypeScript demo live-free boundary sync pass.
- Focused tests pass.
- Full pytest passes.
- Benchmark still passes.
