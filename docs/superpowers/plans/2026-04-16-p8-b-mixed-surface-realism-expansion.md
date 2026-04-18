# P8-B Mixed-Surface Realism Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand deterministic mixed-surface benchmark and verification realism across functional, maintenance, worktree, and executor-result cases.

**Architecture:** Reuse the existing benchmark runner, verification comparer, and executor-result ingest summaries. Add narrow expectation aliases and summary fields only where fixtures need extra realism. Most of the work lands in committed fixture data, benchmark tests, verification tests, self-inspection coverage guards, and docs.

**Tech Stack:** Python, pytest, QA-Z benchmark runner, seeded JSON artifacts, Markdown docs.

---

### Task 1: Lock The New Benchmark And Verification Contract

**Files:**
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_verification.py`

- [ ] Add failing tests for new additive expectation keys such as `expected_ingest_status`, `expected_recommendation`, and `remaining_issue_count_min`.
- [ ] Add failing verification coverage for unchanged maintenance-style evidence with explicit remaining-issue counts.
- [ ] Run the targeted pytest nodes and confirm they fail for the expected missing fields or aliases.

### Task 2: Add Mixed-Surface Realism Fixtures

**Files:**
- Create: `benchmarks/fixtures/mixed_fast_handoff_functional_worktree_cleanup/**`
- Create: `benchmarks/fixtures/mixed_docs_schema_sync_maintenance_candidate/**`
- Create: `benchmarks/fixtures/executor_result_partial_mixed_verify_candidate/**`
- Create: `benchmarks/fixtures/executor_result_no_op_with_justification_candidate/**`
- Create: `benchmarks/fixtures/mixed_cleanup_only_worktree_risk_candidate/**`
- Modify: `tests/test_benchmark.py`

- [ ] Add a committed-corpus guard for the new realism fixtures.
- [ ] Seed each fixture with only the files and artifacts needed for deterministic execution or comparison.
- [ ] Re-run the committed-corpus pytest guard until it passes.

### Task 3: Implement Minimal Runtime Support

**Files:**
- Modify: `src/qa_z/benchmark.py`
- Modify: `src/qa_z/verification.py`
- Modify: `tests/test_self_improvement.py` if needed for coverage-gap behavior

- [ ] Add only the summary fields and expectation aliases required by the new fixtures.
- [ ] Keep comparison behavior additive and backward compatible.
- [ ] Ensure executed mixed fixture names satisfy the self-inspection coverage-gap heuristic.

### Task 4: Update Current-Truth Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/mvp-issues.md`

- [ ] Document the new mixed-surface realism classes without overstating live executor capability.
- [ ] Explain how executor-result realism and verification realism relate.
- [ ] Update roadmap text to reflect the new benchmark state and remaining future work.

### Task 5: Validate

**Commands:**
- [ ] `python -m pytest tests/test_benchmark.py tests/test_verification.py tests/test_self_improvement.py -q`
- [ ] `python -m ruff format --check .`
- [ ] `python -m ruff check .`
- [ ] `python -m mypy src tests`
- [ ] `python -m pytest`
- [ ] `python -m qa_z benchmark --json`
