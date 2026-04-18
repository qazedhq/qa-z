# Closure-Aware Compact Evidence Priority Design

## Purpose

`qa-z self-inspect --json` now records closure-aware commit-isolation evidence, but human `qa-z select-next` output still uses the first evidence item. For commit-isolation candidates this can surface a generic current-state summary while hiding the more actionable alpha closure readiness snapshot.

## Selected Approach

Use a narrow evidence-summary priority rule:

- keep selected task JSON unchanged
- keep loop plan evidence list unchanged
- change only `compact_backlog_evidence_summary()` so evidence summaries containing `alpha closure readiness snapshot` are chosen before generic summaries
- fall back to the current first-evidence behavior when no closure-aware evidence exists

This is better than reordering candidate evidence because JSON artifacts should preserve all evidence in source order. The issue is only the compact one-line human summary.

## Behavior

For a selected task with evidence:

```json
[
  {"source": "current_state", "summary": "report calls out commit-order dependency or commit-isolation work"},
  {"source": "worktree_commit_plan", "summary": "alpha closure readiness snapshot pins full gate pass and commit-split action"}
]
```

the compact summary should be:

```text
worktree_commit_plan: alpha closure readiness snapshot pins full gate pass and commit-split action
```

If no closure-aware evidence is present, compact summaries keep the existing first usable evidence behavior.

## Files

- `src/qa_z/self_improvement.py`: prioritize closure-aware evidence in compact summaries
- `tests/test_self_improvement.py`: pin compact summary priority
- `docs/reports/current-state-analysis.md`: mention compact selected-task evidence now surfaces closure-aware commit-isolation context
- `docs/reports/next-improvement-roadmap.md`: mark this report/sync maintenance pass
- `docs/superpowers/plans/2026-04-18-closure-aware-compact-evidence-priority.md`: implementation plan

## Non-Goals

- no selected-task JSON schema change
- no candidate score or selection order change
- no loop-plan evidence list reordering
- no live executor, remote orchestration, commit, push, or branch mutation

## Verification

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_compact_evidence_summary_prioritizes_alpha_closure_snapshot -q
python -m pytest tests/test_self_improvement.py tests/test_current_truth.py -q
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```
