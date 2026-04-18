# Dry-Run Repeated No-Op Rule Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align repeated no-op dry-run verdicts with rule-level attention counts by marking `retry_boundary_is_manual` as attention for `repeated_no_op_attempts`.

**Architecture:** Reuse the existing retry-boundary rule instead of adding a new rule. The only production behavior change is expanding the signal set that makes `retry_boundary_is_manual` attention. Fixture and docs updates keep benchmark/current-truth aligned.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, JSON artifacts, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_dry_run_logic.py`
- Modify: `tests/test_executor_dry_run_logic.py`
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`
- Modify: `benchmarks/fixtures/executor_dry_run_repeated_noop_operator_actions/expected.json`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add Failing Logic Assertions

- [ ] **Step 1: Require repeated no-op rule attention**

In `tests/test_executor_dry_run_logic.py`, update
`test_build_dry_run_summary_guides_repeated_no_op_attempts`:

```python
    assert [
        item["id"]
        for item in summary["rule_evaluations"]
        if item["status"] == "attention"
    ] == ["retry_boundary_is_manual"]
    assert summary["rule_status_counts"] == {"clear": 5, "attention": 1, "blocked": 0}
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -k "repeated_no_op" -q
```

Expected: fail because repeated no-op history currently leaves every rule clear.

## Task 2: Implement Rule Alignment

- [ ] **Step 1: Update retry-boundary signal set**

In `src/qa_z/executor_dry_run_logic.py`, replace the repeated retry pressure
set in the `retry_boundary_is_manual` rule with:

```python
{
    "repeated_partial_attempts",
    "repeated_rejected_attempts",
    "repeated_no_op_attempts",
}
```

Use the same set for both the `status` expression and the summary expression.

- [ ] **Step 2: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -k "repeated_no_op" -q
```

Expected: pass.

## Task 3: Update Benchmark Contract

- [ ] **Step 1: Require fixture rule ids**

In `tests/test_benchmark.py`, add this assertion in
`test_committed_benchmark_corpus_has_executor_dry_run_fixture_set`:

```python
    assert by_name[
        "executor_dry_run_repeated_noop_operator_actions"
    ].expectation.expect_executor_dry_run["attention_rule_ids"] == [
        "retry_boundary_is_manual"
    ]
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: fail until the repeated no-op fixture expected values are updated.

- [ ] **Step 3: Update repeated no-op fixture**

In `benchmarks/fixtures/executor_dry_run_repeated_noop_operator_actions/expected.json`,
set:

```json
"attention_rule_ids": [
  "retry_boundary_is_manual"
],
"attention_rule_count": 1,
"clear_rule_count": 5
```

- [ ] **Step 4: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: pass.

## Task 4: Docs And Current-Truth

- [ ] **Step 1: Add current-truth assertion**

In `tests/test_current_truth.py`, add:

```python
    assert "repeated no-op rule attention" in benchmarking
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs mention the rule-alignment pass.

- [ ] **Step 3: Update docs**

Mention repeated no-op rule attention in:

- `README.md`
- `docs/benchmarking.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 4: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

## Task 5: Verify

- [ ] **Step 1: Run repeated no-op fixture benchmark**

Run:

```bash
python -m qa_z benchmark --fixture executor_dry_run_repeated_noop_operator_actions --json
```

Expected: the selected fixture passes and reports one attention rule.

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py tests/test_benchmark.py tests/test_current_truth.py -q
```

Expected: pass.

- [ ] **Step 3: Run full tests**

Run:

```bash
python -m pytest
```

Expected: all tests pass except the existing skipped test.

- [ ] **Step 4: Run full benchmark**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: every committed fixture passes.

## VCS Note

Do not stage or commit in this pass. The active workspace already contains many
unrelated local changes.
