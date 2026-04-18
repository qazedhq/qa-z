# P16 Dry-Run Action Mapping Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make autonomy actions point directly at session-local dry-run review when selected tasks are driven by dry-run safety signals.

**Architecture:** Extend `action_for_task()` to inspect dry-run severity signals and reuse the existing session-id extraction helper to build better next-action packets.

**Tech Stack:** Python, pytest, Markdown docs

---

### Task 1: Add failing autonomy tests

**Files:**
- Modify: `tests/test_autonomy.py`

- [ ] **Step 1: Add blocked dry-run action expectations**

- [ ] **Step 2: Add attention dry-run action expectations**

### Task 2: Implement signal-aware action mapping

**Files:**
- Modify: `src/qa_z/autonomy.py`
- Modify: `README.md`

- [ ] **Step 1: Add specialized action packets**

- [ ] **Step 2: Re-run focused autonomy tests**

### Task 3: Validate

- [ ] `python -m pytest tests/test_autonomy.py -q`
- [ ] `python -m pytest`
