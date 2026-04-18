# Benchmark Report Generated-Policy Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated benchmark Markdown reports explicitly state their generated-output policy and category coverage status.

**Architecture:** Keep the benchmark summary data contract unchanged. Extend only the Markdown renderer with a fixed policy section and a derived coverage label based on each category total, then update docs and tests to pin the behavior.

**Tech Stack:** Python, pytest, QA-Z benchmark summary data, Markdown docs.

---

## Files

- Modify: `src/qa_z/benchmark.py`
- Modify: `tests/test_benchmark.py`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Pin Report Policy And Coverage

- [ ] **Step 1: Add a failing report-renderer test**

Add this test after `test_render_benchmark_report_includes_failed_fixture_reasons()` in `tests/test_benchmark.py`:

```python
def test_render_benchmark_report_includes_generated_policy_and_category_coverage() -> None:
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="handoff_case",
                passed=False,
                failures=[
                    "handoff.target_sources missing expected values: deep_finding"
                ],
                categories={
                    "detection": None,
                    "handoff": False,
                    "verify": None,
                    "artifact": None,
                    "policy": None,
                },
                actual={},
                artifacts={},
            )
        ]
    )

    report = render_benchmark_report(summary)

    assert "## Generated Output Policy" in report
    assert (
        "- `benchmarks/results/summary.json` and "
        "`benchmarks/results/report.md` are generated benchmark outputs."
    ) in report
    assert (
        "- They are local by default; commit them only as intentional frozen "
        "evidence with surrounding context."
    ) in report
    assert (
        "- `benchmarks/results/work/` is disposable scratch output."
    ) in report
    assert "- handoff: 0/1 (0.0, covered)" in report
    assert "- detection: 0/0 (0.0, not covered)" in report
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_benchmark.py::test_render_benchmark_report_includes_generated_policy_and_category_coverage -q
```

Expected: FAIL because `render_benchmark_report()` has no generated-output policy section and category lines have no coverage label.

## Task 2: Implement Markdown Renderer Changes

- [ ] **Step 1: Add a small coverage helper**

Add this helper near `rate()` in `src/qa_z/benchmark.py`:

```python
def category_coverage_label(category_summary: dict[str, int | float]) -> str:
    """Return whether a category has selected-fixture coverage."""
    return "covered" if int(category_summary["total"]) > 0 else "not covered"
```

- [ ] **Step 2: Add policy text and coverage labels**

Update `render_benchmark_report()` so the initial `lines` list includes:

```python
        "## Generated Output Policy",
        "",
        (
            "- `benchmarks/results/summary.json` and "
            "`benchmarks/results/report.md` are generated benchmark outputs."
        ),
        (
            "- They are local by default; commit them only as intentional frozen "
            "evidence with surrounding context."
        ),
        "- `benchmarks/results/work/` is disposable scratch output.",
        "",
```

Then update the category append call to render:

```python
        coverage = category_coverage_label(category_summary)
        lines.append(
            "- "
            f"{category}: {category_summary['passed']}/"
            f"{category_summary['total']} "
            f"({category_summary['rate']}, {coverage})"
        )
```

- [ ] **Step 3: Verify GREEN**

Run:

```bash
python -m pytest tests/test_benchmark.py::test_render_benchmark_report_includes_generated_policy_and_category_coverage -q
```

Expected: PASS.

## Task 3: Sync Documentation

- [ ] **Step 1: Update benchmark docs**

In `docs/benchmarking.md`, extend the generated artifact paragraph to say `report.md` repeats the generated-output policy and labels each category as `covered` or `not covered`.

- [ ] **Step 2: Update the roadmap**

In `docs/reports/next-improvement-roadmap.md`, extend Priority 4 to mention that benchmark report generated-policy and category-coverage labeling is landed.

- [ ] **Step 3: Run focused docs and benchmark tests**

Run:

```bash
python -m pytest tests/test_current_truth.py tests/test_benchmark.py -q
```

Expected: PASS.

## Task 4: Full Verification

- [ ] **Step 1: Run full Python tests**

Run:

```bash
python -m pytest
```

Expected: PASS.

- [ ] **Step 2: Run full benchmark corpus**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: PASS with every selected fixture passing.

- [ ] **Step 3: Run static checks**

Run:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```

Expected: all commands exit `0`.

## Commit Decision

Do not commit inside this plan in the current session. The worktree already contains a large integrated alpha baseline, and commit splitting is governed by `docs/reports/worktree-commit-plan.md`.
