# QA-Z MVP Issues

This file tracks the first public slice of work as issue-sized deliverables.

Historical note: the early milestone sections below record the scope at the time
they were written. For current public capability, product direction, and
validation gates, use the root README and `docs/product/` documents as the
current-truth sources.

## Public Launch Productization Slice

Goal: make the public repository immediately legible to developers who use AI
coding agents and want deterministic merge evidence.

Included:

- README first screen repositioned around "The safety belt for AI-generated
  code."
- Five-minute `examples/agent-auth-bug` demo showing an unsafe auth refactor
  caught by QA-Z.
- Quickstart, comparison, GitHub Action, Codex, Claude Code, Cursor, launch
  package, and launch-post docs.
- Social preview upload asset under `docs/assets/qa-z-social-preview.png`
  with editable source at `docs/assets/qa-z-social-preview.svg`.
- Good-first-issue seeds and topic recommendations in `docs/launch-package.md`.

Still external to the local repository:

- GitHub social preview upload.
- Repository topic mutation.
- Opening public GitHub issues.
- Publishing a standalone `qazedhq/qa-z-action@v0` repository.

## v0.1.0-alpha Scope

Goal: ship a Python-first vertical slice that can reproduce:

```text
init -> plan -> fast -> review --from-run -> repair-prompt
```

Included:

- `init`, `plan`, `fast`, `review`, and `repair-prompt`
- a clear `deep` placeholder, now advanced in mainline to a skeleton artifact writer
- Python fast runner
- JSON and Markdown artifacts
- tests and CI
- one runnable Python workflow example

Excluded until later milestones:

- TypeScript runner
- real `deep` check execution
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

- Diff parser groundwork and contract changed-file metadata
- Changed-files-aware Python fast selection
- `summary.json` v2 selection evidence
- Review and repair packet selection context
- Additional failure-mode tests
- README product positioning improvements

### P2

- Release notes draft for `v0.1.0-alpha`
- CONTRIBUTING and development workflow docs
- Issue templates and default label guidance

## v0.2.0-beta Scope

Goal: extend the reproducible fast loop into mixed Python and TypeScript repositories:

```text
init -> plan -> fast --selection smart -> review --from-run -> repair-prompt -> github-summary
```

Included:

- TypeScript fast check ids: `ts_lint`, `ts_type`, and `ts_test`
- TypeScript changed-file classification for `.ts`, `.tsx`, `.cts`, and `.mts`
- smart selection for TypeScript lint and Vitest tests
- conservative full `tsc --noEmit` type checks
- GitHub workflow artifact upload for `.qa-z/runs`
- compact GitHub Actions Job Summary output with optional repair outcome publishing
- failure-preserving CI flow that still writes review and repair artifacts

Excluded until later milestones:

- TypeScript deep QA automation
- SARIF and GitHub annotations
- framework-specific TypeScript adapters
- live Codex or Claude runtime adapters
- benchmark corpus

## v0.3.0-alpha Deep GitHub Flow

Goal: integrate the Semgrep-backed deep slice into the full QA-Z GitHub flow:

```text
fast -> deep -> review --from-run -> repair-prompt -> github-summary
```

Included:

- `sg_scan` Semgrep subprocess execution when configured under `deep.checks`
- Semgrep JSON parsing into normalized QA-Z findings
- `deep/checks/sg_scan.json` per-check artifacts
- failed status when Semgrep reports one or more findings
- evidence-preserving artifacts when Semgrep fails before producing valid JSON
- smart deep selection for docs-only skips, source/test targeting, and conservative full-scan escalation
- review, repair-prompt, and GitHub summary consumption of sibling deep findings
- GitHub workflows that run fast, deep, review, repair-prompt, and github-summary in order
- artifact upload even when fast or deep fails
- final GitHub job failure based on the preserved fast and deep exit codes

Excluded until later milestones:

- SARIF and GitHub annotations
- CodeQL, Trivy, property, mutation, or smoke-test engines
- automatic local Semgrep installation by QA-Z

## v0.3.1-alpha Deep Policy Hardening

Goal: make the Semgrep-backed deep runner practical as an always-on CI gate by reducing noise while preserving deterministic evidence.

Included:

- Semgrep severity thresholds through `semgrep.fail_on_severity`
- custom Semgrep config through `semgrep.config`
- grouped findings by `rule_id`, `path`, and `severity`
- path suppression through `deep.selection.exclude_paths`
- rule suppression through `semgrep.ignore_rules`
- artifact fields for total, blocking, filtered, severity, grouped, and active findings
- review, repair-prompt, and GitHub summary rendering that prefers grouped findings when available

Excluded until later milestones:

- SARIF and GitHub annotations
- AI-based finding reclassification
- multi-engine deep orchestration
- rule auto-tuning

## v0.4.0-alpha SARIF and GitHub Code Scanning

Goal: make the Semgrep-backed deep findings consumable by GitHub code scanning without changing the existing fast/deep/review/repair flow.

Included:

- SARIF 2.1.0 generation from normalized deep Semgrep findings
- `deep/results.sarif` written beside every deep summary artifact
- optional `qa-z deep --sarif-output <path>` copy path for CI systems that require a stable SARIF filename
- severity mapping from QA-Z/Semgrep severities to SARIF levels
- grouped-finding fallback for older or compact deep artifacts
- GitHub workflow upload through `github/codeql-action/upload-sarif@v4`
- job-level `security-events: write` permissions in shipped workflow examples

Excluded until later milestones:

- standalone `::warning` workflow-command annotations
- Checks API review annotations
- SARIF output for non-Semgrep deep engines
- auto-installation or auto-configuration of GitHub code scanning

## v0.5.0-alpha Repair Adapter Handoff

Goal: make QA-Z produce deterministic repair handoff artifacts that Codex and Claude style executors can consume without adding live orchestration.

Included:

- normalized `handoff.json` repair contract generated by `qa-z repair-prompt`
- selected repair targets from failed fast checks and blocking deep findings
- affected-file, constraint, non-goal, provenance, and validation command sections
- `codex.md` action-oriented executor prompt
- `claude.md` explanatory executor prompt with explicit workflow and non-goals
- `qa-z repair-prompt --adapter codex`, `--adapter claude`, and `--handoff-json`

Excluded until later milestones:

- live Codex or Claude API calls
- scheduler, queue, or remote execution controller
- remote or agent-driven post-repair orchestration
- executor-specific logic inside the core planner

## v0.6.0-alpha Post-Repair Verification

Goal: make QA-Z evaluate whether a claimed repair improved the repository state by comparing baseline and candidate run artifacts.

Included:

- `qa-z verify --baseline-run <run> --candidate-run <run>` comparison command
- optional `qa-z verify --baseline-run <run> --rerun` candidate creation through existing deterministic fast and deep runners
- fast check delta classification for resolved, still failing, regressed, newly introduced, and skipped or non-comparable checks
- conservative deep finding identity with strict and relaxed matching
- blocking deep finding comparison based on recorded `semgrep.fail_on_severity` policy
- `verify/summary.json`, `verify/compare.json`, and `verify/report.md` artifacts
- deterministic final verdicts: `improved`, `unchanged`, `mixed`, `regressed`, and `verification_failed`

Excluded until later milestones:

- live Codex or Claude API calls
- scheduler, queue, or remote execution controller
- GitHub bot comments from verification results
- new deep engines or speculative root-cause inference
- autonomous code repair

## v0.7.0-alpha Benchmark Corpus

Goal: make QA-Z behavior measurable across seeded fixtures before adding orchestration or live executor integrations.

Included:

- top-level `benchmarks/fixtures` corpus with fast, deep, mixed, and verification cases
- TypeScript fast benchmark fixtures for `ts_lint`, `ts_type`, `ts_test`, multiple simultaneous fast failures, and TypeScript verification verdicts
- mixed-language verification fixtures for Python and TypeScript cross-regression, all-resolved, and partial-resolved-with-regression verdicts
- mixed-surface realism fixtures for executed fast/handoff cleanup work, docs/schema maintenance, cleanup-only unchanged verification, and partial or justified no-op executor-result cases
- executor-result benchmark fixtures that exercise `repair-session`, `executor-bridge`, and `executor-result ingest` with attached mixed-language candidate verification
- deep policy benchmark fixtures for Semgrep severity thresholds, ignored rules, excluded paths, grouping, filtered/blocking count consistency, and config-error surfacing
- explicit fixture `expected.json` contracts for fast failures, Semgrep rule ids, repair handoff properties, and verification verdicts
- `qa-z benchmark` runner that copies fixtures into isolated work directories before execution
- machine-readable `benchmarks/results/summary.json`
- human-readable `benchmarks/results/report.md`
- benchmark tests for discovery, expected-contract parsing, comparison, aggregation, report rendering, CLI entry, and representative execution
- documentation for running benchmarks and adding fixtures

Excluded until later milestones:

- live Codex or Claude execution
- remote orchestration, queues, or schedulers
- new deep engines
- benchmark scoring based on LLM-only review quality

## v0.8.0-alpha Repair Session Orchestration

Goal: connect the deterministic repair handoff and post-repair verification pieces into one local workflow directory without live executor integration.

Included:

- `qa-z repair-session start --baseline-run <run>` session creation
- `qa-z repair-session status --session <session>` state and path inspection
- `qa-z repair-session verify --session <session> --candidate-run <run>` existing-candidate verification
- `qa-z repair-session verify --session <session> --rerun` session-local candidate creation through existing fast, deep, and review paths
- `.qa-z/sessions/<session-id>/session.json` manifest
- session-local handoff artifacts and `executor_guide.md`
- session-local verify artifacts, `outcome.md`, and workflow `summary.json`
- deterministic next recommendations based on verification verdicts

Excluded until later milestones:

- live Codex or Claude API calls
- remote orchestration, queues, schedulers, or agents
- GitHub bot comments or automatic PR updates
- auto-commit, auto-push, or branch management
- new deep engines

## v0.9.0-alpha Self-Improvement Planning

Goal: make QA-Z inspect its own deterministic artifacts and decide what to improve next without adding live executor integration.

Included:

- `qa-z self-inspect` report generation
- `.qa-z/loops/latest/self_inspect.json`
- `.qa-z/improvement/backlog.json`
- evidence-backed candidates from benchmark failures, verification regressions, incomplete sessions, missing companion artifacts, docs/schema drift indicators, benchmark fixture coverage gaps, report-backed structural gaps, live worktree signals, and repeated empty-loop history
- deterministic priority scoring from impact, likelihood, confidence, repair cost, recurrence, and grounded bonuses for roadmap gaps, service-readiness gaps, worktree risk, commit-order dependency, generated artifact ambiguity, and empty-loop chains
- `qa-z backlog --json` backlog inspection
- `qa-z select-next` selection of the top 1 to 3 open backlog items
- `.qa-z/loops/latest/selected_tasks.json`
- `.qa-z/loops/latest/loop_plan.md`
- `.qa-z/loops/history.jsonl` loop memory skeleton
- structural backlog reseeding when direct bug candidates are absent

Excluded until later milestones:

- live Codex or Claude API calls
- autonomous code editing
- remote orchestration, queues, schedulers, or agents
- automatic verification/benchmark result ingestion after external repair

## v0.9.1-alpha Autonomy Workflow

Goal: tie self-inspection and task selection into repeatable local planning loops without adding live executor integration or automatic code repair.

Included:

- `qa-z autonomy --loops N`
- `qa-z autonomy --min-runtime-hours H --min-loop-seconds S`
- `qa-z autonomy status`
- per-loop directories under `.qa-z/loops/<loop-id>/`
- `.qa-z/loops/latest/` mirror for the most recent loop
- `outcome.json` with selected task ids, evidence used, prepared actions, created session ids, state transitions, next recommendations, and per-loop runtime accounting
- `autonomy_summary.json` for the most recent autonomy run, including runtime target/elapsed/remaining progress
- enriched `.qa-z/loops/history.jsonl` entries with outcome path, prepared action types, final state, state transitions, next recommendations, and elapsed-time fields
- deterministic mapping from selected task categories to next-action plans
- local `repair-session` creation for verification-regression tasks when `verify/compare.json` identifies the baseline run
- explicit `fallback_selected` and `blocked_no_candidates` loop outcomes
- deterministic stop after repeated blocked empty loops instead of runtime-budget no-op spinning
- light recent-history selection penalties so the same fallback task or category does not immediately repeat when comparable alternatives exist

Excluded until later milestones:

- live Codex or Claude API calls
- autonomous code editing
- remote orchestration, queues, schedulers, daemons, or agents
- automatic candidate reruns after an external repair
- GitHub bot comments, Checks API publishing, commits, pushes, or branch management

## v0.9.4-alpha Backlog Reseeding And Empty-Loop Prevention

Goal: keep the local self-improvement loop producing meaningful work even when the explicit backlog runs empty.

Included:

- self-inspection promotion of structural gaps from `docs/reports/current-state-analysis.md`, `docs/reports/next-improvement-roadmap.md`, `docs/reports/worktree-triage.md`, and `docs/reports/worktree-commit-plan.md`
- synthetic but evidence-backed categories such as `backlog_reseeding_gap` and `autonomy_selection_gap`
- empty-loop chain detection from `.qa-z/loops/history.jsonl`
- fallback loop states such as `fallback_selected` and `blocked_no_candidates`
- deterministic empty-loop stop cap during `qa-z autonomy`

Excluded until later milestones:

- live Codex or Claude API calls
- autonomous code editing
- remote orchestration, queues, schedulers, daemons, or agents
- automatic repair execution after fallback task selection

## v0.9.5-alpha Worktree And Integration Risk Promotion

Goal: turn dirty worktree state and integration cleanup risk into first-class self-improvement work instead of leaving it as implicit operator debt.

Included:

- live worktree signal ingestion for modified, untracked, and staged counts
- report-backed cleanup promotion from `docs/reports/worktree-triage.md` and `docs/reports/worktree-commit-plan.md`
- explicit backlog categories such as `worktree_risk`, `commit_isolation_gap`, `artifact_hygiene_gap`, `runtime_artifact_cleanup_gap`, `deferred_cleanup_gap`, and `evidence_freshness_gap`
- deterministic recommendations such as `reduce_integration_risk`, `triage_and_isolate_changes`, `isolate_foundation_commit`, `separate_runtime_from_source_artifacts`, and `clarify_generated_vs_frozen_evidence_policy`
- autonomy fallback selection of integration-cleanup work when structural cleanup risk is the strongest available evidence
- light diversity penalties in `select-next` so identical fallback tasks rotate less aggressively
- recommendation-aware autonomy action packets for cleanup and integration work, including additive `context_paths` and stable follow-up commands for local report triage
- `qa-z autonomy status` now surfaces the latest prepared cleanup and integration action packet so operators can see the next recommendation and report context without opening loop artifacts directly
- human `qa-z backlog` output now focuses on active items and collapses closed backlog residue to a count, so closed history no longer drowns the current work queue
- `qa-z autonomy status` now also carries compact details for the actual latest selected tasks, so the selected loop state stays readable even if the current backlog later shifts
- human `qa-z select-next` output now mirrors selected task title, recommendation, score, penalty residue, and compact evidence instead of only artifact paths
- autonomy human runtime lines now say `no minimum budget` when the runtime target is unset
- `qa-z autonomy status` now preserves the latest selected-task penalty residue as well, so selection diversity signals stay readable after the loop
- persisted `loop_plan.md` output now carries the same selection score and penalty residue, so saved plans stay aligned with the CLI surfaces

Excluded until later milestones:

- live Codex or Claude API calls
- autonomous code editing
- remote orchestration, queues, schedulers, daemons, or agents
- automatic cleanup execution or commit splitting
- policy decisions that freeze generated benchmark evidence without an explicit repository choice

## v0.9.6-alpha Fallback Diversity Hardening

Goal: keep autonomy fallback selection from circling the same structural family when comparable alternatives exist, while preserving explicit evidence about why a fallback loop repeated.

Included:

- fallback-family classification for structural backlog categories such as loop-health, cleanup, workflow-remediation, docs-sync, and benchmark-expansion work
- stronger `select-next` diversity penalties when the same fallback family keeps winning across recent loop history and another fallback family is available
- explicit `selected_fallback_families` metadata in loop history and autonomy outcomes
- self-inspection detection for repeated fallback-family reuse, promoted as an `autonomy_selection_gap`
- deterministic recommendation `improve_fallback_diversity` for repeated fallback-family loops

Excluded until later milestones:

- probabilistic or LLM-chosen diversity heuristics
- remote retry scheduling or delayed fallback queue orchestration
- autonomous execution of the selected fallback work

## v0.9.2-alpha External Executor Bridge

Goal: package autonomy outcomes, repair sessions, and handoff artifacts into executor-ready local directories without adding live executor integration.

Included:

- `qa-z executor-bridge --from-loop <loop>`
- `qa-z executor-bridge --from-session <session>`
- `.qa-z/executor/<bridge-id>/bridge.json`
- bridge-local `executor_guide.md`, `codex.md`, and `claude.md`
- copied bridge inputs for autonomy outcome, session manifest, and handoff JSON
- copied bridge inputs for repair-session action `context_paths` under `inputs/context/` when loop evidence provides them
- manifest fields for source loop/session, selected task ids, prepared action type, baseline run, handoff paths, validation commands, safety constraints, non-goals, and return contract
- explicit return-to-verification instructions using `repair-session verify`

Excluded until later milestones:

- live Codex or Claude API calls
- autonomous code editing
- remote orchestration, queues, schedulers, daemons, or agents
- automatic candidate reruns after external repair
- executor result application
- GitHub bot comments, Checks API publishing, commits, pushes, or branch management

## v0.9.3-alpha Executor Result Ingest

Goal: close the local external-executor loop with a structured return contract and deterministic re-entry into repair-session verification.

Included:

- `qa-z executor-result ingest --result <path>`
- `qa_z.executor_result` schema with explicit `completed`, `partial`, `failed`, `no_op`, and `not_applicable` classifications
- bridge-local `result_template.json`
- session manifest enrichment with latest executor-result path, status, validation status, and bridge id
- optional verification resume through the existing `repair-session verify` flow using `rerun` or `candidate_run`
- loop history enrichment for bridge-backed executor results
- benchmark coverage for the `candidate_run` attach path on mixed Python/TypeScript verification evidence
- changed-file scope validation that rejects executor results outside the bridge handoff `affected_files`
- freshness checks against bridge, session, and ingest-reference timestamps
- provenance checks against bridge, session, and loop ids
- explicit ingest artifacts under `.qa-z/executor-results/<result-id>/`
- verify-resume gating for stale, mismatched, future-dated, partial, failed, no-op, weak completed, and validation-conflicted results
- backlog implications for freshness, provenance, partial-completion, validation-consistency, and no-op safeguard gaps

Excluded until later milestones:

- live Codex or Claude API calls
- autonomous code editing
- remote orchestration, queues, schedulers, daemons, or agents
- multi-result retry scheduling or automatic re-dispatch
- GitHub bot comments, Checks API publishing, commits, pushes, or branch management

## v0.9.7-alpha Pre-Live Executor Safety Package

Goal: freeze QA-Z's pre-live executor safety boundary as one explicit local contract shared by repair sessions, executor bridges, and public docs before any live executor work is attempted.

Included:

- `qa_z.executor_safety` schema with stable `package_id`, `status`, `rules`, `non_goals`, and `enforcement_points`
- session-local `executor_safety.json` and `executor_safety.md`
- repair-session manifest `safety_artifacts` pointers
- bridge-local copied `inputs/executor_safety.json` and `inputs/executor_safety.md`
- bridge manifest `safety_package` summary with copied policy paths and rule ids
- executor and bridge guides that point to the same frozen rule set instead of restating policy ad hoc
- explicit rules for no-op explanation, retry boundary, mutation scope limits, unrelated-refactor prohibition, verification-required completion, and honest executor outcome classification

Excluded until later milestones:

- live Codex or Claude API calls
- autonomous code editing
- remote orchestration, queues, schedulers, daemons, or agents
- automatic retries, redispatch, or multi-result scheduling
- branch creation, commits, pushes, or GitHub bot behavior

## v0.9.8-alpha Live-Free Safety Dry-Run And Multi-Result History

Goal: audit richer executor-result histories against the frozen pre-live safety package without adding live execution, automatic retries, or a second orchestration layer.

Included:

- session-local `executor_results/history.json`
- session-local `executor_results/attempts/<attempt-id>.json`
- backfill of one readable legacy attempt when an older session already has `executor_result.json`
- `qa-z executor-result dry-run --session <session>`
- session-local `executor_results/dry_run_summary.json` and `executor_results/dry_run_report.md`
- dry-run verdicts for `clear`, `attention_required`, and `blocked`
- stable dry-run `verdict_reason` and `rule_status_counts` fields
- deterministic history signals for repeated partial, repeated rejected, repeated no-op, scope-failed, and verification-blocked patterns
- self-inspection candidates driven by repeated executor-result history friction
- self-inspection consumption of session-local dry-run summaries for blocked or no-op-warning histories
- CLI and artifact-schema coverage for the new history and dry-run artifacts
- benchmark fixtures for dry-run `clear`, `attention_required`, and `blocked` histories without live executor execution

Excluded until later milestones:

- live executor invocation
- automatic retry scheduling or redispatch
- code mutation from dry-run
- remote orchestration, queues, schedulers, daemons, or agents
- branch creation, commits, pushes, or GitHub bot behavior

## Issue 1: Diff and context intake

- Goal: ingest issue text, spec docs, and git diff metadata into a single planning context.
- Acceptance: a planner object can normalize issue, diff, and spec inputs into one payload.
- Status: P1 adds git-style diff parsing into `ChangeSet` metadata, optional plan titles resolved from issue/spec/diff/default fallbacks, and YAML front matter on generated contracts.

## Issue 2: Contract extraction v1

- Goal: derive scope, assumptions, invariants, risk edges, negative cases, and acceptance checks.
- Acceptance: QA-Z can render a contract document into `qa/contracts/`.
- Status: bootstrap slice landed with `qa-z plan`; next step is richer diff-aware extraction.

## Issue 3: Fast runner orchestration

- Goal: run lint, typecheck, and unit checks based on configured language plugins.
- Acceptance: `qa-z fast` executes configured fast checks and returns a summarized result.
- Status: Python vertical slice landed with explicit subprocess checks, JSON/Markdown run artifacts, documented exit codes, and P1 smart selection for built-in Python lint, format, typecheck, and pytest checks. P2 adds TypeScript lint, typecheck, and Vitest fast checks on the same summary v2 contract.

## Issue 4: Reporter pipeline

- Goal: emit Markdown, SARIF, and GitHub-friendly annotations from runner output.
- Acceptance: one runner invocation can produce at least Markdown plus one machine-readable format.
- Status: bootstrap slice landed with markdown and JSON review-packet output from `qa-z review`; `qa-z review --from-run` can include fast run verdicts, selection context, executed checks, failed-check evidence, and sibling deep findings. `qa-z fast` emits JSON plus Markdown run summaries and a latest-run manifest. P2 adds `qa-z github-summary` for compact GitHub Actions Job Summary Markdown, and the deep slice adds a Deep QA section when sibling deep artifacts exist. v0.4.0 adds SARIF 2.1.0 for normalized deep findings and ships GitHub code scanning upload through SARIF. P4-B adds concise verification/session outcome sections and deterministic publish recommendations. Standalone workflow-command and Checks API annotations remain future work.

## Issue 5: Repair packet generation

- Goal: compress failures into an agent-friendly repair prompt packet.
- Acceptance: QA-Z produces a structured payload with failures, impacted files, and next questions.
- Status: first repair loop landed with `qa-z repair-prompt`, shared run/contract artifact loading, deterministic candidate file extraction, selection context, sibling deep finding context, suggested fix ordering, and `packet.json` plus `prompt.md` artifacts. v0.5.0 adds normalized `handoff.json`, exact validation commands, and Codex/Claude Markdown renderers without live execution.

## Issue 6: Python plugin

- Goal: support pytest, Hypothesis, and mutmut selection for Python repositories.
- Acceptance: plugin can map configured checks into concrete Python commands.

## Issue 7: TypeScript plugin

- Goal: support Vitest or Jest, fast-check, Stryker, and Playwright smoke tests.
- Acceptance: plugin can map configured checks into concrete TypeScript commands.
- Status: P2 adds the first deterministic TypeScript fast slice with ESLint, `tsc --noEmit`, and `vitest run`. Deep TypeScript tools remain future work.

## Issue 8: Security plugin

- Goal: wire CodeQL, Semgrep, and Trivy into the deep-check layer.
- Acceptance: QA-Z can run at least one security command and normalize its output.
- Status: v0.3.1 keeps Semgrep as the single deep engine and adds policy controls for severity thresholds, custom config, grouped findings, and path/rule suppression. v0.4.0 emits SARIF for those Semgrep findings and uploads it through GitHub code scanning. CodeQL, Trivy, and non-Semgrep SARIF remain future work.

## Issue 9: Codex adapter

- Goal: produce Codex-friendly prompts, review packets, and repository templates.
- Acceptance: repo ships a working review prompt and adapter-facing contract output shape.
- Status: v0.5.0 adds `codex.md` from normalized repair handoff data and `qa-z repair-prompt --adapter codex`. Live Codex execution remains future work.

## Issue 10: Claude adapter

- Goal: produce CLAUDE.md guidance, skills, and hook integration points.
- Acceptance: repo ships reusable Claude templates that match QA-Z contract stages.
- Status: v0.5.0 adds `claude.md` from normalized repair handoff data and `qa-z repair-prompt --adapter claude`. Live Claude execution remains future work.

## Issue 11: Example repositories

- Goal: add one FastAPI demo and one Next.js demo.
- Acceptance: examples show both fast and deep policy modes with realistic config.
- Status: The dependency-light FastAPI demo is runnable as a deterministic fast and repair-prompt example. The TypeScript demo is runnable as a fast-only ESLint, `tsc --noEmit`, and Vitest example. The Next.js placeholder live-free boundary is now explicit: `examples/nextjs-demo` remains placeholder-only and non-runnable until it has its own `package.json`, `qa-z.yaml`, source, tests, and deterministic expected commands. It does not call live agents and does not run `executor-bridge` or `executor-result`. TypeScript-specific deep automation remains future work; current deep examples are Semgrep-backed.

## Issue 12: Benchmark seed set

- Goal: define a seeded bug corpus and usefulness metrics for QA-Z evaluation.
- Acceptance: benchmark folder contains at least an initial case taxonomy and expected outputs.
- Status: v0.7.0 adds `qa-z benchmark`, a top-level `benchmarks/fixtures` corpus, expected outcome contracts, deterministic support helpers, and summary/report artifacts for detection, handoff, and verification behavior. P5-A extends the corpus with deterministic TypeScript fast fixtures for lint, type, test, multi-failure, unchanged verification, and regressed verification cases. P5-B adds deep policy fixtures for severity threshold, ignore rule, exclude path, grouping/dedupe, filtered-vs-blocking counts, and config error handling. P5-C adds mixed Python/TypeScript verification fixtures for cross-language regressions, all-resolved repairs, and partial repairs that still introduce regressions. P8-B expands mixed-surface realism with executed fast/handoff cleanup coverage, docs/schema maintenance cases that stay `unchanged`, cleanup-only unchanged verification, partial executor-result realism, justified no-op realism, and additive benchmark expectations for remaining issues plus ingest recommendations. P12 adds seeded executor-result dry-run fixtures for clear, repeated-partial attention, and completed-but-verify-blocked safety outcomes under the existing policy summary category. P14 extends those fixtures so benchmark comparisons also pin dry-run `verdict_reason` and rule-status counts.

## Issue 13: Post-repair verification loop

- Goal: compare a pre-repair run with a post-repair run and decide whether the repair improved deterministic QA evidence.
- Acceptance: `qa-z verify` writes summary, compare, and report artifacts, classifies resolved/still-failing/regressed/newly introduced evidence, and returns a deterministic final verdict.
- Status: v0.6.0 adds existing-run comparison and optional local rerun candidate creation without live agent execution or remote orchestration.

## Issue 14: Repair session workflow

- Goal: help users move from baseline run, to handoff, to external repair, to candidate verification without stitching every command together manually.
- Acceptance: `qa-z repair-session` writes a manifest, executor guide, session-local handoff artifacts, session-local verification artifacts, and an outcome summary while reusing existing deterministic repair and verify code paths.
- Status: v0.8.0 adds `repair-session start`, `repair-session status`, and `repair-session verify` without live Codex/Claude execution, queues, schedulers, GitHub bot behavior, or new deep engines.

## Issue 15: Verification/session publishing

- Goal: make post-repair verification and repair-session outcomes readable from GitHub Actions job summaries without adding live GitHub API behavior.
- Acceptance: `qa-z github-summary` includes a concise repair outcome section when verification artifacts or a matching repair session are available, with resolved/remaining/regression counts, key artifact paths, and deterministic recommendations.
- Status: P4-B adds a local publish-summary model, Markdown renderer, automatic session/run detection, explicit `--from-session`, and recommendation mapping. GitHub bot comments, Checks API publishing, status changes, and remote orchestration remain future work.

## Issue 16: Self-improvement backlog

- Goal: turn existing QA-Z artifacts back into a prioritized improvement queue for future self-improvement loops.
- Acceptance: `qa-z self-inspect` writes a self-inspection report and backlog, `qa-z select-next` writes selected-task and loop-plan artifacts, and `qa-z backlog --json` prints the current queue.
- Status: v0.9.0 adds artifact-driven self-inspection, backlog scoring, task selection, and JSONL loop memory. v0.9.1 adds `qa-z autonomy` to run repeatable planning loops, write per-loop outcomes, map selected tasks to action plans, and prepare local repair sessions for verification regressions when baseline evidence is available. v0.9.2 adds `qa-z executor-bridge` to package loop/session/handoff evidence for an external executor with validation and return contracts. v0.9.3 adds `qa-z executor-result ingest` to validate structured executor return artifacts, store them under the owning session, optionally rerun deterministic verification, and enrich loop history. P8-A hardens that return path with freshness checks, provenance checks, explicit ingest artifacts, verify-resume gating, and structural backlog implications for stale, mismatched, partial, and weak no-op executor outcomes. v0.9.4 strengthens backlog reseeding from report evidence and recent empty-loop history, adds explicit `fallback_selected` and `blocked_no_candidates` loop outcomes, and stops repeated blocked empty loops early. v0.9.5 promotes live dirty-worktree and integration cleanup evidence into first-class backlog items, adds categories for commit isolation and artifact hygiene, and applies light recent-history penalties so fallback selection rotates instead of re-picking the same task immediately. v0.9.6 hardens that rotation by penalizing repeated fallback-family reuse, recording `selected_fallback_families` in loop memory and autonomy outcomes, and turning repeated single-family fallback chains back into `autonomy_selection_gap` backlog items. v0.9.7 freezes the shared pre-live executor safety package. v0.9.8 adds session-local executor-result history plus a live-free dry-run audit command that evaluates repeated attempt patterns without invoking a live executor. P18 carries dry-run verdict and reason into publish-ready repair summaries, P19 preserves dry-run attempt residue in completed session summaries and outcome Markdown, P20 aligns README, artifact-schema, and current-truth tests with those landed surfaces, P21 adds a history-only fallback so repair-session and publish summaries still synthesize dry-run residue when `dry_run_summary.json` has not been materialized yet, P22 pins that same history-only fallback on the human CLI surfaces for `repair-session status` and `github-summary`, P23 reuses the same synthesized residue inside `self-inspect` so backlog scoring no longer depends on a materialized dry-run summary file, P27 carries explicit dry-run provenance (`materialized` vs `history_fallback`) into repair-session summaries and status JSON, P28 preserves that provenance through publish and GitHub summary rendering, P29 keeps dry-run residue visible even when session `summary.json` is missing but verify artifacts and executor history remain, P30 adds direct unit coverage for signal precedence inside the live-free dry-run history logic, P32 makes the materialized dry-run artifact self-identify with `summary_source: materialized`, P33 mirrors that provenance on human `repair-session status`, P34 extends benchmark dry-run expectations with an additive source alias, P35 pins that new provenance in the seeded dry-run corpus, P36-P39 carry the same provenance into self-inspection evidence summaries, backfill `materialized` for older dry-run summary artifacts during self-inspection, mark synthesized evidence as `history_fallback`, and align docs plus current-truth tests with that behavior, P40-P42 resync report surfaces so self-inspection stops reseeding stale executor-return work, P43-P46 filter generated-artifact backlog gaps through explicit ignore policy, P47-P50 add a light within-batch fallback-family penalty so `select-next` spreads 2 to 3 slots across comparable task families when alternatives exist, P67-P70 strengthen the human planning surfaces by surfacing selected-task detail directly on `qa-z select-next` while replacing autonomy's confusing `elapsed/0 seconds` wording with an explicit `no minimum budget` runtime message, P71-P74 carry selected-task penalty residue into `qa-z autonomy status`, P75-P78 mirror selection score plus penalty residue inside persisted `loop_plan.md`, P79-P82 make autonomy loop plans self-contained by copying selected-task evidence into the saved Markdown plan, and P83-P86 harden loop-health residue by classifying every taskless loop as `blocked_no_candidates` while recording `selection_gap_reason` plus backlog-open counts before and after inspection across outcome, history, plan, and status surfaces. Live model execution, autonomous repair, remote orchestration, multi-result retry scheduling, and GitHub bot behavior remain future work.
