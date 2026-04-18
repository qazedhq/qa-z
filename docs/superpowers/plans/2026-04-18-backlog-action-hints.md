# Backlog Action Hints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make plain `qa-z backlog` output show deterministic action hints for active backlog items.

**Architecture:** Reuse the existing `selected_task_action_hint()` helper from `src/qa_z/self_improvement.py` inside `render_backlog()` in `src/qa_z/cli.py`. This keeps all recommendation-to-action wording in one place and avoids changing the JSON backlog artifact.

**Tech Stack:** Python standard library, pytest, existing QA-Z CLI rendering helpers.

---

### Task 1: Pin Backlog Action Rendering

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Extend the existing backlog plain-output test**

In `test_backlog_plain_output_focuses_on_open_items`, add:

```python
assert (
    "action: inspect the dirty worktree and separate generated artifacts, "
    "then rerun self-inspection" in output
)
```

- [ ] **Step 2: Run the RED test**

```bash
python -m pytest tests/test_cli.py::test_backlog_plain_output_focuses_on_open_items -q
```

Expected: fail because `render_backlog()` does not print an action line yet.

### Task 2: Implement Backlog Action Hints

**Files:**
- Modify: `src/qa_z/cli.py`

- [ ] **Step 1: Add the action line to `render_backlog()`**

After the status/recommendation line, render:

```python
f"  action: {selected_task_action_hint(item)}",
```

The helper is already imported for `select-next` rendering.

- [ ] **Step 2: Run the focused GREEN test**

```bash
python -m pytest tests/test_cli.py::test_backlog_plain_output_focuses_on_open_items -q
```

Expected: pass.

### Task 3: Sync Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Update operator-surface wording**

State that plain `qa-z backlog` now shows active item title, recommendation,
deterministic action hint, and compact evidence summary. Keep `--json` wording
unchanged.

- [ ] **Step 2: Keep the live-free boundary explicit**

Ensure docs still say these commands decide or explain work only; humans or
external executors perform code changes.

### Task 4: Verify

**Files:**
- No additional edits expected.

- [ ] **Step 1: Run focused tests**

```bash
python -m pytest tests/test_cli.py tests/test_current_truth.py -q
```

- [ ] **Step 2: Run full gates**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```

- [ ] **Step 3: Manual smoke output**

```bash
python -m qa_z backlog
```

Expected: active items include `action:` lines and no source files are modified
by the command.
