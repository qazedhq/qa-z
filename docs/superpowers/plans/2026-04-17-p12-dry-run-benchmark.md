# P12 Dry-Run Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic benchmark coverage for `qa-z executor-result dry-run` and session-local executor-result history without widening the benchmark contract into a second schema.

**Architecture:** Extend the benchmark runner with one additive `expect_executor_dry_run` section, normalize current dry-run summary fields into benchmark actual data, and seed three small fixtures that cover clear, attention, and blocked safety outcomes.

**Tech Stack:** Python, pytest, JSON fixtures, Markdown docs

---

### Task 1: Add failing benchmark tests for dry-run support

**Files:**
- Modify: `tests/test_benchmark.py`
- Read: `src/qa_z/benchmark.py`
- Read: `src/qa_z/executor_dry_run.py`

- [ ] **Step 1: Add expectation and summary-shape tests**

Add tests for:

- `BenchmarkExpectation.from_dict()` loading `expect_executor_dry_run`
- `compare_expected()` matching dry-run additive aliases such as `expected_recommendation`
- policy category coverage when dry-run expectations are present

- [ ] **Step 2: Add a runner test for one seeded dry-run fixture**

Create a temp fixture with:

- seeded `session.json`
- seeded `executor_results/history.json`
- `run.executor_result_dry_run`
- `expect_executor_dry_run`

Assert the benchmark run passes and records the normalized dry-run verdict and rule ids.

- [ ] **Step 3: Run the focused benchmark tests and verify they fail**

Run: `python -m pytest tests/test_benchmark.py -q`
Expected: FAIL because the benchmark contract and runner do not yet support dry-run expectations.

### Task 2: Implement additive benchmark support

**Files:**
- Modify: `src/qa_z/benchmark.py`

- [ ] **Step 1: Extend the expectation model**

Add:

- `expect_executor_dry_run`
- `executor_result_dry_run_config()`

- [ ] **Step 2: Execute and summarize dry-run fixtures**

Call the existing dry-run runner and store normalized benchmark actual output under `actual["executor_dry_run"]`.

- [ ] **Step 3: Extend comparison and category logic**

Add dry-run comparison to `compare_expected()`.

Count dry-run fixtures under `policy` by treating `executor_dry_run.` failures as policy failures when `expect_executor_dry_run` is present.

- [ ] **Step 4: Re-run focused benchmark tests and verify they pass**

Run: `python -m pytest tests/test_benchmark.py -q`
Expected: PASS

### Task 3: Add committed dry-run fixtures and docs

**Files:**
- Create: `benchmarks/fixtures/executor_dry_run_clear_verified_completed/**`
- Create: `benchmarks/fixtures/executor_dry_run_repeated_partial_attention/**`
- Create: `benchmarks/fixtures/executor_dry_run_completed_verify_blocked/**`
- Modify: `docs/benchmarking.md`
- Modify: `README.md`
- Modify: `docs/mvp-issues.md`

- [ ] **Step 1: Seed the three committed fixtures**

Each fixture should include:

- `expected.json`
- `repo/qa-z.yaml`
- `repo/.qa-z/sessions/<session-id>/session.json`
- `repo/.qa-z/sessions/<session-id>/executor_results/history.json`

- [ ] **Step 2: Update benchmark docs**

Describe:

- the new `expect_executor_dry_run` section
- the dry-run fixture set
- the fact that dry-run coverage currently rolls into the `policy` category

- [ ] **Step 3: Add committed-corpus assertions**

Extend `tests/test_benchmark.py` to assert the committed dry-run fixtures exist and expose the expected verdicts.

### Task 4: Full validation

**Files:**
- Read: `benchmarks/fixtures/**/expected.json`
- Read: `docs/benchmarking.md`

- [ ] **Step 1: Run formatting, lint, types, and tests**

Run: `python -m ruff format --check .`
Expected: already formatted

Run: `python -m ruff check .`
Expected: all checks passed

Run: `python -m mypy src tests`
Expected: success

Run: `python -m pytest`
Expected: full suite passes

- [ ] **Step 2: Run the benchmark corpus**

Run: `python -m qa_z benchmark --json`
Expected: all fixtures pass, including the new dry-run fixtures
