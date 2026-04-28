# Worktree Commit-Plan Untracked Expansion And Command Spine Plan

**Goal:** Make `scripts/worktree_commit_plan.py` safe enough to drive real batch
staging by expanding untracked paths to file granularity and keeping the shared
command spine in patch-add-only territory.

**Context / repo evidence:**

- Before this package, the helper still read `git status --short`, so Git could
  collapse untracked directories like `src/qa_z/commands/` into one path and
  understate the real batch boundary risk.
- Popper's read-only review of the current dirty tree highlighted that
  `src/qa_z/cli.py` and modular command wrappers were still mixed across
  planning, repair, autonomy, benchmark, and executor surfaces.
- The live L24 helper refresh now shows the difference directly: `477` default
  porcelain entries versus `516` entries from
  `git status --short --untracked-files=all`.
- The refreshed strict snapshot at
  `.qa-z/tmp/worktree-commit-plan-strict-l24.json` shows `31` generated roots,
  `26` local-only runtime artifact roots, `5` local-by-default benchmark
  evidence roots, `shared_patch_add_count=16`,
  `unassigned_source_path_count=0`, and `multi_batch_path_count=0`.

**Decision:**

- The helper now uses `--untracked-files=all` so per-batch ownership is derived
  from real source files rather than collapsed directory placeholders.
- Feature-specific command wrappers move to their owning batches, while the
  shared CLI/command registration/runtime spine remains cross-cutting and
  patch-add only.
- Generated descendants are still collapsed back to root buckets in strict mode
  so cleanup and freeze decisions stay operator-sized instead of file-noisy.

**Scope:**

- Update commit-plan runtime and support code.
- Lock the new ownership and generated-bucket semantics in commit-plan tests.
- Sync continuity docs and current-truth guards to the new strict snapshot and
  shared command-spine staging rule.

## Verification

- `python -m pytest -q tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_filtering.py`
- `python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan-l24-postfix.json`
- `python scripts/worktree_commit_plan.py --include-ignored --fail-on-generated --json --output .qa-z/tmp/worktree-commit-plan-strict-l24.json`
- `python -m pytest -q tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_filtering.py tests/test_worktree_commit_plan_output.py tests/test_worktree_commit_plan_architecture.py tests/test_current_truth.py`
- `python -m pytest -q tests/test_alpha_release_gate_evidence.py tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_filtering.py tests/test_worktree_commit_plan_output.py tests/test_worktree_commit_plan_architecture.py tests/test_current_truth.py`
- `python -m pytest -q`
- `python -m mypy src tests`
- `python scripts/alpha_release_gate.py --allow-dirty --output .qa-z/tmp/alpha-release-gate-l24-rerun.json --json`

## Blocker

- type: `TEST`
- location: `tests/test_alpha_release_gate_evidence.py`,
  `.qa-z/tmp/alpha-release-gate-l24.json`
- symptom: the first broader `pytest -q` rerun failed because the alpha release
  evidence test still expected generated artifact file counts from the
  pre-bucket helper semantics, and the first alpha gate rerun also failed on
  `ruff_format` because touched Python files had not been reformatted yet.
- root cause (hypothesis): L24 deliberately changed the worktree helper to
  collapse generated descendants to directory/root buckets, but one release
  evidence assertion still expected a file-level count. The same loop had also
  edited several Python files after the previous formatter pass.
- unblock condition: update the release evidence expectation to the new
  directory-bucket semantics, run Ruff format on the touched Python files, and
  rerun the broader gate.
- risk: without rerunning the broader gate, the package would look locally green
  from targeted helper tests while still failing the repo-standard alpha release
  verification surface.

## Outcome

- The helper no longer recommends staging collapsed directory placeholders.
- `planning_runtime_foundation` now excludes the shared command spine from
  wholesale staging.
- Continuity docs now preserve the current `31 / 26 / 5` strict snapshot and
  explain why `517` expanded paths is the new staging truth instead of the
  shorter default porcelain count.
- The final alpha release gate rerun passed with `29/29` checks after the
  blocker was resolved, and the latest full local pytest refresh is
  `1129 passed`.

## Follow-up

- Close this loop by rerunning broader commit-plan/current-truth regression,
  then a broader gate refresh, before using the refreshed helper to split real
  commit batches.
