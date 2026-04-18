# Dry-Run Rule Bucket Completeness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every committed executor dry-run benchmark fixture pin the complete dry-run rule id partition across clear, attention, and blocked buckets.

**Architecture:** Keep production dry-run behavior unchanged. Add a committed-corpus contract test, then update fixture expectations and current-truth docs so benchmark evidence catches missing, renamed, or re-bucketed rules.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, JSON expectations, Markdown docs.

---

## Files

- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`
- Modify: `benchmarks/fixtures/executor_dry_run_*/expected.json`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add The Benchmark Contract Test

- [ ] **Step 1: Add the known rule set helper inside the test**

In `tests/test_benchmark.py`, add a test near
`test_committed_executor_dry_run_fixtures_pin_operator_action_residue`:

```python
def test_committed_executor_dry_run_fixtures_pin_complete_rule_buckets() -> None:
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    dry_run_fixtures = [
        fixture for fixture in fixtures if fixture.name.startswith("executor_dry_run_")
    ]

    assert dry_run_fixtures

    expected_rule_ids = {
        "executor_history_recorded",
        "no_op_requires_explanation",
        "retry_boundary_is_manual",
        "mutation_scope_limited",
        "unrelated_refactors_prohibited",
        "verification_required_for_completed",
        "outcome_classification_must_be_honest",
    }
    required_buckets = {
        "clear_rule_ids": "clear_rule_count",
        "attention_rule_ids": "attention_rule_count",
        "blocked_rule_ids": "blocked_rule_count",
    }

    missing: list[str] = []
    mismatched_counts: list[str] = []
    duplicate_ids: list[str] = []
    mismatched_rule_sets: list[str] = []

    for fixture in dry_run_fixtures:
        expected = fixture.expectation.expect_executor_dry_run
        observed_rule_ids: set[str] = set()
        for bucket_key, count_key in required_buckets.items():
            if bucket_key not in expected:
                missing.append(f"{fixture.name}:{bucket_key}")
                continue
            bucket = expected[bucket_key]
            if len(bucket) != len(set(bucket)):
                duplicate_ids.append(f"{fixture.name}:{bucket_key}")
            if len(bucket) != expected[count_key]:
                mismatched_counts.append(
                    f"{fixture.name}:{bucket_key}:{len(bucket)}!={expected[count_key]}"
                )
            observed_rule_ids.update(bucket)
        if observed_rule_ids != expected_rule_ids:
            mismatched_rule_sets.append(
                f"{fixture.name}:{sorted(observed_rule_ids)}"
            )

    assert missing == []
    assert duplicate_ids == []
    assert mismatched_counts == []
    assert mismatched_rule_sets == []
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "complete_rule_buckets" -q
```

Expected: fail because most committed fixtures do not yet include complete
`clear_rule_ids`, `attention_rule_ids`, and `blocked_rule_ids`.

## Task 2: Pin Complete Buckets In Fixtures

- [ ] **Step 1: Update every dry-run expected JSON file**

Use these exact bucket mappings:

```text
executor_dry_run_clear_verified_completed
  clear: all seven rules
  attention: []
  blocked: []

executor_dry_run_empty_history_operator_actions
  clear: all rules except executor_history_recorded
  attention: [executor_history_recorded]
  blocked: []

executor_dry_run_repeated_partial_attention
executor_dry_run_repeated_rejected_operator_actions
executor_dry_run_repeated_noop_operator_actions
  clear: all rules except retry_boundary_is_manual
  attention: [retry_boundary_is_manual]
  blocked: []

executor_dry_run_missing_noop_explanation_operator_actions
  clear: all rules except no_op_requires_explanation
  attention: [no_op_requires_explanation]
  blocked: []

executor_dry_run_scope_validation_operator_actions
  clear: all rules except mutation_scope_limited
  attention: []
  blocked: [mutation_scope_limited]

executor_dry_run_completed_verify_blocked
  clear: executor_history_recorded, no_op_requires_explanation,
    retry_boundary_is_manual, mutation_scope_limited,
    unrelated_refactors_prohibited
  attention: [outcome_classification_must_be_honest]
  blocked: [verification_required_for_completed]

executor_dry_run_validation_noop_operator_actions
  clear: executor_history_recorded, retry_boundary_is_manual,
    mutation_scope_limited, unrelated_refactors_prohibited,
    verification_required_for_completed
  attention: [no_op_requires_explanation,
    outcome_classification_must_be_honest]
  blocked: []

executor_dry_run_blocked_mixed_history_operator_actions
  clear: executor_history_recorded, no_op_requires_explanation,
    mutation_scope_limited, unrelated_refactors_prohibited
  attention: [retry_boundary_is_manual,
    outcome_classification_must_be_honest]
  blocked: [verification_required_for_completed]
```

- [ ] **Step 2: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "complete_rule_buckets" -q
```

Expected: pass.

## Task 3: Add Current-Truth Guard And Docs

- [ ] **Step 1: Add a current-truth assertion**

In `tests/test_current_truth.py`, inside
`test_executor_dry_run_retry_noop_benchmark_density_is_documented`, add:

```python
    assert "complete dry-run rule buckets" in benchmarking
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs mention complete dry-run rule buckets.

- [ ] **Step 3: Update current-truth docs**

Update:

- `README.md`
- `docs/benchmarking.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

Required phrase:

```text
complete dry-run rule buckets
```

- [ ] **Step 4: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

## Task 4: Verification

- [ ] **Step 1: Run focused benchmark fixture checks**

Run:

```bash
python -m qa_z benchmark --fixture executor_dry_run_empty_history_operator_actions --fixture executor_dry_run_blocked_mixed_history_operator_actions --json
```

Expected: both selected fixtures pass.

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_benchmark.py tests/test_current_truth.py -q
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

Expected: every committed benchmark fixture passes.

## VCS Note

Do not stage or commit in this pass. The active workspace already contains many
unrelated local changes.
