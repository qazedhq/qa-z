# P14 Dry-Run Benchmark Parity Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend benchmark dry-run coverage so it guards the richer P13 diagnostic fields, not only the top-level verdict and rule-id buckets.

**Architecture:** Normalize `verdict_reason` and rule-status counts into the benchmark actual payload, add tests for those fields, and update the committed dry-run fixtures to assert them.

**Tech Stack:** Python, pytest, JSON fixtures, Markdown docs

---

### Task 1: Add failing benchmark tests

**Files:**
- Modify: `tests/test_benchmark.py`
- Read: `src/qa_z/benchmark.py`

- [ ] **Step 1: Extend expectation-comparison coverage**

Add a benchmark test that expects:

- `verdict_reason`
- `clear_rule_count`
- `attention_rule_count`
- `blocked_rule_count`

from a normalized dry-run actual section.

- [ ] **Step 2: Extend committed-corpus assertions**

Assert that the committed dry-run fixtures pin at least one of the new fields.

- [ ] **Step 3: Run focused benchmark tests and verify they fail**

Run:

- `python -m pytest tests/test_benchmark.py -q`

Expected: FAIL before benchmark normalization is updated.

### Task 2: Implement benchmark parity

**Files:**
- Modify: `src/qa_z/benchmark.py`
- Modify: `benchmarks/fixtures/executor_dry_run_*/expected.json`

- [ ] **Step 1: Normalize new dry-run fields**

Expose:

- `verdict_reason`
- `clear_rule_count`
- `attention_rule_count`
- `blocked_rule_count`

- [ ] **Step 2: Update committed dry-run fixture expectations**

Add the new expected values to the three dry-run fixtures.

- [ ] **Step 3: Re-run focused benchmark tests**

Run:

- `python -m pytest tests/test_benchmark.py -q`

Expected: PASS

### Task 3: Update docs and validate

**Files:**
- Modify: `docs/benchmarking.md`
- Modify: `docs/mvp-issues.md`

- [ ] **Step 1: Document the expanded dry-run expectation keys**

- [ ] **Step 2: Run benchmark validation**

Run:

- `python -m qa_z benchmark --json`

Expected: PASS
