# Dry-Run Mixed-Attention Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve live-free executor dry-run diagnostics so non-blocked mixed-attention histories explain combined validation, no-op, and retry pressure.

**Architecture:** Keep existing signal priority and action ordering. Add a small formatter helper inside `executor_dry_run_logic.py` that only changes `operator_summary` when multiple non-blocked attention signals are present, then pin the behavior through unit tests and a committed benchmark fixture.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, JSON artifacts, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_dry_run_logic.py`
- Modify: `tests/test_executor_dry_run_logic.py`
- Modify: `tests/test_benchmark.py`
- Create: `benchmarks/fixtures/executor_dry_run_mixed_attention_operator_actions/expected.json`
- Create: `benchmarks/fixtures/executor_dry_run_mixed_attention_operator_actions/repo/qa-z.yaml`
- Create: `benchmarks/fixtures/executor_dry_run_mixed_attention_operator_actions/repo/qa/contracts/contract.md`
- Create: `benchmarks/fixtures/executor_dry_run_mixed_attention_operator_actions/repo/src/app.py`
- Create: `benchmarks/fixtures/executor_dry_run_mixed_attention_operator_actions/repo/.qa-z/sessions/session-mixed-attention/session.json`
- Create: `benchmarks/fixtures/executor_dry_run_mixed_attention_operator_actions/repo/.qa-z/sessions/session-mixed-attention/executor_results/history.json`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Unit-Test Mixed Attention Summary

- [ ] **Step 1: Add a failing unit test**

Add `test_build_dry_run_summary_explains_mixed_attention_signals()` to `tests/test_executor_dry_run_logic.py`:

```python
def test_build_dry_run_summary_explains_mixed_attention_signals() -> None:
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_skipped",
                "verification_verdict": None,
                "warning_ids": ["no_op_without_explanation"],
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_skipped",
                "verification_verdict": None,
                "warning_ids": ["validation_summary_conflicts_with_results"],
                "provenance_reason": None,
            },
        ]
    )

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "classification_conflict_requires_review"
    assert summary["history_signals"] == [
        "repeated_no_op_attempts",
        "validation_conflict",
        "missing_no_op_explanation",
    ]
    assert summary["operator_summary"] == (
        "Executor history has validation conflicts, no-op explanation gaps, and "
        "retry pressure; review all recommended actions before another retry."
    )
    assert [action["id"] for action in summary["recommended_actions"]] == [
        "review_validation_conflict",
        "require_no_op_explanation",
        "inspect_no_op_pattern",
    ]
    assert summary["rule_status_counts"] == {"clear": 4, "attention": 3, "blocked": 0}
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py::test_build_dry_run_summary_explains_mixed_attention_signals -q
```

Expected: FAIL because the current `operator_summary` only mentions validation conflicts.

## Task 2: Implement Mixed Attention Summary

- [ ] **Step 1: Add a helper and route operator summary through it**

In `src/qa_z/executor_dry_run_logic.py`, add this helper before `operator_summary()`:

```python
def mixed_attention_summary(signals: list[str]) -> str | None:
    """Return a combined non-blocking attention summary when useful."""
    signal_set = set(signals)
    if {"scope_validation_failed", "completed_verify_blocked"} & signal_set:
        return None

    labels: list[str] = []
    if "validation_conflict" in signal_set:
        labels.append("validation conflicts")
    if "missing_no_op_explanation" in signal_set:
        labels.append("no-op explanation gaps")
    if {
        "repeated_partial_attempts",
        "repeated_rejected_attempts",
        "repeated_no_op_attempts",
    } & signal_set:
        labels.append("retry pressure")

    if len(labels) < 2:
        return None
    if len(labels) == 2:
        joined = " and ".join(labels)
        review_target = "both"
    else:
        joined = f"{', '.join(labels[:-1])}, and {labels[-1]}"
        review_target = "all"
    return (
        f"Executor history has {joined}; review {review_target} recommended "
        "actions before another retry."
    )
```

Then call it near the start of `operator_summary()` after blocked checks and before single-signal attention checks:

```python
    mixed_summary = mixed_attention_summary(signals)
    if mixed_summary is not None:
        return mixed_summary
```

- [ ] **Step 2: Verify GREEN**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py::test_build_dry_run_summary_explains_mixed_attention_signals -q
```

Expected: PASS.

- [ ] **Step 3: Run the full dry-run logic test file**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -q
```

Expected: PASS.

## Task 3: Add Benchmark Fixture Coverage

- [ ] **Step 1: Require the fixture in committed corpus tests**

Add `executor_dry_run_mixed_attention_operator_actions` to the dry-run fixture set in `tests/test_benchmark.py` and assert:

```python
    assert by_name[
        "executor_dry_run_mixed_attention_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "review_validation_conflict",
        "require_no_op_explanation",
        "inspect_no_op_pattern",
    ]
    assert (
        by_name[
            "executor_dry_run_mixed_attention_operator_actions"
        ].expectation.expect_executor_dry_run["operator_summary"]
        == (
            "Executor history has validation conflicts, no-op explanation gaps, and "
            "retry pressure; review all recommended actions before another retry."
        )
    )
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_benchmark.py::test_committed_benchmark_corpus_has_executor_dry_run_fixture_set -q
```

Expected: FAIL because the fixture is not committed yet.

- [ ] **Step 3: Add the fixture files**

Create a fixture with session id `session-mixed-attention`, two accepted no-op attempts, warning ids `no_op_without_explanation` and `validation_summary_conflicts_with_results`, and expected dry-run fields:

```json
{
  "verdict": "attention_required",
  "verdict_reason": "classification_conflict_requires_review",
  "history_signals": [
    "repeated_no_op_attempts",
    "validation_conflict",
    "missing_no_op_explanation"
  ],
  "operator_decision": "review_validation_conflict",
  "operator_summary": "Executor history has validation conflicts, no-op explanation gaps, and retry pressure; review all recommended actions before another retry.",
  "recommended_action_ids": [
    "review_validation_conflict",
    "require_no_op_explanation",
    "inspect_no_op_pattern"
  ],
  "attention_rule_ids": [
    "no_op_requires_explanation",
    "retry_boundary_is_manual",
    "outcome_classification_must_be_honest"
  ],
  "clear_rule_count": 4,
  "attention_rule_count": 3,
  "blocked_rule_count": 0
}
```

- [ ] **Step 4: Verify fixture corpus test**

Run:

```bash
python -m pytest tests/test_benchmark.py::test_committed_benchmark_corpus_has_executor_dry_run_fixture_set -q
```

Expected: PASS.

- [ ] **Step 5: Run the new fixture**

Run:

```bash
python -m qa_z benchmark --fixture executor_dry_run_mixed_attention_operator_actions --json
```

Expected: PASS with `fixtures_passed` equal to `1`, `fixtures_total` equal to `1`, and `overall_rate` equal to `1.0`.

## Task 4: Sync Documentation

- [ ] **Step 1: Update benchmark docs**

Add `executor_dry_run_mixed_attention_operator_actions` to the dry-run fixture list in `docs/benchmarking.md`.

- [ ] **Step 2: Update next roadmap**

In `docs/reports/next-improvement-roadmap.md`, extend Priority 5 to say that mixed non-blocked attention histories are now pinned by `executor_dry_run_mixed_attention_operator_actions`.

- [ ] **Step 3: Run docs/current truth tests**

Run:

```bash
python -m pytest tests/test_current_truth.py tests/test_benchmark.py -q
```

Expected: PASS.

## Task 5: Full Verification

- [ ] **Step 1: Run all tests**

Run:

```bash
python -m pytest
```

Expected: PASS.

- [ ] **Step 2: Run benchmark corpus**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: PASS with 47/47 fixtures and `overall_rate` equal to `1.0`.

- [ ] **Step 3: Run static gates**

Run:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```

Expected: all PASS.

## Self-Review

- Spec coverage: the plan covers mixed attention behavior, benchmark evidence, docs, and verification.
- Placeholder scan: no deferred implementation placeholders remain.
- Type consistency: the new helper returns `str | None`; `operator_summary()` remains `str`.
