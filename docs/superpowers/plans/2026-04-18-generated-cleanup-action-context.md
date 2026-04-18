# Generated Cleanup Action Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Make autonomy prepared action packets for deferred generated cleanup
carry the generated versus frozen evidence policy in `context_paths`.

**Architecture:** Extend the existing recommendation-to-context-path mapping in
`src/qa_z/autonomy.py`. Pin the behavior through `action_for_task()` so all
surfaces that render prepared actions inherit the same context path without
duplicating rendering logic.

**Tech Stack:** Python standard library, pytest, existing QA-Z autonomy helpers.

---

### Task 1: Pin Deferred Cleanup Context

**Files:**
- Modify: `tests/test_autonomy.py`

- [x] **Step 1: Add action mapping regression test**

Add a test that builds an `action_for_task()` packet with:

- `category`: `deferred_cleanup_gap`
- `recommendation`: `triage_and_isolate_changes`
- report evidence from `docs/reports/current-state-analysis.md`
- generated output evidence from `benchmarks/results/report.md`

Assert the action stays an `integration_cleanup_plan` and its `context_paths`
include:

- `benchmarks/results/report.md`
- `docs/generated-vs-frozen-evidence-policy.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/worktree-commit-plan.md`
- `docs/reports/worktree-triage.md`

- [x] **Step 2: Run RED test**

```bash
python -m pytest tests/test_autonomy.py::test_deferred_cleanup_action_includes_generated_policy_context_path -q
```

Expected: fail because the generated evidence policy path is not included yet.

### Task 2: Implement Context Mapping

**Files:**
- Modify: `src/qa_z/autonomy.py`

- [x] **Step 1: Extend recommendation context paths**

Add `docs/generated-vs-frozen-evidence-policy.md` to
`recommendation_context_paths("triage_and_isolate_changes")`.

- [x] **Step 2: Run GREEN test**

```bash
python -m pytest tests/test_autonomy.py::test_deferred_cleanup_action_includes_generated_policy_context_path -q
```

Expected: pass.

### Task 3: Sync Truth Surfaces

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update documentation**

Document that deferred cleanup prepared actions include generated/frozen policy
context through `context_paths`.

- [x] **Step 2: Update truth assertions and test count**

If the full pytest count changes, update the alpha closure snapshot and the
matching current-truth assertion.

### Task 4: Verify

**Files:**
- Test only

- [x] **Step 1: Run focused checks**

```bash
python -m pytest tests/test_autonomy.py tests/test_current_truth.py -q
python -m qa_z autonomy --loops 1 --json
python -m qa_z autonomy status
```

Expected: focused tests pass, and the latest prepared action/status surface can
carry context paths when selected work has a prepared action.

- [x] **Step 2: Run full gates**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If formatting is needed, format only touched files and
rerun the full gate suite.
