# QA-Z Current State Analysis

Date: 2026-04-24
Branch context: `codex/qa-z-bootstrap`

## Purpose

This report captures the current integrated QA-Z state after the accumulated
runner, benchmark, self-improvement, autonomy, repair-session, publishing, and
executor-bridge work already present in the worktree.

This is a repository-analysis baseline, not a feature proposal. It is meant to
answer three questions:

1. What QA-Z can do today
2. Which subsystems look stable enough to treat as the current alpha baseline
3. Which remaining gaps should drive the next improvement roadmap

## Current Capability Snapshot

The current repository surface supports a coherent local QA control-plane flow:

- repository bootstrap with `init`
- contract generation with `plan`
- deterministic fast QA for Python and TypeScript with `fast`
- Semgrep-backed deep QA with `deep`
- run-aware review packets and repair prompts with `review` and `repair-prompt`
- post-repair comparison with `verify`
- local repair orchestration with `repair-session`
- publish-ready GitHub Actions summary rendering with `github-summary`
- seeded local benchmark execution with `benchmark`
- artifact-driven self-inspection, backlog merge, and task selection with
  `self-inspect`, `backlog`, and `select-next`
- deterministic planning loops with `autonomy`
- external packaging for a human or external executor with `executor-bridge`
- structured executor-result ingest and a frozen pre-live executor safety package

Evidence for the command surface is consistent across:

- `README.md`
- `src/qa_z/cli.py`
- `tests/test_cli.py`

The current alpha loop is local and deterministic. It packages evidence for an
external repair actor, but it does not perform live model execution, remote
orchestration, autonomous code editing, commit/push flows, or GitHub bot actions.

Current verification refresh for this work package:

- `python -m pytest`: 1184 passed
- `python -m qa_z benchmark --json`: 54/54 fixtures, overall_rate 1.0
- `python -m ruff check .`: passed
- `python -m ruff format --check .`: 562 files already formatted
- `python -m mypy src tests`: Success: no issues found in 500 source files
- release stageability reference: `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting --output %TEMP%\qa-z-worktree-plan-l19-compact.json`: attention required only for `cross_cutting_paths_present`, with `generated_artifact_count=0`, `generated_local_only_count=0`, `generated_local_by_default_count=0`, `cross_cutting_count=12`, `cross_cutting_group_count=5`, and `unassigned_source_path_count=0`
- ignored-artifact policy reference: `python scripts/worktree_commit_plan.py --include-ignored --summary-only --json --output %TEMP%\qa-z-worktree-plan-l20-include-ignored-postcleanup.json`: ready with `generated_artifact_count=7`, `generated_local_only_count=0`, `generated_local_by_default_count=7`, `cross_cutting_count=12`, `cross_cutting_group_count=5`, and `unassigned_source_path_count=0`
- runtime cleanup reference: `python scripts/runtime_artifact_cleanup.py --apply --json`: deleted 17 local-only runtime artifact roots, left 7 local-by-default benchmark result roots in `review_local_by_default`, and reported `skipped_tracked=0`
- local-only remote preflight reference: `python scripts/alpha_release_preflight.py --skip-remote --allow-dirty --expected-origin-url https://github.com/qazedhq/qa-z.git --json --output %TEMP%\qa-z-preflight-l12-expected-origin.json`: passed with `release_path_state=local_only_remote_preflight`, `remote_readiness=ready_for_remote_checks`, and `origin_target_matches_repository`
- remote publish reference: `python scripts/alpha_release_preflight.py --repository-url https://github.com/qazedhq/qa-z.git --expected-origin-url https://github.com/qazedhq/qa-z.git --allow-dirty --json --output %TEMP%\qa-z-alpha-remote-preflight-l20.json`: still fails with `release_path_state=blocked_repository`, `remote_readiness=needs_repository_bootstrap`, and `remote_blocker=repository_missing` after the configured `origin` matched the intended target
- direct remote ref probe: `git ls-remote --refs https://github.com/qazedhq/qa-z.git`: still fails with `remote: Repository not found.`
- broader alpha-closure reference: `python scripts/alpha_release_gate.py --allow-dirty --output %TEMP%\qa-z-alpha-gate-l18-rerun.json --json`: alpha release gate passed locally again with `1184 passed`, `54/54 fixtures, overall_rate 1.0`, `562 files already formatted`, `500 source files`, build, artifact smoke, bundle manifest, and CLI help all green; the nested local-only preflight still auto-carries the configured `origin` as `--expected-origin-url`

Release evidence hardening is part of this current baseline: alpha gate and
preflight JSON now carry `generated_at`, human output prints `Generated at:`,
remote publish-path evidence now includes `ready_for_remote_checks`,
`actual_origin_target`, `remote_ref_count`, and `remote_ref_sample`,
`release_evidence_consistency` failures include repair-oriented next actions,
and self-inspection exposes live `release_evidence_count` diagnostics without
turning generated local evidence into a new backlog candidate by itself.
The worktree commit-plan evidence is now more actionable too: generated
artifacts split into `generated_local_only_paths` versus
`generated_local_by_default_paths`, and the summary now carries
`generated_local_only_count` plus `generated_local_by_default_count` so
alpha-release evidence can preserve the same bucket counts. The latest strict
audit stays limited to generated artifact review instead of source-ownership
drift. That helper now expands untracked source paths with
`git status --short --untracked-files=all`, so batch ownership is based on real
file paths rather than collapsed directory entries. Shared patch-add command
spine paths also stay explicit instead of leaking wholesale into the
planning/runtime batch: `src/qa_z/cli.py`,
`src/qa_z/commands/command_registration.py`,
`src/qa_z/commands/command_registry.py`, `src/qa_z/commands/execution.py`,
`src/qa_z/commands/runtime.py`, and their direct runtime/architecture tests now
remain cross-cutting staging surfaces. The fresh compact strict snapshot now
reports `0` visible generated artifact roots and no source-ownership drift; the
remaining strict attention is the `12` cross-cutting staging surfaces that need
patch-add ownership. The include-ignored policy snapshot still keeps ignored
output visible for operator review after cleanup: `7` generated roots total,
`0` local-only runtime artifact roots, and `7` local-by-default benchmark
evidence roots. The
helper-backed runtime cleanup path mirrors that same policy split by discovering
the same local-only buckets that strict worktree planning reports. That means
`.qa-z/**`, `benchmarks/results/work/**`, `build/**`, `dist/**`,
`src/qa_z.egg-info/**`, literal `%TEMP%/**` scratch roots, root `/tmp_*`
scratch, `/benchmarks/minlock-*`, and cache trees such as `__pycache__/`,
`.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.mypy_cache_safe/`, and
`.ruff_cache_safe/` can all move into `planned`/`deleted`, while
`benchmarks/results/` plus `benchmarks/results-*` stay
`review_local_by_default` even when `--apply` is used. The tracked `mypy.ini`
now keeps mypy's cache under `$TEMP/qa-z-mypy-cache`, so Windows mypy runs do
not recreate workspace-local cache pressure while preserving a deterministic
config surface.

## Stable Subsystems

### 1. Core Execution, Selection, And Analysis

This is one of the strongest parts of the repository.

What is already present:

- Python and TypeScript fast checks with full and smart selection
- diff-aware selection metadata and changed-file tracking
- Semgrep-backed deep checks with severity thresholds, ignore rules, exclude
  paths, grouping, config-error surfacing, and normalized findings
- Semgrep scan-quality warnings surfaced as `scan_warning_count`,
  `scan_warnings`, and summary-level `scan_quality`, so taint-analysis timeouts
  remain non-blocking but visible without opening raw stdout tails
- SARIF generation for deep findings
- review and repair packet generation that can include deep context
- repair handoff rendering for Codex and Claude

Primary evidence:

- `src/qa_z/runners/fast.py`
- `src/qa_z/runners/deep.py`
- `src/qa_z/runners/selection.py`
- `src/qa_z/runners/selection_deep.py`
- `src/qa_z/runners/selection_typescript.py`
- `src/qa_z/runners/semgrep.py`
- `src/qa_z/reporters/sarif.py`
- `src/qa_z/repair_handoff.py`
- `tests/test_fast_selection.py`
- `tests/test_fast_config.py`
- `tests/test_deep_selection.py`
- `tests/test_deep_run_resolution.py`
- `tests/test_semgrep_normalization.py`
- `tests/test_repair_handoff.py`
- `tests/test_repair_prompt.py`

Assessment:

- strong deterministic foundation
- good regression coverage on selection and Semgrep normalization
- clear separation between core engine behavior and adapter rendering

### 2. Verification, Repair Sessions, And Publishing

This is also in good shape for a local alpha baseline.

What is already present:

- baseline vs candidate comparison across fast checks and deep findings
- verdicts for `improved`, `unchanged`, `mixed`, `regressed`, and
  `verification_failed`
- repair-session manifests, executor guides, handoff packaging, rerun-based
  verification, and outcome summaries
- session-local executor-result history and live-free dry-run audit artifacts
- executor-result ingest stdout diagnostics with source context, report path,
  live repository context, freshness/provenance checks, and backlog implications
- concise verification/session publish summaries
- GitHub Actions summary rendering with failed checks, deep context, and repair
  outcome context

Primary evidence:

- `src/qa_z/verification.py`
- `src/qa_z/repair_session.py`
- `src/qa_z/executor_history.py`
- `src/qa_z/executor_dry_run.py`
- `src/qa_z/reporters/verification_publish.py`
- `src/qa_z/reporters/github_summary.py`
- `tests/test_verification.py`
- `tests/test_repair_session.py`
- `tests/test_executor_result.py`
- `tests/test_verification_publish_summary.py`
- `tests/test_verification_publish_session.py`
- `tests/test_verification_publish_architecture.py`
- `tests/test_github_summary_render.py`
- `tests/test_github_summary_session.py`
- `tests/test_github_summary_deep.py`

Assessment:

- verification contract is already meaningful, not placeholder documentation
- repair-session flow provides a usable local orchestration shell around existing
  handoff and verification artifacts
- publishing layer stays deterministic and avoids pretending to be live GitHub
  automation

### 3. Benchmark And Regression Protection

The benchmark layer is one of the clearest strengths in the current repository.

What is already present:

- local fixture discovery and execution
- expectation contracts for fast, deep, handoff, verify, artifact, executor bridge, executor-result ingest, and executor-result dry-run outcomes
- category-level summary rates for detection, handoff, verify, artifact, and
  policy
- committed Python fast fixtures
- committed TypeScript fast fixtures
- committed deep-policy fixtures, including `deep_scan_warning_diagnostics` and
  `deep_scan_warning_multi_source_diagnostics` for non-blocking Semgrep
  `scan_warning_count`, `scan_warnings`, multi-source warning path/type, and
  `scan_quality` coverage
- deep benchmark summaries now expose `run_resolution_source`,
  `attached_to_fast_run`, and `run_resolution_fast_summary_path`, so attached
  and standalone deep evidence cannot silently swap artifact lineage
- committed mixed-language verification fixtures
- committed executed mixed fast plus deep handoff coverage through
  `mixed_fast_deep_handoff_dual_surface` and
  `mixed_fast_deep_handoff_ts_lint_python_deep`, plus
  `mixed_fast_deep_handoff_py_lint_ts_test_dual_deep` and
  `mixed_fast_deep_scan_warning_fast_only`
- committed executor bridge action-context packaging coverage through
  `executor_bridge_action_context_inputs` and
  `executor_bridge_missing_action_context_inputs`
- committed mixed-surface executor-result dry-run safety fixtures, including
  `executor_dry_run_validation_noop_operator_actions`,
  `executor_dry_run_repeated_rejected_operator_actions`, and
  `executor_dry_run_validation_conflict_repeated_rejected_operator_actions`, and
  `executor_dry_run_repeated_noop_operator_actions`,
  plus `executor_dry_run_blocked_mixed_history_operator_actions` and
  `executor_dry_run_empty_history_operator_actions`, and
  `executor_dry_run_scope_validation_operator_actions`, plus
  `executor_dry_run_missing_noop_explanation_operator_actions`
- the repeated rejected dry-run fixture now keeps rejected-result inspection
  ahead of partial retry review when mixed partial and rejected histories repeat
- benchmark runs now protect each `--results-dir` with `.benchmark.lock` before
  resetting `work/`, which avoids Windows race conditions when operators run
  parallel fixture experiments

Primary evidence:

- `src/qa_z/benchmark.py`
- `docs/benchmarking.md`
- `tests/test_benchmark.py`
- `benchmarks/fixtures/**`
- `benchmarks/support/**`

Important current-state note:

Mixed-language verification coverage is already present in the current worktree.
The roadmap should not treat "add any mixed-language benchmark at all" as an
unstarted item. The remaining benchmark gap is narrower: executed mixed-surface
cases and live-free dry-run histories still have room for more breadth, but the
contract class itself is already landed.

Assessment:

- strong regression-defense story for an alpha project
- benchmark corpus is aligned with deterministic contracts rather than vague QA
  aspirations
- repository claims are increasingly backed by executable evidence

### 4. Self-Inspection, Backlog, And Autonomy Planning

The planning layer is real and already internally consistent.

What is already present:

- artifact inspection across benchmark, verification, session, docs, and schema
  signals
- deterministic backlog merge and scoring
- selection of the next 1 to 3 open tasks
- loop plan and history artifacts
- deterministic autonomy loops that can prepare repair sessions when verification
  evidence points to a baseline run

Primary evidence:

- `src/qa_z/self_improvement.py`
- `src/qa_z/autonomy.py`
- `tests/test_self_improvement.py`
- `tests/test_autonomy.py`

Assessment:

- QA-Z now has a real planning brain
- backlog generation is evidence-based rather than prompt-only
- loop output is structured enough to support later executor integration

### 5. External Executor Packaging

The packaging side of external execution is ready enough to count as part of the
current alpha state.

What is already present:

- bridge creation from a repair session or autonomy loop
- copied session, handoff, and optional autonomy inputs
- copied session-local executor safety artifacts and a bridge `safety_package` summary
- executor-facing Markdown wrappers
- validation command arrays and return-to-verification instructions
- explicit non-goals, safety constraints, and a shared pre-live safety package

Primary evidence:

- `src/qa_z/executor_bridge.py`
- `docs/repair-sessions.md`
- `tests/test_executor_bridge.py`
- `docs/artifact-schema-v1.md`

Assessment:

- export side is coherent
- bridge contract clearly says QA-Z is not the live executor
- the pre-live safety boundary is now explicit instead of scattered

## Known Gaps

### 1. Loop Health And Empty-Loop Handling Is Explicit

QA-Z already has backlog reseeding, fallback-family rotation, blocked-loop
stopping rules, and explicit taskless-loop residue through `selection_gap_reason`
plus backlog-open counts before and after inspection.

The taskless-loop evidence is now also summarized through `loop_health` objects
on autonomy outcomes, history, and status surfaces. The summary records
`classification`, selected count, fallback state, stale open items closed, and a
human-readable explanation. Taskless loops also keep blocked no-candidate chain
residue visible through `blocked_chain_length` and
`blocked_chain_remaining_until_stop`, and `blocked_chain_loop_ids`, so the human
surfaces can show how close a run is to the repeated-blocked stop rule and
which loop ids produced that residue without reopening loop history. Autonomy run summaries also preserve `stop_reason`
when repeated `blocked_no_candidates` loops stop a run before a runtime budget is
met. Autonomy status JSON, human status output, and saved loop plans now also
mirror selected fallback families when they are recorded, so repeated cleanup or
loop-health fallback reuse can be diagnosed without opening `outcome.json`.
Loop-health prepared actions now also carry selected task evidence paths,
loop-local self-inspection, and current-state and roadmap references through
`context_paths`, so fallback-diversity handoffs point directly at
`.qa-z/loops/history.jsonl` while still carrying the loop-local inspection
packet that produced the recommendation.
Loop-local self-inspection now also stays attached to cleanup and workflow prepared actions through `context_paths`, so worktree-oriented handoffs preserve the exact self-inspection artifact that produced the recommendation instead of depending on a later `latest` mirror.
Autonomy-created repair-session actions now also preserve loop-local
self-inspection plus selected verification evidence in `context_paths`, and
executor bridges copy existing action context
files into `inputs/context/` while recording `inputs.action_context` and
`inputs.action_context_missing` in `bridge.json`. Human executor-bridge stdout
now mirrors action-context package health and missing action-context diagnostics
so an operator can see skipped optional context without opening the manifest.

The remaining gap is maintenance: keep future loop-health signals additive and
readable without changing the deterministic selection boundary.

### 2. Generated Versus Frozen Evidence Policy Is Now Explicit

QA-Z now has an explicit generated versus frozen evidence policy in
`docs/generated-vs-frozen-evidence-policy.md`. Root `.qa-z/**` and
`benchmarks/results/work/**` stay local. `benchmarks/results/summary.json` and
`benchmarks/results/report.md` are local by default and should be committed only
as intentional frozen evidence with surrounding context.

Self-inspection now treats the policy as explicit only when both the ignore
rules and policy document are present. The remaining work is maintenance:
preserve that boundary as new artifact surfaces are added. Deferred generated
cleanup action packets now also carry the policy document through
`context_paths`, so autonomy handoffs preserve the local-only versus intentional
frozen evidence decision with the prepared action.
When that policy is explicit, live runtime artifact paths can still keep
artifact-hygiene and runtime-cleanup work open, but they no longer reopen
`evidence_freshness_gap` by themselves. This keeps cleanup signals actionable
without relabeling an already-documented policy as ambiguous.
In that explicit-policy state, runtime-cleanup now ranks ahead of generic
artifact-hygiene so operators clear policy-managed local artifacts before
revisiting the broader source/evidence separation work.
Deferred cleanup, commit-isolation, and integration report-only evidence is not
enough to reseed those candidates when the live worktree is clean. Those
self-inspection cleanup-family candidates now require live git or runtime
artifact evidence, so older worktree reports remain useful context without
reopening already-resolved cleanup work. Report-driven artifact-hygiene and
evidence-freshness policy candidates remain separate policy-maintenance signals.

### 3. Mixed-Surface Coverage Is Stronger, But Still Finite

The benchmark corpus now protects mixed Python/TypeScript verification verdicts,
executed mixed-surface realism cases, four mixed fast plus deep interactions
through `mixed_fast_deep_handoff_dual_surface`,
`mixed_fast_deep_handoff_ts_lint_python_deep`,
`mixed_fast_deep_handoff_py_lint_ts_test_dual_deep`, and
`mixed_fast_deep_scan_warning_fast_only`, and live-free dry-run safety
  verdicts plus operator-action fixtures including
`executor_dry_run_validation_noop_operator_actions`,
`executor_dry_run_repeated_rejected_operator_actions`, and
`executor_dry_run_validation_conflict_repeated_rejected_operator_actions`, and
`executor_dry_run_repeated_noop_operator_actions`, plus the blocked mixed-history
case `executor_dry_run_blocked_mixed_history_operator_actions` and the
empty-history ingest-guidance case
`executor_dry_run_empty_history_operator_actions`, plus the scope-validation
scope-drift case `executor_dry_run_scope_validation_operator_actions` and the
missing no-op explanation case
`executor_dry_run_missing_noop_explanation_operator_actions`. The bridge-local
action context copy path is also pinned by
`executor_bridge_action_context_inputs`, and missing optional action context is
pinned by `executor_bridge_missing_action_context_inputs`, so loop-prepared
repair-session evidence must continue to appear under executor bridge
`inputs/context/` when available and remain visible in guide diagnostics when a
context file cannot be copied. The same fixtures now also pin human stdout
diagnostics, so action-context package health remains visible in benchmark
evidence rather than only in unit tests. It can still broaden its proof surface
across:

- smart fast selection in mixed repos
- denser mixed fast plus deep interactions beyond the first three executed fixtures
- mixed repair handoff aggregation for additional real executed failures
- additional denser dry-run history combinations that stay deterministic

This is no longer a missing-class problem. It is now a breadth and density gap.

### 4. Report And Template Current-Truth Sync Still Needs Ongoing Discipline

README, schema docs, benchmark docs, and tests now reflect much more of the
landed system. A template and example sync first pass now also keeps the public
config example, README excerpt wording, downstream agent templates, and the
Next.js placeholder aligned with the current alpha command surface and live-free
executor boundary. A workflow template live-free gate sync pass now also pins
the shipped GitHub workflow and workflow template as deterministic CI gates that
preserve artifacts before failing on fast/deep verdicts and do not call live
executors, ingest executor results, perform autonomous repair, mutate branches,
commit, push, or post bot comments. A TypeScript demo live-free boundary sync
pass now also pins the runnable TypeScript example as a fast-only demo, not a
Next.js demo, TypeScript-specific deep automation example, or live executor
workflow. A FastAPI demo deterministic boundary sync pass now pins the runnable
Python example as a dependency-light deterministic fast and repair-prompt demo,
not a mandatory web-server, deep automation, repair-session, executor bridge,
executor-result, or live-agent workflow. A Next.js placeholder live-free
boundary sync pass now pins `examples/nextjs-demo` as a placeholder-only,
non-runnable directory with no `package.json`, no `qa-z.yaml`, no live-agent
call, and no executor bridge/result workflow. These surfaces still need regular
sync so self-inspection is not driven by stale roadmap assumptions.

This is a narrower current-truth problem than before, but it is still real as
the alpha surface keeps changing.

### 5. Live-Free Safety Dry Runs Have A First Operator Diagnostic Pass

QA-Z now has an explicit pre-live safety package plus a local dry-run command
that audits recorded executor-result history against it. An operator diagnostics first pass now records deterministic operator decision, operator summary and recommended actions in dry-run summaries and carries that guidance through repair-session and publish surfaces. Repair-session outcome Markdown and GitHub-facing publish summaries now also keep ordered `Action <id>:` lines for those recommended actions instead of flattening mixed-history residue into one sentence. The blocked mixed-history path now keeps verification blockers primary while still saying validation conflicts and retry pressure still need review. The benchmark now pins that path across all committed dry-run fixtures,
including `executor_dry_run_validation_noop_operator_actions` and
`executor_dry_run_blocked_mixed_history_operator_actions`; empty-history sessions
are now also pinned by `executor_dry_run_empty_history_operator_actions`, which
keeps the next recommendation aligned with the `ingest_executor_result` action,
and scope-validation failures are pinned by
`executor_dry_run_scope_validation_operator_actions`, which keeps the blocked
mutation-scope verdict aligned with `inspect_scope_drift`. Missing no-op
explanations are pinned by
`executor_dry_run_missing_noop_explanation_operator_actions`, and the attention
fixtures now keep top-level next recommendations aligned with their specific
operator actions. Repeated no-op history now also marks
`retry_boundary_is_manual` as attention, keeping rule counts aligned with the
manual retry-review verdict. Empty-history sessions now mark
`executor_history_recorded` as attention, keeping no-recorded-attempt verdicts
aligned with rule counts as well. All committed dry-run fixtures now also pin
complete dry-run rule buckets, so clear, attention, and blocked rule partitions
are regression-protected rather than only counted. The repeated rejected
fixture now also keeps rejected-result inspection ahead of partial retry review
when mixed partial and rejected histories repeat. The validation-conflict mixed
retry fixture now keeps validation-conflict review primary while preserving
rejected-result inspection and partial retry review in non-blocked history. The
blocked mixed-history
fixture now also keeps verification blockers primary while saying validation
conflicts and retry pressure still need review.
Executor-result ingest operator diagnostics now also mirror source context in
non-JSON stdout and split partial source provenance into a `Source Context`
section in reports even when no live repository snapshot is available.
The remaining gap is no longer basic visibility but depth: broader mixed-history
coverage and richer explanations around what repeated mixed histories should
trigger next.

## Deliberate Non-Gaps

The following are intentionally out of scope for the current alpha and should not
be mislabeled as missing baseline work:

- live Codex or Claude API execution
- remote orchestration, queues, or schedulers
- autonomous code editing loops
- multi-engine deep QA beyond the current Semgrep-backed path
- TypeScript deep automation
- property, mutation, or smoke deep execution

Those items can come later. They are not blockers for stabilizing the current
baseline.

## Worktree And Integration Caveats

The current state is best understood as an accumulated alpha integration branch,
not as a single reviewable feature diff.

The already-written commit reports remain the right baseline references:

- `docs/reports/worktree-triage.md`
- `docs/reports/worktree-commit-plan.md`

The alpha closure readiness snapshot is now pinned in
`docs/reports/worktree-commit-plan.md`, including the latest full local gate pass,
benchmark count, static checks, and generated-output staging policy.
Self-inspection now uses that snapshot as closure-aware commit-isolation evidence,
so the backlog can point operators toward commit splitting with the gate context
already attached. Compact selected-task evidence summaries now prioritize that
closure-aware commit-isolation context over generic report-drift summaries, so
human `qa-z select-next` output leads with the actionable gate snapshot. The same
selected-task surfaces now also render a deterministic action hint from the
recommendation id, so closure work such as `isolate_foundation_commit` points at
the commit plan before the operator reruns self-inspection. The fallback-diversity
action hint now also says to surface a non-cleanup fallback family before
selecting more cleanup work when loop-history evidence names cleanup as the
repeated family, so loop-health plans stay aligned with the batch-diversity
selection contract. Plain `qa-z backlog`
output now reuses that same action hint, so active backlog review and task
selection show the same first operator move without changing the JSON artifact.
The worktree commit-plan helper no longer leaves the shared subprocess/tooling
quartet (`pyproject.toml`, `src/qa_z/subprocess_env.py`,
`src/qa_z/runners/subprocess.py`, and `tests/test_release_script_environment.py`)
in the generic unassigned bucket, so the remaining dirty-worktree risk is now
generated-artifact review and actual batch staging rather than missing path
ownership.
Plain `qa-z self-inspect` now also prints the top candidates with the same
action-hint vocabulary, so the inspection, backlog, and selection handoff
surfaces all expose the next operator move before anyone opens the JSON files.
Those same human planning surfaces and generated loop plans now also include a
deterministic `validation:` command hint, so the operator can refresh evidence
after the work without changing the machine-readable backlog or selection
artifacts.
Dirty-worktree self-inspection evidence now also classifies modified and
untracked paths into deterministic repository areas such as benchmark, docs,
source, tests, examples, templates, workflow, config, and runtime artifacts. That
keeps commit-split triage visible in the compact evidence summary instead of
requiring every operator to reopen the full worktree status first.
When those area counts exist, the dirty-worktree `action:` hint now names the
top one or two areas as the first triage target, keeping the operator handoff
aligned with the compact evidence.
Commit-isolation candidates now reuse the same area counts in their `git_status`
evidence, and their action hint can name the top areas to isolate into the
foundation split while preserving the closure-aware commit-plan evidence as the
compact summary.
When compact evidence leads with that closure snapshot, the human summary now
adds an `action basis:` suffix with the area-bearing `git_status` evidence, so
the area-aware action text stays explainable without opening the JSON evidence
array.
Benchmark result snapshots under `benchmarks/results-*` are now kept visible as
local-by-default benchmark result evidence rather than being folded into
`runtime_artifact_paths`, and deferred cleanup action hints still name the
local-only versus intentional frozen evidence decision before source
integration.
When deferred cleanup compact evidence leads with report context, the human
summary now appends the concrete `generated_outputs` or `runtime_artifacts`
evidence as `action basis:`, so the freeze/local-only decision is visible without
opening the JSON evidence array.
Deferred cleanup, commit-isolation, and integration report-only evidence is not
enough for those candidates anymore: the current implementation requires live
git or runtime artifact evidence before report wording can seed that work.
Integration-gap candidates now append live `git_status` area evidence too, so
`audit_worktree_integration` guidance can point at the benchmark/docs/source/tests
surfaces instead of sending operators back to report text alone.
Self-inspection JSON now also carries a top-level `live_repository` snapshot with
dirty counts, runtime artifact count, benchmark result count,
`dirty_benchmark_result_count`, generated alpha release evidence count,
`generated_artifact_policy_explicit`, `current_branch`, `current_head`, and
`dirty_area_summary`, so operators can verify candidate currentness without
reverse-engineering the evidence list.
Dirty snapshot roots matching `benchmarks/results-*` now contribute to
`benchmark_result_count` and `dirty_benchmark_result_count` without reopening
`runtime_artifact_cleanup_gap` by themselves when the policy is already
explicit.
Those local-by-default benchmark result roots also stay in the `benchmark`
bucket for `dirty_area_summary`, so self-inspection and action hints do not
misread them as local-only runtime cleanup pressure.
Human `Live repository:` lines normalize detached checkouts to
`branch=detached`, so git's raw `HEAD` marker does not leak into operator-facing
status text.
Runtime artifact cleanup can also be raised directly from live artifact paths,
even when no report prose repeats the same issue.

Recommended commit order remains:

1. runner, repair, and verification foundations
2. benchmark coverage
3. self-inspection, backlog, and task selection
4. autonomy loops
5. repair-session and verification publishing
6. executor bridge packaging
7. cleanup reports and residual docs

Generated or deferred items should continue to stay outside normal source commits:

- root `.qa-z/**`
- `benchmarks/results/work/**`
- `benchmarks/results/summary.json`
- `benchmarks/results/report.md`
- any local cache or personal runtime state

## Recommended Next Priorities

The first report/template/example sync pass is now landed, and the documented
Priority 5 mixed-history slice is now committed across logic, benchmark,
publish, and continuity surfaces. The next roadmap should focus on the
remaining layers that make the current local control plane easier to stabilize
and easier to extend without drift:

1. preserve generated versus frozen evidence policy as artifact surfaces evolve
2. maintain loop-health summary clarity as autonomy surfaces grow
3. deepen operator-facing executor diagnostics selectively as new mixed-history combinations add unique residue, without adding live execution
4. broaden mixed-surface benchmark realism only where a new deterministic slice adds unique evidence
5. keep report, template, and example surfaces in current-truth sync as maintenance so they do not drift

These priorities are expanded in `docs/reports/next-improvement-roadmap.md`.
The latest Priority 2 maintenance slice is now also closed on the release path:
alpha release preflight reuses the same helper-derived generated-artifact
bucket split already used by worktree planning and runtime cleanup, so tracked
generated roots now surface as either local-only runtime artifacts or
local-by-default benchmark evidence instead of one opaque preflight blocker.
Nested gate evidence carries those tracked-generated counts forward without
promoting full path lists, and release docs/schema now describe the same split.
The latest narrower continuity slice is now closed as well: cleanup and
workflow prepared actions now keep loop-local self-inspection in
`context_paths`, and current-truth release continuity pins the same contract
across README, schema, current state, and roadmap wording. The release track is
no longer blocked on source stageability: `python scripts/alpha_release_gate.py
--allow-dirty --output .qa-z/tmp/alpha-release-gate-l35.json --json` now
passes locally again even after `origin` bootstrap, and the strict helper no
longer reports unassigned source paths. The remaining blocker is remote
publication:
`python scripts/alpha_release_preflight.py --repository-url
https://github.com/qazedhq/qa-z.git --expected-origin-url
https://github.com/qazedhq/qa-z.git --allow-dirty --json --output
.qa-z/tmp/alpha-release-preflight-remote-l35.json` fails with
`release_path_state=blocked_repository`,
`remote_readiness=needs_repository_bootstrap`, and
`remote_blocker=repository_missing` because `qazedhq/qa-z` still returns
`404 Not Found` even though `origin` now points at the intended URL.
The 2026-04-24 live recheck keeps that same blocker classification: fresh
remote preflight evidence was written to
`.qa-z/tmp/alpha-release-preflight-remote-live.json`, GitHub app search returned
no visible `qazedhq/qa-z` repository, the only installed account visible to this
session is `ggbu75769-dot`, and GitHub org visibility is
empty, so Stage 4-5 remain blocked by external repository bootstrap plus access
alignment rather than a new repo-local release gap.
A later same-day probe kept that result unchanged:
`git ls-remote --refs https://github.com/qazedhq/qa-z.git` still returned
`remote: Repository not found.`, so the blocker remains at the remote owner
boundary rather than inside QA-Z's local release surface.

For the current release track, the immediate blocker sequence is narrower than
the standing roadmap:

1. create or expose the public `qazedhq/qa-z` repository, or deliberately align the expected target to a different reachable repository
2. rerun remote preflight against the configured `origin`
3. choose direct publish versus release-PR cutover only after the remote target is reachable and empty-or-known by policy
4. tag only after the remote baseline is pushed and remote CI passes

## Validation Baseline

The repository baseline for this analysis pass is:

```text
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest
python -m qa_z benchmark --json
```

Latest observed outputs:

```text
python -m pytest -> 1184 passed
python -m qa_z benchmark --json -> 54/54 fixtures, overall_rate 1.0
python -m ruff check . -> passed
python -m ruff format --check . -> 562 files already formatted
python -m mypy src tests -> Success: no issues found in 500 source files
python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting --output %TEMP%\qa-z-worktree-plan-l19-compact.json -> attention_required, generated_artifact_count=0, generated_local_only_count=0, generated_local_by_default_count=0, cross_cutting_count=12, cross_cutting_group_count=5, unassigned_source_path_count=0
python scripts/worktree_commit_plan.py --include-ignored --summary-only --json --output %TEMP%\qa-z-worktree-plan-l20-include-ignored-postcleanup.json -> ready, generated_artifact_count=7, generated_local_only_count=0, generated_local_by_default_count=7, cross_cutting_count=12, cross_cutting_group_count=5, unassigned_source_path_count=0
python scripts/alpha_release_preflight.py --repository-url https://github.com/qazedhq/qa-z.git --expected-origin-url https://github.com/qazedhq/qa-z.git --allow-dirty --json --output %TEMP%\qa-z-alpha-remote-preflight-l20.json -> release preflight failed, release_path_state=blocked_repository, remote_readiness=needs_repository_bootstrap, remote_blocker=repository_missing
python scripts/alpha_release_gate.py --allow-dirty --output %TEMP%\qa-z-alpha-gate-l18-rerun.json --json -> alpha release gate passed locally again; remote publish remains blocked by missing repository bootstrap
```

Useful smoke checks for the current alpha surface:

```text
python -m qa_z --help
python -m qa_z self-inspect --help
python -m qa_z select-next --help
python -m qa_z autonomy --help
python -m qa_z repair-session --help
python -m qa_z executor-bridge --help
python -m qa_z github-summary --help
```

