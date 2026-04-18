# Dry-Run Scope-Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pin scope-validation dry-run failures in the benchmark corpus and keep the scope-drift operator action visible in current-truth docs.

**Architecture:** Add one seeded executor-result history fixture. Existing dry-run logic already maps `scope_validation_failed` to the blocked verdict and `inspect_scope_drift` action, so production code should not need to change unless the new fixture exposes a mismatch.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, JSON artifacts, Markdown docs.

---

## Files

- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`
- Create: `benchmarks/fixtures/executor_dry_run_scope_validation_operator_actions/expected.json`
- Create: `benchmarks/fixtures/executor_dry_run_scope_validation_operator_actions/repo/qa-z.yaml`
- Create: `benchmarks/fixtures/executor_dry_run_scope_validation_operator_actions/repo/qa/contracts/contract.md`
- Create: `benchmarks/fixtures/executor_dry_run_scope_validation_operator_actions/repo/src/app.py`
- Create: `benchmarks/fixtures/executor_dry_run_scope_validation_operator_actions/repo/.qa-z/sessions/session-scope/session.json`
- Create: `benchmarks/fixtures/executor_dry_run_scope_validation_operator_actions/repo/.qa-z/sessions/session-scope/executor_results/history.json`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add Failing Benchmark Corpus Test

- [ ] **Step 1: Require the new fixture**

Add `executor_dry_run_scope_validation_operator_actions` to the fixture-name set
in `test_committed_benchmark_corpus_has_executor_dry_run_fixture_set`.

- [ ] **Step 2: Require the operator action**

Add this assertion in the same test:

```python
    assert by_name[
        "executor_dry_run_scope_validation_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "inspect_scope_drift"
    ]
```

- [ ] **Step 3: Confirm RED**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: fail because the fixture is not present yet.

## Task 2: Add Scope-Validation Fixture

- [ ] **Step 1: Add `expected.json`**

Use:

```json
{
  "description": "Executor-result dry-run should block scope-validation failures and preserve the scope-drift operator action.",
  "expect_executor_dry_run": {
    "attention_rule_count": 0,
    "blocked_rule_ids": [
      "mutation_scope_limited"
    ],
    "blocked_rule_count": 1,
    "clear_rule_count": 5,
    "evaluated_attempt_count": 1,
    "expected_source": "materialized",
    "expected_recommendation": "inspect executor scope drift before another attempt",
    "history_signals": [
      "scope_validation_failed"
    ],
    "latest_ingest_status": "rejected_invalid",
    "latest_result_status": "partial",
    "operator_summary": "Executor history is blocked by scope validation; inspect handoff scope before another attempt.",
    "recommended_action_ids": [
      "inspect_scope_drift"
    ],
    "recommended_action_summaries": [
      "Inspect changed files against the bridge handoff scope before another attempt."
    ],
    "schema_version": 1,
    "session_id": "session-scope",
    "verdict": "blocked",
    "verdict_reason": "scope_validation_failed"
  },
  "name": "executor_dry_run_scope_validation_operator_actions",
  "run": {
    "executor_result_dry_run": {
      "session_id": "session-scope"
    }
  }
}
```

- [ ] **Step 2: Add minimal fixture repo**

Create no-check `qa-z.yaml`, a short contract, tiny `src/app.py`, session
manifest, and one seeded `executor_results/history.json` attempt whose
`provenance_reason` is `scope_validation_failed`.

- [ ] **Step 3: Confirm benchmark corpus test GREEN**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: pass.

## Task 3: Docs And Current-Truth

- [ ] **Step 1: Add current-truth fixture assertion**

Add `executor_dry_run_scope_validation_operator_actions` to the dry-run fixture
list in `tests/test_current_truth.py`.

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs mention the new fixture.

- [ ] **Step 3: Update docs**

Mention scope-validation/scope-drift dry-run coverage in README, benchmark docs,
current-state report, and roadmap.

- [ ] **Step 4: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

## Task 4: Verify

- [ ] **Step 1: Run the new fixture**

Run:

```bash
python -m qa_z benchmark --fixture executor_dry_run_scope_validation_operator_actions --json
```

Expected: one selected fixture passes.

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

Expected: every committed fixture passes.

## VCS Note

Do not stage or commit in this pass. The active workspace already contains many
unrelated local changes.
