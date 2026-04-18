# Next.js Placeholder Boundary Sync Design

## Goal

Keep `examples/nextjs-demo` honest as a placeholder-only example until it contains a real package, QA-Z config, source, tests, and deterministic expected commands.

## Current Evidence

`examples/nextjs-demo` currently contains only `README.md`. The README says the directory is not wired and points users to `examples/typescript-demo`, but it does not explicitly pin the same live-free and executor-boundary language used by the runnable FastAPI and TypeScript demos. `docs/mvp-issues.md` also still lists the original FastAPI plus Next.js example goal without a current status note, which can make the placeholder look more complete than it is.

## Design

Add a current-truth sync pass for the Next.js placeholder:

- strengthen the example test so the directory is required to remain README-only until a real runnable demo lands
- require the placeholder README to say it is placeholder-only, not a runnable Next.js project, and does not include `package.json` or `qa-z.yaml`
- require the placeholder README to say it does not call live agents and does not run `executor-bridge` or `executor-result`
- update `docs/mvp-issues.md` so Issue 11 distinguishes the landed FastAPI demo, the landed TypeScript fast-only demo, and the non-runnable Next.js placeholder
- update report-style docs so the roadmap and current-state analysis name the Next.js placeholder live-free boundary sync pass

No CLI, runner, benchmark, or template behavior changes are needed.

## Non-Goals

- Do not scaffold a real Next.js project.
- Do not add package files, source files, tests, or a QA-Z config to `examples/nextjs-demo`.
- Do not claim TypeScript-specific deep automation exists.
- Do not add live executor behavior.

## Acceptance

The focused example/current-truth tests fail before the README and docs are updated, then pass after the sync. Full `python -m pytest` and `python -m qa_z benchmark --json` remain green.
