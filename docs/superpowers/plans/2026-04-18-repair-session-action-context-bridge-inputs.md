# Repair Session Action Context Bridge Inputs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve selected repair-session action context from autonomy through executor bridge packaging by copying existing evidence files into bridge-local `inputs/context/`.

**Architecture:** Extend the autonomy `repair_session_action()` call path to accept selected task evidence paths, then extend executor bridge input packaging to copy action context paths from the selected loop action. The copied evidence is additive metadata under `manifest["inputs"]`; existing session, handoff, safety, validation, and return contracts stay unchanged.

**Tech Stack:** Python standard library, pytest, existing QA-Z autonomy and executor bridge helpers.

---

### Task 1: Pin Repair-Session Action Context

**Files:**
- Modify: `tests/test_autonomy.py`

- [x] **Step 1: Add autonomy repair-session context test**

Assert that `run_autonomy()` prepares a `repair_session` action with the selected verification evidence paths in `context_paths`.

- [x] **Step 2: Run RED test**

```bash
python -m pytest tests/test_autonomy.py::test_autonomy_prepares_repair_session_with_context_paths -q
```

Expected: fail because repair-session actions currently omit `context_paths`.

### Task 2: Pin Bridge Context Input Copying

**Files:**
- Modify: `tests/test_executor_bridge.py`

- [x] **Step 1: Add executor bridge context input test**

Assert that a loop-sourced bridge copies the selected repair-session action context files into `inputs/context/`, records `inputs.action_context`, records no missing context for present files, and mentions action context in `executor_guide.md`.

- [x] **Step 2: Run RED test**

```bash
python -m pytest tests/test_executor_bridge.py::test_executor_bridge_copies_repair_action_context_inputs -q
```

Expected: fail because executor bridge currently copies only the loop outcome, session, handoff, and safety package.

### Task 3: Implement Context Propagation

**Files:**
- Modify: `src/qa_z/autonomy.py`
- Modify: `src/qa_z/executor_bridge.py`

- [x] **Step 1: Add context paths to repair-session action**

Pass `task_context_paths(task)` into the autonomy repair-session action path and include the field only when non-empty.

- [x] **Step 2: Copy action context inputs in bridge packaging**

Copy existing file paths under the repository root into `inputs/context/<ordinal>-<filename>`, record copied entries in `inputs.action_context`, and record missing/skipped entries in `inputs.action_context_missing`.

- [x] **Step 3: Surface action context in bridge guides**

Render copied context input paths in `executor_guide.md` and executor-specific guides when present.

- [x] **Step 4: Run GREEN tests**

```bash
python -m pytest tests/test_autonomy.py::test_autonomy_prepares_repair_session_with_context_paths tests/test_executor_bridge.py::test_executor_bridge_copies_repair_action_context_inputs -q
```

Expected: both tests pass.

### Task 4: Sync Truth Surfaces

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update documentation**

Document that autonomy-created repair-session actions preserve selected evidence `context_paths`, and executor bridges copy those files into bridge-local context inputs.

- [x] **Step 2: Update truth assertions and test count**

If the full pytest count changes, update the alpha closure snapshot and matching current-truth assertion.

### Task 5: Verify

**Files:**
- Test only

- [x] **Step 1: Run focused checks**

```bash
python -m pytest tests/test_autonomy.py tests/test_executor_bridge.py tests/test_current_truth.py -q
python -m qa_z autonomy --loops 1 --json
python -m qa_z executor-bridge --from-loop <latest-repair-loop> --bridge-id <scratch-id> --json
```

Expected: focused tests pass; CLI smoke remains local and live-free. If the current workspace's latest loop is not a repair-session loop, use test coverage as the bridge proof and report that no natural bridge smoke was available.

- [x] **Step 2: Run full gates**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If formatting is needed, format only touched files and rerun the affected checks.
