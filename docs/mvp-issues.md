# QA-Z MVP Issues

This file tracks the first public slice of work as issue-sized deliverables.

## v0.1.0-alpha Scope

Goal: ship a Python-first vertical slice that can reproduce:

```text
init -> plan -> fast -> review --from-run -> repair-prompt
```

Included:

- `init`, `plan`, `fast`, `review`, and `repair-prompt`
- a clear `deep` placeholder
- Python fast runner
- JSON and Markdown artifacts
- tests and CI
- one runnable Python workflow example

Excluded until later milestones:

- TypeScript runner
- real `deep` execution
- SARIF and GitHub annotations
- live Codex or Claude runtime adapters
- benchmark corpus and quantitative success metrics

## Alpha Backlog

### P0

- Initial commit and repository baseline
- CI for `python -m pytest` and `python -m qa_z fast`
- Artifact schema v1 documentation and schema stability tests
- Run-aware review flow documentation
- Example Python workflow with passing and failing repair loops

### P1

- Diff parser groundwork
- Changed-files-aware fast selection
- Additional failure-mode tests
- README product positioning improvements

### P2

- Release notes draft for `v0.1.0-alpha`
- CONTRIBUTING and development workflow docs
- Issue templates and default label guidance

## Issue 1: Diff and context intake

- Goal: ingest issue text, spec docs, and git diff metadata into a single planning context.
- Acceptance: a planner object can normalize issue, diff, and spec inputs into one payload.

## Issue 2: Contract extraction v1

- Goal: derive scope, assumptions, invariants, risk edges, negative cases, and acceptance checks.
- Acceptance: QA-Z can render a contract document into `qa/contracts/`.
- Status: bootstrap slice landed with `qa-z plan`; next step is richer diff-aware extraction.

## Issue 3: Fast runner orchestration

- Goal: run lint, typecheck, and unit checks based on configured language plugins.
- Acceptance: `qa-z fast` executes configured fast checks and returns a summarized result.
- Status: Python-only vertical slice landed with explicit subprocess checks, JSON/Markdown run artifacts, and documented exit codes. TypeScript and deeper selection remain future work.

## Issue 4: Reporter pipeline

- Goal: emit Markdown, SARIF, and GitHub-friendly annotations from runner output.
- Acceptance: one runner invocation can produce at least Markdown plus one machine-readable format.
- Status: bootstrap slice landed with markdown and JSON review-packet output from `qa-z review`; `qa-z review --from-run` can include fast run verdicts, executed checks, and failed-check evidence. `qa-z fast` emits JSON plus Markdown run summaries. SARIF and annotation output remain next.

## Issue 5: Repair packet generation

- Goal: compress failures into an agent-friendly repair prompt packet.
- Acceptance: QA-Z produces a structured payload with failures, impacted files, and next questions.
- Status: first repair loop landed with `qa-z repair-prompt`, shared run/contract artifact loading, deterministic candidate file extraction, suggested fix ordering, and `packet.json` plus `prompt.md` artifacts.

## Issue 6: Python plugin

- Goal: support pytest, Hypothesis, and mutmut selection for Python repositories.
- Acceptance: plugin can map configured checks into concrete Python commands.

## Issue 7: TypeScript plugin

- Goal: support Vitest or Jest, fast-check, Stryker, and Playwright smoke tests.
- Acceptance: plugin can map configured checks into concrete TypeScript commands.

## Issue 8: Security plugin

- Goal: wire CodeQL, Semgrep, and Trivy into the deep-check layer.
- Acceptance: QA-Z can run at least one security command and normalize its output.

## Issue 9: Codex adapter

- Goal: produce Codex-friendly prompts, review packets, and repository templates.
- Acceptance: repo ships a working review prompt and adapter-facing contract output shape.

## Issue 10: Claude adapter

- Goal: produce CLAUDE.md guidance, skills, and hook integration points.
- Acceptance: repo ships reusable Claude templates that match QA-Z contract stages.

## Issue 11: Example repositories

- Goal: add one FastAPI demo and one Next.js demo.
- Acceptance: examples show both fast and deep policy modes with realistic config.

## Issue 12: Benchmark seed set

- Goal: define a seeded bug corpus and usefulness metrics for QA-Z evaluation.
- Acceptance: benchmark folder contains at least an initial case taxonomy and expected outputs.
