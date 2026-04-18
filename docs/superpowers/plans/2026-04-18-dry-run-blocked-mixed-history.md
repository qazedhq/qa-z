# Dry-Run Blocked Mixed-History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic benchmark fixture proving blocked dry-run histories preserve secondary validation and retry operator actions.

**Architecture:** Reuse the existing benchmark fixture format and dry-run runner. Add one seeded session history, one expected contract, corpus/current-truth tests, and matching docs. Production dry-run logic should remain unchanged unless the new fixture exposes a real mismatch.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, JSON artifacts, Markdown docs.

---

## Files

- Create: `benchmarks/fixtures/executor_dry_run_blocked_mixed_history_operator_actions/expected.json`
- Create: `benchmarks/fixtures/executor_dry_run_blocked_mixed_history_operator_actions/repo/qa-z.yaml`
- Create: `benchmarks/fixtures/executor_dry_run_blocked_mixed_history_operator_actions/repo/qa/contracts/contract.md`
- Create: `benchmarks/fixtures/executor_dry_run_blocked_mixed_history_operator_actions/repo/src/app.py`
- Create: `benchmarks/fixtures/executor_dry_run_blocked_mixed_history_operator_actions/repo/.qa-z/sessions/session-blocked-mixed/session.json`
- Create: `benchmarks/fixtures/executor_dry_run_blocked_mixed_history_operator_actions/repo/.qa-z/sessions/session-blocked-mixed/executor_results/history.json`
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add Failing Corpus Tests

- [ ] **Step 1: Require the new fixture name**

Add `executor_dry_run_blocked_mixed_history_operator_actions` to the fixture-name set in `test_committed_benchmark_corpus_has_executor_dry_run_fixture_set`.

- [ ] **Step 2: Require the mixed action order**

Add this assertion in the same test:

```python
    assert by_name[
        "executor_dry_run_blocked_mixed_history_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "resolve_verification_blockers",
        "review_validation_conflict",
        "inspect_partial_attempts",
    ]
```

- [ ] **Step 3: Confirm RED**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: failure because the new fixture does not exist yet.

## Task 2: Add The Fixture

- [ ] **Step 1: Create `expected.json`**

Use this expectation:

```json
{
  "description": "Executor-result dry-run should keep blocked verdict priority while preserving validation-conflict and repeated-partial operator actions.",
  "expect_executor_dry_run": {
    "attention_rule_ids": [
      "retry_boundary_is_manual",
      "outcome_classification_must_be_honest"
    ],
    "attention_rule_count": 2,
    "blocked_rule_ids": [
      "verification_required_for_completed"
    ],
    "blocked_rule_count": 1,
    "clear_rule_count": 3,
    "evaluated_attempt_count": 3,
    "expected_source": "materialized",
    "expected_recommendation": "resolve verification blocking evidence before another completed attempt",
    "history_signals": [
      "repeated_partial_attempts",
      "completed_verify_blocked",
      "validation_conflict"
    ],
    "latest_ingest_status": "accepted_with_warning",
    "latest_result_status": "completed",
    "operator_summary": "A completed executor attempt is still blocked by verification evidence.",
    "recommended_action_ids": [
      "resolve_verification_blockers",
      "review_validation_conflict",
      "inspect_partial_attempts"
    ],
    "recommended_action_summaries": [
      "Review verify/summary.json and repair remaining or regressed blockers before accepting completion.",
      "Compare executor validation claims with deterministic verification artifacts before retrying.",
      "Review unresolved repair targets across repeated partial attempts before retrying."
    ],
    "schema_version": 1,
    "session_id": "session-blocked-mixed",
    "verdict": "blocked",
    "verdict_reason": "completed_attempt_not_verification_clean"
  },
  "name": "executor_dry_run_blocked_mixed_history_operator_actions",
  "run": {
    "executor_result_dry_run": {
      "session_id": "session-blocked-mixed"
    }
  }
}
```

- [ ] **Step 2: Add minimal repo config and contract**

Create a no-check Python QA-Z config, a contract that describes the mixed-history purpose, and a tiny `src/app.py`.

- [ ] **Step 3: Add session manifest and history**

Seed three attempts: two partial accepted attempts and one completed accepted-with-warning attempt that remains `verify_blocked` with `completed_validation_failed`.

- [ ] **Step 4: Confirm GREEN for corpus test**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: pass.

## Task 3: Update Current-Truth Tests And Docs

- [ ] **Step 1: Add current-truth assertion**

Extend `test_executor_dry_run_retry_noop_benchmark_density_is_documented` so README, benchmark docs, current-state, and roadmap must mention `executor_dry_run_blocked_mixed_history_operator_actions`.

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: failure until docs mention the new fixture.

- [ ] **Step 3: Update docs**

Mention the new fixture in README, `docs/benchmarking.md`, current-state report, and roadmap. Keep the wording honest: this is deterministic mixed-history dry-run benchmark coverage, not live execution.

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
python -m qa_z benchmark --fixture executor_dry_run_blocked_mixed_history_operator_actions --json
```

Expected: one selected fixture passes.

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "executor_dry_run" -q
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

Do not stage or commit in this pass. The active worktree already contains many
unrelated local changes.
