# Benchmark Summary Failure Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure self-inspection still creates benchmark-gap evidence when a failed benchmark summary has only aggregate failure counts and no per-fixture details.

**Architecture:** Keep detailed fixture evidence as the primary path. Add a summary-level fallback inside `discover_benchmark_candidates` only when no detailed benchmark candidate was created for a summary whose `fixtures_failed` count is positive.

**Tech Stack:** Python, pytest, Markdown docs.

---

### Task 1: Pin Aggregate Failure Fallback

**Files:**
- Modify: `tests/test_self_improvement.py`

- [x] **Step 1: Add a summary-only benchmark fixture helper**

Create a helper that seeds the existing failed benchmark summary and removes
both `fixtures` and `failed_fixtures`.

- [x] **Step 2: Add RED coverage**

Add a self-inspection test that expects a `benchmark_gap-summary` backlog item
with evidence containing:

```text
snapshot=1/2 fixtures, overall_rate 0.5
benchmark summary reports 1 failed fixture without fixture details
```

- [x] **Step 3: Run RED verification**

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_self_inspection_creates_summary_candidate_for_aggregate_benchmark_failure -q
```

Expected: fails because aggregate benchmark failures without fixture names are
currently dropped.

### Task 2: Implement Summary-Level Candidate

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Track per-summary candidate creation**

Inside `discover_benchmark_candidates`, capture the candidate count before
processing each summary.

- [x] **Step 2: Add fallback candidate**

After the detailed fixture and `failed_fixtures` paths, if no candidate was
created for this summary and `fixtures_failed` is positive, append:

```python
benchmark_candidate(
    root,
    path,
    "summary",
    failures=[
        (
            f"benchmark summary reports {failed_count} failed "
            f"{pluralize('fixture', failed_count)} without fixture details"
        )
    ],
    snapshot=snapshot,
)
```

Use a small local pluralization expression rather than adding a broad helper.

- [x] **Step 3: Run focused GREEN verification**

Run the new focused test again and expect it to pass.

### Task 3: Sync Docs And Current Truth

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Document aggregate fallback behavior**

Document that self-inspection creates a summary-level benchmark-gap item when a
failed benchmark summary has only aggregate failure counts.

- [x] **Step 2: Pin docs with current-truth tests**

Assert README and schema mention:

```text
summary-level benchmark-gap item
```

- [x] **Step 3: Run focused verification**

Run:

```bash
python -m pytest tests/test_self_improvement.py tests/test_current_truth.py -q
```

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

Expected: all gates pass; benchmark output still reports `50/50 fixtures`.
