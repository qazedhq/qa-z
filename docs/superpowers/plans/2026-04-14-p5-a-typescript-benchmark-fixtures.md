# P5-A TypeScript Benchmark Fixtures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the QA-Z benchmark corpus with deterministic TypeScript fast-check fixtures.

**Architecture:** Reuse the existing language-neutral benchmark contract and runner. Add fixture data under `benchmarks/fixtures/`, tests in `tests/test_benchmark.py`, and TypeScript fixture guidance in `docs/benchmarking.md`.

**Tech Stack:** Python, pytest, QA-Z benchmark runner, deterministic benchmark support scripts.

---

### Task 1: Lock The TypeScript Corpus Contract

**Files:**
- Modify: `tests/test_benchmark.py`

- [x] **Step 1: Write a failing corpus test**

Add a test that requires `ts_lint_failure`, `ts_type_error`, `ts_test_failure`, `ts_multiple_fast_failures`, `ts_unchanged_candidate`, and `ts_regressed_candidate` to exist in `benchmarks/fixtures/`.

- [x] **Step 2: Run the failing test**

Run: `python -m pytest tests/test_benchmark.py::test_committed_benchmark_corpus_has_typescript_fast_fixture_set -q`

Expected: FAIL because the TypeScript fixtures do not exist yet.

### Task 2: Add Deterministic TypeScript Fixtures

**Files:**
- Create: `benchmarks/fixtures/ts_lint_failure/**`
- Create: `benchmarks/fixtures/ts_type_error/**`
- Create: `benchmarks/fixtures/ts_test_failure/**`
- Create: `benchmarks/fixtures/ts_multiple_fast_failures/**`
- Create: `benchmarks/fixtures/ts_unchanged_candidate/**`
- Create: `benchmarks/fixtures/ts_regressed_candidate/**`

- [ ] **Step 1: Add fast failure fixtures**

Use `python .qa-z-benchmark/fast_check.py fail ...` commands with `ts_lint`, `ts_type`, and `ts_test` ids.

- [ ] **Step 2: Add verification fixtures**

Seed `.qa-z/runs/baseline/fast/summary.json` and `.qa-z/runs/candidate/fast/summary.json` with TypeScript check ids to cover unchanged and regressed verdicts.

- [ ] **Step 3: Run the corpus test**

Run: `python -m pytest tests/test_benchmark.py::test_committed_benchmark_corpus_has_typescript_fast_fixture_set -q`

Expected: PASS.

### Task 3: Document TypeScript Fixture Authoring

**Files:**
- Modify: `docs/benchmarking.md`

- [ ] **Step 1: Add TypeScript fixture guidance**

Document supported fixture types, deterministic helper usage, and the decision to reuse `expect_fast`, `expect_handoff`, and `expect_verify`.

- [ ] **Step 2: Run documentation-sensitive tests**

Run: `python -m pytest tests/test_benchmark.py -q`

Expected: PASS.
