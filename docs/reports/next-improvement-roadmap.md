# QA-Z Next Improvement Roadmap

Date: 2026-04-17
Branch context: `codex/qa-z-bootstrap`

## Purpose

This roadmap tracks the highest-value follow-up work after the integrated
executor-history, dry-run provenance, mixed-surface realism, and autonomy-control
passes already present in the worktree. It is grounded in repository evidence,
not in hypothetical future architecture.

It assumes the current cleanup reasoning remains in force:

- use `docs/reports/worktree-commit-plan.md` as the commit split order
- keep generated runtime artifacts out of source commits
- do not start live executor work until the current baseline is commitable and
  validated

Status update:

- the external executor return contract and deterministic return path are landed
- executed mixed-surface realism coverage is landed and now in breadth-expansion mode
- session-local multi-result history plus the live-free safety dry-run are landed
- dry-run provenance now stays visible across repair-session, publish, benchmark, and self-inspection surfaces
- generated versus frozen evidence policy is now explicit in `docs/generated-vs-frozen-evidence-policy.md`
- loop health now has explicit `loop_health` summaries and repeated-blocked stop reasons
- the remaining active roadmap is now about benchmark breadth, report/template sync, operator diagnostics, and policy maintenance rather than missing baseline return-path foundations

## Ordering Principle

The next work should improve the current control plane where it is most
structurally incomplete:

1. expand benchmark realism where current coverage is still thin
2. keep report, template, and example current-truth sync ahead of drift
3. deepen operator diagnostics around executor history without adding live execution
4. preserve the generated versus frozen evidence policy as artifact surfaces evolve
5. maintain loop-health summary clarity as autonomy surfaces grow

## Priority 1: Empty-Loop And Loop-Health Maintenance

### Why This Matters

Autonomy already has backlog reseeding, fallback-family rotation, blocked-loop
stopping rules, explicit `loop_health` summaries, and repeated-blocked
`stop_reason` evidence. The remaining work is to keep that explanation layer
current as new loop states are added.

### Repository Evidence

- `.qa-z/loops/history.jsonl` can accumulate recent empty-loop chains
- `outcome.json`, `loop_plan.md`, history, and `qa-z autonomy status` now
  preserve `selection_gap_reason`, backlog-open counts, `loop_health`, and
  stale-open-item closure counts for taskless loops
- `src/qa_z/autonomy.py` and `src/qa_z/self_improvement.py` already classify
  blocked and fallback loops, so the remaining work is refinement rather than a
  missing subsystem
- `tests/test_autonomy.py` and `tests/test_self_improvement.py` already cover
  the current empty-loop and reseeding behavior

### Scope

- keep empty-loop classification and stop conditions explicit
- keep loop history readable when no task is selected
- preserve additive `loop_health` fields as autonomy evolves
- keep selected fallback families visible in status and loop plans for repeated-selection diagnostics
- keep loop-health prepared action `context_paths` pointing at loop-history evidence for fallback-diversity work
- keep autonomy-created repair-session action `context_paths` flowing into executor bridge `inputs/context/` files

## Priority 2: Generated Versus Frozen Evidence Policy Maintenance

### Why This Matters

QA-Z now produces valuable runtime evidence, and the boundary between generated
local artifacts and intentionally tracked repository evidence is explicit in
`docs/generated-vs-frozen-evidence-policy.md`. The remaining need is to keep new
artifact surfaces aligned with that policy.

### Repository Evidence

- `benchmarks/results/summary.json` and `benchmarks/results/report.md`
- `.qa-z/**` runtime state and loop artifacts
- `docs/generated-vs-frozen-evidence-policy.md`
- `.gitignore`
- self-inspection artifact-hygiene and evidence-freshness policy snapshot fields

### Scope

- keep root `.qa-z/**` and `benchmarks/results/work/**` local
- keep `benchmarks/results/summary.json` and `benchmarks/results/report.md` local by default unless intentionally frozen evidence is documented
- update the policy document and self-inspection terms when new artifact surfaces are added
- keep `triage_and_isolate_changes` prepared actions carrying `docs/generated-vs-frozen-evidence-policy.md` through `context_paths`

## Priority 3: Mixed-Surface Benchmark Breadth

### Why This Matters

Executed mixed-surface realism is now landed. The first mixed fast plus deep executed fixture, `mixed_fast_deep_handoff_dual_surface`, is landed. The second mixed fast plus deep executed fixture, `mixed_fast_deep_handoff_ts_lint_python_deep`, is also landed. The third mixed fast plus deep executed fixture, `mixed_fast_deep_handoff_py_lint_ts_test_dual_deep`, is landed with Python lint, TypeScript test, and dual deep evidence. Executor bridge action-context packaging is now pinned by `executor_bridge_action_context_inputs`, and missing action-context guide/stdout diagnostics are pinned by `executor_bridge_missing_action_context_inputs`, but the corpus still has room to broaden without redesigning its contract.

### Repository Evidence

- `docs/benchmarking.md`
- `tests/test_benchmark.py`
- committed fixtures under `benchmarks/fixtures/`

### Scope

- add more mixed fast plus deep executed combinations beyond the first three executed fixtures
- add denser mixed repair handoff aggregation cases
- keep `executor_bridge_action_context_inputs` and `executor_bridge_missing_action_context_inputs` passing as bridge-local action context copying and missing-context diagnostics evolve
- add more deterministic dry-run history combinations where they increase realism

## Priority 4: Report, Template, And Example Sync

### Why This Matters

The main README and schema docs have moved closer to current truth. A
template/example sync first pass now also keeps the public config example,
downstream agent templates, and placeholder examples honest about the current
alpha surface. A workflow template live-free gate sync pass now pins the
repository workflow and reusable workflow template as deterministic CI gates
that preserve artifacts before applying fast/deep verdicts and do not call live
executors, mutate branches, commit, push, or post bot comments. A TypeScript demo live-free boundary sync pass now also pins the runnable TypeScript example as a fast-only demo, not a Next.js demo, TypeScript-specific deep automation example, or live executor workflow. A FastAPI demo deterministic boundary sync pass now pins the runnable Python example as a dependency-light deterministic fast and repair-prompt demo, not a mandatory web-server, deep automation, repair-session, executor bridge, executor-result, or live-agent workflow. A Next.js placeholder live-free boundary sync pass now pins `examples/nextjs-demo` as placeholder-only and non-runnable until real package/config/source/test files exist, with no live-agent call and no executor bridge/result workflow. A benchmark report generated-output policy sync pass now makes `report.md` repeat its local generated-artifact policy and label category rows as covered or not covered for selected runs. Report-style docs, workflow templates, and examples still need regular sync so they do not keep reseeding stale backlog items.

### Repository Evidence

- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`
- `qa-z.yaml.example`
- workflow templates under `templates/`

### Scope

- keep reports aligned with landed executor-history, benchmark, and template/example surfaces
- keep examples and templates aligned with actual CLI/runtime behavior as it evolves
- avoid stale report language that reopens already-landed work

## Priority 5: Executor Operator Diagnostics

### Why This Matters

The live-free safety dry-run exists, its provenance is clearer, and an operator diagnostics first pass now carries operator decision, operator summary and recommended actions through dry-run, repair-session, publish, and benchmark surfaces. Together, all committed dry-run fixtures now pin operator decision, operator summary, and recommended action residue, including `executor_dry_run_validation_noop_operator_actions`, `executor_dry_run_repeated_rejected_operator_actions`, `executor_dry_run_repeated_noop_operator_actions`, `executor_dry_run_blocked_mixed_history_operator_actions`, `executor_dry_run_empty_history_operator_actions`, `executor_dry_run_scope_validation_operator_actions`, `executor_dry_run_missing_noop_explanation_operator_actions`, and `executor_dry_run_mixed_attention_operator_actions`. Attention fixtures now also keep top-level next recommendations aligned with their specific operator actions, empty-history sessions mark `executor_history_recorded` as attention, and repeated no-op history keeps rule counts aligned by marking `retry_boundary_is_manual` as attention. Complete dry-run rule buckets are now pinned across the committed fixtures as well, so rule partition drift is treated as a benchmark regression. A mixed-attention depth pass now also makes non-blocked histories explain combined validation conflict, no-op explanation, and retry pressure in the operator summary while preserving the existing priority action ordering. The next step remains additional depth, not a new baseline surface.

### Repository Evidence

- `src/qa_z/executor_dry_run.py`
- `src/qa_z/executor_dry_run_logic.py`
- `src/qa_z/reporters/verification_publish.py`
- current dry-run fixtures and self-inspection history candidates

### Scope

- enrich deterministic explanations for retry, pause, and escalation decisions
- keep history-aware diagnostics readable without adding orchestration
- add denser mixed-history cases around the operator decision diagnostics
- preserve the live-free safety boundary

## Deferred Or Optional After These Priorities

These should stay deferred until the current baseline remains stable and the
remaining sync work is complete:

- live Codex or Claude execution
- automatic candidate reruns after external repair
- remote orchestration, queues, schedulers, or daemons
- standalone GitHub annotation/reporting surfaces beyond the current summary and
  SARIF path
- new deep engines beyond the current Semgrep-backed implementation

## Immediate Execution Rule

Do not start a fresh feature line before the current worktree is split into the
existing commit batches and the full validation baseline is rerun. The current
repository has enough value already that preserving a clean, explainable baseline
is worth more than adding one more unsplit feature. The alpha closure readiness snapshot
in `docs/reports/worktree-commit-plan.md` is the current gate reference
for that split, and self-inspection now carries that snapshot as closure-aware
commit-isolation evidence. Compact selected-task evidence summaries now
prioritize that closure-aware evidence for human `qa-z select-next` output, and
the selected-task human surfaces now add deterministic action hints for closure
recommendations without changing the live-free boundary. Plain `qa-z backlog`
output now mirrors the same hints for active items while `--json` stays stable.
Plain `qa-z self-inspect` now carries matching top-candidate summaries, so the
planning path is readable from inspection through selection without adding live
execution. These human planning surfaces and generated loop plans now also carry
deterministic `validation:` command hints, making the evidence-refresh step
visible without changing the JSON contract. Dirty-worktree evidence now also
summarizes modified and untracked paths by deterministic repository area, so the
remaining commit-isolation work can start from benchmark/docs/source/test counts
instead of a raw path dump. The corresponding dirty-worktree action hint now
uses those top areas when present, so selection and loop-plan handoff text points
at the same first triage surface as the evidence.
Commit-isolation handoff now follows the same pattern: the candidate keeps the
closure plan as its primary compact evidence, but its full evidence and action
hint can reuse dirty area counts to make the foundation split target clearer.
The compact human summary now appends an `action basis:` suffix when those area
counts explain the action hint, preserving the closure snapshot as the primary
evidence while keeping the area-specific handoff readable.
Benchmark result snapshot directories such as `benchmarks/results-*` now fall
under generated runtime artifact handling, so remaining alpha closure cleanup can
separate local-only outputs from intentional frozen evidence before commit
splitting.
Generated cleanup handoff now mirrors the area-basis pattern: compact human
evidence can append `action basis:` with `generated_outputs` or
`runtime_artifacts` evidence when the primary compact line is report context.
