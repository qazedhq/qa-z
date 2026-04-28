# Runtime Artifact Cleanup Review-Only Benchmark Evidence Plan

**Goal:** Prevent `scripts/runtime_artifact_cleanup.py --apply` from deleting
local-by-default benchmark evidence while keeping deterministic cleanup for
local-only runtime artifacts.

**Context / repo evidence:**

- `docs/generated-vs-frozen-evidence-policy.md` already says
  `benchmarks/results/summary.json`, `benchmarks/results/report.md`, and
  `benchmarks/results-*` are local by default unless intentionally frozen.
- `scripts/worktree_commit_plan_support.py` already distinguishes generated
  `local_only` versus `local_by_default` paths, and the strict helper snapshot
  at `.qa-z/tmp/worktree-commit-plan-strict-l23.json` shows `25` local-only
  runtime roots plus `5` local-by-default benchmark evidence roots.
- Before this package, `scripts/runtime_artifact_cleanup_support.py` treated
  `.qa-z/`, `benchmarks/results/`, and `benchmarks/results-*` as one deletable
  cleanup bucket, so `--apply` could remove untracked benchmark evidence roots
  without a deliberate keep-local versus freeze-evidence decision.

**Decision:**

- `runtime_artifact_cleanup` now emits an explicit `policy_bucket` per
  candidate.
- Only `local_only` candidates may move into `planned` or `deleted`.
- Benchmark evidence roots in the `local_by_default` bucket always stay
  `review_local_by_default`, even when `--apply` is used.
- Tracked local-only roots still surface as `skipped_tracked`.

**Scope:**

- Update runtime cleanup helper behavior and human/JSON output.
- Lock the new contract in cleanup tests first.
- Sync README, generated-policy guidance, current-truth coverage, and worktree
  continuity docs to the new semantics.

## Blocker

- type: `TEST`
- location: `.qa-z/tmp/alpha-release-gate-l23.json`, `tests/test_current_truth.py`
- symptom: the first broader alpha gate rerun failed on `ruff_format` and the
  nested `qa_z_fast` gate failed for the same reason.
- root cause (hypothesis): the new current-truth assertions were semantically
  correct but left `tests/test_current_truth.py` unformatted, and `qa_z_fast`
  runs `ruff format --check .` as part of its fast gate.
- unblock condition: format `tests/test_current_truth.py` and rerun the full
  alpha gate.
- risk: without rerunning the gate, the package would look locally green from
  targeted checks while still failing the repo's broader release surface.

## Verification

- `python -m pytest -q tests/test_runtime_artifact_cleanup.py`
- `python -m pytest -q tests/test_current_truth.py -k generated_vs_frozen_policy_is_documented_and_linked`
- `python -m pytest -q`
- `python -m ruff check scripts/runtime_artifact_cleanup.py scripts/runtime_artifact_cleanup_support.py tests/test_runtime_artifact_cleanup.py tests/test_current_truth.py`
- `python -m mypy src tests`
- `python scripts/runtime_artifact_cleanup.py --json`
- `python scripts/worktree_commit_plan.py --include-ignored --fail-on-generated --json --output .qa-z/tmp/worktree-commit-plan-strict-l23.json`
- `python scripts/alpha_release_gate.py --allow-dirty --output .qa-z/tmp/alpha-release-gate-l23.json --json`
- `python -m ruff format tests/test_current_truth.py`
- `python scripts/alpha_release_gate.py --allow-dirty --output .qa-z/tmp/alpha-release-gate-l23-rerun.json --json`

## Outcome

- Cleanup dry-run now reports `.qa-z/` as the only `planned` root in the live
  repository and reports the five benchmark evidence roots as
  `review_local_by_default`.
- Apply mode is now safe against accidental deletion of local-by-default
  benchmark evidence.
- The final alpha gate rerun passed with `29/29` checks after the formatter
  blocker was resolved.

## Follow-up

- Keep the commit split as the next major package. This loop only hardened the
  cleanup policy seam so future staging work does not accidentally delete
  benchmark evidence that still needs a keep-local versus freeze decision.
- A later package may still want one shared generated-artifact policy helper
  consumed by worktree planning, runtime cleanup, and alpha release preflight.
  Bacon's review notes that current docs support `keep_local` as the default
  for today's `benchmarks/results-*` roots, but they do not yet provide a
  machine-readable allowlist that would justify treating any specific snapshot
  directory as automatically freezeable evidence.
