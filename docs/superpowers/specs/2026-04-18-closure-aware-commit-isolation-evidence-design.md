# Closure-Aware Commit-Isolation Evidence Design

## Purpose

Self-inspection already promotes `commit_isolation_gap-foundation-order` when the worktree is large and the commit plan calls out commit-order risk. After the alpha closure readiness snapshot was added, the evidence summary should tell operators that the baseline is ready for commit splitting, not merely that a generic commit-order dependency exists.

## Selected Approach

Use a narrow deterministic enhancement inside `commit_isolation_evidence()`:

- preserve the existing candidate id, category, recommendation, score, and signals
- preserve generic commit-plan matching when no closure snapshot exists
- when `docs/reports/worktree-commit-plan.md` contains the readiness snapshot and the split action, render a more specific evidence summary for that report
- do not add new backlog categories, CLI flags, or runtime artifacts

This is better than changing selection priority because the selector already chooses cleanup/commit isolation work. The missing piece is explanation quality.

## Behavior

When the commit plan contains:

- `## Alpha Closure Readiness Snapshot`
- `latest full local gate pass`
- `split the worktree by this commit plan`

then self-inspection evidence for `worktree_commit_plan` should summarize:

```text
alpha closure readiness snapshot pins full gate pass and commit-split action
```

The candidate remains:

- id: `commit_isolation_gap-foundation-order`
- recommendation: `isolate_foundation_commit`
- signals: `commit_order_dependency_exists`, `worktree_integration_risk`

## Files

- `src/qa_z/self_improvement.py`: add closure-aware evidence summary logic
- `tests/test_self_improvement.py`: add RED/GREEN test for snapshot-specific evidence
- `docs/reports/current-state-analysis.md`: mention that self-inspection now carries closure-aware commit-isolation evidence
- `docs/reports/next-improvement-roadmap.md`: note this as a report/sync maintenance pass
- `docs/superpowers/plans/2026-04-18-closure-aware-commit-isolation-evidence.md`: implementation plan

## Non-Goals

- no commit, stage, or branch mutation
- no new command
- no scoring or selection priority change
- no live executor, remote orchestration, or autonomous editing
- no generated benchmark results committed as frozen evidence

## Verification

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_self_inspection_uses_alpha_closure_snapshot_for_commit_isolation_evidence -q
python -m pytest tests/test_self_improvement.py tests/test_current_truth.py -q
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```
