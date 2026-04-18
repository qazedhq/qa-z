# Fallback Diversity Action Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add evidence `context_paths` to loop-health prepared actions so fallback-diversity handoffs point directly at loop-history evidence.

**Architecture:** Extend the existing `action_for_task()` branch for `backlog_reseeding_gap` and `autonomy_selection_gap` to pass `task_context_paths(task)` into `prepared_action()`. Existing loop plan and status renderers already display action context paths, so this stays a small action-packet mapping change.

**Tech Stack:** Python standard library, pytest, existing QA-Z autonomy helpers.

---

### Task 1: Pin Loop-Health Action Context

**Files:**
- Modify: `tests/test_autonomy.py`

- [x] **Step 1: Add fallback-diversity action mapping test**

Add:

```python
def test_action_mapping_loop_health_plan_includes_task_context_paths(
    tmp_path: Path,
) -> None:
    action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "autonomy_selection_gap-repeated-fallback-cleanup",
            "category": "autonomy_selection_gap",
            "recommendation": "improve_fallback_diversity",
            "signals": ["recent_fallback_family_repeat"],
            "evidence": [
                {
                    "source": "loop_history",
                    "path": ".qa-z/loops/history.jsonl",
                    "summary": (
                        "recent_fallback_family=cleanup; loops=3; "
                        "states=unknown, completed, unknown"
                    ),
                }
            ],
        },
    )

    assert action["type"] == "loop_health_plan"
    assert action["commands"] == [
        "python -m qa_z self-inspect",
        "python -m qa_z autonomy --loops 1",
    ]
    assert action["context_paths"] == [".qa-z/loops/history.jsonl"]
    assert action["next_recommendation"] == (
        "rerun autonomy after tightening loop health rules"
    )
```

- [x] **Step 2: Run RED test**

```bash
python -m pytest tests/test_autonomy.py::test_action_mapping_loop_health_plan_includes_task_context_paths -q
```

Expected: fail with missing `context_paths`.

### Task 2: Implement Action Context

**Files:**
- Modify: `src/qa_z/autonomy.py`

- [x] **Step 1: Pass task context into loop-health action**

In the `category in {"backlog_reseeding_gap", "autonomy_selection_gap"}` branch
of `action_for_task()`, add:

```python
context_paths=task_context_paths(task),
```

- [x] **Step 2: Run GREEN test**

```bash
python -m pytest tests/test_autonomy.py::test_action_mapping_loop_health_plan_includes_task_context_paths -q
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

Document that loop-health prepared actions now carry evidence `context_paths`
for fallback-diversity diagnostics.

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

Expected: focused tests pass and the latest loop-health action carries
`.qa-z/loops/history.jsonl` as context when fallback-diversity work is selected.

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
