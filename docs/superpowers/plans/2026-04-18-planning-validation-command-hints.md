# Planning Validation Command Hints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic validation command hints to human planning surfaces without changing JSON artifacts or executing the commands.

**Architecture:** Add `selected_task_validation_command()` in `src/qa_z/self_improvement.py` beside the existing action hint helper. Import it in `src/qa_z/cli.py` and render one `validation:` line in `self-inspect`, `backlog`, and `select-next` human output. Render the same command in `render_loop_plan()` with Markdown code formatting.

**Tech Stack:** Python standard library, pytest, existing QA-Z CLI rendering helpers.

---

### Task 1: Pin Validation Command Helper

**Files:**
- Modify: `tests/test_self_improvement.py`

- [x] **Step 1: Import the helper**

Add `selected_task_validation_command` to the existing import from
`qa_z.self_improvement`.

- [x] **Step 2: Add helper tests**

Add:

```python
def test_selected_task_validation_command_specializes_known_recommendations() -> None:
    assert selected_task_validation_command(
        {"recommendation": "isolate_foundation_commit"}
    ) == "python -m qa_z self-inspect"
    assert selected_task_validation_command(
        {"recommendation": "add_benchmark_fixture"}
    ) == "python -m qa_z benchmark --json"
```

- [x] **Step 3: Run RED helper test**

```bash
python -m pytest tests/test_self_improvement.py::test_selected_task_validation_command_specializes_known_recommendations -q
```

Expected: fail because the helper does not exist yet.

### Task 2: Pin Human Surface Rendering

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Extend loop-plan test**

In `test_loop_plan_includes_selected_task_action_hint`, assert:

```python
assert "   - validation: `python -m qa_z self-inspect`" in plan
```

- [x] **Step 2: Extend `select-next` renderer test**

In `test_render_select_next_stdout_surfaces_selected_task_details`, assert:

```python
assert "validation: python -m qa_z self-inspect" in output
```

- [x] **Step 3: Extend `self-inspect` renderer test**

In `test_render_self_inspect_stdout_surfaces_top_candidate_details`, assert:

```python
assert "validation: python -m qa_z self-inspect" in output
```

- [x] **Step 4: Extend backlog test**

In `test_backlog_plain_output_focuses_on_open_items`, assert:

```python
assert "validation: python -m qa_z self-inspect" in output
```

- [x] **Step 5: Run RED renderer tests**

```bash
python -m pytest tests/test_cli.py::test_render_select_next_stdout_surfaces_selected_task_details tests/test_cli.py::test_render_self_inspect_stdout_surfaces_top_candidate_details tests/test_cli.py::test_backlog_plain_output_focuses_on_open_items tests/test_self_improvement.py::test_loop_plan_includes_selected_task_action_hint -q
```

Expected: fail because no validation lines are rendered yet.

### Task 3: Implement Helper And Rendering

**Files:**
- Modify: `src/qa_z/self_improvement.py`
- Modify: `src/qa_z/cli.py`

- [x] **Step 1: Implement helper**

Add:

```python
def selected_task_validation_command(item: dict[str, Any]) -> str:
    recommendation = str(item.get("recommendation") or "").strip()
    commands = {
        "add_benchmark_fixture": "python -m qa_z benchmark --json",
        "reduce_integration_risk": "python -m qa_z self-inspect",
        "isolate_foundation_commit": "python -m qa_z self-inspect",
        "audit_worktree_integration": "python -m qa_z self-inspect",
        "improve_fallback_diversity": "python -m qa_z autonomy --loops 1",
        "stabilize_verification_surface": (
            "python -m qa_z verify --baseline-run <baseline> --candidate-run <candidate>"
        ),
        "create_repair_session": (
            "python -m qa_z repair-session status --session <session>"
        ),
    }
    return commands.get(recommendation, "python -m qa_z self-inspect")
```

- [x] **Step 2: Render in loop plan**

After the action line, add:

```python
f"   - validation: `{selected_task_validation_command(item)}`",
```

- [x] **Step 3: Render in CLI surfaces**

Import the helper in `src/qa_z/cli.py`. After each action line in
`render_self_inspect_stdout()`, `render_backlog()`, and
`render_select_next_stdout()`, add:

```python
f"  validation: {selected_task_validation_command(item)}"
```

- [x] **Step 4: Run GREEN tests**

Run the RED commands again. Expected: pass.

### Task 4: Sync Documentation And Verify

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update docs**

Document that human planning surfaces include deterministic validation command
hints and that JSON artifacts remain unchanged.

- [x] **Step 2: Update pytest snapshot if the test count changes**

Run `python -m pytest`, then update the alpha closure snapshot and truth test if
the test count increased.

- [x] **Step 3: Run full verification**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
python -m qa_z self-inspect
python -m qa_z backlog
python -m qa_z select-next
```

Expected: all gates pass; smoke outputs include `validation:` lines; generated
`.qa-z/**` artifacts remain local.
