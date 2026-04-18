# Benchmark Snapshot Artifact Decision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make benchmark result snapshot directories visible as generated artifacts that need a local-only versus frozen-evidence decision.

**Architecture:** Extend the existing `is_runtime_artifact_path()` helper so `benchmarks/results-*` sibling snapshots follow the same local-generated-artifact path as `benchmarks/results/`. Add a deterministic `triage_and_isolate_changes` action hint so deferred cleanup tasks tell operators to separate generated artifacts and decide whether to freeze evidence intentionally. Tests pin detection and action text before implementation.

**Tech Stack:** Python standard library, pytest, existing QA-Z self-improvement helpers.

---

### Task 1: Pin Benchmark Snapshot Runtime Classification

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Import runtime artifact helper**

Add `is_runtime_artifact_path` to the import list from `qa_z.self_improvement`.

- [x] **Step 2: Add runtime snapshot detection test**

Add:

```python
def test_runtime_artifact_path_detects_benchmark_snapshot_siblings() -> None:
    assert is_runtime_artifact_path("benchmarks/results/report.md") is True
    assert is_runtime_artifact_path("benchmarks/results-p12-dry-run/report.md") is True
    assert is_runtime_artifact_path("benchmarks/results-p12-dry-run/work/run.json") is True
    assert is_runtime_artifact_path("benchmarks/fixtures/py_test_failure/expected.json") is False
```

- [x] **Step 3: Add area classification test**

Add:

```python
def test_worktree_area_classifies_benchmark_snapshots_as_runtime_artifacts() -> None:
    assert (
        classify_worktree_path_area("benchmarks/results-p12-dry-run/report.md")
        == "runtime_artifact"
    )
    assert (
        classify_worktree_path_area("benchmarks/fixtures/py_test_failure/expected.json")
        == "benchmark"
    )
```

- [x] **Step 4: Run RED classification tests**

```bash
python -m pytest tests/test_self_improvement.py::test_runtime_artifact_path_detects_benchmark_snapshot_siblings tests/test_self_improvement.py::test_worktree_area_classifies_benchmark_snapshots_as_runtime_artifacts -q
```

Expected: the `benchmarks/results-p12-*` assertions fail because sibling
snapshots are not runtime artifacts yet.

### Task 2: Pin Generated Snapshot Decision Action

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Add action hint test**

Add:

```python
def test_selected_task_action_hint_names_generated_snapshot_decision() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "triage_and_isolate_changes",
            "evidence": [
                {
                    "source": "runtime_artifacts",
                    "summary": (
                        "generated runtime artifacts need explicit cleanup handling: "
                        "benchmarks/results-p12-dry-run/report.md"
                    ),
                }
            ],
        }
    ) == (
        "decide whether generated artifacts stay local-only or become intentional "
        "frozen evidence, separate them from source changes, then rerun "
        "self-inspection"
    )
```

- [x] **Step 2: Run RED action test**

```bash
python -m pytest tests/test_self_improvement.py::test_selected_task_action_hint_names_generated_snapshot_decision -q
```

Expected: fail because the generic recommendation currently falls back to
`turn triage and isolate changes into a scoped repair plan`.

### Task 3: Implement Runtime Classification And Action Hint

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Extend runtime artifact detection**

Change `is_runtime_artifact_path()` to return true for:

```python
normalized.startswith(".qa-z/")
or normalized.startswith("benchmarks/results/")
or normalized.startswith("benchmarks/results-")
```

- [x] **Step 2: Add action hint mapping**

Add this entry to `selected_task_action_hint()`'s `hints` dictionary:

```python
"triage_and_isolate_changes": (
    "decide whether generated artifacts stay local-only or become intentional "
    "frozen evidence, separate them from source changes, then rerun "
    "self-inspection"
),
```

- [x] **Step 3: Run GREEN tests**

```bash
python -m pytest tests/test_self_improvement.py::test_runtime_artifact_path_detects_benchmark_snapshot_siblings tests/test_self_improvement.py::test_worktree_area_classifies_benchmark_snapshots_as_runtime_artifacts tests/test_self_improvement.py::test_selected_task_action_hint_names_generated_snapshot_decision -q
```

Expected: all three tests pass.

### Task 4: Sync Documentation And Truth Tests

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update docs**

Document that `benchmarks/results-*` sibling snapshots are treated as generated
runtime artifacts unless they are intentionally frozen with context.

- [x] **Step 2: Update truth assertions**

Add assertions that README/schema mention `benchmarks/results-*` and
`intentional frozen evidence`.

### Task 5: Verify Alpha Closure Gates

**Files:**
- Test only

- [x] **Step 1: Run focused checks**

```bash
python -m pytest tests/test_self_improvement.py tests/test_cli.py tests/test_current_truth.py -q
python -m qa_z self-inspect
python -m qa_z select-next
```

Expected: focused tests pass and planning output remains live-free.

- [x] **Step 2: Run full gate suite**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If the pytest count changes, update the alpha closure
snapshot and current-truth assertion, then rerun full pytest.
