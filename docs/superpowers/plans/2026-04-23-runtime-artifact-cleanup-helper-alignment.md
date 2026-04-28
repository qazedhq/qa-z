# Runtime Artifact Cleanup Helper Alignment Plan

**Goal:** Make `scripts/runtime_artifact_cleanup.py` consume the same
generated-policy roots as `scripts/worktree_commit_plan.py`, then verify that
post-gate cleanup returns the strict helper to the `5 / 0 / 5` snapshot.

**Context / repo evidence:**

- L24 left the strict worktree helper at `generated_artifact_count=31`,
  `generated_local_only_count=26`, and `generated_local_by_default_count=5`.
- Before this package, `scripts/runtime_artifact_cleanup_support.py` still used
  a narrower hard-coded candidate list, so cleanup could not fully clear the
  local-only roots that strict worktree planning already reported.
- Popper's read-only package review highlighted four risks that had to stay
  closed together: reuse the strict helper policy buckets instead of drifting,
  preserve review-only handling for `benchmarks/results/**`, avoid deleting
  fixture-local `.qa-z` inputs, and keep deleted directory candidates typed as
  directories in apply-mode JSON.
- The first broader gate rerun for this package failed before closure because
  `ruff_format` and nested `qa_z_fast` still saw formatting drift in the touched
  Python surfaces.

**Decision:**

- Runtime cleanup now discovers candidates from the same generated-policy
  buckets that the strict worktree helper reports.
- Only `local_only` roots can move into `planned` or `deleted`; all
  `local_by_default` benchmark evidence roots stay `review_local_by_default`.
- Apply-mode JSON captures the candidate kind before deletion so deleted
  directories do not fall back to `"file"`.
- The cleanup and strict-helper runtimes now set `sys.dont_write_bytecode = True`
  so rerunning them does not recreate `__pycache__` roots inside the same loop.

**Scope:**

- Update runtime cleanup discovery and apply-mode reporting.
- Lock the behavior in direct cleanup and architecture tests.
- Sync README, generated-policy docs, current-state/worktree continuity docs,
  and current-truth coverage to the post-gate snapshot.

## Blocker

- type: `TEST`
- location: `.qa-z/tmp/alpha-release-gate-l25-rerun.json`
- symptom: the first broader alpha gate rerun failed on `ruff_format`, and the
  nested `qa_z_fast` gate failed for the same reason.
- root cause (hypothesis): the helper-alignment package touched multiple Python
  files after the previous formatter pass, so the broader gate still saw stale
  formatting drift even though the targeted cleanup tests were green.
- unblock condition: confirm the touched Python files are formatted, then rerun
  the full alpha gate.
- risk: without the broader rerun, the package could look green from local
  cleanup tests while still failing the repo-standard release gate.

## Verification

- `python -B -m pytest -p no:cacheprovider tests/test_runtime_artifact_cleanup.py tests/test_runtime_artifact_cleanup_architecture.py tests/test_worktree_commit_plan_architecture.py tests/test_current_truth.py -q`
- `python -m ruff check --no-cache scripts/runtime_artifact_cleanup.py scripts/runtime_artifact_cleanup_support.py scripts/worktree_commit_plan.py tests/test_runtime_artifact_cleanup.py tests/test_runtime_artifact_cleanup_architecture.py tests/test_worktree_commit_plan_architecture.py tests/test_current_truth.py`
- `python scripts/alpha_release_gate.py --allow-dirty --output .qa-z/tmp/alpha-release-gate-l25-rerun.json --json`
- `python scripts/runtime_artifact_cleanup.py --apply --json`
- `python scripts/runtime_artifact_cleanup.py --json`
- `python scripts/worktree_commit_plan.py --include-ignored --fail-on-generated --json`

## Outcome

- The cleanup/runtime helper seam now shares the same generated-policy roots as
  strict worktree planning instead of drifting through a smaller hard-coded
  cleanup list.
- The broader alpha gate rerun passed with `29/29` checks after the formatter
  blocker was cleared.
- Post-gate cleanup deleted `17` recreated local-only roots, and the follow-up
  strict helper refresh returned to `generated_artifact_count=5`,
  `generated_local_only_count=0`, and `generated_local_by_default_count=5`.

## Follow-up

- Keep benchmark result roots review-only until an operator intentionally freezes
  or drops them during commit isolation.
- Reuse the strict helper snapshot as the source of truth for later cleanup or
  staging packages; do not reintroduce separate candidate heuristics.
