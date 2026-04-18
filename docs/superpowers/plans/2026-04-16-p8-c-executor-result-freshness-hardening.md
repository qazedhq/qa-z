# P8-C Executor-Result Freshness And Ingest Hardening Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make executor-result ingest more realistic and conservative by hardening freshness handling, validation-evidence consistency, and benchmark coverage for rejected or warning-only outcomes.

**Architecture:** Keep the current executor-result contract and repair-session resume flow intact. Add a narrow ingest-time freshness comparison, explicit validation-consistency warnings, backlog implications for suspicious accepted results, and benchmark support for stored rejection outcomes. Extend docs only where the behavior is now real.

**Tech Stack:** Python dataclasses, JSON artifacts, pytest, QA-Z benchmark fixtures, Markdown docs.

---

### Task 1: Lock The P8-C Behavior With Tests

**Files:**
- Modify: `tests/test_executor_result.py`
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_self_improvement.py`

- [ ] Add a failing ingest test for a future-dated executor result that should be rejected against the ingest reference time.
- [ ] Add a failing ingest test for a completed result whose validation summary conflicts with detailed results and therefore blocks verify resume.
- [ ] Add failing benchmark coverage for a rejected freshness fixture and an accepted-with-warning validation-conflict fixture.
- [ ] Extend self-inspection coverage if new backlog implications need a regression guard.

### Task 2: Add Committed P8-C Benchmark Fixtures

**Files:**
- Create: `benchmarks/fixtures/executor_result_future_timestamp_rejected/**`
- Create: `benchmarks/fixtures/executor_result_validation_conflict_blocked/**`
- Modify: `tests/test_benchmark.py`

- [ ] Seed one rejected freshness fixture that proves benchmark execution can assert stored ingest rejections.
- [ ] Seed one validation-conflict fixture that proves accepted-with-warning results do not over-trigger verification.
- [ ] Update committed-corpus discovery guards so the new fixtures stay part of the shipped benchmark set.

### Task 3: Implement Narrow Ingest Hardening

**Files:**
- Modify: `src/qa_z/executor_ingest.py`
- Modify: `src/qa_z/benchmark.py`

- [ ] Add an optional ingest reference time to executor-result ingest and record it in `freshness_check`.
- [ ] Reject future-dated executor results deterministically.
- [ ] Add explicit validation-consistency warnings and wire them into verify-resume blocking.
- [ ] Emit structural backlog implications for suspicious validation evidence.
- [ ] Let the benchmark harness capture stored ingest rejections as normal fixture outcomes.

### Task 4: Sync Current-Truth Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`

- [ ] Document ingest-time freshness checks and validation-consistency gating without overstating live executor capability.
- [ ] Explain the new benchmark fixture classes and what regression they protect against.
- [ ] Update roadmap text so executor-result ingest no longer sounds limited to bridge/session freshness only.

### Task 5: Validate

**Commands:**
- [ ] `python -m pytest tests/test_executor_result.py tests/test_benchmark.py tests/test_self_improvement.py -q`
- [ ] `python -m ruff format --check .`
- [ ] `python -m ruff check .`
- [ ] `python -m mypy src tests`
- [ ] `python -m pytest`
- [ ] `python -m qa_z benchmark --json`
