# Autonomy Runtime Budget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `qa-z autonomy` track elapsed loop time and continue until a minimum runtime budget is satisfied, so a 4-hour self-improvement run is enforceable instead of implied.

**Architecture:** Extend the autonomy workflow with explicit runtime-budget parameters and per-loop elapsed accounting. Persist runtime progress into autonomy summary, per-loop outcome artifacts, history/status surfaces, and CLI output without introducing schedulers or remote orchestration.

**Tech Stack:** Python CLI, local JSON artifacts, deterministic tests with injected monotonic/sleep callables

---

### Task 1: Runtime-budget tests

**Files:**
- Modify: `tests/test_autonomy.py`

- [ ] Add failing tests for minimum runtime behavior, per-loop elapsed accounting, and CLI/status exposure.
- [ ] Verify the new tests fail for the expected missing runtime-budget fields or stop conditions.

### Task 2: Autonomy runtime implementation

**Files:**
- Modify: `src/qa_z/autonomy.py`
- Modify: `src/qa_z/cli.py`

- [ ] Add runtime-budget arguments to `run_autonomy` and loop until both loop-count and runtime budget are satisfied.
- [ ] Record loop elapsed seconds, cumulative elapsed seconds, remaining budget, and runtime target in summary/outcome/history/state surfaces.
- [ ] Add CLI flags for runtime-budget control without changing existing default behavior.

### Task 3: Documentation and artifact truth sync

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`

- [ ] Document the new runtime-budget CLI surface and artifact fields.
- [ ] Make the service-readiness story explicit: `autonomy` can now enforce a wall-clock minimum run such as 4 hours.

### Task 4: Full validation

**Files:**
- Verify only

- [ ] Run `python -m ruff format --check .`
- [ ] Run `python -m ruff check .`
- [ ] Run `python -m mypy src tests`
- [ ] Run `python -m pytest`
- [ ] Run `python -m qa_z benchmark --json`
