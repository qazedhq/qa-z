# Executor Bridge Stdout Missing Context Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make human `qa-z executor-bridge` stdout surface copied and missing action-context diagnostics that are already present in bridge manifests and executor guides.

**Architecture:** Reuse the existing `bridge_action_context_inputs()` and `bridge_missing_action_context_inputs()` helpers inside `render_bridge_stdout()`. This is an additive human-rendering change; JSON manifest output and bridge packaging stay unchanged.

**Tech Stack:** Python standard library, pytest, existing QA-Z executor bridge helpers.

---

### Task 1: Pin Human Stdout Diagnostics

**Files:**
- Modify: `tests/test_executor_bridge.py`

- [x] **Step 1: Add CLI stdout missing-context test**

Create a loop-sourced bridge with one existing action context file and one
missing optional context path. Assert default human stdout reports copied action
context count, missing action context count, and the missing path.

- [x] **Step 2: Run RED test**

```bash
python -m pytest tests/test_executor_bridge.py::test_executor_bridge_cli_stdout_surfaces_missing_action_context -q
```

Expected: fail because stdout currently omits action-context diagnostics.

### Task 2: Implement Stdout Rendering

**Files:**
- Modify: `src/qa_z/executor_bridge.py`

- [x] **Step 1: Render copied context count**

Call `bridge_action_context_inputs(manifest)` from `render_bridge_stdout()` and
append `Action context inputs: <count>` when at least one context input was
copied.

- [x] **Step 2: Render missing context diagnostics**

Call `bridge_missing_action_context_inputs(manifest)` from
`render_bridge_stdout()` and append `Missing action context: <count> (<paths>)`
when skipped optional context paths exist.

- [x] **Step 3: Run GREEN test**

```bash
python -m pytest tests/test_executor_bridge.py::test_executor_bridge_cli_stdout_surfaces_missing_action_context -q
```

Expected: pass.

### Task 3: Sync Truth Surfaces

**Files:**
- Modify: `README.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update user-facing docs**

Document that human executor-bridge stdout includes action-context package
health and missing-context diagnostics.

- [x] **Step 2: Update current-truth assertions and gate snapshot**

If the full pytest count changes, update the alpha closure snapshot and matching
truth assertion.

### Task 4: Verify

**Files:**
- Test only

- [x] **Step 1: Run focused checks**

```bash
python -m pytest tests/test_executor_bridge.py tests/test_current_truth.py -q
```

Expected: pass.

- [x] **Step 2: Run full gates**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If formatting is needed, format only touched files and rerun the affected checks.
