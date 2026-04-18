# P15 Dry-Run Priority Calibration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Calibrate backlog scoring so blocked dry-run safety states outrank lighter dry-run attention states.

**Architecture:** Add dry-run severity signals to history-derived backlog candidates and teach the deterministic scorer to reward those signals.

**Tech Stack:** Python, pytest, Markdown docs

---

### Task 1: Add failing self-improvement tests

**Files:**
- Modify: `tests/test_self_improvement.py`
- Read: `src/qa_z/self_improvement.py`

- [ ] **Step 1: Add score tests**

Prove that a blocked dry-run workflow candidate scores above a no-op attention candidate.

- [ ] **Step 2: Add signal assertions**

Assert that self-inspection emits `executor_dry_run_blocked` on blocked candidates.

### Task 2: Implement scoring calibration

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [ ] **Step 1: Emit dry-run severity signals**

- [ ] **Step 2: Add scoring bonuses**

- [ ] **Step 3: Re-run focused tests**

### Task 3: Validate

- [ ] `python -m pytest tests/test_self_improvement.py -q`
- [ ] `python -m pytest`
