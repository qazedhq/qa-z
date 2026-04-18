# P13 Dry-Run Diagnostics And Self-Inspection Bridge Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `qa-z executor-result dry-run` more legible and make self-inspection consume its structured evidence directly.

**Architecture:** Add stable diagnostic fields to dry-run summaries, surface them in the Markdown report, and teach self-inspection to derive backlog candidates from `dry_run_summary.json` as well as `history.json`.

**Tech Stack:** Python, pytest, JSON artifacts, Markdown docs

---

### Task 1: Add failing tests for dry-run diagnostics

**Files:**
- Modify: `tests/test_executor_result.py`
- Modify: `tests/test_self_improvement.py`
- Read: `src/qa_z/executor_dry_run.py`
- Read: `src/qa_z/self_improvement.py`

- [ ] **Step 1: Extend dry-run outcome tests**

Assert that dry-run JSON now includes:

- `verdict_reason`
- `rule_status_counts`

for representative `clear`, `attention_required`, and `blocked` histories.

- [ ] **Step 2: Add self-inspection tests for dry-run evidence**

Add tests showing that:

- a single blocked dry-run summary still produces a `workflow_gap`
- a missing no-op explanation in dry-run output produces a `no_op_safeguard_gap`

- [ ] **Step 3: Run focused tests and verify they fail**

Run:

- `python -m pytest tests/test_executor_result.py -q`
- `python -m pytest tests/test_self_improvement.py -q`

Expected: FAIL before implementation.

### Task 2: Implement additive dry-run diagnostics

**Files:**
- Modify: `src/qa_z/executor_dry_run.py`

- [ ] **Step 1: Add summary fields**

Add:

- `verdict_reason`
- `rule_status_counts`

- [ ] **Step 2: Improve report rendering**

Expose the reason and rule counts in `dry_run_report.md`.

- [ ] **Step 3: Re-run focused dry-run tests**

Run:

- `python -m pytest tests/test_executor_result.py -q`

Expected: PASS

### Task 3: Bridge dry-run evidence into self-inspection

**Files:**
- Modify: `src/qa_z/self_improvement.py`
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`

- [ ] **Step 1: Read dry-run summaries beside executor history**

When available, load sibling `dry_run_summary.json` and use it as additional evidence.

- [ ] **Step 2: Promote dry-run-specific gaps**

Create or enrich:

- `partial_completion_gap`
- `no_op_safeguard_gap`
- `workflow_gap`

from dry-run verdicts and signals even when history length is short.

- [ ] **Step 3: Update docs**

Describe the new dry-run summary fields and the fact that self-inspection consumes dry-run artifacts directly.

### Task 4: Full validation

**Files:**
- Read: `src/qa_z/executor_dry_run.py`
- Read: `src/qa_z/self_improvement.py`

- [ ] **Step 1: Run formatting, lint, types, and tests**

Run:

- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy src tests`
- `python -m pytest`

Expected: PASS
