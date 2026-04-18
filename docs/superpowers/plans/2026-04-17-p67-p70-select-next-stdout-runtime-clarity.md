# Select-Next Stdout And Runtime Clarity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `qa-z select-next` and `qa-z autonomy` human output easier to triage without changing the underlying planning contracts.

**Architecture:** Keep machine-readable artifacts untouched. Add one CLI stdout renderer for selected-task summaries and one shared autonomy runtime formatter so the human surfaces stay consistent. Update docs only where the new operator-facing behavior is actually visible.

**Tech Stack:** Python CLI rendering, pytest, README/schema docs

---

### Task 1: Lock The New Human Output In Tests

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `tests/test_autonomy.py`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Write the failing tests**
- [x] **Step 2: Run the focused tests to verify they fail for the expected missing renderer/runtime wording**

### Task 2: Implement The Minimal Renderers

**Files:**
- Modify: `src/qa_z/cli.py`
- Modify: `src/qa_z/autonomy.py`

- [ ] **Step 1: Add `select-next` human stdout rendering for selected task details**
- [ ] **Step 2: Add a shared autonomy runtime formatter that spells out zero-budget runs clearly**
- [ ] **Step 3: Run the focused tests to verify they pass**

### Task 3: Align Docs With The Landed Surface

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`

- [ ] **Step 1: Document the stronger `select-next` human output honestly**
- [ ] **Step 2: Document the explicit autonomy no-budget runtime wording**
- [ ] **Step 3: Re-run current-truth coverage**

### Task 4: Full Verification

**Files:**
- Modify: none

- [ ] **Step 1: Run `python -m ruff format --check .`**
- [ ] **Step 2: Run `python -m ruff check .`**
- [ ] **Step 3: Run `python -m mypy src tests`**
- [ ] **Step 4: Run `python -m pytest`**
- [ ] **Step 5: Run `python -m qa_z benchmark --json`**
