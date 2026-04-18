# Alpha Closure Readiness Snapshot Design

## Purpose

The current alpha worktree is valuable but large. The next improvement is to make the pre-commit readiness state explicit and regression-protected before more feature work is added.

## Selected Approach

Use a narrow documentation and current-truth guard:

- add an `Alpha Closure Readiness Snapshot` section to `docs/reports/worktree-commit-plan.md`
- record the latest full local validation commands and observed baseline shape
- explicitly restate that generated benchmark outputs stay local unless frozen with context
- add a current-truth test so the closure snapshot does not disappear from the commit plan, current-state report, or roadmap

This is better than adding a new CLI command because the immediate blocker is commit isolation and evidence hygiene, not another runtime surface.

## Behavior

The closure snapshot should state:

- full pytest result shape
- full benchmark fixture count and pass rate
- Ruff check and format-check state
- mypy state
- generated-result staging policy, including the generated `report.md` policy section
- the next operator action: split the worktree by `docs/reports/worktree-commit-plan.md`

The current-truth test should fail if the snapshot is removed or if reports stop mentioning it.

## Files

- `docs/reports/worktree-commit-plan.md`: add the readiness snapshot
- `docs/reports/current-state-analysis.md`: mention the snapshot as the current closure reference
- `docs/reports/next-improvement-roadmap.md`: mention the snapshot under the immediate execution rule
- `tests/test_current_truth.py`: pin the snapshot and required commands
- `docs/superpowers/plans/2026-04-18-alpha-closure-readiness-snapshot.md`: implementation plan

## Non-Goals

- no new CLI command
- no new runtime artifact
- no schema change
- no commit/stage operation
- no claim that live executor, remote orchestration, or autonomous editing exists

## Verification

Run:

```bash
python -m pytest tests/test_current_truth.py::test_alpha_closure_readiness_snapshot_is_pinned -q
python -m pytest tests/test_current_truth.py -q
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```
