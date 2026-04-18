# Dry-Run Empty-History Rule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit `executor_history_recorded` dry-run rule so empty-history attention verdicts have matching rule-level evidence.

**Architecture:** Add one new rule to `evaluate_rules()` before the existing safety rules. Empty history marks that rule as attention; all non-empty histories mark it clear. Existing verdict, recommendation, operator summary, and action ids remain unchanged.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, JSON artifacts, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_dry_run_logic.py`
- Modify: `tests/test_executor_dry_run_logic.py`
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`
- Modify: all `benchmarks/fixtures/executor_dry_run_*/expected.json`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add Failing Empty-History Logic Test

- [ ] **Step 1: Require an empty-history attention rule**

In `tests/test_executor_dry_run_logic.py`, extend
`test_build_dry_run_summary_guides_operators_when_history_is_empty`:

```python
    assert [
        item["id"]
        for item in summary["rule_evaluations"]
        if item["status"] == "attention"
    ] == ["executor_history_recorded"]
    assert summary["rule_status_counts"] == {"clear": 6, "attention": 1, "blocked": 0}
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -k "history_is_empty" -q
```

Expected: fail because no dry-run rule currently represents no recorded attempts.

## Task 2: Add `executor_history_recorded` Rule

- [ ] **Step 1: Add the rule to `evaluate_rules()`**

Insert this dictionary at the beginning of the returned rule list in
`src/qa_z/executor_dry_run_logic.py`:

```python
        {
            "id": "executor_history_recorded",
            "status": "attention"
            if "no_recorded_attempts" in signals
            else "clear",
            "summary": (
                "Executor history contains at least one recorded attempt."
                if "no_recorded_attempts" not in signals
                else (
                    "No executor attempts are recorded; ingest a result before "
                    "relying on dry-run safety evidence."
                )
            ),
        },
```

- [ ] **Step 2: Confirm empty-history GREEN**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -k "history_is_empty" -q
```

Expected: pass.

## Task 3: Update Logic Count Expectations

- [ ] **Step 1: Update affected count assertions**

Because the total rule count rises from 6 to 7, update the existing assertions:

```python
repeated partial: {"clear": 6, "attention": 1, "blocked": 0}
scope validation: {"clear": 6, "attention": 0, "blocked": 1}
validation + no-op: {"clear": 5, "attention": 2, "blocked": 0}
missing no-op: {"clear": 6, "attention": 1, "blocked": 0}
repeated no-op: {"clear": 6, "attention": 1, "blocked": 0}
completed verify blocked: {"clear": 6, "attention": 0, "blocked": 1}
```

- [ ] **Step 2: Confirm logic suite GREEN**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -q
```

Expected: pass.

## Task 4: Benchmark Contract

- [ ] **Step 1: Add benchmark assertion for empty-history rule id**

In `tests/test_benchmark.py`, add:

```python
    assert by_name[
        "executor_dry_run_empty_history_operator_actions"
    ].expectation.expect_executor_dry_run["attention_rule_ids"] == [
        "executor_history_recorded"
    ]
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: fail until the empty-history fixture expected values are updated.

- [ ] **Step 3: Update all dry-run expected counts**

Set these count updates:

```text
executor_dry_run_blocked_mixed_history_operator_actions: clear 4, attention 2, blocked 1
executor_dry_run_clear_verified_completed: clear 7, attention 0, blocked 0
executor_dry_run_completed_verify_blocked: clear 5, attention 1, blocked 1
executor_dry_run_empty_history_operator_actions: attention_rule_ids ["executor_history_recorded"], clear 6, attention 1, blocked 0
executor_dry_run_missing_noop_explanation_operator_actions: clear 6, attention 1, blocked 0
executor_dry_run_repeated_noop_operator_actions: clear 6, attention 1, blocked 0
executor_dry_run_repeated_partial_attention: clear 6, attention 1, blocked 0
executor_dry_run_repeated_rejected_operator_actions: clear 6, attention 1, blocked 0
executor_dry_run_scope_validation_operator_actions: clear 6, attention 0, blocked 1
executor_dry_run_validation_noop_operator_actions: clear 5, attention 2, blocked 0
```

- [ ] **Step 4: Confirm benchmark corpus test GREEN**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: pass.

## Task 5: Docs And Current-Truth

- [ ] **Step 1: Add current-truth assertion**

In `tests/test_current_truth.py`, add:

```python
    assert "empty-history rule attention" in benchmarking
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs mention the new rule-level attention bucket.

- [ ] **Step 3: Update docs**

Mention `executor_history_recorded` and empty-history rule attention in:

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

## Task 6: Verify

- [ ] **Step 1: Run empty-history fixture benchmark**

Run:

```bash
python -m qa_z benchmark --fixture executor_dry_run_empty_history_operator_actions --json
```

Expected: the selected fixture passes and reports `executor_history_recorded` as the only attention rule.

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
