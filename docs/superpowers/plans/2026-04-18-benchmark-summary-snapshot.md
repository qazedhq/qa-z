# Benchmark Summary Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic benchmark `snapshot` summary field and mirror it in human/report documentation.

**Architecture:** Keep the behavior inside `qa_z.benchmark` where aggregate fixture counts are already computed. Expose the compact string as additive summary data and render it in `report.md`.

**Tech Stack:** Python, pytest, Markdown docs.

---

### Task 1: Pin Summary Snapshot Behavior

**Files:**
- Modify: `tests/test_benchmark.py`

- [x] **Step 1: Write the failing test**

Add assertions to `test_build_benchmark_summary_calculates_category_rates`:

```python
assert summary["snapshot"] == "1/2 fixtures, overall_rate 0.5"
```

Add an assertion to `test_render_benchmark_report_includes_failed_fixture_reasons`:

```python
assert "- Snapshot: 0/1 fixtures, overall_rate 0.0" in report
```

- [x] **Step 2: Run RED verification**

Run:

```bash
python -m pytest tests/test_benchmark.py::test_build_benchmark_summary_calculates_category_rates tests/test_benchmark.py::test_render_benchmark_report_includes_failed_fixture_reasons -q
```

Expected: fails because `summary["snapshot"]` is missing and the report does not render the snapshot line.

### Task 2: Implement Snapshot Formatting

**Files:**
- Modify: `src/qa_z/benchmark.py`

- [x] **Step 1: Add the summary field**

In `build_benchmark_summary`, compute `overall_rate` once and include:

```python
"snapshot": benchmark_snapshot(passed, len(results), overall_rate),
```

Add:

```python
def benchmark_snapshot(fixtures_passed: int, fixtures_total: int, overall_rate: float) -> str:
    """Return the compact benchmark snapshot used by reports and docs."""
    return f"{fixtures_passed}/{fixtures_total} fixtures, overall_rate {overall_rate}"
```

- [x] **Step 2: Render the snapshot in reports**

In `render_benchmark_report`, add:

```python
f"- Snapshot: {summary['snapshot']}",
```

near the top of the report.

- [x] **Step 3: Run GREEN verification**

Run:

```bash
python -m pytest tests/test_benchmark.py::test_build_benchmark_summary_calculates_category_rates tests/test_benchmark.py::test_render_benchmark_report_includes_failed_fixture_reasons -q
```

Expected: both tests pass.

### Task 3: Sync Docs And Current Truth

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Document the field**

Update benchmark docs to say `summary.json` includes the compact `snapshot`
field and `report.md` repeats it.

- [x] **Step 2: Pin the current-truth wording**

Add a current-truth assertion that the worktree commit plan references the
benchmark summary snapshot field.

- [x] **Step 3: Run focused docs tests**

Run:

```bash
python -m pytest tests/test_benchmark.py tests/test_current_truth.py -q
```

Expected: all selected tests pass.

### Task 4: Full Verification

**Files:**
- No additional edits.

- [x] **Step 1: Run the repository gates**

Run:

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass; benchmark remains live-free and reports the new
`snapshot` field in JSON output.
