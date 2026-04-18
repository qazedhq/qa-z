# P5-C Mixed-Language Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic mixed Python/TypeScript verification benchmark fixtures.

**Architecture:** Reuse the existing benchmark runner and verification comparison code. Add fixture data under `benchmarks/fixtures/`, a committed-corpus guard in `tests/test_benchmark.py`, and documentation updates in README, benchmark docs, and MVP issues.

**Tech Stack:** Python, pytest, QA-Z benchmark runner, seeded JSON artifacts.

---

### Task 1: Lock The P5-C Corpus Contract

**Files:**
- Modify: `tests/test_benchmark.py`

- [x] Add a test requiring `mixed_py_resolved_ts_regressed_candidate`, `mixed_ts_resolved_py_regressed_candidate`, `mixed_all_resolved_candidate`, and `mixed_partial_resolved_with_regression_candidate`.
- [x] Run `python -m pytest tests/test_benchmark.py::test_committed_benchmark_corpus_has_mixed_language_verification_fixture_set -q`.
- [x] Confirm the test fails because the fixtures are absent.

### Task 2: Add Mixed Verification Fixtures

**Files:**
- Create: `benchmarks/fixtures/mixed_py_resolved_ts_regressed_candidate/**`
- Create: `benchmarks/fixtures/mixed_ts_resolved_py_regressed_candidate/**`
- Create: `benchmarks/fixtures/mixed_all_resolved_candidate/**`
- Create: `benchmarks/fixtures/mixed_partial_resolved_with_regression_candidate/**`

- [x] Add `expected.json`, `repo/qa-z.yaml`, `repo/qa/contracts/contract.md`, and seeded baseline/candidate fast summaries for each fixture.
- [x] Run the corpus-contract test again and confirm it passes.
- [x] Run the four selected benchmark fixtures together with an isolated results directory.

### Task 3: Update Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/mvp-issues.md`

- [x] Document that the benchmark corpus now includes mixed Python/TypeScript verification verdicts.
- [x] Add a mixed-language verification fixture section to `docs/benchmarking.md`.
- [x] Update the MVP issue status for P5-C.

### Task 4: Validate

**Commands:**
- [x] `python -m pytest tests/test_benchmark.py`
- [x] `python -m qa_z benchmark --results-dir <temp>/qa-z-full-benchmark-results --json`
- [x] `python -m pytest`
