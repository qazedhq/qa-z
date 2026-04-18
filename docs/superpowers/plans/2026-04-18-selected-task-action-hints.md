# Selected Task Action Hints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make selected-task human surfaces show a deterministic first action in addition to recommendation ids and evidence.

**Architecture:** Add a small pure helper in `src/qa_z/self_improvement.py` that translates selected backlog item recommendations into readable action hints. Reuse the helper from `render_loop_plan()` and `src/qa_z/cli.py` human `select-next` rendering so the CLI and saved loop plan stay aligned without changing `selected_tasks.json`.

**Tech Stack:** Python standard library, pytest, existing QA-Z CLI rendering helpers.

---

### Task 1: Pin Action Hint Behavior

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing helper test**

Add a test that imports `selected_task_action_hint` and asserts:

```python
def test_selected_task_action_hint_specializes_closure_recommendations() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "isolate_foundation_commit",
            "evidence": [
                {
                    "source": "worktree_commit_plan",
                    "path": "docs/reports/worktree-commit-plan.md",
                    "summary": "alpha closure readiness snapshot pins full gate pass",
                }
            ],
        }
    ) == (
        "follow docs/reports/worktree-commit-plan.md to split the foundation "
        "commit, then rerun self-inspection"
    )
```

- [ ] **Step 2: Write the failing loop-plan test**

Extend or add a `render_loop_plan()` test that expects:

```text
   - action: follow docs/reports/worktree-commit-plan.md to split the foundation commit, then rerun self-inspection
```

- [ ] **Step 3: Write the failing CLI rendering test**

Extend `test_render_select_next_stdout_includes_selected_task_details` to expect:

```text
  action: inspect the dirty worktree and separate generated artifacts, then rerun self-inspection
```

- [ ] **Step 4: Run RED tests**

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_selected_task_action_hint_specializes_closure_recommendations tests/test_self_improvement.py::test_loop_plan_includes_selected_task_action_hint tests/test_cli.py::test_render_select_next_stdout_includes_selected_task_details -q
```

Expected: fail because `selected_task_action_hint` and action rendering do not exist yet.

### Task 2: Implement Action Hints

**Files:**
- Modify: `src/qa_z/self_improvement.py`
- Modify: `src/qa_z/cli.py`

- [ ] **Step 1: Add the pure helper**

Add `selected_task_action_hint(item: dict[str, Any]) -> str` with a local mapping:

```python
def selected_task_action_hint(item: dict[str, Any]) -> str:
    recommendation = str(item.get("recommendation") or "").strip()
    hints = {
        "reduce_integration_risk": (
            "inspect the dirty worktree and separate generated artifacts, "
            "then rerun self-inspection"
        ),
        "isolate_foundation_commit": (
            "follow docs/reports/worktree-commit-plan.md to split the foundation "
            "commit, then rerun self-inspection"
        ),
        "audit_worktree_integration": (
            "inspect current-state, triage, and commit-plan reports, then rerun "
            "self-inspection"
        ),
    }
    if recommendation in hints:
        return hints[recommendation]
    if recommendation:
        return f"turn {recommendation.replace('_', ' ')} into a scoped repair plan"
    return "turn selected evidence into a scoped repair plan"
```

- [ ] **Step 2: Render in loop plans**

In `render_loop_plan()`, add:

```python
f"   - action: {selected_task_action_hint(item)}",
```

after the recommendation line.

- [ ] **Step 3: Render in CLI stdout**

Import `selected_task_action_hint` in `src/qa_z/cli.py` and add:

```python
lines.append(f"  action: {selected_task_action_hint(item)}")
```

after the recommendation line for each selected task.

- [ ] **Step 4: Run GREEN tests**

Run the same focused pytest command. Expected: pass.

### Task 3: Sync Docs And Verify

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Update human-surface docs**

Describe that human `select-next` output and `loop_plan.md` now include a
deterministic action hint derived from the recommendation id, while `--json`
keeps the original artifact shape.

- [ ] **Step 2: Run focused tests**

```bash
python -m pytest tests/test_self_improvement.py tests/test_cli.py -q
```

- [ ] **Step 3: Run full gates**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```

- [ ] **Step 4: Confirm live-free boundary**

Run:

```bash
python -m qa_z select-next
```

Expected: output includes action hints, writes only local `.qa-z/loops/**`
artifacts, and does not edit source, call an executor, stage, commit, push, or
post comments.
