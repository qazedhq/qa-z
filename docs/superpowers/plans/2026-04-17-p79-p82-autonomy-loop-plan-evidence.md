# Autonomy Loop Plan Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make saved autonomy `loop_plan.md` artifacts self-contained by carrying the selected-task evidence that already exists in `selected_tasks.json`.

**Architecture:** Reuse the stored selected-task artifact as the source of truth. Extend only the autonomy Markdown renderer, then sync docs and current-truth coverage so the persisted planning contract stays honest.

**Tech Stack:** Python Markdown renderers, pytest, README/schema docs

---

### Task 1: Lock The Missing Evidence In Tests

**Files:**
- Modify: `tests/test_autonomy.py`

- [x] **Step 1: Add a failing test for selected-task evidence inside autonomy loop plans**
- [x] **Step 2: Run the focused autonomy tests to confirm the old renderer drops that evidence**

### Task 2: Implement Minimal Renderer Support

**Files:**
- Modify: `src/qa_z/autonomy.py`

- [x] **Step 1: Mirror selected-task evidence lines into autonomy `loop_plan.md`**
- [x] **Step 2: Preserve the existing score and penalty residue rendering**
- [x] **Step 3: Re-run focused autonomy tests**

### Task 3: Sync Current-Truth Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`
- Modify: `tests/test_current_truth.py`

- [ ] **Step 1: Document that autonomy loop plans now mirror selected-task evidence**
- [ ] **Step 2: Re-run current-truth coverage**

### Task 4: Full Verification

**Files:**
- Modify: none

- [ ] **Step 1: Run `python -m ruff format --check .`**
- [ ] **Step 2: Run `python -m ruff check .`**
- [ ] **Step 3: Run `python -m mypy src tests`**
- [ ] **Step 4: Run `python -m pytest`**
- [ ] **Step 5: Run `python -m qa_z benchmark --json`**
