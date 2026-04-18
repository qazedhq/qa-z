# QA-Z MVP Issues

This file tracks the first public slice of work as issue-sized deliverables.

## Alpha Foundation Scope

Goal: ship a deterministic local QA loop that can reproduce:

```text
init -> plan -> fast -> deep -> review --from-run -> repair-prompt -> verify
```

Included:

- `init`, `plan`, `fast`, `deep`, `review`, `repair-prompt`, and `verify`
- Python and TypeScript command-based fast checks
- full and smart fast/deep selection
- Semgrep-backed deep execution
- normalized deep findings and SARIF output
- JSON and Markdown run artifacts
- run-aware review packets
- repair packet and normalized handoff artifacts
- post-repair verification comparison
- seeded benchmark corpus for fast, deep, handoff, and verification behavior`n- artifact-driven self-inspection, improvement backlog, selected next-task planning, and local autonomy loop artifacts
- tests and local CI examples

Excluded until later milestones:

- live model execution
- remote orchestration or automatic code repair
- GitHub API mutation surfaces
- deep engines beyond Semgrep
- autonomous code editing loops

## Alpha Issue Queue

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

- Semgrep-backed deep runner
- SARIF output for normalized deep findings
- Repair handoff artifacts for Codex and Claude prompt renderers
- Post-repair verification comparison
- Benchmark corpus for TypeScript fast checks and Semgrep deep policy cases

## Issue 1: Diff and context intake

- Goal: ingest issue text, spec docs, and git diff metadata into a single planning context.
- Acceptance: a planner object can normalize issue, diff, and spec inputs into one payload.
- Status: bootstrap context intake landed through `qa-z plan`; diff parsing groundwork also supports smart runner selection.

## Issue 2: Contract extraction v1

- Goal: derive scope, assumptions, invariants, risk edges, negative cases, and acceptance checks.
- Acceptance: QA-Z can render a contract document into `qa/contracts/`.
- Status: bootstrap slice landed with `qa-z plan`; next step is richer diff-aware extraction.

## Issue 3: Fast runner orchestration

- Goal: run lint, typecheck, and unit checks based on configured language commands.
- Acceptance: `qa-z fast` executes configured fast checks and returns a summarized result.
- Status: Python and TypeScript command-based fast checks are supported through explicit subprocess checks. Fast runs write JSON/Markdown artifacts, latest-run manifests, and schema v2 selection metadata when selection context exists.

## Issue 4: Reporter pipeline

- Goal: emit Markdown, SARIF, and machine-readable artifacts from runner output.
- Acceptance: one runner invocation can produce Markdown plus one machine-readable format.
- Status: `qa-z fast` and `qa-z deep` emit summary artifacts; `qa-z review --from-run` can include fast run verdicts, selection context, executed checks, failed-check evidence, and sibling deep findings. `qa-z deep` emits SARIF 2.1.0 from normalized deep findings.

## Issue 5: Repair packet generation

- Goal: compress failures into an agent-friendly repair prompt packet.
- Acceptance: QA-Z produces a structured payload with failures, impacted files, and next validation criteria.
- Status: `qa-z repair-prompt` builds packet and prompt artifacts from failed fast checks and blocking deep findings, carries selection context, and writes normalized `handoff.json`, `codex.md`, and `claude.md` artifacts without live execution.

## Issue 6: Python command support

- Goal: support deterministic Python lint, type, format, and test commands.
- Acceptance: configured Python checks run as subprocesses and normalize no-tests, missing-tool, and non-zero exit behavior.
- Status: Python command support is functional through the fast runner.

## Issue 7: TypeScript command support

- Goal: support deterministic TypeScript lint, type, and test commands.
- Acceptance: configured TypeScript checks can run through the same deterministic fast-runner contract.
- Status: TypeScript command examples are included in `qa-z.yaml.example`; runner selection can target TypeScript paths and common TypeScript config files.

## Issue 8: Security/deep checks

- Goal: wire at least one deep static-analysis command into the deep-check layer.
- Acceptance: QA-Z can run a configured deep command and normalize its output.
- Status: Semgrep-backed `sg_scan` is functional. QA-Z normalizes active findings, grouped findings, severity thresholds, ignored rules, excluded paths, and missing-tool behavior.

## Issue 9: Codex handoff renderer

- Goal: produce Codex-friendly prompts and handoff artifacts from deterministic repair evidence.
- Acceptance: repo ships a Codex-facing Markdown renderer derived from the same normalized handoff JSON.
- Status: `qa-z repair-prompt --adapter codex` renders `codex.md` and always writes `handoff.json` with validation commands and non-goals.

## Issue 10: Claude handoff renderer

- Goal: produce Claude-friendly prompts and handoff artifacts from deterministic repair evidence.
- Acceptance: repo ships a Claude-facing Markdown renderer derived from the same normalized handoff JSON.
- Status: `qa-z repair-prompt --adapter claude` renders `claude.md` and shares the normalized handoff contract.

## Issue 11: Example repositories

- Goal: add realistic examples that exercise fast, deep, repair, and verification policy modes.
- Acceptance: examples show deterministic local commands with explicit policy.
- Status: Python examples remain the primary runnable path. TypeScript command examples are present in the config surface; additional runnable example hardening remains future work.

## Issue 12: Verification loop

- Goal: compare a pre-repair run with a post-repair run and decide whether deterministic QA evidence improved.
- Acceptance: `qa-z verify` writes summary, compare, and report artifacts, classifies resolved, still-failing, regressed, newly introduced, and not-comparable evidence, and returns a deterministic verdict.
- Status: `qa-z verify` is functional for existing candidate runs and can create a candidate with `--rerun` using the existing fast and deep runners.


## Issue 13: Benchmark corpus

- Goal: measure QA-Z behavior against deterministic fixture repositories.
- Acceptance: `qa-z benchmark` discovers fixtures, runs selected local QA-Z flows, compares observed artifacts with `expected.json`, and writes summary/report artifacts.
- Status: seeded corpus covers Python fast failures, TypeScript fast failures, Semgrep deep policy cases, repair handoff generation, and post-repair verification comparisons.
## Issue 14: Self-improvement backlog

- Goal: turn existing QA-Z artifacts back into a prioritized improvement queue for future local improvement loops.
- Acceptance: `qa-z self-inspect` writes a self-inspection report and backlog, `qa-z select-next` writes selected-task and loop-plan artifacts, and `qa-z backlog --json` prints the current queue.
- Status: artifact-driven self-inspection, backlog scoring, task selection, and JSONL loop memory are implemented without live model execution, remote orchestration, or autonomous code editing.
## Issue 15: Autonomy planning loops

- Goal: make QA-Z repeat the local self-inspection and task-selection workflow while preserving loop outcomes, status, and runtime-budget evidence.
- Acceptance: `qa-z autonomy` writes per-loop outcome artifacts, mirrors latest loop state, records runtime progress, and `qa-z autonomy status --json` exposes the latest planning state.
- Status: local artifact-only autonomy planning loops are implemented without live model execution, remote orchestration, external repair dispatch, or autonomous code editing.

## Issue 16: Repair sessions

- Goal: package repair handoff evidence into a named local session with an explicit return path for candidate verification.
- Acceptance: `qa-z repair-session start`, `status`, and `verify` write session manifests, handoff artifacts, verification artifacts, and outcome summaries from deterministic local evidence.
- Status: local repair sessions are implemented without live model execution, remote dispatch, or hidden network dependencies.

## Issue 17: GitHub summary publishing

- Goal: render QA-Z run and verification evidence into GitHub Actions job summaries without adding GitHub API mutation surfaces.
- Acceptance: `qa-z github-summary` renders Markdown and JSON from run, verify, or repair-session artifacts, and workflow examples append the Markdown to `$GITHUB_STEP_SUMMARY`.
- Status: local summary rendering is implemented; comments, labels, Checks API annotations, and hosted status mutations remain out of scope.
