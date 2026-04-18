# Dry-Run Retry And No-Op Benchmark Density Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add committed benchmark fixtures for repeated rejected and repeated no-op executor dry-run operator actions.

**Architecture:** Reuse the existing benchmark fixture runner and dry-run logic. Add pre-seeded repair-session history artifacts plus expected dry-run contracts; no new production behavior is required unless the benchmark summary no longer exposes the needed fields.

**Tech Stack:** Python, pytest, JSON fixture artifacts, QA-Z benchmark runner.

---

### Task 1: Write Failing Corpus Tests

**Files:**
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`

- [ ] **Step 1: Require the new fixture names**

Extend `test_committed_benchmark_corpus_has_executor_dry_run_fixture_set()` to require:

- `executor_dry_run_repeated_rejected_operator_actions`
- `executor_dry_run_repeated_noop_operator_actions`

- [ ] **Step 2: Require the expected action ids**

Assert that the rejected fixture expects `inspect_rejected_results` and the no-op fixture expects `inspect_no_op_pattern`.

- [ ] **Step 3: Add current-truth doc assertions**

Assert README, benchmarking docs, current-state report, and roadmap mention both fixture names.

- [ ] **Step 4: Run focused tests**

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
python -m pytest tests/test_current_truth.py -q
```

Expected: failures because fixtures and docs are not present yet.

### Task 2: Add Repeated Rejected Fixture

**Files:**
- Create: `benchmarks/fixtures/executor_dry_run_repeated_rejected_operator_actions/expected.json`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_rejected_operator_actions/repo/qa-z.yaml`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_rejected_operator_actions/repo/qa/contracts/contract.md`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_rejected_operator_actions/repo/src/app.py`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_rejected_operator_actions/repo/.qa-z/sessions/session-rejected/session.json`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_rejected_operator_actions/repo/.qa-z/sessions/session-rejected/executor_results/history.json`

- [ ] **Step 1: Seed two rejected attempts**

Use ingest statuses that start with `rejected_`, but avoid `scope_validation_failed` so the verdict remains attention rather than blocked.

- [ ] **Step 2: Pin expected dry-run fields**

Expect:

- `verdict`: `attention_required`
- `verdict_reason`: `manual_retry_review_required`
- `history_signals`: `["repeated_rejected_attempts"]`
- `recommended_action_ids`: `["inspect_rejected_results"]`

### Task 3: Add Repeated No-Op Fixture

**Files:**
- Create: `benchmarks/fixtures/executor_dry_run_repeated_noop_operator_actions/expected.json`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_noop_operator_actions/repo/qa-z.yaml`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_noop_operator_actions/repo/qa/contracts/contract.md`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_noop_operator_actions/repo/src/app.py`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_noop_operator_actions/repo/.qa-z/sessions/session-noop-repeat/session.json`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_noop_operator_actions/repo/.qa-z/sessions/session-noop-repeat/executor_results/history.json`

- [ ] **Step 1: Seed two accepted no-op attempts**

Use `result_status: "no_op"` and `ingest_status: "accepted_no_op"` without missing-explanation warnings.

- [ ] **Step 2: Pin expected dry-run fields**

Expect:

- `verdict`: `attention_required`
- `verdict_reason`: `manual_retry_review_required`
- `history_signals`: `["repeated_no_op_attempts"]`
- `recommended_action_ids`: `["inspect_no_op_pattern"]`

### Task 4: Sync Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Mention the new fixtures**

Add both fixture names to benchmark-related docs.

- [ ] **Step 2: Explain the scope**

State that these fixtures broaden operator-action dry-run coverage without
adding live executor behavior.

### Task 5: Verify

- [ ] **Step 1: Run focused benchmark tests**

```bash
python -m pytest tests/test_benchmark.py -k "executor_dry_run or compare_expected_supports_executor_dry_run_expectations" -q
```

- [ ] **Step 2: Run current-truth tests**

```bash
python -m pytest tests/test_current_truth.py -q
```

- [ ] **Step 3: Run full tests**

```bash
python -m pytest
```

- [ ] **Step 4: Run benchmark corpus**

```bash
python -m qa_z benchmark --json
```

Expected: no failed tests and no failed benchmark fixtures.
