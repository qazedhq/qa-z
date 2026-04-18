# Fallback Family Status Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface recorded selected fallback families in autonomy status and saved loop plans so repeated fallback reuse is visible without opening `outcome.json`.

**Architecture:** Reuse the `selected_fallback_families` already written to each autonomy outcome. Copy it into `load_autonomy_status()` as an additive `latest_selected_fallback_families` field, render it in human status output, and pass the same list into `render_autonomy_loop_plan()` when the loop plan is created.

**Tech Stack:** Python standard library, pytest, existing QA-Z autonomy and current-truth docs.

---

### Task 1: Pin Status And Loop-Plan Visibility

**Files:**
- Modify: `tests/test_autonomy.py`

- [x] **Step 1: Add status JSON assertion**

In `test_autonomy_cli_run_and_status`, add:

```python
assert status["latest_selected_fallback_families"] == ["benchmark_expansion"]
```

- [x] **Step 2: Add human status rendering assertion**

In `test_render_autonomy_status_surfaces_prepared_actions_and_context_paths`,
add this input field:

```python
"latest_selected_fallback_families": ["cleanup"],
```

Then assert:

```python
assert "Selected fallback families: cleanup" in output
```

- [x] **Step 3: Add loop plan rendering assertion**

Add:

```python
def test_render_autonomy_loop_plan_includes_selected_fallback_families() -> None:
    plan = render_autonomy_loop_plan(
        loop_id="loop-fallback-family",
        generated_at=NOW,
        selected_tasks=[
            {
                "id": "worktree_risk-dirty-worktree",
                "title": "Reduce dirty worktree integration risk",
                "category": "worktree_risk",
                "recommendation": "reduce_integration_risk",
                "priority_score": 65,
            }
        ],
        actions=[],
        selected_fallback_families=["cleanup"],
    )

    assert "- Selected fallback families: `cleanup`" in plan
```

- [x] **Step 4: Run RED tests**

```bash
python -m pytest tests/test_autonomy.py::test_autonomy_cli_run_and_status tests/test_autonomy.py::test_render_autonomy_status_surfaces_prepared_actions_and_context_paths tests/test_autonomy.py::test_render_autonomy_loop_plan_includes_selected_fallback_families -q
```

Expected: fail because status does not expose the field yet and
`render_autonomy_loop_plan()` does not accept the new parameter.

### Task 2: Implement Additive Surfaces

**Files:**
- Modify: `src/qa_z/autonomy.py`

- [x] **Step 1: Add loop plan parameter**

Extend `render_autonomy_loop_plan()` with:

```python
selected_fallback_families: list[str] | None = None,
```

Render non-empty values near the loop metadata:

```python
fallback_families = [
    str(item)
    for item in (selected_fallback_families or [])
    if isinstance(item, str) and item.strip()
]
if fallback_families:
    lines.append(
        "- Selected fallback families: "
        + ", ".join(f"`{family}`" for family in fallback_families)
    )
```

- [x] **Step 2: Pass recorded families into loop plan**

In `run_autonomy_loop()`, pass:

```python
selected_fallback_families=selected_fallback_families,
```

- [x] **Step 3: Expose status JSON field**

In `load_autonomy_status()`, add:

```python
"latest_selected_fallback_families": string_list(
    outcome.get("selected_fallback_families")
),
```

If there is no local helper, use a short list comprehension that keeps only
non-empty strings.

- [x] **Step 4: Render human status line**

In `render_autonomy_status()`, read `latest_selected_fallback_families` and add:

```python
if selected_fallback_families:
    lines.append(
        "Selected fallback families: "
        + ", ".join(selected_fallback_families)
    )
```

- [x] **Step 5: Run GREEN tests**

```bash
python -m pytest tests/test_autonomy.py::test_autonomy_cli_run_and_status tests/test_autonomy.py::test_render_autonomy_status_surfaces_prepared_actions_and_context_paths tests/test_autonomy.py::test_render_autonomy_loop_plan_includes_selected_fallback_families -q
```

Expected: pass.

### Task 3: Sync Truth Surfaces

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update documentation**

Document that autonomy status JSON and human status output mirror selected
fallback families, and loop plans include the same line when present.

- [x] **Step 2: Update truth assertions and test count**

If the full pytest count changes, update the alpha closure snapshot and matching
current-truth assertion.

### Task 4: Verify

**Files:**
- Test only

- [x] **Step 1: Run focused checks**

```bash
python -m pytest tests/test_autonomy.py tests/test_current_truth.py -q
python -m qa_z autonomy --loops 1 --json
python -m qa_z autonomy status
```

Expected: focused tests pass, status JSON includes
`latest_selected_fallback_families`, and human status prints the selected
fallback family line when present.

- [x] **Step 2: Run full gates**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If formatting is needed, format only touched files and
rerun the full gate suite.
