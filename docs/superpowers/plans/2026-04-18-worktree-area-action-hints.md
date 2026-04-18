# Worktree Area Action Hints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make dirty-worktree action hints use deterministic area-count evidence when it is available.

**Architecture:** Add a small parser helper in `src/qa_z/self_improvement.py` that reads the existing `areas=` evidence segment from backlog items. Update `selected_task_action_hint()` so only `reduce_integration_risk` changes, and only when the parser returns one or more areas. Existing CLI renderers automatically pick up the improved hint because they already call the shared helper.

**Tech Stack:** Python standard library, pytest, existing QA-Z CLI/self-improvement helpers.

---

### Task 1: Pin Area Extraction

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Import the helper**

Add `worktree_action_areas` to the existing import from `qa_z.self_improvement`.

- [x] **Step 2: Add extraction tests**

Add:

```python
def test_worktree_action_areas_reads_area_summary_from_evidence() -> None:
    assert worktree_action_areas(
        {
            "evidence": [
                {
                    "source": "git_status",
                    "summary": (
                        "modified=31; untracked=488; staged=0; "
                        "areas=benchmark:271, docs:160, source:42; "
                        "sample=.github/workflows/ci.yml, README.md"
                    ),
                }
            ]
        }
    ) == ["benchmark", "docs", "source"]
```

- [x] **Step 3: Add malformed extraction test**

Add:

```python
def test_worktree_action_areas_ignores_missing_or_malformed_area_summary() -> None:
    assert worktree_action_areas({"evidence": [{"summary": "modified=1"}]}) == []
    assert worktree_action_areas({"evidence": [{"summary": "areas=, broken"}]}) == []
```

- [x] **Step 4: Run RED extraction tests**

```bash
python -m pytest tests/test_self_improvement.py::test_worktree_action_areas_reads_area_summary_from_evidence tests/test_self_improvement.py::test_worktree_action_areas_ignores_missing_or_malformed_area_summary -q
```

Expected: fail because `worktree_action_areas` is not defined yet.

### Task 2: Pin Action Hint Behavior

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add direct action-hint tests**

Add:

```python
def test_selected_task_action_hint_uses_dirty_worktree_area_evidence() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "reduce_integration_risk",
            "evidence": [
                {
                    "source": "git_status",
                    "summary": "modified=31; areas=benchmark:271, docs:160, source:42",
                }
            ],
        }
    ) == (
        "triage benchmark and docs changes first, separate generated artifacts, "
        "then rerun self-inspection"
    )
```

Add:

```python
def test_selected_task_action_hint_keeps_fallback_without_area_evidence() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "reduce_integration_risk",
            "evidence": [{"source": "git_status", "summary": "modified=31"}],
        }
    ) == (
        "inspect the dirty worktree and separate generated artifacts, "
        "then rerun self-inspection"
    )
```

- [x] **Step 2: Update CLI fixture evidence**

In the existing CLI renderer tests for selected task, self-inspect, and backlog,
change the dirty-worktree evidence summary to include:

```text
modified=25; untracked=346; staged=0; areas=docs:2, source:1
```

Then update the expected action assertion to:

```text
action: triage docs and source changes first, separate generated artifacts, then rerun self-inspection
```

- [x] **Step 3: Run RED action tests**

```bash
python -m pytest tests/test_self_improvement.py::test_selected_task_action_hint_uses_dirty_worktree_area_evidence tests/test_self_improvement.py::test_selected_task_action_hint_keeps_fallback_without_area_evidence tests/test_cli.py::test_render_select_next_stdout_surfaces_selected_task_details tests/test_cli.py::test_render_self_inspect_stdout_surfaces_top_candidate_details tests/test_cli.py::test_backlog_plain_output_focuses_on_open_items -q
```

Expected: fail because action hints do not parse area evidence yet.

### Task 3: Implement Area-Aware Action Hints

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Add parser helper**

Add:

```python
def worktree_action_areas(item: dict[str, Any]) -> list[str]:
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return []
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        summary = str(entry.get("summary") or "")
        marker = "areas="
        if marker not in summary:
            continue
        area_segment = summary.split(marker, maxsplit=1)[1].split(";", maxsplit=1)[0]
        areas: list[str] = []
        for pair in area_segment.split(","):
            name = pair.strip().split(":", maxsplit=1)[0].strip()
            if name:
                areas.append(name)
        return areas
    return []
```

- [x] **Step 2: Add phrase helper**

Add:

```python
def join_action_areas(areas: list[str], *, limit: int = 2) -> str:
    selected = [area for area in areas if area.strip()][:limit]
    if not selected:
        return ""
    if len(selected) == 1:
        return selected[0]
    return " and ".join(selected)
```

- [x] **Step 3: Use helper in `selected_task_action_hint()`**

Before the static `hints` lookup returns for `reduce_integration_risk`, add:

```python
if recommendation == "reduce_integration_risk":
    area_phrase = join_action_areas(worktree_action_areas(item))
    if area_phrase:
        return (
            f"triage {area_phrase} changes first, separate generated artifacts, "
            "then rerun self-inspection"
        )
```

- [x] **Step 4: Run GREEN tests**

Run the RED action tests again. Expected: pass.

### Task 4: Sync Documentation And Verify

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update docs**

Document that dirty-worktree action hints use existing area evidence when present
and fall back to the existing generic hint otherwise.

- [x] **Step 2: Run focused verification**

```bash
python -m pytest tests/test_self_improvement.py tests/test_cli.py tests/test_current_truth.py -q
python -m qa_z self-inspect
python -m qa_z select-next
```

Expected: focused tests pass and human output includes an area-aware action hint
when dirty-worktree evidence includes `areas=`.

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
