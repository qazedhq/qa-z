# Dry-Run Operator Benchmark Density Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add benchmark coverage for executor dry-run operator summaries and recommended actions.

**Architecture:** Keep dry-run diagnostic generation in `executor_dry_run_logic.py`; the benchmark only summarizes and compares the fields already emitted by dry-run. Add one committed fixture that seeds session-local history and runs the existing live-free dry-run path.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, JSON artifact contracts.

---

### Task 1: Add Failing Benchmark Contract Tests

**Files:**
- Modify: `tests/test_benchmark.py`

- [ ] **Step 1: Extend the alias comparison test**

Add `operator_summary`, `recommended_action_ids`, and `recommended_action_summaries` to the existing dry-run expectation test so benchmark comparison fails until actual summaries expose those fields.

- [ ] **Step 2: Extend the committed corpus test**

Require `executor_dry_run_validation_noop_operator_actions` in the committed dry-run fixture set and assert its action ids include `review_validation_conflict` and `require_no_op_explanation`.

- [ ] **Step 3: Run the focused tests**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "executor_dry_run or compare_expected_supports_executor_dry_run_expectations" -q
```

Expected: failure showing missing `recommended_action_ids` and missing fixture.

### Task 2: Expose Diagnostic Fields In Benchmark Actuals

**Files:**
- Modify: `src/qa_z/benchmark.py`

- [ ] **Step 1: Summarize recommended actions**

In `summarize_executor_dry_run_actual()`, normalize `recommended_actions` into:

- `operator_summary`
- `recommended_action_ids`
- `recommended_action_summaries`

- [ ] **Step 2: Run the focused tests**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "compare_expected_supports_executor_dry_run_expectations" -q
```

Expected: pass.

### Task 3: Add The Committed Fixture

**Files:**
- Create: `benchmarks/fixtures/executor_dry_run_validation_noop_operator_actions/expected.json`
- Create: `benchmarks/fixtures/executor_dry_run_validation_noop_operator_actions/repo/qa-z.yaml`
- Create: `benchmarks/fixtures/executor_dry_run_validation_noop_operator_actions/repo/qa/contracts/contract.md`
- Create: `benchmarks/fixtures/executor_dry_run_validation_noop_operator_actions/repo/src/app.py`
- Create: `benchmarks/fixtures/executor_dry_run_validation_noop_operator_actions/repo/.qa-z/sessions/session-validation-noop/session.json`
- Create: `benchmarks/fixtures/executor_dry_run_validation_noop_operator_actions/repo/.qa-z/sessions/session-validation-noop/executor_results/history.json`

- [ ] **Step 1: Seed the session**

Create a repair-session manifest with `session_id` set to `session-validation-noop`.

- [ ] **Step 2: Seed the mixed attention history**

Create one no-op attempt with both warning ids:

- `validation_summary_conflicts_with_results`
- `no_op_without_explanation`

- [ ] **Step 3: Pin the expectation**

Expect `attention_required`, `classification_conflict_requires_review`, both history signals, two attention rules, and both recommended action ids.

- [ ] **Step 4: Run the committed corpus test**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_benchmark_corpus_has_executor_dry_run_fixture_set" -q
```

Expected: pass.

### Task 4: Sync Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `tests/test_current_truth.py`

- [ ] **Step 1: Add current-truth assertions**

Assert the new fixture name and operator-action benchmark wording appear in docs.

- [ ] **Step 2: Update docs**

Mention that dry-run fixtures now pin operator summary and recommended actions.

- [ ] **Step 3: Run current-truth tests**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

### Task 5: Full Verification

- [ ] **Step 1: Run benchmark-focused tests**

```bash
python -m pytest tests/test_benchmark.py -k "executor_dry_run or compare_expected_supports_executor_dry_run_expectations" -q
```

- [ ] **Step 2: Run full tests**

```bash
python -m pytest
```

- [ ] **Step 3: Run benchmark corpus**

```bash
python -m qa_z benchmark --json
```

Expected: all tests pass and benchmark reports the expanded fixture corpus with no failed fixtures.
