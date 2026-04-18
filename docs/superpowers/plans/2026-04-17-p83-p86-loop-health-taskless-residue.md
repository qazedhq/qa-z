# Loop Health Taskless Residue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten autonomy loop health by ensuring taskless loops are classified as blocked and carry enough residue to explain why selection produced no work.

**Architecture:** Reuse the existing autonomy outcome as the source of truth. Add only additive loop-health fields, mirror them through history and human surfaces, then sync docs and current-truth tests.

**Tech Stack:** Python autonomy workflow code, pytest, README/schema docs

---

### Task 1: Lock The Taskless-Loop Gap In Tests

**Files:**
- Modify: `tests/test_autonomy.py`

- [x] **Step 1: Add failing coverage for taskless loops after stale backlog closure**
- [x] **Step 2: Add failing coverage for human status output to show the taskless-loop reason**
- [x] **Step 3: Run focused autonomy tests and confirm the old behavior fails**

### Task 2: Implement Minimal Loop-Health Residue

**Files:**
- Modify: `src/qa_z/autonomy.py`

- [x] **Step 1: Classify taskless loops as `blocked_no_candidates`**
- [x] **Step 2: Preserve `selection_gap_reason` and before/after backlog counts**
- [x] **Step 3: Mirror that residue through loop plan, history, and status**
- [x] **Step 4: Re-run focused autonomy coverage**

### Task 3: Sync Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `tests/test_current_truth.py`

- [ ] **Step 1: Document the narrower taskless-loop contract honestly**
- [ ] **Step 2: Re-run current-truth coverage**

### Task 4: Full Verification

**Files:**
- Modify: none

- [ ] **Step 1: Run `python -m ruff format --check .`**
- [ ] **Step 2: Run `python -m ruff check .`**
- [ ] **Step 3: Run `python -m mypy src tests`**
- [ ] **Step 4: Run `python -m pytest`**
- [ ] **Step 5: Run `python -m qa_z benchmark --json`**
