# QA-Z Release Readiness Stages 1-5 Execution

Date: 2026-04-23
Branch context: `codex/qa-z-bootstrap`

## Objective

Turn the previously approved five-stage release outline into executable
repository work, starting with the highest-value blocker for trustworthy release
evidence and then rechecking later release stages against fresh helper output.

## Scope

1. Close the remaining Priority 2 continuity/provenance slice across autonomy
   prepared-action context, self-inspection provenance, and schema/current-truth
   wording.
2. Re-evaluate release-stageability with the existing deterministic worktree and
   release helpers after Stage 1 lands.
3. Record any real Stage 2-5 blockers in the repository docs instead of keeping
   them in chat-only memory.

## Repository Evidence

- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`
- `docs/releases/v0.9.8-alpha-publish-handoff.md`
- `src/qa_z/autonomy.py`
- `src/qa_z/autonomy_actions.py`
- `src/qa_z/autonomy_action_context.py`
- `src/qa_z/autonomy_action_cleanup.py`
- `src/qa_z/self_improvement_inspection.py`
- `src/qa_z/selection_context.py`
- `src/qa_z/self_improvement_selection.py`
- `tests/test_autonomy.py`
- `tests/test_autonomy_action_context.py`
- `tests/test_autonomy_action_cleanup.py`
- `tests/test_self_improvement.py`
- `tests/test_self_improvement_selection.py`
- `tests/test_current_truth.py`

## Design Decision

- Keep the existing release plan order from the roadmap: continuity/provenance
  hardening first, release-stageability second, publish-path work only after
  the local continuity and helper evidence are stable.
- Treat autonomy prepared actions as part of release evidence continuity,
  because those packets are copied into later executor/release handoff surfaces.
- Do not claim release readiness from stale gate evidence. Re-check release
  helpers after Stage 1 and document whatever still blocks Stage 2-5.

## Implementation Outline

### Stage 1

- Add failing regressions for cleanup/workflow prepared actions so loop-local
  self-inspection context is preserved alongside task and report evidence.
- Implement the smallest code change that carries that loop-local context
  through those prepared actions without changing unrelated action types.
- Sync README/schema/current-state/roadmap/current-truth wording to the new
  continuity contract.

### Stage 2

- Re-run the deterministic worktree/release helper path after Stage 1:
  `worktree_commit_plan`, `alpha_release_preflight`, and any narrow release
  checks needed to classify stageability honestly.
- If stageability is still blocked, document the exact blocker and handoff.

### Stage 3-5

- Only advance further if Stage 2 evidence shows the repo is actually ready for
  fresh release-gate work.
- Otherwise leave behind exact next-step guidance tied to the current helper
  outputs and release handoff docs.

## Verification Plan

- Targeted RED/GREEN tests for the new prepared-action continuity behavior.
- Impacted-area regression packs around autonomy, self-improvement, and
  current-truth.
- `python -m pytest`
- `python -m mypy src tests`
- `python -m ruff check .`
- `python -m ruff format --check .`
- Stage 2 helper reruns only after Stage 1 lands cleanly.

## Guardrails

- Do not weaken deterministic release gates or helper checks.
- Do not rewrite unrelated dirty worktree state.
- Do not promote stale release evidence as current truth.

## Blocker

- type: TEST
- location: `tests/test_current_truth.py`, `tests/test_current_truth_release_surfaces.py`, `tests/test_current_truth_architecture.py`
- symptom: the new release continuity assertion pushed the main current-truth file over its split budget and then overflowed the release-surface split pack as well
- root cause (hypothesis): release/current-truth continuity needed one more split boundary, but the assertion first landed inside files that were already close to their architecture limits
- unblock condition: move the new continuity assertion into its own split pack and rerun architecture plus full regression
- risk: Stage 1 continuity would look complete while `python -m pytest` still failed on architecture only

## Result

### Stage 1 Outcome

- `src/qa_z/autonomy_actions.py` now passes loop-local context through cleanup
  and workflow action builders.
- `src/qa_z/autonomy_action_cleanup.py` now merges
  `loop_local_self_inspection_context_paths(...)` into cleanup/workflow
  `context_paths`, so those prepared actions keep the exact loop-local
  self-inspection artifact instead of relying on mutable `latest` pointers.
- README, artifact schema, current state, roadmap, and current-truth wording
  now pin the same continuity contract.
- `tests/test_current_truth_release_continuity.py` now owns the new release
  continuity assertion so the split-budget guard stays green.

### Stage 2-3 Result

- `python -m pytest -q tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_filtering.py tests/test_worktree_commit_plan_output.py tests/test_worktree_commit_plan_architecture.py`
  passed with `56 passed` after the helper ownership fix.
- `python scripts/worktree_commit_plan.py --include-ignored --fail-on-generated --json --output .qa-z/tmp/worktree-commit-plan-l34.json`
  still returned strict generated-artifact attention, but now with
  `generated_artifact_count=24`, `generated_local_only_count=17`,
  `generated_local_by_default_count=7`, and `unassigned_source_path_count=0`.
- `python scripts/alpha_release_preflight.py --skip-remote --allow-dirty --json --output .qa-z/tmp/alpha-release-preflight-l34.json`
  passed locally.
- `python scripts/alpha_release_gate.py --allow-dirty --json --output .qa-z/tmp/alpha-release-gate-l34b.json`
  passed locally; nested preflight, build, artifact smoke, bundle manifest,
  benchmark, pytest, mypy, Ruff, and CLI help checks all passed.

### Stage 4-5 Blocker

- type: EXTERNAL + ACCESS
- location: direct remote preflight against configured `origin`
- symptom: remote publish path stops on `github_repository` and
  `remote_reachable`
- root cause (hypothesis): `qazedhq/qa-z` still returns `404 Not Found`, `git`
  reports `remote: Repository not found.`, `gh` is unavailable in this
  environment, and `GITHUB_TOKEN` / `GH_TOKEN` are absent, so the repository
  cannot be created or exposed from this session
- unblock condition: create or expose `qazedhq/qa-z`, or intentionally align
  the expected target to a different reachable repository, then rerun direct
  remote preflight against the configured `origin`
- risk: Stage 4-5 publish work cannot push, open a release PR, or create a
  remote tag from a repository target that does not yet exist

### L35 Follow-Through

- A live-like GitHub `404 Not Found` regression is now pinned in
  `tests/test_alpha_release_preflight_remote_refs.py` so preflight payloads
  cannot collapse `status_code=404` to `404404` or misclassify the blocker as
  `repository_target_mismatch` just because the GitHub error body includes a
  `documentation_url`.
- `scripts/alpha_release_preflight_evidence.py` now parses `status_code=` as a
  single three-digit code and prefers `repository_missing` before the
  wrong-target fallback when GitHub actually returns `404`.
- `python scripts/alpha_release_gate.py --allow-dirty --json --output .qa-z/tmp/alpha-release-gate-l35.json`
  now passes locally again after `origin` bootstrap because the nested
  local-only preflight keeps carrying `--expected-origin-url
  https://github.com/qazedhq/qa-z.git`.
- The remote blocker is unchanged but now better classified:
  `python scripts/alpha_release_preflight.py --repository-url https://github.com/qazedhq/qa-z.git --expected-origin-url https://github.com/qazedhq/qa-z.git --allow-dirty --json --output .qa-z/tmp/alpha-release-preflight-remote-l35.json`
  fails with `release_path_state=blocked_repository`,
  `remote_readiness=needs_repository_bootstrap`, and
  `remote_blocker=repository_missing`.

## BLOCKER

- type: TEST / ARCH
- location: `tests/test_alpha_release_preflight_remote.py`,
  `tests/test_alpha_release_preflight_remote_refs.py`,
  `tests/test_alpha_release_preflight_architecture.py`
- symptom: the new live-like GitHub 404 regression initially pushed the remote
  split pack over its file budget, which made full `pytest` and the local alpha
  release gate fail even though the runtime fix itself was correct
- root cause (hypothesis): the new regression landed in the wrong split pack;
  `test_alpha_release_preflight_remote.py` already sat close to its 620-line
  limit
- unblock condition: move the regression into the existing remote-refs split
  pack, pin that location in the architecture guard, and rerun formatting plus
  the affected gate pack
- risk: Stage 3 would look fixed while the release gate still failed on test
  architecture only

## RESULT

- resolved
- evidence: the regression now lives in
  `tests/test_alpha_release_preflight_remote_refs.py`, the architecture guard
  stays green, and the local alpha release gate passes again
- remaining risk: Stage 4-5 are still externally blocked until the intended
  GitHub repository target exists or is intentionally changed

## Verification Results

- `python -m pytest -q tests/test_autonomy_action_cleanup.py tests/test_self_improvement.py tests/test_self_improvement_selection.py tests/test_current_truth.py` -> `63 passed`
- `python -m pytest -q tests/test_autonomy.py tests/test_autonomy_action_context.py tests/test_autonomy_action_cleanup.py tests/test_self_improvement.py tests/test_self_improvement_inspection.py tests/test_self_improvement_selection.py tests/test_self_improvement_selection_output.py tests/test_current_truth.py` -> `122 passed`
- `python -m pytest -q tests/test_current_truth.py tests/test_current_truth_release_surfaces.py tests/test_current_truth_release_continuity.py tests/test_current_truth_architecture.py` -> `53 passed`
- `python -m ruff format --check .` -> `1014 files already formatted`
- `python -m qa_z fast --selection smart --json` -> `passed`
- `python -m pytest` -> `1157 passed`
- `python -m qa_z benchmark --json` -> `54/54 fixtures, overall_rate 1.0`
- `python -m mypy src tests` -> `Success: no issues found in 498 source files`
- `python -m ruff check .` -> `All checks passed!`
- `python scripts/worktree_commit_plan.py --include-ignored --fail-on-generated --json --output .qa-z/tmp/worktree-commit-plan-l34.json` -> `attention_required`
- `python scripts/alpha_release_preflight.py --skip-remote --allow-dirty --json --output .qa-z/tmp/alpha-release-preflight-l34.json` -> `release preflight passed`
- `python -m pytest -q tests/test_alpha_release_preflight_remote.py tests/test_alpha_release_preflight_remote_refs.py tests/test_alpha_release_preflight_architecture.py -k "github_error_body or remote_is_missing or split_budget or remote_ref_contracts_live_in_split_pack"` -> `6 passed`
- `python scripts/alpha_release_gate.py --allow-dirty --json --output .qa-z/tmp/alpha-release-gate-l35.json` -> `alpha release gate passed`
- `python scripts/alpha_release_preflight.py --repository-url https://github.com/qazedhq/qa-z.git --expected-origin-url https://github.com/qazedhq/qa-z.git --allow-dirty --json --output .qa-z/tmp/alpha-release-preflight-remote-l35.json` -> `release preflight failed`
