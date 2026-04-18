# Loop Health Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact loop-health summary contract to autonomy outcomes, history, status, and human loop plans.

**Architecture:** Keep the change additive inside `src/qa_z/autonomy.py`. A helper builds the `loop_health` object from selected count, fallback state, selection gap reason, and backlog counts. Existing artifacts keep their current fields while also carrying `loop_health`.

**Tech Stack:** Python standard library, pytest, Markdown docs.

---

### Task 1: Pin Loop Health Outcome Behavior

**Files:**
- Modify: `tests/test_autonomy.py`
- Modify: `src/qa_z/autonomy.py`

- [ ] **Step 1: Write failing tests**

Add assertions to empty and stale-backlog taskless-loop tests:

```python
assert outcome["loop_health"]["classification"] == "taskless"
assert outcome["loop_health"]["selected_count"] == 0
assert outcome["loop_health"]["selection_gap_reason"] == "no_open_backlog_after_inspection"
assert "Loop health: `taskless`" in plan
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_autonomy.py -k "empty_evidence or stale_backlog" -q`

Expected: fail with missing `loop_health`.

- [ ] **Step 3: Implement `build_loop_health()` and write it to outcome**

Add a helper that returns the compact loop-health object. Write it into `outcome.json`, pass it to `render_autonomy_loop_plan()`, and keep existing fields unchanged.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_autonomy.py -k "empty_evidence or stale_backlog" -q`

Expected: pass.

### Task 2: Mirror Loop Health To History And Status

**Files:**
- Modify: `tests/test_autonomy.py`
- Modify: `src/qa_z/autonomy.py`

- [ ] **Step 1: Write failing tests**

Assert history lines contain `loop_health`, `load_autonomy_status()` exposes `latest_loop_health`, and `render_autonomy_status()` prints the classification and summary.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_autonomy.py -k "loop_health or next_recommendations_without_actions" -q`

Expected: fail until history/status mirroring exists.

- [ ] **Step 3: Implement mirroring**

Copy `loop_health` in `update_history_entry()`, expose it in `load_autonomy_status()`, and render it in `render_autonomy_status()`.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_autonomy.py -k "loop_health or next_recommendations_without_actions" -q`

Expected: pass.

### Task 3: Add Stop Reason For Repeated Blocked Loops

**Files:**
- Modify: `tests/test_autonomy.py`
- Modify: `src/qa_z/autonomy.py`

- [ ] **Step 1: Write failing test**

Extend the repeated blocked-loop test:

```python
assert summary["stop_reason"] == "repeated_blocked_no_candidates"
assert summary["consecutive_blocked_loops"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_autonomy.py -k "stops_after_repeated_blocked" -q`

Expected: fail with missing `stop_reason`.

- [ ] **Step 3: Implement stop reason fields**

Set `stop_reason` before breaking the loop and include `consecutive_blocked_loops` in the summary.

- [ ] **Step 4: Run focused test**

Run: `python -m pytest tests/test_autonomy.py -k "stops_after_repeated_blocked" -q`

Expected: pass.

### Task 4: Sync Docs And Validate

**Files:**
- Modify: `tests/test_current_truth.py`
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Add current-truth assertions**

Assert README and schema docs mention `loop_health`, `classification`, `stale_open_items_closed`, and `stop_reason`.

- [ ] **Step 2: Update docs**

Document the additive fields and adjust reports so loop health is described as landed, with remaining work limited to ongoing maintenance.

- [ ] **Step 3: Run targeted tests**

Run: `python -m pytest tests/test_autonomy.py tests/test_current_truth.py -q`

Expected: pass.

- [ ] **Step 4: Run full validation**

Run: `python -m pytest`

Expected: pass.

Run: `python -m qa_z benchmark --json`

Expected: all benchmark fixtures pass.
