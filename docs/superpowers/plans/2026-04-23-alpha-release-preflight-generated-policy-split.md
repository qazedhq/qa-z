## Objective

Align alpha release preflight with the repository's generated-evidence policy so tracked generated artifacts are reported as either local-only runtime artifacts or local-by-default benchmark evidence.

## Context / Evidence

- `scripts/alpha_release_preflight.py` currently scans `.qa-z`, `benchmarks/results`, `benchmarks/results-*`, `dist`, `build`, and `src/qa_z.egg-info`, but it reports any tracked hits through one flat `generated_artifacts_untracked` failure detail.
- `scripts/worktree_commit_plan_support.py` already distinguishes generated local-only roots from generated local-by-default benchmark evidence through helper-derived buckets and next actions.
- `docs/generated-vs-frozen-evidence-policy.md`, `README.md`, and live-repository/current-truth surfaces now treat dirty `benchmarks/results-*` snapshot roots as local-by-default benchmark result evidence rather than local-only runtime cleanup pressure.
- `docs/artifact-schema-v1.md` still has wording drift in the live-repository section and does not document a preflight split for tracked generated artifacts.

## Problem Statement

Release-facing operator guidance still flattens tracked generated artifacts into one preflight blocker even though the repository has already adopted a stricter policy split elsewhere. That makes public release guidance less precise than the current generated-evidence contract.

## Blocker

### BLOCKER
- type: `AMBIGUITY`
- location: `scripts/alpha_release_preflight.py`, `scripts/alpha_release_preflight_evidence.py`, release-facing docs/schema
- symptom: tracked `.qa-z/**`, `dist/**`, and tracked `benchmarks/results-*` evidence all surface as the same undifferentiated preflight failure
- root cause (hypothesis): alpha release preflight predates the helper-derived generated-artifact bucket split now used by runtime cleanup, worktree planning, and live repository signals
- unblock condition: preflight payload, next actions, compact release evidence, and current-truth docs all distinguish tracked local-only generated roots from tracked local-by-default benchmark evidence
- risk: operators may treat intentionally frozen benchmark evidence like disposable runtime artifacts or fail to notice that tracked benchmark snapshots need an explicit keep-local versus freeze decision

## Design Decision

- Keep the existing `generated_artifacts_untracked` check id for compatibility.
- Reuse helper-derived generated-artifact buckets so tracked preflight hits collapse to deterministic roots.
- Promote additive payload fields for tracked generated roots and split them into:
  - local-only tracked generated artifacts
  - local-by-default tracked benchmark evidence
- Preserve compact gate evidence by carrying counts forward rather than full path lists.
- Update artifact schema, README, publish handoff, state, and roadmap wording to match the split.

## Scope

- `scripts/alpha_release_preflight.py`
- `scripts/alpha_release_preflight_evidence.py`
- `scripts/alpha_release_gate_evidence.py`
- `tests/test_alpha_release_preflight.py`
- `tests/test_alpha_release_gate_evidence.py`
- `tests/test_artifact_schema.py`
- `tests/test_current_truth.py`
- `tests/test_current_truth_release_surfaces.py`
- `docs/artifact-schema-v1.md`
- `docs/generated-vs-frozen-evidence-policy.md`
- `README.md`
- `docs/releases/v0.9.8-alpha-publish-handoff.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

## Implementation Plan

1. Add failing tests that pin the new tracked-generated split in preflight payload/evidence and current-truth docs.
2. Implement helper-derived tracked generated bucket classification in alpha release preflight.
3. Add additive payload fields plus category-specific next actions.
4. Carry the new counts into release gate evidence.
5. Update schema and release-facing docs to describe the split and correct live-repository wording drift.
6. Re-run targeted and broad verification, then update current state and roadmap with the closed loop result.

## Verification Plan

- `python -m pytest -q tests/test_alpha_release_preflight.py tests/test_alpha_release_gate_evidence.py tests/test_artifact_schema.py tests/test_current_truth.py tests/test_current_truth_release_surfaces.py`
- `python -m pytest`
- `python -m mypy src tests`
- `python -m ruff check .`
- `python -m ruff format --check .`

## Guardrails

- Do not change the core preflight command surface.
- Do not weaken the tracked generated-artifact release check.
- Do not relabel local-only runtime artifacts as benchmark evidence.

## Outcomes

- `scripts/alpha_release_preflight.py` now collapses tracked generated hits to helper-derived roots and preserves the existing `generated_artifacts_untracked` check id while distinguishing local-only runtime artifacts from local-by-default benchmark evidence.
- `scripts/alpha_release_preflight_evidence.py` now carries additive tracked-generated counts and path lists into preflight JSON plus category-specific next actions.
- `scripts/alpha_release_gate_evidence.py` now preserves the tracked-generated split counts in compact gate evidence and human release evidence summaries.
- README, release handoff, generated-evidence policy, artifact schema, and current-truth tests now describe the same tracked generated-root split.

## Verification Results

- `python -m pytest -q tests/test_alpha_release_preflight.py tests/test_alpha_release_gate_evidence.py tests/test_artifact_schema.py tests/test_current_truth.py tests/test_current_truth_release_surfaces.py tests/test_current_truth_release_handoff.py` -> `93 passed`
- `python -m pytest -q tests/test_alpha_release_preflight.py tests/test_alpha_release_preflight_cli_render.py tests/test_alpha_release_preflight_remote.py tests/test_alpha_release_preflight_remote_refs.py tests/test_alpha_release_preflight_architecture.py tests/test_alpha_release_gate.py tests/test_alpha_release_gate_environment.py tests/test_alpha_release_gate_evidence.py tests/test_release_script_environment.py tests/test_artifact_schema.py tests/test_current_truth.py tests/test_current_truth_release_surfaces.py tests/test_current_truth_release_handoff.py` -> `162 passed`
- `python -m pytest` -> `1150 passed`
- `python -m mypy src tests` -> `Success: no issues found in 497 source files`
- `python -m ruff check .` -> `All checks passed!`
- `python -m ruff format --check .` -> `862 files already formatted`
- `python scripts/alpha_release_preflight.py --skip-remote --allow-dirty --json --output .qa-z/tmp/alpha-release-preflight-l31.json` -> passed
- `python scripts/alpha_release_gate.py --allow-dirty --json --output .qa-z/tmp/alpha-release-gate-l31.json` -> failed on `worktree_commit_plan` attention only; nested local preflight passed and compact gate evidence preserved the tracked-generated split

## Result

### RESULT
- resolved: yes
- evidence: alpha release preflight now preserves deterministic tracked-generated split counts/paths, release gate evidence carries the same counts, and release-facing docs/schema/current-truth all match the implemented policy
- remaining risk: the integrated branch is still not release-stageable as-is because `worktree_commit_plan` reports dirty generated roots plus unassigned source paths; that is a staging/integration problem, not a preflight policy split problem
