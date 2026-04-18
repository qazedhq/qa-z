# Dry-Run Empty-History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make empty executor-result history give an exact ingest recommendation and pin it in the benchmark corpus.

**Architecture:** Change only the pure dry-run recommendation mapping for `no_recorded_attempts`, then add one seeded benchmark fixture that exercises the CLI/benchmark path with no pre-recorded attempts.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, JSON artifacts, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_dry_run_logic.py`
- Modify: `tests/test_executor_dry_run_logic.py`
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`
- Create: `benchmarks/fixtures/executor_dry_run_empty_history_operator_actions/expected.json`
- Create: `benchmarks/fixtures/executor_dry_run_empty_history_operator_actions/repo/qa-z.yaml`
- Create: `benchmarks/fixtures/executor_dry_run_empty_history_operator_actions/repo/qa/contracts/contract.md`
- Create: `benchmarks/fixtures/executor_dry_run_empty_history_operator_actions/repo/src/app.py`
- Create: `benchmarks/fixtures/executor_dry_run_empty_history_operator_actions/repo/.qa-z/sessions/session-empty/session.json`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add Failing Unit Test

- [ ] **Step 1: Add the empty-history recommendation assertion**

In `tests/test_executor_dry_run_logic.py`, extend
`test_build_dry_run_summary_guides_operators_when_history_is_empty`:

```python
    assert summary["next_recommendation"] == (
        "ingest executor result before relying on dry-run safety evidence"
    )
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -k "history_is_empty" -q
```

Expected: fail because the current recommendation is generic retry inspection.

## Task 2: Implement Recommendation Mapping

- [ ] **Step 1: Update `next_recommendation()`**

Add this branch before the generic `attention_required` fallback:

```python
    if "no_recorded_attempts" in signal_set:
        return "ingest executor result before relying on dry-run safety evidence"
```

- [ ] **Step 2: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -k "history_is_empty" -q
```

Expected: pass.

## Task 3: Add Failing Benchmark Corpus Test

- [ ] **Step 1: Require the new fixture**

Add `executor_dry_run_empty_history_operator_actions` to the fixture-name set in
`test_committed_benchmark_corpus_has_executor_dry_run_fixture_set`.

- [ ] **Step 2: Require the action id**

Add this assertion in the same test:

```python
    assert by_name[
        "executor_dry_run_empty_history_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "ingest_executor_result"
    ]
```

- [ ] **Step 3: Confirm RED**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: fail because the fixture is not present yet.

## Task 4: Add Empty-History Fixture

- [ ] **Step 1: Add `expected.json`**

Use:

```json
{
  "description": "Executor-result dry-run should guide operators to ingest a result when a session has no recorded executor attempts.",
  "expect_executor_dry_run": {
    "attention_rule_count": 0,
    "blocked_rule_count": 0,
    "clear_rule_count": 6,
    "evaluated_attempt_count": 0,
    "expected_source": "materialized",
    "expected_recommendation": "ingest executor result before relying on dry-run safety evidence",
    "history_signals": [
      "no_recorded_attempts"
    ],
    "operator_summary": "No executor attempts are recorded for this session.",
    "recommended_action_ids": [
      "ingest_executor_result"
    ],
    "recommended_action_summaries": [
      "Run executor-result ingest for a completed external attempt before relying on dry-run safety evidence."
    ],
    "schema_version": 1,
    "session_id": "session-empty",
    "verdict": "attention_required",
    "verdict_reason": "no_recorded_attempts"
  },
  "name": "executor_dry_run_empty_history_operator_actions",
  "run": {
    "executor_result_dry_run": {
      "session_id": "session-empty"
    }
  }
}
```

- [ ] **Step 2: Add minimal fixture repo**

Create no-check `qa-z.yaml`, a short contract, tiny `src/app.py`, and a session
manifest. Do not create `executor_results/history.json`; the dry-run path should
materialize empty history itself.

- [ ] **Step 3: Confirm benchmark corpus test GREEN**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: pass.

## Task 5: Docs And Current-Truth

- [ ] **Step 1: Add current-truth fixture assertion**

Add `executor_dry_run_empty_history_operator_actions` to the fixture list in
`test_executor_dry_run_retry_noop_benchmark_density_is_documented`.

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs mention the new fixture.

- [ ] **Step 3: Update docs**

Mention empty-history/no-recorded-attempts dry-run coverage in README,
benchmark docs, current-state report, and roadmap.

- [ ] **Step 4: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

## Task 6: Verify

- [ ] **Step 1: Run the new fixture**

Run:

```bash
python -m qa_z benchmark --fixture executor_dry_run_empty_history_operator_actions --json
```

Expected: one selected fixture passes.

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py tests/test_benchmark.py -k "executor_dry_run or history_is_empty" -q
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
