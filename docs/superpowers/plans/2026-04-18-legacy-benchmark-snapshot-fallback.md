# Legacy Benchmark Snapshot Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve compact benchmark state in self-inspection evidence even when a legacy benchmark summary lacks the generated `snapshot` field.

**Architecture:** Keep `benchmark_summary_snapshot` as the single formatting helper. Preserve explicit `snapshot` values first, then synthesize the same text from `fixtures_passed`, `fixtures_total`, and `overall_rate` for legacy summaries.

**Tech Stack:** Python, pytest, Markdown docs.

---

### Task 1: Pin Legacy Summary Fallback

**Files:**
- Modify: `tests/test_self_improvement.py`

- [x] **Step 1: Add a legacy summary fixture helper**

Create a helper that seeds the existing benchmark summary fixture and removes
the `snapshot` field from `benchmarks/results/summary.json`.

- [x] **Step 2: Add RED coverage**

Add a self-inspection test proving a legacy summary still produces evidence
containing:

```text
snapshot=1/2 fixtures, overall_rate 0.5
```

- [x] **Step 3: Run RED verification**

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_self_inspection_synthesizes_snapshot_for_legacy_benchmark_summary -q
```

Expected: fails because the helper currently returns an empty snapshot when the
field is absent.

### Task 2: Implement Fallback

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Preserve explicit snapshot values**

Keep the existing behavior of returning a non-empty `snapshot` string unchanged.

- [x] **Step 2: Synthesize from legacy numeric fields**

When `snapshot` is absent, synthesize:

```text
<fixtures_passed>/<fixtures_total> fixtures, overall_rate <overall_rate>
```

only if all three source fields are present.

- [x] **Step 3: Run focused GREEN verification**

Run the new focused test again and expect it to pass.

### Task 3: Sync Docs And Current Truth

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Document legacy fallback behavior**

Update current-truth docs to say benchmark-gap evidence preserves generated
`snapshot` values and synthesizes the same compact text for legacy benchmark
summaries.

- [x] **Step 2: Pin docs with current-truth tests**

Assert README and schema mention legacy benchmark summaries while preserving
the existing exact phrase:

```text
benchmark-gap evidence preserves the generated benchmark `snapshot`
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

Expected: all gates pass; generated benchmark output still reports a
`snapshot` such as `50/50 fixtures, overall_rate 1.0`.
