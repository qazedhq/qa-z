## Goal

Close the next documented Priority 2 gap by aligning live-repository and
self-inspection policy signals with the generated-versus-frozen evidence policy
for `benchmarks/results-*` snapshot roots.

## Context / repo evidence

- `docs/generated-vs-frozen-evidence-policy.md` classifies
  `benchmarks/results-*` snapshot directories as local-by-default benchmark
  results, not local-only runtime artifacts.
- `scripts/runtime_artifact_cleanup_support.py` and
  `scripts/worktree_commit_plan_support.py` already preserve that distinction by
  reporting `benchmarks/results-*` under `local_by_default`.
- A live repro against `qa_z.live_repository.collect_live_repository_signals`
  currently misclassifies `benchmarks/results-l30-policy/summary.json` as a
  runtime artifact:
  - `runtime_artifact_paths=['benchmarks/results-l30-policy/summary.json']`
  - `benchmark_result_paths=[]`
- That drift means self-inspection and operator-facing live repository summaries
  can present local-by-default benchmark snapshots as local-only runtime
  cleanup pressure.

## Decision

- Treat this as a policy-alignment package, not a roadmap rewrite.
- Add failing tests first for:
  - live repository signal collection
  - live repository summary counts
  - self-inspection candidate behavior when only a `benchmarks/results-*`
    snapshot root is dirty
- Implement the smallest change that:
  - surfaces `benchmarks/results-*` snapshot roots through
    `benchmark_result_paths`
  - keeps them out of `runtime_artifact_paths`
  - preserves existing `.qa-z/**` and `benchmarks/results/work/**`
    local-only behavior
- Refresh continuity docs so the next session can see that Priority 2 now
  includes self-inspection/live-repository parity with cleanup/worktree helper
  policy buckets.

## Scope

- `src/qa_z/live_repository.py`
- `src/qa_z/live_repository_render.py` only if summary behavior must change
- `tests/test_self_improvement_live_repository.py`
- `tests/test_self_improvement.py` if candidate/output behavior needs a direct
  regression
- `tests/test_current_truth.py`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

## Verification Plan

- `python -m pytest -q tests/test_self_improvement_live_repository.py tests/test_self_improvement.py tests/test_current_truth.py`
- `python -m pytest`
- `python -m mypy src tests`
- `python -m ruff check .`
- `python -m ruff format --check .`

## Blocker

- type: `AMBIGUITY`
- location: live repository policy signals
- symptom: cleanup/worktree helpers distinguish `benchmarks/results-*` as
  local-by-default benchmark evidence, but live repository signals currently
  collapse dirty snapshot roots into `runtime_artifact_paths`
- root cause (hypothesis): live repository discovery only seeds
  `benchmark_result_paths` from fixed `benchmarks/results/summary.json` and
  `benchmarks/results/report.md`, while `is_runtime_artifact_path()` still
  catches snapshot directories generically
- unblock condition: tests pin `benchmarks/results-*` snapshot roots as
  benchmark results in live signals and self-inspection surfaces
- risk: self-inspection can overstate local-only cleanup pressure and understate
  policy-managed review-only benchmark evidence

## Result

- resolved
- `src/qa_z/live_repository.py` now keeps dirty `benchmarks/results-*` snapshot
  roots in `benchmark_result_paths` and `dirty_benchmark_result_count` instead
  of collapsing them into `runtime_artifact_paths`
- continuity docs and current-truth coverage now describe those snapshot roots
  as local-by-default benchmark evidence, not local-only runtime cleanup
  pressure

## Outcome

- cleanup/worktree helper policy buckets and live repository signals now agree
  on the generated-versus-frozen evidence split for
  `benchmarks/results-*` snapshot roots
- self-inspection can still reopen runtime-artifact cleanup work from true
  local-only paths such as root `.qa-z/**` and `benchmarks/results/work/**`,
  while review-only benchmark snapshots stay visible without becoming cleanup
  pressure by themselves
- roadmap/state continuity no longer repeats the stale `30 / 25 / 5` helper
  snapshot in the live handoff sections

## Verification Results

- `python -m pytest -q tests/test_self_improvement_live_repository.py tests/test_self_improvement.py tests/test_self_improvement_lifecycle.py tests/test_self_improvement_report_freshness.py tests/test_self_improvement_reseed_policy.py tests/test_autonomy.py tests/test_cli.py` -> `125 passed`
- `python -m pytest -q tests/test_current_truth.py` -> `40 passed`
- `python -m pytest` -> `1145 passed`
- `python -m mypy src tests` -> `Success: no issues found in 497 source files`
- `python -m ruff check .` -> passed
- `python -m ruff format --check .` -> `862 files already formatted`

## Next Focus

- remain on Priority 2 generated-versus-frozen evidence policy maintenance for
  adjacent artifact/report surfaces that could still drift back toward
  local-only versus frozen-evidence ambiguity
