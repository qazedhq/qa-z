# Benchmark Snapshot Schema Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document the benchmark summary `snapshot` field in the artifact schema and pin it with tests.

**Architecture:** Keep runtime behavior unchanged. Add schema tests that exercise `build_benchmark_summary`, and current-truth tests that require the artifact schema doc to list the additive field.

**Tech Stack:** Python, pytest, Markdown docs.

---

### Task 1: Pin The Missing Schema Documentation

**Files:**
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Write the failing current-truth test**

Add a test that reads `docs/artifact-schema-v1.md` and requires the benchmark
summary schema section to mention the compact snapshot field:

```python
def test_benchmark_summary_snapshot_is_documented_in_artifact_schema() -> None:
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")

    assert "## Benchmark Summary" in schema
    assert "`snapshot`: compact generated benchmark result text" in schema
    assert "derived from `fixtures_passed`, `fixtures_total`, and `overall_rate`" in schema
```

- [x] **Step 2: Run RED verification**

Run:

```bash
python -m pytest tests/test_current_truth.py::test_benchmark_summary_snapshot_is_documented_in_artifact_schema -q
```

Expected: fails because the schema doc does not yet list `snapshot`.

### Task 2: Pin The Payload Contract

**Files:**
- Modify: `tests/test_artifact_schema.py`

- [x] **Step 1: Add a benchmark summary schema test**

Import `BenchmarkFixtureResult` and `build_benchmark_summary`, then add:

```python
def test_benchmark_summary_schema_v1_snapshot_field_is_stable() -> None:
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="passing_case",
                passed=True,
                failures=[],
                categories={"detection": True},
                actual={},
                artifacts={},
            ),
            BenchmarkFixtureResult(
                name="failing_case",
                passed=False,
                failures=["fast.status expected passed but got failed"],
                categories={"detection": False},
                actual={},
                artifacts={},
            ),
        ]
    )

    assert summary["kind"] == "qa_z.benchmark_summary"
    assert summary["schema_version"] == 1
    assert {
        "kind",
        "schema_version",
        "fixtures_total",
        "fixtures_passed",
        "fixtures_failed",
        "overall_rate",
        "snapshot",
        "category_rates",
        "failed_fixtures",
        "fixtures",
    } <= summary.keys()
    assert summary["snapshot"] == "1/2 fixtures, overall_rate 0.5"
```

- [x] **Step 2: Run the schema test**

Run:

```bash
python -m pytest tests/test_artifact_schema.py::test_benchmark_summary_schema_v1_snapshot_field_is_stable -q
```

Expected: passes because runtime behavior already emits the additive field.

### Task 3: Update Artifact Schema Documentation

**Files:**
- Modify: `docs/artifact-schema-v1.md`

- [x] **Step 1: Add the documented field**

In the `Benchmark Summary` section, add:

```markdown
- `snapshot`: compact generated benchmark result text such as `50/50 fixtures, overall_rate 1.0`, derived from `fixtures_passed`, `fixtures_total`, and `overall_rate`
```

- [x] **Step 2: Note report parity**

Add one sentence after the field list:

```markdown
The generated `report.md` repeats `snapshot` near the top so human closure notes can quote generated benchmark evidence instead of recomputing counts.
```

- [x] **Step 3: Run focused verification**

Run:

```bash
python -m pytest tests/test_artifact_schema.py tests/test_current_truth.py -q
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

Expected: all gates pass; benchmark JSON still includes `snapshot`.
