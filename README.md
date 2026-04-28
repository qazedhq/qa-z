# QA-Z

QA-Z is a Codex-first, model-agnostic QA control plane for coding agents.

It generates QA contracts, runs deterministic fast checks, runs Semgrep-backed deep checks, and emits review/repair/session/verification/GitHub/SARIF outputs from run artifacts.

QA-Z runs diff-aware fast QA for Python and TypeScript, and can also run a Semgrep-backed deep QA pass that feeds review packets, repair prompts, local repair sessions, post-repair verification, GitHub summaries, benchmark measurement, and self-improvement backlog planning.

Today, QA-Z can:

- initialize a repository scaffold
- generate QA contracts from issue, spec, and diff inputs, including changed-file metadata
- run deterministic fast checks for Python and TypeScript projects
- run Python and TypeScript smart selection from a CLI diff or contract metadata
- run configured Semgrep deep checks with severity thresholds, grouping, suppression, full or smart selection, and normalized findings artifacts
- emit run-aware review packets with sibling deep findings when available
- generate repair prompts from failed fast checks and blocking Semgrep findings
- generate normalized repair handoff artifacts plus Codex and Claude executor prompts
- create local repair sessions that package baseline evidence, handoff artifacts, an explicit pre-live executor safety package, executor guidance, candidate verification, and outcome summaries
- compare baseline and candidate runs to verify whether a repair improved, stayed unchanged, mixed fixes with regressions, or regressed
- publish compact GitHub Actions summaries from fast, deep, verification, and repair-session artifacts
- emit SARIF 2.1.0 for normalized deep findings so GitHub code scanning can annotate pull requests
- run a seeded local benchmark corpus that measures Python fast, TypeScript fast, mixed-language verification, four executed mixed fast plus deep handoff fixtures, mixed-surface maintenance and executor-result realism, executor bridge action-context packaging and missing-context diagnostics, live-free executor-result dry-run safety history, Semgrep deep policy including `deep_scan_warning_diagnostics` and `deep_scan_warning_multi_source_diagnostics`, repair handoff, and post-repair verification behavior
- inspect its own QA-Z artifacts, reports, and loop history, maintain an improvement backlog, reseed structural candidates when the queue runs thin, and select the next 1 to 3 evidence-backed tasks for an external executor
- inspect its own QA-Z artifacts, live worktree signals, cleanup reports, and loop history, promote worktree/integration risk into backlog items, reseed structural candidates when the queue runs thin, and select the next 1 to 3 evidence-backed tasks for an external executor with a light immediate-reselection penalty plus fallback-family rotation
- run deterministic autonomy planning loops that chain self-inspection, backlog selection, fallback/reseed handling, worktree-driven cleanup task selection, per-loop outcomes, history updates, and local repair-session preparation when baseline evidence is available
- package autonomy outcomes and repair sessions into external executor bridge directories for Codex, Claude, or human operators, including a copied pre-live executor safety package and bridge-local action context inputs
- ingest external executor result artifacts back into repair-session verification, session-local multi-result history, and loop history without adding live executor calls

QA-Z does not yet implement:

- property, mutation, or smoke-test deep check execution
- standalone workflow-command or Checks API annotations beyond GitHub code scanning SARIF upload
- autonomous code editing loops
- live Codex or Claude execution, API calls, queues, or remote orchestration

## Why this exists

Most agentic coding tools are optimized to generate or edit code. QA-Z is optimized to answer a different question:

> Should this change be merged, and if not, what should the agent fix next?

The project is intentionally:

- `QA-first`, not codegen-first
- `contract-first`, not prompt-only
- `deterministic-gated`, not LLM-judged
- `model-agnostic`, not tied to a single coding agent
- `repair-oriented`, not just pass/fail

## Alpha Status

This repository is preparing `v0.9.8-alpha`: artifact-driven self-improvement planning, local autonomy workflow preparation, executor bridge packaging, a frozen pre-live executor safety package, executor-result ingest, and an explicit live-free safety dry-run on top of the existing fast, deep, repair handoff, SARIF, GitHub summary, post-repair verification, benchmark, and repair-session artifacts, not a finished autonomous executor.

The reproducible alpha loop is:

```text
init -> plan -> fast -> deep -> review --from-run -> repair-prompt -> repair-session start -> external repair -> executor-result ingest -> github-summary
```

The benchmark measurement loop is:

```text
benchmark fixtures -> QA-Z flows -> expected outcome comparison -> summary/report
```

The committed corpus now includes an executed `repair-session -> executor-bridge -> executor-result ingest -> verify` fixture that attaches a mixed Python/TypeScript candidate run through the same return contract used outside the benchmark. It also now includes `mixed_fast_deep_handoff_dual_surface` for executed mixed Python/TypeScript fast failures plus Semgrep-backed deep findings in one repair handoff, `mixed_fast_deep_handoff_ts_lint_python_deep` for TypeScript lint evidence plus Python deep evidence in one repair handoff, `mixed_fast_deep_handoff_py_lint_ts_test_dual_deep` for Python lint evidence, TypeScript test evidence, and dual Python/TypeScript deep findings in one repair handoff, `mixed_fast_deep_scan_warning_fast_only` for TypeScript lint evidence plus non-blocking multi-source Semgrep warning lineage in one fast-only handoff, `executor_bridge_action_context_inputs` for bridge-local `inputs/context/` action-context packaging, `executor_bridge_missing_action_context_inputs` for missing action-context guide and stdout diagnostics, executed mixed fast/handoff cleanup coverage, maintenance-only unchanged cases, partial executor-result realism that preserves bridge self-inspection and live repository context through ingest, justified no-op realism, cleanup-only unchanged verification cases, a future-dated ingest rejection case, a validation-conflict ingest case that blocks optimistic verify resume, and seeded live-free dry-run safety cases for clear, attention, blocked, empty-history, scope-validation, missing no-op explanations, and operator-action executor-result histories including `executor_dry_run_validation_noop_operator_actions`, `executor_dry_run_repeated_rejected_operator_actions`, `executor_dry_run_validation_conflict_repeated_rejected_operator_actions`, `executor_dry_run_repeated_noop_operator_actions`, `executor_dry_run_blocked_mixed_history_operator_actions`, `executor_dry_run_empty_history_operator_actions`, `executor_dry_run_scope_validation_operator_actions`, and `executor_dry_run_missing_noop_explanation_operator_actions`. The repeated rejected dry-run fixture now keeps rejected-result inspection ahead of partial retry review when mixed partial and rejected histories repeat, the validation-conflict mixed retry fixture keeps validation-conflict review primary while preserving rejected-result inspection and partial retry review, and the blocked mixed-history fixture now keeps verification blockers primary while showing that validation conflicts and retry pressure still need review. Outside the benchmark, the same return path now accumulates session-local executor-result attempt history and can be audited with an explicit live-free dry-run command.

The self-improvement planning loop is:

```text
benchmark/verify/session/publish artifacts -> self-inspect -> backlog -> select-next -> loop plan -> external repair -> executor-result ingest -> verify/benchmark -> next self-inspect
```

The autonomy workflow loop is:

```text
autonomy -> per-loop self-inspect/select/plan/outcome -> optional repair-session start -> external repair -> executor-result ingest -> verification evidence -> next autonomy loop
```

The current implementation includes:

- a public-facing product narrative
- a repository-level `AGENTS.md`
- a starter `qa-z.yaml.example`
- a minimal Python CLI with stable command names
- a working `qa-z plan` contract generator
- a working `qa-z fast` deterministic runner for Python and TypeScript checks with full and smart selection modes
- a working `qa-z deep` runner that resolves an attachable run, selects Semgrep scope conservatively, applies Semgrep severity thresholds and suppression policy, and normalizes grouped Semgrep JSON findings
- a working `qa-z review` review-packet generator, including run-aware fast and deep context
- a working `qa-z repair-prompt` generator for failed fast checks and blocking Semgrep findings
- a normalized repair handoff contract with Codex and Claude Markdown renderers
- a working `qa-z repair-session` workflow that creates session manifests, executor guides, session-local verification artifacts, and outcome summaries without live executor calls
- a working `qa_z.executor_safety` package emitted into each repair session as JSON plus Markdown
- a working `qa-z verify` command that compares baseline and candidate run artifacts and writes verification JSON/Markdown
- a working `qa-z github-summary` renderer for GitHub Actions Job Summary Markdown with Deep QA and repair outcome context
- a SARIF 2.1.0 reporter for normalized deep findings, written by `qa-z deep`
- a working `qa-z benchmark` runner with seeded Python fast, TypeScript fast, mixed Python/TypeScript verification, four executed mixed fast plus deep handoff fixtures, mixed-surface realism, executor bridge action-context packaging and missing-context diagnostics, executor-result dry-run safety, Semgrep deep, deep policy including `deep_scan_warning_diagnostics` and `deep_scan_warning_multi_source_diagnostics`, repair handoff, verification, and executor-result ingest fixtures
- a working `qa-z self-inspect`, `qa-z backlog`, and `qa-z select-next` planning layer that writes improvement backlog and loop artifacts without editing code, including executor-result follow-up candidates for partial, failed, and no-op external outcomes plus dry-run-aware history candidates
- a working `qa-z autonomy` workflow that records per-loop artifacts, enforces optional runtime budgets, prepares deterministic next-action plans, appends loop history, and creates local repair sessions for verification regressions when compare evidence identifies a baseline run
- a working `qa-z executor-bridge` package generator that bundles loop/session/handoff inputs with copied safety artifacts, executor guides, Codex/Claude-facing docs, validation commands, safety constraints, and a return-to-verification contract
- a working `qa-z executor-result ingest` command that hardens external result re-entry with ingest-time freshness checks, provenance checks, validation-evidence consistency gating, explicit ingest artifacts, verify-resume gating, strict scope validation, session-local multi-result history, and loop-history enrichment when the result came from an autonomy bridge
- a working `qa-z executor-result dry-run` command that evaluates a session's recorded executor-result history against the frozen pre-live safety package without live execution, retries, or code mutation
- Codex and Claude integration templates
- GitHub workflow examples that run fast and deep, upload SARIF to code scanning, upload `.qa-z/runs` and `.qa-z/sessions`, and keep review/repair/summary artifacts on failed fast or deep runs

Roadmap work that is intentionally not part of this alpha slice:

- TypeScript deep QA automation
- property, mutation, smoke-test, and multi-engine security automation
- standalone annotation reporters outside GitHub code scanning
- live Codex or Claude adapter runtimes
- remote orchestration, queues, schedulers, or automatic agent execution

## Command surface

QA-Z reserves these commands from day one:

```text
qa-z init
qa-z doctor
qa-z plan
qa-z fast
qa-z deep
qa-z review
qa-z repair-prompt
qa-z repair-session
qa-z verify
qa-z github-summary
qa-z benchmark
qa-z self-inspect
qa-z select-next
qa-z backlog
qa-z autonomy
qa-z executor-bridge
qa-z executor-result
```

In this bootstrap, `init`, `doctor`, `plan`, `fast`, `deep`, `review`, `repair-prompt`, `repair-session`, `verify`, `github-summary`, `benchmark`, `self-inspect`, `select-next`, `backlog`, `autonomy`, `executor-bridge`, and `executor-result` are functional. `init` can write Python, TypeScript, or monorepo starter configs plus packaged Codex/Claude templates and a small GitHub workflow. `doctor` validates config shape, legacy paths, timeout values, and configured adapter instruction files without adding runtime dependencies. `deep` runs configured `sg_scan` Semgrep checks with full or smart selection and writes a skeleton summary when no deep checks are configured. `repair-session` packages handoff, a session-local pre-live executor safety package, and verification artifacts into a local workflow; it does not call an agent or repair code by itself. `verify` compares two run artifact sets. `benchmark` runs seeded fixtures and compares their observed artifacts against expected outcomes. `self-inspect` and `select-next` only plan evidence-backed improvement work. `autonomy` chains those planning steps into repeatable local loops and may prepare repair sessions. `executor-bridge` packages an existing loop/session for an outside executor and copies the same safety package plus any prepared repair-session action context files into bridge inputs. `executor-result ingest` is the return path: it validates freshness, provenance, and scope, records an ingest artifact and report, stores only accepted results under the session, appends readable session-local attempt history when the owning session is known, and reruns deterministic verification only when verify-resume preconditions pass. Its non-JSON stdout mirrors source self-inspection, source loop, live repository context, freshness/provenance checks, warnings, and backlog implications. `executor-result dry-run` evaluates that recorded session history against the frozen safety package and writes a local summary plus report without live execution. None of these commands edits code, calls live model APIs, schedules jobs, commits, pushes, or posts GitHub comments.

## Quickstart

Install the project locally:

```bash
python -m pip install -e .[dev]
```

For QA-Z's own release gate, the root `qa-z.yaml` is Python-only so this Python package can validate without requiring the TypeScript demo toolchain, and the root deep scan is scoped to `src` and `tests` so intentionally vulnerable benchmark fixtures stay out of the repository release gate. TypeScript checks remain covered by `qa-z.yaml.example`, `examples/typescript-demo/qa-z.yaml`, and benchmark fixtures.

Inspect the command surface:

```bash
python -m qa_z --help
```

Initialize a repository with a starter policy:

```bash
python -m qa_z init
python -m qa_z init --profile python --with-agent-templates
python -m qa_z init --profile monorepo --with-github-workflow
python -m qa_z doctor --json
```

Generate a first QA contract draft:

```bash
python -m qa_z plan --title "Protect billing auth guard" --issue issue.md --spec spec.md
python -m qa_z plan --issue issue.md --spec spec.md --diff changes.diff
python -m qa_z plan --diff changes.diff
```

Run the fast gate and write JSON/Markdown artifacts:

```bash
python -m qa_z fast
python -m qa_z fast --json
python -m qa_z fast --output-dir .qa-z/runs/local
python -m qa_z fast --strict-no-tests
python -m qa_z fast --selection smart --diff changes.diff
```

Run configured Semgrep deep checks attached to the latest fast run, or to an explicit run directory:

```bash
python -m qa_z deep
python -m qa_z deep --json
python -m qa_z deep --from-run .qa-z/runs/local
python -m qa_z deep --output-dir .qa-z/runs/local
python -m qa_z deep --selection smart --diff changes.diff
python -m qa_z deep --sarif-output qa-z.sarif
```

`--from-run` attaches deep evidence to an existing fast run. `--output-dir`
creates a standalone deep run. `--from-run` and `--output-dir` cannot be
combined because silently choosing one would make the artifact lineage
ambiguous. Deep summaries record `run_resolution` so downstream review can tell
whether evidence came from `latest`, an explicit `from_run`, an `output_dir`, or
a new standalone run.

`deep` expects Semgrep on `PATH` when `sg_scan` is enabled. Missing tools and malformed Semgrep output are recorded in the summary artifacts instead of dropping the run evidence. In smart mode, docs-only changes skip Semgrep, source/test changes target the changed paths, and config, high-risk, deleted, renamed, unknown, or oversized changes escalate to a full scan. Semgrep findings are always counted, but only severities listed in `semgrep.fail_on_severity` block the deep verdict. Non-blocking Semgrep scan-quality warnings are surfaced as `scan_warning_count`, `scan_warnings`, and summary-level `diagnostics.scan_quality` instead of living only in stdout tails, including warning paths and check ids when that provenance is available. Grouped findings are used by review packets, repair prompts, and GitHub summaries so repeated hits stay readable.

Every `qa-z deep` run writes SARIF to:

```text
.qa-z/runs/<run-id>/deep/results.sarif
```

Use `--sarif-output <path>` when a CI system or local tool needs a copy at a stable path. SARIF is generated from the same normalized active findings used by review and repair output; if only grouped findings are present in an older artifact, QA-Z emits one representative SARIF result per group.

Render a review packet from a run:

```bash
python -m qa_z review --from-run latest
python -m qa_z review --from-run .qa-z/runs/local --json
python -m qa_z review --from-run latest --output-dir .qa-z/runs/local/review
```

Generate an agent-friendly repair packet from the latest fast run:

```bash
python -m qa_z repair-prompt
python -m qa_z repair-prompt --from-run latest
python -m qa_z repair-prompt --from-run .qa-z/runs/local
python -m qa_z repair-prompt --from-run latest --output-dir .qa-z/runs/local/repair
python -m qa_z repair-prompt --from-run latest --adapter codex
python -m qa_z repair-prompt --from-run latest --adapter claude
python -m qa_z repair-prompt --json
python -m qa_z repair-prompt --handoff-json
```

`repair-prompt` keeps the original `packet.json` and `prompt.md` artifacts, and also writes:

```text
.qa-z/runs/<run-id>/repair/handoff.json
.qa-z/runs/<run-id>/repair/codex.md
.qa-z/runs/<run-id>/repair/claude.md
```

`handoff.json` is the normalized executor contract. It includes source artifact provenance, selected blocking repair targets, affected files, constraints, non-goals, exact validation commands, and suggested post-repair workflow steps. `codex.md` is shorter and action-oriented for Codex-style execution. `claude.md` keeps the same data but uses a more explanatory structure with explicit non-goals and workflow guidance. These files do not call external LLM APIs.

Create a local repair session from a baseline run:

```bash
python -m qa_z repair-session start --baseline-run .qa-z/runs/<baseline>
python -m qa_z repair-session status --session .qa-z/sessions/<session-id>
python -m qa_z repair-session verify --session .qa-z/sessions/<session-id> --rerun
python -m qa_z repair-session verify --session .qa-z/sessions/<session-id> --candidate-run .qa-z/runs/<candidate>
```

`repair-session start` writes a session manifest, executor guide, `executor_safety.json`, `executor_safety.md`, and handoff artifacts under `.qa-z/sessions/<session-id>/`. The guide is meant for a human, Codex, Claude, or another external executor to read and act on manually, and it points at the same pre-live safety package consumed by bridge packaging. `repair-session verify --rerun` creates a candidate under the session by running the existing deterministic fast and deep runners, then compares it against the baseline and writes `verify/summary.json`, `verify/compare.json`, `verify/report.md`, `outcome.md`, and a session-level `summary.json`. It does not perform live autonomous repair. See `docs/repair-sessions.md` and `docs/pre-live-executor-safety.md` for the artifact layout, state model, and frozen safety boundary.

Verify a post-repair candidate against the original baseline run:

```bash
python -m qa_z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
python -m qa_z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate --json
python -m qa_z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate --output-dir .qa-z/runs/candidate/verify
python -m qa_z verify --baseline-run .qa-z/runs/baseline --rerun --rerun-output-dir .qa-z/runs/candidate
```

`verify` treats the baseline as the pre-repair run and the candidate as the post-repair run. It compares fast check status changes and blocking deep findings, writes `summary.json`, `compare.json`, and `report.md` under the candidate run's `verify/` directory by default, and returns a final verdict of `improved`, `unchanged`, `mixed`, `regressed`, or `verification_failed`. `--rerun` creates a candidate by running the existing deterministic `fast` and `deep` runners before comparing; it still does not perform automatic code repair, live Codex/Claude execution, queueing, scheduling, or remote orchestration.

Render compact Markdown for GitHub Actions Job Summary:

```bash
python -m qa_z github-summary --from-run latest
python -m qa_z github-summary --from-run latest --output .qa-z/runs/local/github-summary.md
python -m qa_z github-summary --from-session .qa-z/sessions/<session-id>
python -m qa_z github-summary --from-run .qa-z/runs/candidate --from-session .qa-z/sessions/<session-id>
```

`github-summary` stays local and deterministic. It renders the fast/deep run view, then adds a concise repair outcome section when the source run has `verify/` artifacts, when a completed repair session points at that candidate run, or when `--from-session` is provided. If `--from-session` is given without an explicit `--from-run`, QA-Z now follows that session's `candidate_run_dir` instead of whichever run currently owns `latest`, so GitHub-facing summaries stay aligned with the chosen repair session. When the session summary also carries dry-run evidence, that repair outcome section preserves the session dry-run verdict, reason, source, attempt counts, and history signals plus operator decision, operator summary and recommended actions so GitHub-facing output keeps the same executor-safety residue visible in local session artifacts. Those GitHub-facing repair outcome sections now keep ordered `Action <id>:` lines for recommended actions instead of flattening mixed-history residue into one sentence, so the stable action ids stay visible beside each summary. When that explicit dry-run summary is missing but the session still has readable executor history, QA-Z now synthesizes the same residue from `executor_results/history.json` instead of dropping the signal and marks the dry-run source as history fallback instead of pretending it was materialized. The publish recommendation is derived from the recorded verification verdict: `improved` -> `safe_to_review`, `mixed` -> `review_required`, `regressed` -> `do_not_merge`, `verification_failed` -> `rerun_required`, and `unchanged` -> `continue_repair`. It does not post bot comments or call the GitHub Checks API.

Run the benchmark corpus:

```bash
python -m qa_z benchmark
python -m qa_z benchmark --json
python -m qa_z benchmark --fixture semgrep_eval
```

`benchmark` copies each fixture into an isolated work directory, runs the requested QA-Z flows, compares observed fast/deep/handoff/verify/executor-bridge fields against `expected.json`, and writes `benchmarks/results/summary.json` plus `benchmarks/results/report.md`. `summary.json` now carries a compact `snapshot` string such as `54/54 fixtures, overall_rate 1.0`, and `report.md` repeats the same value for alpha closure notes while surfacing deep warning paths, warning checks, and per-fixture artifact paths when Semgrep scan-quality warnings or generated artifact pointers are present. The seeded corpus includes deterministic Python and TypeScript fast failures, mixed Python/TypeScript verification verdicts, `mixed_fast_deep_handoff_dual_surface`, `mixed_fast_deep_handoff_ts_lint_python_deep`, `mixed_fast_deep_handoff_py_lint_ts_test_dual_deep`, and `mixed_fast_deep_scan_warning_fast_only` for executed mixed fast plus deep handoff aggregation and fast-only handoff retention under non-blocking deep warnings, `executor_bridge_action_context_inputs` for bridge-local action context copying into `inputs/context/` plus loop-local self-inspection/live repository provenance, `executor_bridge_missing_action_context_inputs` for missing action-context guide and stdout diagnostics, executed mixed fast/handoff worktree cleanup coverage, docs/schema maintenance cases that remain `unchanged`, Semgrep deep findings, deep policy edge cases including `deep_scan_warning_diagnostics` and `deep_scan_warning_multi_source_diagnostics` for non-blocking `scan_warning_count`, `scan_warnings`, `scan_quality`, and warning-check provenance coverage, repair handoff checks, partial executor-result ingest cases that pin loop-context preservation and ingest stdout diagnostics, justified no-op executor-result ingest cases, and live-free executor-result dry-run cases that pin `clear`, `attention_required`, `blocked`, repeated rejected, validation-conflict plus repeated rejected retry pressure, repeated no-op, blocked mixed-history, empty-history ingest guidance, scope-validation scope-drift guidance, missing no-op explanation guidance, operator decision, operator summary and recommended action residue. Empty-history sessions now mark `executor_history_recorded` as attention, and repeated no-op history now marks `retry_boundary_is_manual` as attention, so rule counts match attention verdicts. The repeated rejected fixture also keeps rejected-result inspection ahead of partial retry review when mixed partial and rejected histories repeat, the validation-conflict mixed retry fixture keeps validation-conflict review primary while preserving rejected-result inspection and partial retry review, and blocked mixed-history summaries now preserve blocked priority while still saying validation conflicts and retry pressure still need review. Every committed executor dry-run fixture now pins complete dry-run rule buckets plus operator decision, operator summary, recommended action residue, and action-aligned next recommendations, so guidance or rule-partition regressions cannot hide behind an unchanged verdict. The executor safety rule catalog is the six-rule frozen pre-live set, and the dry-run rule catalog is a seven-rule runtime audit set that extends the frozen safety package by adding the `executor_history_recorded` history-presence rule. It does not perform live repair or call Codex or Claude.

Run one benchmark process per `--results-dir`. The runner creates
`.benchmark.lock` before resetting `work/` and returns a benchmark error if the
same directory is already active; use a distinct `--results-dir` for parallel
fixture experiments. Lock failures remain plain-text usage errors even with
`--json`, so automation should key off exit code `2`.

Inspect QA-Z's own artifacts and select the next improvement tasks:

```bash
python -m qa_z self-inspect
python -m qa_z self-inspect --json
python -m qa_z backlog --refresh
python -m qa_z backlog --json
python -m qa_z select-next --count 3
python -m qa_z select-next --refresh --count 3
python -m qa_z select-next --json
```

`self-inspect` reads local benchmark, verification, repair-session, executor-result, executor-result history, executor-result dry-run summaries, docs/schema, report, fixture, loop-history, and live repository evidence where those artifacts exist. The JSON report records a compact `live_repository` snapshot with git dirty counts, runtime artifact count, benchmark result count, dirty benchmark result count, generated alpha release evidence count, generated-artifact policy status, and `dirty_area_summary` before listing candidates, and human output prints the same data on a `Live repository:` line. When inspection had to repopulate an empty backlog from fresh structural evidence, the report now records `backlog_reseeded` as `true` and lists the concrete `reseeded_candidate_ids`, while the persisted backlog keeps only the concrete candidates instead of leaving a synthetic `backlog_reseeding_gap` item open. When a session only has readable executor history and not an explicit dry-run summary yet, self-inspection now synthesizes the same dry-run residue from that history before scoring workflow, no-op, or partial-completion gaps. Its candidate evidence summaries also preserve dry-run provenance as `source=materialized` or `source=history_fallback`, so backlog review can tell whether a dry-run signal came from `dry_run_summary.json` or from synthesized history without opening a second artifact. benchmark-gap evidence preserves the generated benchmark `snapshot` from `benchmarks/results/summary.json`, so backlog and loop-plan compact evidence can show the failed fixture together with the overall benchmark pass-rate line. It also now filters runtime-artifact policy gaps through the live ignore policy and `docs/generated-vs-frozen-evidence-policy.md`, so stale report language and report-only deferred cleanup wording do not keep re-promoting generated benchmark outputs that are already explicitly local-only. Root `.qa-z/**` and `benchmarks/results/work/**` stay local; `benchmarks/results/summary.json`, `benchmarks/results/report.md`, and dirty snapshot roots matching `benchmarks/results-*` are local by default and should be committed only as intentional frozen evidence with surrounding context. Those benchmark outputs now count as deferred-cleanup pressure only when they are also dirty in the current git snapshot, so self-inspection does not reopen cleanup or commit-isolation work just because clean local benchmark outputs happen to exist. When the generated-artifact ignore rules and policy doc are already explicit, dirty `benchmarks/results-*` snapshot roots stay visible through `benchmark_result_count` and `dirty_benchmark_result_count` without being promoted into `runtime_artifact_paths`, so live repository summaries can distinguish review-only benchmark evidence from local-only runtime cleanup pressure. In that explicit-policy state, live runtime artifact paths can still keep `artifact_hygiene_gap` and `runtime_artifact_cleanup_gap` open, but they no longer reopen `evidence_freshness_gap` by themselves. `runtime_artifact_cleanup_gap` now outranks the broader `artifact_hygiene_gap`, so operators clear policy-managed runtime artifacts before revisiting longer-lived source/evidence separation work. When the current inspection also knows the live `HEAD`, commit-isolation and deferred-cleanup report seeds now require an explicit matching report `Head:` line before they are treated as fresh enough to reopen structural backlog work. When an `open` backlog item is no longer observed on the latest inspection pass, QA-Z now closes it instead of leaving stale work permanently selectable. Besides direct failures, it can promote structural gaps such as mixed-surface benchmark realism, current-truth docs drift, executor contract completeness, repeated partial or no-op executor history patterns, blocked dry-run safety verdicts, dirty worktree risk, deferred cleanup work, commit-isolation risk, runtime artifact hygiene gaps, generated-versus-frozen evidence ambiguity, repeated empty-loop chains, and repeated fallback-family reuse into `.qa-z/improvement/backlog.json`. Human `qa-z self-inspect` output now prints the top three candidates with title, recommendation, deterministic action hint, priority score, and compact evidence summary while `--json` keeps the full report. `select-next` still chooses the highest-priority open backlog items, but now applies a small penalty when the exact same fallback task, category, or fallback family was selected in the last two loops so comparable alternatives can rotate in. When more than one task is selected in the same batch, it also applies a light within-batch fallback-family penalty if an alternative family is available, which helps avoid spending all 2 to 3 slots on near-identical cleanup work. When loop-health evidence names a repeated fallback family such as cleanup, the human fallback-diversity hint now says to surface a non-cleanup fallback family before selecting more cleanup work, so `self-inspect`, `backlog`, `select-next`, and `loop_plan.md` all carry the same diversity contract. The selected task artifact records both the penalty and its reasons. It writes `.qa-z/loops/latest/selected_tasks.json`, renders `.qa-z/loops/latest/loop_plan.md`, and appends `.qa-z/loops/history.jsonl`. Human `qa-z select-next` output now echoes each selected task's title, recommendation, deterministic action hint, selection score, penalty reasons, and compact evidence summary instead of only printing artifact paths, and the written loop plans now mirror selection score and penalty residue plus the same action hint as well. Runtime-artifact cleanup items that still use `triage_and_isolate_changes` on the JSON side now tell operators to clear policy-managed runtime artifacts before source integration and keep frozen evidence only when intentional. Use `qa-z select-next --refresh` when the operator wants task selection to start from a just-refreshed self-inspection pass instead of the existing backlog file. autonomy loop plans now mirror selected-task evidence summaries too, so the saved plan can stand on its own without reopening `selected_tasks.json`. Human `qa-z backlog` output now focuses on open or active items, prints the backlog `Updated:` timestamp, shows item title, recommendation, deterministic action hint, and compact evidence summary, and collapses closed history to a count while `--json` keeps the full backlog artifact. Use `qa-z backlog --refresh` when the operator wants to run self-inspection immediately before printing, avoiding a stale read after a recent worktree or artifact change. These commands decide what to improve next; a human or external executor still performs the code changes.
Those same dirty benchmark result roots now stay in the `benchmark` bucket for `dirty_area_summary`, so area-aware self-inspection and selection hints do not fold review-only benchmark evidence back into local-only runtime cleanup pressure.

For legacy benchmark summaries that predate `snapshot`, benchmark-gap evidence synthesizes the same compact text from `fixtures_passed`, `fixtures_total`, and `overall_rate` when those fields are present.
If a failed benchmark summary has only aggregate failure counts and no per-fixture details, self-inspection creates a summary-level benchmark-gap item instead of dropping the failure evidence.

The human planning surfaces now also print deterministic `validation:` command hints. Plain `qa-z self-inspect`, `qa-z backlog`, `qa-z select-next`, and generated loop plans show the local command an operator should run to refresh evidence after the selected work, while JSON reports and backlog artifacts keep their existing shape. When `qa-z backlog --refresh` or `qa-z select-next --refresh` runs self-inspection first, the human output prints `Refreshed: yes` so operators can distinguish a state-changing read from a plain artifact read.

Dirty-worktree self-inspection evidence now also includes deterministic area counts such as `areas=benchmark:271, docs:160, source:42`, so alpha closure operators can see the dominant integration surfaces before opening the full `git status` output.
Benchmark result snapshot directories that look like `benchmarks/results-*` are treated as local-by-default benchmark result evidence in live repository signals and self-inspection, not as local-only runtime cleanup pressure, unless an operator intentionally freezes them as evidence with surrounding context.
`python scripts/runtime_artifact_cleanup.py` now mirrors that generated-artifact split by reusing the same helper-derived policy roots: `benchmarks/results/` and `benchmarks/results-*` stay review-only local-by-default roots, while `--apply` deletes only local-only runtime artifacts such as root `.qa-z/**`, `benchmarks/results/work/**`, `build/**`, `dist/**`, `src/qa_z.egg-info/**`, root `/tmp_*` scratch probes, `/benchmarks/minlock-*` benchmark lock probes, literal `%TEMP%/**` scratch roots, and cache trees like `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.mypy_cache_safe/`, `.ruff_cache/`, and `.ruff_cache_safe/`. Cleanup JSON and human output now include a `reason` for planned, deleted, skipped tracked, and review-only roots, so `--apply` tells the operator why a root did or did not move. `mypy.ini` is a tracked config surface that pins mypy's cache under `$TEMP/qa-z-mypy-cache` on Windows, not a runtime artifact.
When that area evidence is present, the matching `action:` hint now names the top areas to triage first, such as `triage benchmark and docs changes first`, and now points operators at `python scripts/runtime_artifact_cleanup.py --json` before falling back to the self-inspection refresh guidance.
Commit-isolation candidates reuse the same dirty area evidence when present, so `isolate_foundation_commit` guidance can point operators at the benchmark/docs/source areas to isolate into the foundation split while keeping the commit-plan report as the primary reference.
Integration-gap candidates now append the same live `git_status` area evidence, so `audit_worktree_integration` guidance can name the benchmark/docs/source/tests surfaces to inspect before rerunning self-inspection.
When compact evidence prioritizes that closure snapshot, human planning surfaces append an `action basis:` suffix with the area-bearing `git_status` summary so the area-aware action hint remains explainable without opening the full JSON evidence array.
Deferred cleanup actions now explicitly tell operators to decide whether generated artifacts stay local-only or become intentional frozen evidence before source integration. When compact evidence leads with a report summary, those cleanup items can append an `action basis:` suffix with the concrete `generated_outputs` or `runtime_artifacts` evidence that explains the decision.

Run deterministic autonomy planning loops:

```bash
python -m qa_z autonomy --loops 3
python -m qa_z autonomy --loops 1 --min-runtime-hours 4 --min-loop-seconds 900
python -m qa_z autonomy --loops 1 --json
python -m qa_z autonomy status
python -m qa_z autonomy status --json
```

`autonomy` runs self-inspection, backlog merge, task selection, next-action planning, outcome recording, and history updates for each loop. Each loop writes `.qa-z/loops/<loop-id>/self_inspect.json`, `selected_tasks.json`, `loop_plan.md`, and `outcome.json`; `.qa-z/loops/latest/` mirrors the most recent loop. Those saved autonomy loop plans now mirror selected-task evidence alongside selection score, selected fallback families, latest live repository context, and any penalty residue, so an operator can review the stored plan without reopening `selected_tasks.json`. Loop-local artifacts rewrite `source_self_inspection` to `.qa-z/loops/<loop-id>/self_inspect.json` and preserve the source loop id and timestamp, so a later `latest` update cannot misattribute an older bridge or ingest result. When no task is selected, taskless loops now also carry `selection_gap_reason` plus open backlog counts before and after inspection, so stale backlog closures do not look like successful work. Each autonomy outcome and matching history line also carries a compact `loop_health` summary with `classification`, selected count, fallback state, stale open items closed, a readable explanation, and blocked no-candidate chain residue through `blocked_chain_length`, `blocked_chain_remaining_until_stop`, and `blocked_chain_loop_ids`. When a runtime budget is provided, QA-Z keeps looping until both the requested loop count and the minimum elapsed wall-clock budget are satisfied, unless repeated `blocked_no_candidates` loops show that no evidence-backed work can be derived; `autonomy_summary.json` records that early stop through `stop_reason`. When no runtime budget is configured, the human autonomy surfaces now say `no minimum budget` instead of rendering an awkward `elapsed/0 seconds` line. When the open backlog is empty but structural evidence can reseed it, the loop records `fallback_selected`; when even reseeding cannot produce work, it records `blocked_no_candidates`. Worktree-driven cleanup items are valid fallback work, so dirty integration states can surface as first-class autonomy tasks instead of staying implicit cleanup debt. Loop history and autonomy outcomes now record `selected_fallback_families`, so repeated cleanup-only or loop-health-only fallback reuse can be detected and promoted back into the backlog as an `autonomy_selection_gap`. Selected task categories are mapped deterministically to action packets: benchmark and coverage gaps become fixture plans, docs/schema drift becomes sync plans, backlog/autonomy health gaps become loop-health plans, workflow gaps become remediation plans, worktree and artifact cleanup gaps become integration-cleanup plans, session gaps become follow-up plans, verification regressions prepare a local `repair-session` when `verify/compare.json` identifies the baseline run, and dry-run blocked or attention signals become session-aware executor safety review packets. Autonomy-created repair-session packets now preserve loop-local self-inspection plus selected verification evidence in `context_paths`, so a later bridge can copy both the local selection context and source task context into bridge inputs. Loop-health packets for backlog reseeding and fallback-diversity work now carry their selected task evidence paths, loop-local self-inspection, and current-state and roadmap references through `context_paths`, so repeated fallback-family handoffs point directly at loop-history evidence without reopening the latest report set. For worktree and integration recommendations such as `reduce_integration_risk`, `isolate_foundation_commit`, and `audit_worktree_integration`, those packets now include recommendation-specific commands plus additive `context_paths` so the next operator can see which local reports to inspect before rerunning backlog or self-inspection evidence. Those cleanup and workflow packets now also carry loop-local self-inspection through `context_paths`, so a later executor or release handoff can still recover the exact inspection artifact that produced the recommendation instead of relying on the mutable `latest` mirror. Cleanup-oriented packets now include `python scripts/runtime_artifact_cleanup.py --json` in their deterministic command set, and `reduce_integration_risk` now also carries `python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json` plus `docs/reports/worktree-commit-plan.md` so dirty-worktree follow-through stays aligned with the repo-standard commit-split helper and leaves a local JSON artifact behind even under strict attention exits. Runtime-artifact cleanup packets that still use `triage_and_isolate_changes` now also carry `python scripts/runtime_artifact_cleanup.py --apply --json` and tell operators to clear policy-managed runtime artifacts before rerunning self-inspection. Deferred generated cleanup packets for `triage_and_isolate_changes` still carry `docs/generated-vs-frozen-evidence-policy.md` through `context_paths`, and now also carry `scripts/runtime_artifact_cleanup.py` through `context_paths`, so the local-only versus intentional frozen evidence decision travels with the prepared action. `qa-z autonomy status` now mirrors that latest packet through additive `latest_prepared_actions` and `latest_next_recommendations` fields, carries richer backlog top items with title, recommendation, and compact evidence, and the human-readable status output echoes open session details plus the latest action type, commands, context paths, selected fallback families, and live repository context so operators can triage the next move without opening `outcome.json`. It also now includes `latest_selected_task_details`, derived directly from the stored latest `selected_tasks.json`, `latest_live_repository` from the stored selected-task artifact or outcome, and `latest_selected_fallback_families`, derived directly from the stored latest `outcome.json`, so the status surface preserves the actual selected title, recommendation, evidence summary, selection score, fallback-family context, live repository snapshot, and selection penalty and its reasons even if the live backlog shifts later. When the latest loop was taskless, that status view also mirrors `selection_gap_reason`, the before/after open backlog counts, the latest `loop_health` summary from the stored outcome, the current blocked no-candidate chain, and the exact blocked no-candidate loop ids that produced that residue. The command prepares evidence and handoff material only. External repair, candidate runs, and verification still happen outside the autonomy command.

Package a prepared loop or repair session for an external executor:

```bash
python -m qa_z executor-bridge --from-loop .qa-z/loops/<loop-id>
python -m qa_z executor-bridge --from-session .qa-z/sessions/<session-id>
python -m qa_z executor-bridge --from-loop <loop-id> --bridge-id bridge-local --json
```

`executor-bridge` writes `.qa-z/executor/<bridge-id>/bridge.json`, `result_template.json`, `executor_guide.md`, `codex.md`, `claude.md`, and copied inputs under `inputs/`, including `executor_safety.json`, `executor_safety.md`, and `inputs/context/` files copied from repair-session action `context_paths` when the loop action provides them. For autonomy-created repair sessions, that action-context package now includes the loop-local `.qa-z/loops/<loop-id>/self_inspect.json` artifact plus selected verification evidence, so the bridge keeps the same local selection context that produced the handoff. The manifest records the source loop/session, latest self-inspection live repository context when available, selected task ids, baseline run, handoff paths, validation command, copied inputs, `inputs.action_context` copy metadata, `inputs.action_context_missing` skipped context paths, a `safety_package` summary with ordered rule ids and a safety rule count, safety constraints, non-goals, and the expected return step. The executor-facing guides also render a guide safety rule count, live repository context, and bridge-local action context inputs so operators can audit the copied package without opening the JSON manifest. Human output includes bridge stdout return pointers for the result template, expected result artifact, copied safety package, safety rule count, live repository context, action-context package health, missing action-context diagnostics, and verification command, plus template placeholder guidance so the result summary is replaced before ingest. The bridge is a package and contract only: a human or external Codex/Claude executor may consume it, edit code outside QA-Z, then return by running `repair-session verify`. QA-Z still does not invoke the executor or apply results automatically.

Ingest an external executor result and reconnect it to the owning repair session:

```bash
python -m qa_z executor-result ingest --result .qa-z/executor/<bridge-id>/result.json
python -m qa_z executor-result ingest --result external-result.json --json
```

`executor-result ingest` validates a structured `qa_z.executor_result` payload, confirms that it matches the bridge/session/loop contract, rejects `changed_files` that fall outside the bridge handoff `affected_files`, checks freshness relative to the bridge and session timestamps, classifies the ingest outcome as accepted, accepted-with-warning, accepted-partial, accepted-no-op, rejected-stale, rejected-mismatch, or rejected-invalid, and writes:

```text
.qa-z/executor-results/<result-id>/ingest.json
.qa-z/executor-results/<result-id>/ingest_report.md
```

Accepted results are stored under `.qa-z/sessions/<session-id>/executor_result.json`. Every readable result whose owning session can be resolved also appends `.qa-z/sessions/<session-id>/executor_results/history.json` and stores the readable attempt payload under `.qa-z/sessions/<session-id>/executor_results/attempts/<attempt-id>.json`. The ingest summary makes verify-resume readiness explicit through `ready_for_verify`, `ingested_with_warning`, `verify_blocked`, `stale_result`, or `mismatch_detected`, and when the bridge supplied self-inspection context it carries the same `source_self_inspection`, source loop id, source timestamp, and `live_repository` snapshot into `ingest.json`, `ingest_report.md`, and the session-local attempt history. `rerun` reuses the existing deterministic fast/deep verification flow against the current worktree only when those preconditions pass, `candidate_run` attaches an explicit candidate run directory only when it exists, and `skip` records the result without running verification. The ingest artifact also records backlog implications for freshness, provenance, no-op, and partial-completion gaps so the next self-inspection pass can turn them into structural backlog items. The benchmark corpus now exercises the `candidate_run` attach path, a partial-result mixed verify case, and a justified no-op case that remains functionally unchanged. When the result came from an autonomy bridge, QA-Z also enriches `.qa-z/loops/history.jsonl` with executor-result status, ingest status, verify-resume status, changed files, validation status, and the latest recommendation.

Audit the recorded executor-result history without live execution:

```bash
python -m qa_z executor-result dry-run --session .qa-z/sessions/<session-id>
python -m qa_z executor-result dry-run --session <session-id> --json
```

`executor-result dry-run` evaluates the full recorded session attempt history against the frozen pre-live safety package, then writes `.qa-z/sessions/<session-id>/executor_results/dry_run_summary.json` and `.qa-z/sessions/<session-id>/executor_results/dry_run_report.md`. The materialized summary now self-identifies with `summary_source: materialized`, records an operator decision, operator summary and recommended actions, and `repair-session status`, completed repair-session summaries, session outcome Markdown, and GitHub summary rendering preserve that dry-run verdict plus the source, attempt-count, history-signal, decision, diagnostic, and action residue when it exists. Session outcome Markdown and GitHub-facing summaries now also keep ordered `Action <id>:` lines for those recommended actions so operators can carry the same stable action ids across JSON, local Markdown, and publish summaries. Blocked mixed histories keep the verification blocker primary in `operator_decision` and `next_recommendation`, while the one-line `operator_summary` can still say that validation conflicts and retry pressure still need review. Human stdout mirrors the same operator contract through `Source:`, `Why:`, ordered `Rule counts: clear=..., attention=..., blocked=...`, and `Action <id>:` lines so an operator can see the action id without opening JSON. If the explicit dry-run summary is absent but the session history artifact exists, those repair-session and publish surfaces synthesize the same residue directly from history instead of pretending there is no signal, and they label that provenance as a history fallback. It does not rerun an external executor, mutate code, or schedule retries.

Run the local verification suite:

```bash
python -m pytest
```

Run the one-shot local alpha release gate before publishing or attaching local
artifacts:

```bash
python scripts/alpha_release_gate.py --json --output dist/alpha-release-gate.json
```

Before splitting the current accumulated worktree into release commits, inspect
the dirty-path grouping with:

```bash
python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json
```

That helper compares `git status --short` paths against the alpha commit plan,
separates `generated_artifact_paths`, `generated_local_only_paths`,
`generated_local_by_default_paths`, `cross_cutting_paths`, report paths, and
per-batch changed paths, and flags `unassigned_source_paths` before operators
stage source changes. The helper summary now also records
`generated_local_only_count` and `generated_local_by_default_count` so the same
artifact can distinguish stage-never runtime output from local-by-default
benchmark evidence that might be intentionally frozen with context. JSON and
human output both include `generated_at` freshness metadata, CLI JSON includes
repository `branch` and `head`, and `--output <path>` writes the same JSON
evidence to disk with `output_path` recorded. Add `--include-ignored
--fail-on-generated --fail-on-cross-cutting` for a stricter pre-staging pass
that turns generated local evidence and cross-cutting patch-add work into
`attention_required`, recording `generated_artifacts_present` or
`cross_cutting_paths_present` in `attention_reasons` and the active flags under
`strict_mode`, with `attention_reason_count` summarized for quick triage. Human
output now prints `Generated policy:` plus local-only and local-by-default
previews when generated artifacts are present, prints `Strict mode:` when either
strict flag is active and
`Attention reasons:` when attention blockers are present. Attention reasons are de-duplicated in human output.
Use `--summary-only --json` when a loop or handoff only needs compact evidence:
the payload omits full per-file `batches` details while preserving `summary`,
`attention_reasons`, `changed_batches`, generated-path previews,
`cross_cutting_paths`, `shared_patch_add_paths`, `cross_cutting_groups`, and
repository context.
Next actions are de-duplicated in human output.
The compact summary includes `unchanged_batch_count` alongside changed batch
and path counts so commit-split readiness is visible without reading every batch.
Generated evidence is also split into `generated_artifact_file_count` and
`generated_artifact_dir_count` for local triage.
Shared patch-add paths are also grouped into `cross_cutting_groups` such as
`public_docs_contract`, `command_router_spine`, `current_truth_guards`,
`command_surface_tests`, and `status_reports`, each with a scoped
`git add --patch` command so operators can review cross-cutting changes by
surface instead of staging the whole shared path list. The summary exposes
`cross_cutting_group_count` for compact handoff evidence.
Inside `--summary-only` output, those groups keep ids, titles, `path_count`, and
path previews while omitting full patch-command arrays; oversized group path
lists add `paths_truncated_count`.
Report drift is counted in `report_path_count`.
Human output prints `Batches: changed=` when changed and unchanged batch counts
are available.
Human output prints `Generated artifacts:` with `files=` and `dirs=` when the
generated split is available.
Human output prints `Report paths:` when report drift is present.
Human output prints `Report preview:` with the first dirty report paths.
Batch-filtered human output prints `Selected batch:` and
`Selected staging:` plus `Global attention reasons:` so local batch status,
staging counts, and preserved strict blockers stay visible together.
Each batch `staging_plan` includes `git_add_command` and
`git_add_patch_command` arrays so operators can review exact staging intent
without scraping prose. Strict `--batch` runs keep global blockers: batch filters
preserve generated_artifacts_present as a global blocker, and batch filters
preserve cross_cutting_paths_present as a global blocker, while still reporting
the selected batch status separately with `global_attention_reason_count` and a
selected batch `attention_reason_count`; output write failures return exit code `2`.
Selected batch summaries also record `include_path_count`,
`patch_add_candidate_count`, and `generated_exclude_count` for compact staging
review.
batch filters preserve generated_artifacts_present and
cross_cutting_paths_present in strict mode.

That release gate keeps the publish checklist deterministic by running local
preflight, the worktree commit-plan helper with ignored generated artifacts,
static checks, tests, CLI help smoke checks, QA-Z fast/deep/benchmark, package
build, artifact install smoke, and bundle manifest verification with one JSON
result and one exit code. When `--output` is used, the nested preflight also
writes `dist/alpha-release-gate.preflight.json`, the worktree commit-plan helper
writes `dist/alpha-release-gate.worktree-plan.json`, and the gate JSON records
check counts plus failed check names for release triage.
The gate JSON summarizes pytest, deep, and benchmark evidence so operators can
compare the current pytest pass count, optional pytest skipped count, deep
scan-quality status, and benchmark snapshot without scraping each check's
stdout tail.
When known environment-sensitive failures occur, the gate also records
`evidence.gate_failures` with deterministic blocker kinds such as
`mypy_internal_error`, `semgrep_x509_store_failure`,
`benchmark_results_lock`, `offline_build_dependency_failure`, and
`bundle_path_locked`, plus top-level `environment_failure_count` /
`product_failure_count` counters so operators can see whether the remaining
release blockers are toolchain/runtime issues or QA/product regressions.
Those blocker kinds also promote deterministic `next_actions` and
`next_commands`, so the human gate output points directly at the specific rerun
or cleanup step instead of stopping at a raw traceback.
Each failed gate check also records `failure_scope=environment|product`, and
known environment blockers add `failure_kind` plus a short `failure_summary`, so
the per-check failure list distinguishes local runtime/tooling blockers from
actual QA regressions.
It also summarizes worktree commit-plan evidence, including `changed_batch_count`,
`batch_count`, `changed_path_count`, generated artifact count,
`generated_local_only_count`, `generated_local_by_default_count`,
cross-cutting count, `cross_cutting_group_count`, any unassigned or multi-batch
source-path counts, and copied repository `branch` / `head` context under
`evidence.worktree_commit_plan`.
Strict worktree-plan failures also expose `attention_reasons` and `strict_mode`
in that evidence and promote the helper's `next_actions` into the gate JSON.
If an older benchmark artifact has only counters, the gate synthesizes the same
benchmark `snapshot` from `fixtures_passed`, `fixtures_total`, and
`overall_rate`.
The gate adds a deterministic `release_evidence_consistency` failed check when
summarized benchmark counters disagree with the benchmark `snapshot`, so
publish evidence cannot silently carry contradictory benchmark totals.
That failure also emits a `next_actions` entry telling operators to rerun the
alpha release gate and inspect `python -m qa_z benchmark --json` before
publishing.
The same `release_evidence_consistency` check now fails on a
`worktree generated artifact split mismatch`, telling operators to inspect
`python scripts/worktree_commit_plan.py --include-ignored --json` before
publishing.
The same consistency layer also fails on a
`worktree generated artifact policy split mismatch`, so corrupted helper
payloads cannot silently claim a generated total that no longer matches the
local-only versus local-by-default bucket counts.
It also fails on a `worktree patch-add group mismatch` when compact
`cross_cutting_group_count` exceeds `shared_patch_add_count`, ensuring
cross-cutting review groups always have backing patch-add candidates.
When the nested preflight fails, the gate JSON promotes preflight_failed_checks,
next_actions, and next_commands so the operator can see the blocked preflight
checks, repair steps, and concrete rerun commands without scraping command
output.
The gate JSON deduplicates promoted attention reasons, next_actions, and
next_commands so nested release guidance stays readable when wrappers repeat
the same item.
The gate reads nested preflight output file when stdout is not JSON, so file-backed preflight evidence still surfaces the same failed checks and repair guidance.
The gate reads nested worktree commit-plan output file when stdout is not JSON,
so file-backed commit-split evidence still surfaces the same attention reasons
and repair guidance.
The gate supplements partial preflight stdout from the output file when a wrapper emits JSON without the repair fields.
The gate synthesizes dirty-worktree guidance from failed_checks when an older
partial preflight payload reports worktree_clean without next_actions.
The human-readable gate output prints Next actions and Next commands from the
same preflight payload when repair guidance is available.
Next commands are de-duplicated in human output.
The human-readable gate output prints Evidence from the same pytest, deep, and benchmark summary fields when release evidence is available.
Compact gate Evidence also prints `preflight:` with nested preflight summary and
check counts when preflight evidence is available.
Compact gate Evidence also prints summarized nested preflight `target=`,
optional `origin=`, `origin_state=`, optional `origin_current_target=`,
optional `origin_current=`, `path=`, optional `readiness=`, optional
`blocker=`, optional `refs=` and `ref_sample=`, optional `next_actions=` and
`next_commands=` counts, and `mode=` fields when that evidence is available.
When canonical targets are unavailable it falls back to `target_url=` and
`origin_url=` instead of dropping the raw
repository/origin context.
Compact gate Evidence also prints `artifact smoke:` and `bundle manifest:` with
their compact publish-output summaries when those artifacts are available.
Compact gate Evidence also prints `build:` with the built artifact summary when
package build output is available.
Compact gate Evidence also prints `cli help:` with the number of help surfaces
smoked by the gate.
Deep scan-quality Evidence also prints `warning_types=`, `warning_paths=`, and
`warning_checks=` when Semgrep warning provenance is available.
The human-readable gate Evidence prints unchanged_batches when worktree
commit-plan rollup evidence is available.
The human-readable gate Evidence prints batches and changed_paths when worktree
commit-plan total rollup evidence is available.
The human-readable gate Evidence prints generated_files and generated_dirs when
worktree commit-plan generated split evidence is available.
The human-readable gate Evidence prints `generated_local_only=` and
`generated_local_by_default=` when worktree commit-plan generated policy counts
are available.
The human-readable gate Evidence prints reports= when worktree commit-plan
evidence includes `report_path_count`.
The human-readable gate Evidence prints `patch_add_groups=` when worktree
commit-plan evidence includes `cross_cutting_group_count`.
The human-readable gate Evidence prints output= when worktree commit-plan
evidence records an `output_path`.
The human-readable gate Evidence prints `branch=` and `head=` when worktree
commit-plan evidence records repository provenance, and normalizes detached
checkouts to `branch=detached`.
The human-readable gate output prints Artifacts when nested preflight or
worktree commit-plan evidence paths are available.
The human-readable gate output prints Worktree plan attention when strict
worktree commit-plan attention reasons are available.
The human-readable gate Evidence prints strict=fail_on_generated when strict
worktree commit-plan evidence records active strict flags.
The human-readable gate output prints `Generated at:` when the gate payload
includes freshness metadata.
The nested preflight JSON includes check_count, passed_count, failed_count,
skipped_count, failed_checks, `remote_path`, optional `repository_probe_state`, optional `repository_probe_basis`, optional `repository_probe_generated_at`, optional `repository_probe_freshness`, optional `repository_probe_age_hours`, optional `repository_http_status`, optional `repository_visibility`, optional `repository_archived`, optional `repository_default_branch`, optional `release_path_state`, optional `remote_readiness`,
optional `publish_strategy`,
optional `publish_checklist`,
optional `remote_blocker`, `origin_state`, optional `actual_origin_url`, and optional
`actual_origin_target` alongside the repository, optional canonicalized repository/origin targets,
optional `remote_ref_count`, optional `remote_ref_head_count`, optional
`remote_ref_tag_count`, optional `remote_ref_kinds`, optional
`remote_ref_sample`, branch, tag, and mode inputs.
Both release gate and preflight JSON include `generated_at` so local evidence
freshness can be checked without relying on file mtimes. Human release gate and
preflight output also print `Generated at:` when freshness metadata is present.
Human preflight output now also prints compact `Target:`, `Origin:`, `Mode:`,
and `Decision:` lines before per-check results so remote blockers can be
triaged without re-reading the invoked flags. The `Target:` line now carries
`repo_probe=...`, optional `repo_probe_basis=last_known`, optional
`repo_probe_at=...`, optional `repo_probe_freshness=...`, optional
`repo_probe_age_hours=...`, optional `repo_http=...`, and optional GitHub
metadata such as `repo_visibility=...`, `repo_archived=yes|no`, and
`repo_default_branch=...`. The `Origin:` line now includes the actual
configured origin URL when it is known and `actual=missing` when the repository
has no `origin`.
Compact gate evidence also preserves `repository_http_status` and prints
`repo_http=...` when the nested preflight artifact proves the public GitHub
target responded with a concrete status such as `200` or `404`.
When remote checks were intentionally skipped, the same artifact records
`repository_probe_state=skipped`; otherwise it records
`repository_probe_state=probed` so local-only release evidence does not pretend
it already saw a live remote probe. When `--skip-remote --output <path>` reuses
the last matching live probe stored at that output path, the artifact also adds
`repository_probe_basis=last_known` and preserves
`repository_probe_generated_at`. It also derives
`repository_probe_freshness=carried_forward|stale` plus
`repository_probe_age_hours` so gate evidence can say how old the last matching
GitHub metadata snapshot was when the local-only rehearsal ran.
The same nested GitHub evidence now preserves `repository_visibility`,
`repository_archived`, and `repository_default_branch` so direct-publish
guidance can prove the release target stayed on the public, unarchived default
branch that GitHub reported instead of assuming `main`.
HTTPS, SSH, and schemeless `github.com/owner/repo.git` GitHub URL forms for the
same repository are accepted when preflight compares repository and origin
targets.
The generated-artifact preflight scans root `.qa-z`, `benchmarks/results`,
`benchmarks/results-*`, `dist`, `build`, and `src/qa_z.egg-info` so tracked
generated roots cannot slip into release commits unnoticed.
When that check fails, preflight keeps the existing
`generated_artifacts_untracked` check id but splits tracked generated roots into
local-only runtime artifacts versus local-by-default benchmark evidence, so
tracked benchmark snapshots require an explicit keep-local or freeze decision
instead of being treated like disposable runtime output.
Preflight failures include `next_actions` with the next concrete operator step
and optional `next_commands` with ready-to-run repair commands. Dirty worktree failures now recommend committing, stashing, or intentionally rerunning with
`--allow-dirty`; remote failures recommend creating or exposing the public
`qazedhq/qa-z` repository, `Set --repository-url to https://github.com/qazedhq/qa-z.git`, setting `origin` with
`--expected-origin-url`, choosing the release PR path with
`--allow-existing-refs`, or inspecting an already-published `v0.9.8-alpha`
tag.
When the expected origin target diverges from the repository target, those
`next_commands` normalize back to the intended repository URL and use
`git remote add origin` when `origin` is missing.
When `--skip-remote` is used before public publish and `origin` is still
missing, preflight now marks `remote_readiness=needs_origin_bootstrap` and
emits deterministic `next_commands` to add `origin` and rerun remote checks.
When `origin` is already configured and explicitly acknowledged with
`--expected-origin-url`, the same skip-remote path now marks
`remote_readiness=ready_for_remote_checks` and emits deterministic rerun
commands so the next step is live remote validation, not another local-only
pass.
When remote checks succeed, preflight also records
`release_path_state=remote_direct_publish` for empty-repository direct publish,
`release_path_state=remote_release_pr` for the release PR path,
`release_path_state=local_only_bootstrap_origin` or
`release_path_state=local_only_remote_preflight` for skip-remote local-only
handoff states, and blocker states such as
`release_path_state=blocked_existing_refs`,
`release_path_state=blocked_existing_tag`,
`release_path_state=blocked_origin_alignment`,
`release_path_state=blocked_repository`, or
`release_path_state=blocked_remote_access` when publish cannot proceed yet.
The same artifact also records
`publish_strategy=push_default_branch` for empty-repository direct publish,
`publish_strategy=push_release_branch` for the explicit release PR path, and
`publish_strategy=remote_preflight` or
`publish_strategy=bootstrap_origin` for local-only handoff paths.
Direct publish, release PR, and bootstrap-origin handoff paths also emit a
`publish_checklist` so the post-push CI, PR, origin bootstrap, and tagging
steps stay explicit in the same artifact.
When `origin` is already configured but no `--expected-origin-url` was supplied,
preflight now blocks the publish-path decision until the operator reruns with
the configured origin explicitly acknowledged.

After the public GitHub repository exists, include remote release checks in the
same gate:

```bash
python scripts/alpha_release_gate.py --include-remote --repository-url https://github.com/qazedhq/qa-z.git --expected-origin-url https://github.com/qazedhq/qa-z.git --json
```

`--include-remote` defaults `--expected-origin-url` to the repository URL, so an
equivalent HTTPS or SSH GitHub `origin` for `qazedhq/qa-z` is accepted.
Use `--strict-worktree-plan` during final source staging audits when generated
local evidence should fail the gate instead of remaining advisory. The gate JSON
records that mode as `strict_worktree_plan`.

Try the TypeScript demo:

```bash
cd examples/typescript-demo
npm install
python -m qa_z plan --path . --title "Protect invoice totals" --issue issue.md --spec spec.md
python -m qa_z fast --path . --selection smart
```

## Example policy

`qa-z.yaml.example` is the authoritative full public example config.
The excerpt below shows the intended policy shape:

```yaml
project:
  name: qa-z
  languages:
    - python
    - typescript
  roots:
    - src
    - tests
  critical_paths:
    - auth/**
    - payments/**
    - migrations/**
fast:
  output_dir: .qa-z/runs
  strict_no_tests: false
  fail_on_missing_tool: true
  selection:
    default_mode: full
    full_run_threshold: 40
    high_risk_paths:
      - package.json
      - package-lock.json
      - pnpm-lock.yaml
      - yarn.lock
      - tsconfig.json
      - tsconfig.base.json
      - vitest.config.ts
      - vitest.config.js
      - vite.config.ts
      - vite.config.js
      - eslint.config.js
      - eslint.config.mjs
      - .eslintrc.json
  checks:
    - id: py_lint
      enabled: true
      run: ["ruff", "check", "."]
      kind: lint
    - id: py_format
      enabled: true
      run: ["ruff", "format", "--check", "."]
      kind: format
    - id: py_type
      enabled: true
      run: ["mypy", "src", "tests"]
      kind: typecheck
    - id: py_test
      enabled: true
      run: ["pytest", "-q"]
      kind: test
      no_tests: warn
    - id: ts_lint
      enabled: true
      run: ["eslint", "."]
      kind: lint
    - id: ts_type
      enabled: true
      run: ["tsc", "--noEmit"]
      kind: typecheck
    - id: ts_test
      enabled: true
      run: ["vitest", "run"]
      kind: test
      no_tests: warn
deep:
  fail_on_missing_tool: true
  selection:
    default_mode: full
    full_run_threshold: 15
    exclude_paths:
      - dist/**
      - build/**
      - coverage/**
      - "**/*.generated.*"
    high_risk_paths:
      - qa-z.yaml
      - pyproject.toml
      - package.json
      - tsconfig.json
      - eslint.config.js
  checks:
    - id: sg_scan
      enabled: true
      run: ["semgrep", "--json"]
      kind: static-analysis
      semgrep:
        config: auto
        fail_on_severity:
          - ERROR
        ignore_rules: []
checks:
  selection:
    mode: diff-aware
    max_changed_files: 40
reporters:
  markdown: true
  json: true
  sarif: true
  github_annotations: false
  repair_packet: true
```

The long-term design is for QA-Z to combine:

- repository metadata
- issue or PR context
- explicit QA contracts
- deterministic runner outputs
- agent-friendly repair packets

Today, `qa-z plan` turns optional source files into a contract draft under `qa/contracts/`. If `--title` is omitted, the title is resolved from issue, spec, diff changed file, then `QA-Z Contract`. `qa-z fast` runs configured deterministic Python and TypeScript checks and writes run artifacts under `.qa-z/runs/`; in `--selection smart` mode it can skip docs-only changes, target Python lint/format/test checks, target TypeScript lint/test checks, and conservatively keep Python and TypeScript type checks full. Each fast run updates `.qa-z/runs/latest-run.json` so `latest` resolves deterministically for follow-up commands. `qa-z deep` attaches to `--from-run` when provided, otherwise attaches to the latest valid fast run, creates a new run when no fast run can be attached, and uses `--output-dir` only for standalone deep runs; `--from-run` and `--output-dir` cannot be combined. Deep runs write configured `sg_scan` Semgrep checks into `deep/summary.json`, `deep/summary.md`, `deep/results.sarif`, and `deep/checks/sg_scan.json`; in `--selection smart` mode it skips docs-only changes, targets source/test files, and escalates risky or ambiguous changes to full Semgrep scans. Semgrep policy supports custom `semgrep.config`, `fail_on_severity`, deep `selection.exclude_paths`, and `semgrep.ignore_rules`; artifacts preserve total, blocking, filtered, severity, raw active, grouped, and SARIF finding evidence. `qa-z repair-session` creates a local session manifest, executor guide, session-local pre-live safety artifacts, handoff artifact directory, session-local verification outputs, `outcome.md`, and session `summary.json` around the existing repair and verify code paths. `qa-z verify` compares a baseline run with a candidate run, classifies resolved, still failing, regressed, newly introduced, and skipped or non-comparable evidence, and writes machine-readable plus human-readable verification artifacts. `qa-z self-inspect` turns failed benchmark fixtures, problematic verification verdicts, incomplete sessions, stored executor-result outcomes, executor-result ingest implications, session-local executor-result history patterns, session-local executor-result dry-run verdicts, missing companion artifacts, docs/schema drift indicators, committed benchmark coverage gaps, live dirty-worktree signals, deferred cleanup notes, commit-order dependency reports, runtime artifact hygiene clues, generated-evidence freshness ambiguity, repeated empty-loop history, and repeated fallback-family reuse into a structured backlog. The recorded `live_repository` snapshot now also carries `current_branch`, `current_head`, and `dirty_benchmark_result_count`; stale cleanup-seeding reports are ignored when their date, branch, or head context lags the current inspection surface; clean local benchmark summaries no longer count as deferred-cleanup pressure by themselves; when live `HEAD` is known, structural cleanup and commit-isolation report seeds must also carry a matching report `Head:` line; and human output normalizes detached checkouts to `branch=detached` instead of printing git's raw `HEAD` branch marker. `qa-z select-next` writes selected task and loop-plan artifacts from that backlog, carries the latest self-inspection live repository context forward when available, uses a light recent-history penalty to reduce immediate fallback repetition across exact tasks, categories, and fallback families, and the human stdout now mirrors the selected task title, recommendation, live repository context, selection score, optional penalty reasons, and compact evidence summary instead of only printing artifact paths. `qa-z autonomy` repeats self-inspect/select-next as an auditable loop, can enforce a minimum runtime budget such as four hours, records `fallback_selected` or `blocked_no_candidates` when backlog reseeding is required, now treats any taskless loop as blocked instead of silently leaving it `completed`, writes per-loop and cumulative elapsed timing into outcomes/history, records `selection_gap_reason` plus backlog-open counts before and after inspection when no task survives selection, writes additive `loop_health` summaries with `classification` and `stale_open_items_closed`, maps selected tasks to next actions, records `selected_fallback_families`, creates repair sessions only when local verification compare artifacts identify a usable baseline, records `stop_reason` when repeated blocked loops stop the run, and now renders `no minimum budget` on human runtime lines when that budget is unset. `qa-z executor-bridge` packages a loop-prepared or manually-created repair session into an executor-ready directory with copied inputs, a shared safety-package summary, return-to-verification instructions, and a result template. `qa-z executor-result ingest` is the structured return path that rejects stale, mismatched, or out-of-scope results, records ingest artifacts, stores only accepted external results, appends session-local attempt history when possible, gates verification resume explicitly, and enriches loop history. `qa-z executor-result dry-run` evaluates that stored history against the frozen safety rules, records a stable verdict reason, rule-status counts, operator decision, operator summary, and recommended actions, and stays live-free. `qa-z review`, `qa-z repair-prompt`, and `qa-z github-summary` read sibling `deep/summary.json` when present, so grouped Semgrep findings appear beside fast results without breaking fast-only runs.

The self-inspection, backlog, selected-task, and loop-plan human surfaces include deterministic action and validation command hints, so the next operator move and the evidence refresh command are visible without opening JSON.

Dirty-worktree candidates also summarize changed repository areas in their compact evidence, and the matching action hint uses those top areas when present. That keeps commit-split triage local, deterministic, and reviewable without adding a new command.
Commit-isolation candidates now carry the same dirty area handoff through their `git_status` evidence and area-aware action hint, while preserving the existing candidate id, scoring, JSON shape, and validation command.

See `docs/artifact-schema-v1.md` for the v1/v2 `summary.json`, repair packet, repair handoff, verification, benchmark, self-improvement, executor-result, and adapter artifact fields.

The included CI workflow is a deterministic CI gate: it runs tests, builds the package artifacts, smoke-tests the built wheel and sdist, installs QA-Z and Semgrep, runs `qa-z fast --selection smart --json`, runs `qa-z deep --selection smart --json`, preserves both exit codes, generates review and repair artifacts even when fast or deep checks fail, appends `qa-z github-summary` output to the GitHub Actions Job Summary, uploads `deep/results.sarif` with `github/codeql-action/upload-sarif@v3`, uploads `.qa-z/runs` and `.qa-z/sessions`, and then fails the job according to the original fast/deep verdicts. GitHub PR annotations come from code scanning when the repository grants `security-events: write`; forks or locked-down repositories may still keep the SARIF artifact without publishing code scanning alerts. The workflow template does not run `executor-bridge`, ingest executor results, perform autonomous repair, create branches, commit, push, or post GitHub bot comments.

## Repository map

```text
docs/                     design notes, plans, artifact schema, and MVP backlog
qa/contracts/             QA contract workspace
src/qa_z/                 Python package and CLI surface
templates/                downstream Codex and Claude integration templates
.github/workflows/        CI and Codex review workflows for this repo
examples/                 runnable Python and TypeScript demos plus placeholder examples
benchmarks/               seeded benchmark fixtures, support helpers, and reports
```

## Near-term roadmap

1. Preserve generated versus frozen evidence policy as artifact surfaces evolve.
2. Maintain loop-health summary clarity as autonomy surfaces grow.
3. Broaden operator diagnostics and mixed-history depth only where a new deterministic dry-run slice adds unique evidence.
4. Broaden mixed-surface benchmark realism only where a new deterministic slice adds unique evidence.
5. Keep report, template, and example current-truth sync as maintenance so the alpha docs stay exact.

## Positioning

QA-Z is not another coding agent.

It is the QA layer that helps coding agents reach production quality with traceable contracts, executable checks, and actionable repair feedback.
