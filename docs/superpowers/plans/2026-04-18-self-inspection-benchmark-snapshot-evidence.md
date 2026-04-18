# Self-Inspection Benchmark Snapshot Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Carry benchmark summary `snapshot` text into self-inspection benchmark failure evidence.

**Architecture:** Keep the backlog schema unchanged. Add a small snapshot extraction helper in `qa_z.self_improvement`, pass the extracted text into benchmark-gap candidates, and document that compact evidence now preserves the benchmark snapshot.

**Tech Stack:** Python, pytest, Markdown docs.

---

### Task 1: Pin Snapshot Evidence In Self-Inspection

**Files:**
- Modify: `tests/test_self_improvement.py`

- [x] **Step 1: Seed benchmark summaries with snapshot**

Update `write_benchmark_summary` to include:

```python
"snapshot": "1/2 fixtures, overall_rate 0.5",
```

- [x] **Step 2: Add RED assertions**

In `test_self_inspection_writes_report_and_updates_backlog`, locate the
benchmark item and assert:

```python
benchmark_item = next(
    item for item in backlog["items"] if item["id"] == "benchmark_gap-py_type_error"
)
assert "snapshot=1/2 fixtures, overall_rate 0.5" in benchmark_item["evidence"][0]["summary"]
assert compact_backlog_evidence_summary(benchmark_item).startswith(
    "benchmark: snapshot=1/2 fixtures, overall_rate 0.5; fixture=py_type_error"
)
```

- [x] **Step 3: Run RED verification**

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_self_inspection_writes_report_and_updates_backlog -q
```

Expected: fails because benchmark candidate evidence ignores `snapshot`.

### Task 2: Implement Snapshot Reuse

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Add a helper**

Add:

```python
def benchmark_summary_snapshot(summary: dict[str, Any]) -> str:
    """Return compact benchmark snapshot text when available."""
    snapshot = str(summary.get("snapshot") or "").strip()
    if snapshot:
        return snapshot
    return ""
```

- [x] **Step 2: Pass the snapshot into candidates**

In `discover_benchmark_candidates`, compute:

```python
snapshot = benchmark_summary_snapshot(summary)
```

Then pass `snapshot=snapshot` into every `benchmark_candidate(...)` call.

- [x] **Step 3: Prefix benchmark candidate evidence**

Update `benchmark_candidate` to accept `snapshot: str = ""` and prefix the
existing summary when it is non-empty:

```python
if snapshot:
    summary = f"snapshot={snapshot}; {summary}"
```

- [x] **Step 4: Run GREEN verification**

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_self_inspection_writes_report_and_updates_backlog -q
```

Expected: the test passes.

### Task 3: Sync Docs And Current Truth

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Document the self-inspection evidence behavior**

Document that benchmark-gap candidate evidence preserves `snapshot` from the
benchmark summary when present.

- [x] **Step 2: Add a current-truth assertion**

Add an assertion requiring README/schema docs to mention benchmark snapshot
evidence in self-inspection/backlog surfaces.

- [x] **Step 3: Run focused verification**

Run:

```bash
python -m pytest tests/test_self_improvement.py tests/test_current_truth.py -q
```

Expected: all selected tests pass.

### Task 4: Full Verification

**Files:**
- No additional edits.

- [x] **Step 1: Run all gates**

Run:

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass; benchmark JSON still reports `snapshot=50/50 fixtures, overall_rate 1.0`.
