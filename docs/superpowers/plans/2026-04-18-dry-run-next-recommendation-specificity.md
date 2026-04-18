# Dry-Run Next-Recommendation Specificity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align dry-run `next_recommendation` strings with specific operator actions for validation-conflict, missing-no-op, and repeated-no-op attention signals.

**Architecture:** Change only the pure recommendation mapping in `src/qa_z/executor_dry_run_logic.py`. Existing verdict, rule, summary, and action logic remains intact. Add one focused missing-no-op fixture and update existing fixture expectations where the top-level recommendation becomes more precise.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, JSON artifacts, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_dry_run_logic.py`
- Modify: `tests/test_executor_dry_run_logic.py`
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`
- Modify: `benchmarks/fixtures/executor_dry_run_validation_noop_operator_actions/expected.json`
- Modify: `benchmarks/fixtures/executor_dry_run_repeated_noop_operator_actions/expected.json`
- Create: `benchmarks/fixtures/executor_dry_run_missing_noop_explanation_operator_actions/expected.json`
- Create: `benchmarks/fixtures/executor_dry_run_missing_noop_explanation_operator_actions/repo/qa-z.yaml`
- Create: `benchmarks/fixtures/executor_dry_run_missing_noop_explanation_operator_actions/repo/qa/contracts/contract.md`
- Create: `benchmarks/fixtures/executor_dry_run_missing_noop_explanation_operator_actions/repo/src/app.py`
- Create: `benchmarks/fixtures/executor_dry_run_missing_noop_explanation_operator_actions/repo/.qa-z/sessions/session-missing-noop/session.json`
- Create: `benchmarks/fixtures/executor_dry_run_missing_noop_explanation_operator_actions/repo/.qa-z/sessions/session-missing-noop/executor_results/history.json`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add Failing Pure-Logic Tests

- [ ] **Step 1: Update validation-conflict expected recommendation**

In `tests/test_executor_dry_run_logic.py`, change
`test_build_dry_run_summary_prioritizes_validation_conflicts_over_no_op_gaps`
to expect:

```python
    assert summary["next_recommendation"] == (
        "review executor validation conflict before another retry"
    )
```

- [ ] **Step 2: Add missing no-op explanation test**

Add:

```python
def test_build_dry_run_summary_requires_no_op_explanation_when_missing() -> None:
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
            }
        ]
    )

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "no_op_explanation_missing"
    assert summary["history_signals"] == ["missing_no_op_explanation"]
    assert summary["next_recommendation"] == (
        "require no-op explanation before accepting executor result"
    )
    assert summary["operator_summary"] == (
        "A no-op style executor result needs an explanation before acceptance."
    )
    assert summary["recommended_actions"] == [
        {
            "id": "require_no_op_explanation",
            "summary": (
                "Ask the executor to explain the no-op or not-applicable result "
                "before accepting it."
            ),
        }
    ]
    assert summary["rule_status_counts"] == {"clear": 5, "attention": 1, "blocked": 0}
```

- [ ] **Step 3: Add repeated no-op recommendation test**

Add:

```python
def test_build_dry_run_summary_guides_repeated_no_op_attempts() -> None:
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_skipped",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_skipped",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
        ]
    )

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "manual_retry_review_required"
    assert summary["history_signals"] == ["repeated_no_op_attempts"]
    assert summary["next_recommendation"] == (
        "inspect repeated no-op outcomes before another retry"
    )
    assert summary["operator_summary"] == (
        "Repeated no-op executor attempts need manual review before another retry."
    )
    assert summary["recommended_actions"] == [
        {
            "id": "inspect_no_op_pattern",
            "summary": "Review repeated no-op outcomes before another executor attempt.",
        }
    ]
    assert summary["rule_status_counts"] == {"clear": 6, "attention": 0, "blocked": 0}
```

- [ ] **Step 4: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -q
```

Expected: fail because `next_recommendation()` still returns the generic retry-history recommendation for these signals.

## Task 2: Implement Recommendation Mapping

- [ ] **Step 1: Update `next_recommendation()`**

In `src/qa_z/executor_dry_run_logic.py`, add these branches after
`completed_verify_blocked` and before repeated retry branches:

```python
    if "validation_conflict" in signal_set:
        return "review executor validation conflict before another retry"
    if "missing_no_op_explanation" in signal_set:
        return "require no-op explanation before accepting executor result"
```

Add this branch before `no_recorded_attempts`:

```python
    if "repeated_no_op_attempts" in signal_set:
        return "inspect repeated no-op outcomes before another retry"
```

- [ ] **Step 2: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -q
```

Expected: pass.

## Task 3: Add Failing Benchmark Corpus Test

- [ ] **Step 1: Require the new missing-no-op fixture**

Add `executor_dry_run_missing_noop_explanation_operator_actions` to the fixture
set in `test_committed_benchmark_corpus_has_executor_dry_run_fixture_set`.

- [ ] **Step 2: Require specific recommendations**

Add assertions:

```python
    assert by_name[
        "executor_dry_run_validation_noop_operator_actions"
    ].expectation.expect_executor_dry_run["expected_recommendation"] == (
        "review executor validation conflict before another retry"
    )
    assert by_name[
        "executor_dry_run_repeated_noop_operator_actions"
    ].expectation.expect_executor_dry_run["expected_recommendation"] == (
        "inspect repeated no-op outcomes before another retry"
    )
    assert by_name[
        "executor_dry_run_missing_noop_explanation_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "require_no_op_explanation"
    ]
```

- [ ] **Step 3: Confirm RED**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: fail until the fixture and expected values are updated.

## Task 4: Add Fixture And Update Expectations

- [ ] **Step 1: Update existing expected recommendations**

Set:

- `executor_dry_run_validation_noop_operator_actions`: `review executor validation conflict before another retry`
- `executor_dry_run_repeated_noop_operator_actions`: `inspect repeated no-op outcomes before another retry`

- [ ] **Step 2: Add `expected.json` for missing no-op**

Use:

```json
{
  "description": "Executor-result dry-run should require a no-op explanation and preserve the missing no-op operator action.",
  "expect_executor_dry_run": {
    "attention_rule_ids": [
      "no_op_requires_explanation"
    ],
    "attention_rule_count": 1,
    "blocked_rule_count": 0,
    "clear_rule_count": 5,
    "evaluated_attempt_count": 1,
    "expected_source": "materialized",
    "expected_recommendation": "require no-op explanation before accepting executor result",
    "history_signals": [
      "missing_no_op_explanation"
    ],
    "latest_ingest_status": "accepted_no_op",
    "latest_result_status": "no_op",
    "operator_summary": "A no-op style executor result needs an explanation before acceptance.",
    "recommended_action_ids": [
      "require_no_op_explanation"
    ],
    "recommended_action_summaries": [
      "Ask the executor to explain the no-op or not-applicable result before accepting it."
    ],
    "schema_version": 1,
    "session_id": "session-missing-noop",
    "verdict": "attention_required",
    "verdict_reason": "no_op_explanation_missing"
  },
  "name": "executor_dry_run_missing_noop_explanation_operator_actions",
  "run": {
    "executor_result_dry_run": {
      "session_id": "session-missing-noop"
    }
  }
}
```

- [ ] **Step 3: Add minimal fixture repo**

Create no-check `qa-z.yaml`, a short contract, tiny `src/app.py`, session
manifest, and one seeded history attempt with `warning_ids:
["no_op_without_explanation"]`.

- [ ] **Step 4: Confirm benchmark corpus test GREEN**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: pass.

## Task 5: Docs And Current-Truth

- [ ] **Step 1: Add current-truth fixture assertion**

Add `executor_dry_run_missing_noop_explanation_operator_actions` to the dry-run
fixture list in `tests/test_current_truth.py`.

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs mention the fixture.

- [ ] **Step 3: Update docs**

Mention action-aligned next recommendations and the missing-no-op fixture in:

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

- [ ] **Step 1: Run affected fixture benchmarks**

Run:

```bash
python -m qa_z benchmark --fixture executor_dry_run_validation_noop_operator_actions --fixture executor_dry_run_repeated_noop_operator_actions --fixture executor_dry_run_missing_noop_explanation_operator_actions --json
```

Expected: all selected fixtures pass.

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
