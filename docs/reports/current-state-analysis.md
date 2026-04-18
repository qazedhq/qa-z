# QA-Z Current State Analysis

Date: 2026-04-17
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

## Stable Subsystems

### 1. Core Execution, Selection, And Analysis

This is one of the strongest parts of the repository.

What is already present:

- Python and TypeScript fast checks with full and smart selection
- diff-aware selection metadata and changed-file tracking
- Semgrep-backed deep checks with severity thresholds, ignore rules, exclude
  paths, grouping, config-error surfacing, and normalized findings
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
- `tests/test_verification_publish.py`
- `tests/test_github_summary.py`

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
- committed deep-policy fixtures
- committed mixed-language verification fixtures
- committed executed mixed fast plus deep handoff coverage through
  `mixed_fast_deep_handoff_dual_surface` and
  `mixed_fast_deep_handoff_ts_lint_python_deep`, plus
  `mixed_fast_deep_handoff_py_lint_ts_test_dual_deep`
- committed executor bridge action-context packaging coverage through
  `executor_bridge_action_context_inputs` and
  `executor_bridge_missing_action_context_inputs`
- committed mixed-surface executor-result dry-run safety fixtures, including
  `executor_dry_run_validation_noop_operator_actions`,
  `executor_dry_run_repeated_rejected_operator_actions`, and
  `executor_dry_run_repeated_noop_operator_actions`,
  plus `executor_dry_run_blocked_mixed_history_operator_actions` and
  `executor_dry_run_empty_history_operator_actions`, and
  `executor_dry_run_scope_validation_operator_actions`, plus
  `executor_dry_run_missing_noop_explanation_operator_actions`

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
human-readable explanation. Autonomy run summaries also preserve `stop_reason`
when repeated `blocked_no_candidates` loops stop a run before a runtime budget is
met. Autonomy status JSON, human status output, and saved loop plans now also
mirror selected fallback families when they are recorded, so repeated cleanup or
loop-health fallback reuse can be diagnosed without opening `outcome.json`.
Loop-health prepared actions now also carry selected task evidence paths through
`context_paths`, so fallback-diversity handoffs point directly at
`.qa-z/loops/history.jsonl` when loop history explains the task.
Autonomy-created repair-session actions now also preserve selected verification
evidence in `context_paths`, and executor bridges copy existing action context
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

### 3. Mixed-Surface Coverage Is Stronger, But Still Finite

The benchmark corpus now protects mixed Python/TypeScript verification verdicts,
executed mixed-surface realism cases, three mixed fast plus deep interactions
through `mixed_fast_deep_handoff_dual_surface`,
`mixed_fast_deep_handoff_ts_lint_python_deep`, and
`mixed_fast_deep_handoff_py_lint_ts_test_dual_deep`, and live-free dry-run safety
verdicts plus operator-action fixtures including
`executor_dry_run_validation_noop_operator_actions`,
`executor_dry_run_repeated_rejected_operator_actions`, and
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
config example, downstream agent templates, and the Next.js placeholder aligned
with the current alpha command surface and live-free executor boundary. A
workflow template live-free gate sync pass now also pins the shipped GitHub
workflow and reusable workflow template as deterministic CI gates that preserve
artifacts before failing on fast/deep verdicts and do not call live executors,
mutate branches, commit, push, or post bot comments. A TypeScript demo live-free boundary sync pass now also pins the runnable TypeScript example as a fast-only demo, not a Next.js demo, TypeScript-specific deep automation example, or live executor workflow. A FastAPI demo deterministic boundary sync pass now pins the runnable Python example as a dependency-light deterministic fast and repair-prompt demo, not a mandatory web-server, deep automation, repair-session, executor bridge, executor-result, or live-agent workflow. A Next.js placeholder live-free boundary sync pass now pins `examples/nextjs-demo` as a placeholder-only, non-runnable directory with no `package.json`, no `qa-z.yaml`, no live-agent call, and no executor bridge/result workflow. These surfaces still need regular sync so self-inspection is not driven by stale roadmap assumptions.

This is a narrower current-truth problem than before, but it is still real as
the alpha surface keeps changing.

### 5. Live-Free Safety Dry Runs Have A First Operator Diagnostic Pass

QA-Z now has an explicit pre-live safety package plus a local dry-run command
that audits recorded executor-result history against it. An operator diagnostics first pass now records deterministic operator decision, operator summary and recommended actions in dry-run summaries and carries that guidance through repair-session and publish surfaces. The benchmark now pins that path across all committed dry-run fixtures,
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
are regression-protected rather than only counted.
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
the commit plan before the operator reruns self-inspection. Plain `qa-z backlog`
output now reuses that same action hint, so active backlog review and task
selection show the same first operator move without changing the JSON artifact.
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
Benchmark result snapshots under `benchmarks/results-*` are now classified with
runtime artifacts rather than benchmark fixtures, and deferred cleanup action
hints name the local-only versus intentional frozen evidence decision before
source integration.
When deferred cleanup compact evidence leads with report context, the human
summary now appends the concrete `generated_outputs` or `runtime_artifacts`
evidence as `action basis:`, so the freeze/local-only decision is visible without
opening the JSON evidence array.

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

The next roadmap should focus on the layers that make the current local control
plane easier to stabilize and easier to extend without drift:

1. broaden mixed-surface benchmark breadth without redesigning the contract
2. keep report, template, and example surfaces in current-truth sync
3. deepen operator-facing executor diagnostics beyond the operator decision pass without adding live execution
4. preserve generated versus frozen evidence policy as artifact surfaces evolve
5. maintain loop-health summary clarity as autonomy surfaces grow

These priorities are expanded in `docs/reports/next-improvement-roadmap.md`.

## Validation Baseline

The repository baseline for this analysis pass is:

```text
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest
python -m qa_z benchmark --json
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
