# Objective

Align self-inspection, live-repository, and continuity surfaces with the
generated-versus-frozen evidence policy so local-by-default benchmark result
paths stay visible as benchmark evidence instead of collapsing back into
runtime-artifact area summaries.

## Context / Evidence

- `src/qa_z/live_repository.py` already keeps dirty `benchmarks/results-*` roots
  out of `runtime_artifact_paths` and records them in `benchmark_result_paths`.
- `src/qa_z/live_repository_render.py` still classifies benchmark result paths
  as `runtime_artifact` when building `dirty_area_summary`, because
  `classify_worktree_path_area()` checks `is_runtime_artifact_path()` before the
  benchmark bucket.
- `docs/generated-vs-frozen-evidence-policy.md`, `README.md`, and
  `docs/artifact-schema-v1.md` now describe a stronger contract:
  local-only runtime artifacts, local-by-default benchmark evidence, and
  intentionally frozen evidence.
- `generated_artifact_policy_missing_terms()` still accepts the policy as
  explicit without requiring those stronger local-only/local-by-default terms.
- `docs/reports/current-state-analysis.md` and
  `docs/reports/next-improvement-roadmap.md` are also behind the latest full
  verification refresh after L31.

## Problem Statement

Self-inspection and continuity docs now claim benchmark result paths remain
review-only local-by-default evidence, but live dirty-area summaries can still
bucket those same paths as runtime artifacts. The policy-explicit check is also
weaker than the documented contract, so wording drift could pass unnoticed.

## Blocker

### BLOCKER
- type: `AMBIGUITY`
- location: `src/qa_z/live_repository_render.py`, `src/qa_z/live_repository.py`,
  self-inspection/current-truth docs
- symptom: dirty benchmark result roots can still read like runtime-artifact
  cleanup pressure in area summaries, and the policy-explicit check does not
  require the exact stronger local-only/local-by-default vocabulary
- root cause (hypothesis): live-repository path-area classification and
  generated-policy term checks were not tightened when the repo adopted the
  explicit local-only vs local-by-default split
- unblock condition: benchmark result roots classify as benchmark area evidence,
  policy-explicit checks require the stronger contract language, and continuity
  docs/tests reflect the latest verification snapshot
- risk: operators could misread benchmark evidence as disposable runtime
  cleanup, and future wording drift could silently weaken the explicit policy

## Design Decision

- Preserve `runtime_artifact_paths` versus `benchmark_result_paths` behavior.
- Reclassify local-by-default benchmark result roots to the `benchmark` area in
  `dirty_area_summary` and downstream action hints.
- Tighten `generated_artifact_policy_missing_terms()` so the policy is only
  explicit when the doc includes the stronger local-only/local-by-default
  language.
- Refresh continuity docs and current-truth tests to the latest verified local
  baseline after the L31 package.

## Scope

- `src/qa_z/live_repository.py`
- `src/qa_z/live_repository_render.py`
- `tests/self_improvement_test_support.py`
- `tests/test_self_improvement_live_repository.py`
- `tests/test_current_truth.py`
- `docs/generated-vs-frozen-evidence-policy.md`
- `docs/artifact-schema-v1.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`
- `README.md`

## Implementation Plan

1. Add RED tests for benchmark-result dirty-area classification, stronger
   policy-term requirements, and stale continuity snapshot wording.
2. Reclassify benchmark result paths in live-repository area summaries without
   widening runtime-artifact cleanup pressure.
3. Tighten policy-explicit term checks and sync self-improvement test fixtures.
4. Update README/schema/state/roadmap wording to reflect the stronger contract
   and latest verification snapshot.
5. Re-run targeted plus broad verification and record the L32 outcome.

## Verification Plan

- `python -m pytest -q tests/test_self_improvement_live_repository.py tests/test_current_truth.py`
- `python -m pytest`
- `python -m mypy src tests`
- `python -m ruff check .`
- `python -m ruff format --check .`

## Guardrails

- Do not collapse benchmark result roots back into runtime-artifact cleanup
  pressure.
- Do not weaken the generated-artifact policy to generic wording.
- Do not change the self-inspection JSON shape just to patch the docs.

## Outcomes

- `src/qa_z/live_repository_render.py` now keeps dirty benchmark result evidence
  in the `benchmark` area bucket for `dirty_area_summary` while preserving the
  existing `runtime_artifact_paths` versus `benchmark_result_paths` split.
- `src/qa_z/live_repository.py` now treats the stronger
  `local-only runtime artifacts` plus `local-by-default benchmark evidence`
  wording as part of the explicit generated-artifact policy contract and keeps
  commit-isolation or integration pressure from reopening on dirty
  local-by-default benchmark result evidence alone.
- README, artifact schema, current state, roadmap, and current-truth coverage
  now describe the same benchmark-area versus runtime-cleanup distinction and
  the latest verified baseline.

## Verification Results

- `python -m pytest -q tests/test_self_improvement.py tests/test_self_improvement_reseed_policy.py tests/test_self_improvement_live_repository.py tests/test_current_truth.py` -> `73 passed`
- `python -m pytest` -> `1152 passed`
- `python -m qa_z benchmark --json --results-dir %TEMP%\qa-z-l32-full-benchmark` -> `54/54 fixtures, overall_rate 1.0`
- `python -m mypy src tests` -> `Success: no issues found in 497 source files`
- `python -m ruff check .` -> `All checks passed!`
- `python -m ruff format --check .` -> `862 files already formatted`

## Result

### RESULT
- resolved: yes
- evidence: self-inspection/live-repository summaries now keep local-by-default benchmark evidence in the benchmark area, policy explicitness requires the stronger split wording, and continuity docs/tests match the final L32 verification snapshot
- remaining risk: adjacent Priority 2 continuity surfaces still need direct regressions for autonomy prepared-action `context_paths`, self-inspection provenance carry-forward, and schema wording so those additive policy surfaces do not drift independently
