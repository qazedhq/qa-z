# Commit Isolation Area Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reuse dirty-worktree area evidence in commit-isolation backlog evidence and action hints.

**Architecture:** Update `discover_commit_isolation_candidates()` to append `areas=` to its existing `git_status` evidence using `worktree_area_summary()`. Update `selected_task_action_hint()` so `isolate_foundation_commit` uses `worktree_action_areas()` when available and falls back to the existing static hint otherwise. Tests pin both the evidence and the action text before implementation.

**Tech Stack:** Python standard library, pytest, existing QA-Z self-improvement helpers.

---

### Task 1: Pin Commit-Isolation Area Evidence

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Extend commit-isolation fixture paths**

In `test_self_inspection_uses_alpha_closure_snapshot_for_commit_isolation_evidence`,
set:

```python
modified_paths=["README.md", "src/qa_z/cli.py"],
untracked_paths=["docs/reports/worktree-commit-plan.md"],
```

- [x] **Step 2: Assert area evidence**

Add:

```python
assert "dirty worktree still spans modified=3; untracked=1; areas=docs:2, source:1" in {
    evidence["summary"] for evidence in isolation["evidence"]
}
```

- [x] **Step 3: Run RED evidence test**

```bash
python -m pytest tests/test_self_improvement.py::test_self_inspection_uses_alpha_closure_snapshot_for_commit_isolation_evidence -q
```

Expected: fail because commit-isolation evidence does not render `areas=` yet.

### Task 2: Pin Commit-Isolation Action Hints

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Add area-aware action test**

Add:

```python
def test_selected_task_action_hint_uses_commit_isolation_area_evidence() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "isolate_foundation_commit",
            "evidence": [
                {
                    "source": "git_status",
                    "summary": (
                        "dirty worktree still spans modified=3; untracked=1; "
                        "areas=docs:2, source:1"
                    ),
                }
            ],
        }
    ) == (
        "follow docs/reports/worktree-commit-plan.md and isolate docs and source "
        "changes into the foundation split, then rerun self-inspection"
    )
```

- [x] **Step 2: Keep fallback action test**

Add:

```python
def test_selected_task_action_hint_keeps_commit_isolation_fallback_without_area_evidence() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "isolate_foundation_commit",
            "evidence": [{"source": "git_status", "summary": "dirty worktree"}],
        }
    ) == (
        "follow docs/reports/worktree-commit-plan.md to split the foundation "
        "commit, then rerun self-inspection"
    )
```

- [x] **Step 3: Run RED action tests**

```bash
python -m pytest tests/test_self_improvement.py::test_selected_task_action_hint_uses_commit_isolation_area_evidence tests/test_self_improvement.py::test_selected_task_action_hint_keeps_commit_isolation_fallback_without_area_evidence -q
```

Expected: first test fails because `isolate_foundation_commit` ignores area
evidence.

### Task 3: Implement Area-Aware Commit-Isolation Handoff

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Add area summary to evidence**

In `discover_commit_isolation_candidates()`, build dirty paths:

```python
dirty_paths = list_signal_paths(live_signals, "modified_paths") + list_signal_paths(
    live_signals, "untracked_paths"
)
area_summary = worktree_area_summary(dirty_paths)
summary = f"dirty worktree still spans modified={modified}; untracked={untracked}"
if area_summary:
    summary += "; areas=" + area_summary
```

Use `summary` in the appended `git_status` evidence.

- [x] **Step 2: Use area evidence in action hint**

Before the static `hints` lookup returns for `isolate_foundation_commit`, add:

```python
if recommendation == "isolate_foundation_commit":
    area_phrase = join_action_areas(worktree_action_areas(item))
    if area_phrase:
        return (
            "follow docs/reports/worktree-commit-plan.md and isolate "
            f"{area_phrase} changes into the foundation split, "
            "then rerun self-inspection"
        )
```

- [x] **Step 3: Run GREEN tests**

Run the RED tests again. Expected: pass.

### Task 4: Sync Documentation And Verify

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update docs**

Document that commit-isolation evidence/action handoff reuses dirty area
evidence when present.

- [x] **Step 2: Run focused verification**

```bash
python -m pytest tests/test_self_improvement.py tests/test_cli.py tests/test_current_truth.py -q
python -m qa_z self-inspect
python -m qa_z select-next
```

Expected: focused tests pass and `select-next` keeps the closure action while
using area-aware commit-isolation guidance when its compact evidence includes
the `git_status` area evidence.

- [x] **Step 3: Run full verification**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If the pytest count changes, update the alpha closure
snapshot and truth test, then rerun full pytest.
