# Loop Plan Selection Residue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep saved `loop_plan.md` artifacts aligned with the richer selected-task residue already visible on CLI and autonomy status surfaces.

**Architecture:** Reuse the existing selected-task artifact fields as the source of truth. Extend only the Markdown loop-plan renderers, then sync docs so the persisted planning contract stays honest.

**Tech Stack:** Python Markdown renderers, pytest, README/schema docs

---

### Task 1: Lock Loop-Plan Detail In Tests

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `tests/test_autonomy.py`

- [x] **Step 1: Add failing tests for selection score and penalty residue in loop plans**
- [x] **Step 2: Run focused tests to verify the old renderers drop that residue**

### Task 2: Implement Minimal Loop-Plan Rendering Updates

**Files:**
- Modify: `src/qa_z/self_improvement.py`
- Modify: `src/qa_z/autonomy.py`

- [ ] **Step 1: Mirror selection score on loop-plan task entries when present**
- [ ] **Step 2: Mirror selection penalty residue on loop-plan task entries when present**
- [ ] **Step 3: Re-run focused loop-plan tests**

### Task 3: Sync Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`
- Modify: `tests/test_current_truth.py`

- [ ] **Step 1: Document the richer persisted loop-plan surface honestly**
- [ ] **Step 2: Re-run current-truth coverage**

### Task 4: Full Verification

**Files:**
- Modify: none

- [ ] **Step 1: Run `python -m ruff format --check .`**
- [ ] **Step 2: Run `python -m ruff check .`**
- [ ] **Step 3: Run `python -m mypy src tests`**
- [ ] **Step 4: Run `python -m pytest`**
- [ ] **Step 5: Run `python -m qa_z benchmark --json`**
