# Autonomy Selection Penalty Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve selected-task penalty residue on `qa-z autonomy status` so post-loop inspection stays consistent with `qa-z select-next`.

**Architecture:** Reuse the stored latest `selected_tasks.json` as the source of truth. Extend the compact status copy and human status renderer additively, then sync docs to match the landed output.

**Tech Stack:** Python CLI/status rendering, pytest, README/schema docs

---

### Task 1: Lock The Additive Status Surface In Tests

**Files:**
- Modify: `tests/test_autonomy.py`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Add failing expectations for selected-task penalty residue on autonomy status**
- [x] **Step 2: Run focused tests to verify the current implementation drops that residue**

### Task 2: Implement The Minimal Status Copy And Rendering Change

**Files:**
- Modify: `src/qa_z/autonomy.py`

- [ ] **Step 1: Copy `selection_penalty` and `selection_penalty_reasons` into `latest_selected_task_details`**
- [ ] **Step 2: Render that residue on human `qa-z autonomy status` output when present**
- [ ] **Step 3: Re-run focused autonomy tests**

### Task 3: Sync Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`

- [ ] **Step 1: Describe the additive status residue honestly**
- [ ] **Step 2: Re-run current-truth checks**

### Task 4: Full Verification

**Files:**
- Modify: none

- [ ] **Step 1: Run `python -m ruff format --check .`**
- [ ] **Step 2: Run `python -m ruff check .`**
- [ ] **Step 3: Run `python -m mypy src tests`**
- [ ] **Step 4: Run `python -m pytest`**
- [ ] **Step 5: Run `python -m qa_z benchmark --json`**
