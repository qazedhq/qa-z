# Alpha Closure Readiness Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pin the current alpha closure readiness state in reports and current-truth tests before further feature work is added.

**Architecture:** Add a documentation snapshot to the existing worktree commit plan, then guard it with `tests/test_current_truth.py`. Do not add runtime code or generated artifacts.

**Tech Stack:** Markdown reports, pytest current-truth tests.

---

## Files

- Modify: `tests/test_current_truth.py`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add RED Current-Truth Guard

- [ ] **Step 1: Add the failing test**

Add this test near the existing worktree/current-truth tests in `tests/test_current_truth.py`:

```python
def test_alpha_closure_readiness_snapshot_is_pinned() -> None:
    commit_plan = (ROOT / "docs" / "reports" / "worktree-commit-plan.md").read_text(
        encoding="utf-8"
    )
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "## Alpha Closure Readiness Snapshot" in commit_plan
    assert "latest full local gate pass" in commit_plan
    assert "python -m pytest" in commit_plan
    assert "299 passed, 1 skipped" in commit_plan
    assert "python -m qa_z benchmark --json" in commit_plan
    assert "47/47 fixtures" in commit_plan
    assert "python -m ruff check ." in commit_plan
    assert "python -m ruff format --check ." in commit_plan
    assert "123 files already formatted" in commit_plan
    assert "python -m mypy src tests" in commit_plan
    assert "82 source files" in commit_plan
    assert "Generated Output Policy" in commit_plan
    assert "split the worktree by this commit plan" in commit_plan
    assert "alpha closure readiness snapshot" in current_state.lower()
    assert "alpha closure readiness snapshot" in roadmap.lower()
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_current_truth.py::test_alpha_closure_readiness_snapshot_is_pinned -q
```

Expected: FAIL because the snapshot is not present yet.

## Task 2: Add Closure Snapshot Docs

- [ ] **Step 1: Update the commit plan**

Add `## Alpha Closure Readiness Snapshot` before `## Full Validation Before Tagging` in `docs/reports/worktree-commit-plan.md`. Include:

```text
The latest full local gate pass for this accumulated alpha baseline is:

- `python -m pytest`: 299 passed, 1 skipped
- `python -m qa_z benchmark --json`: 47/47 fixtures, overall_rate 1.0
- `python -m ruff check .`: pass
- `python -m ruff format --check .`: 123 files already formatted
- `python -m mypy src tests`: success across 82 source files
```

Also restate that `benchmarks/results/report.md` now carries `Generated Output Policy` but still stays local unless intentionally frozen.

- [ ] **Step 2: Update current-state report**

In `docs/reports/current-state-analysis.md`, add one sentence under `Worktree And Integration Caveats` saying the alpha closure readiness snapshot is pinned in the commit plan.

- [ ] **Step 3: Update roadmap**

In `docs/reports/next-improvement-roadmap.md`, extend the `Immediate Execution Rule` to mention the alpha closure readiness snapshot.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py::test_alpha_closure_readiness_snapshot_is_pinned -q
```

Expected: PASS.

## Task 3: Verification

- [ ] **Step 1: Run current-truth tests**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full validation**

Run:

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```

Expected: all commands exit `0`.

## Commit Decision

Do not stage or commit inside this plan. The current branch is a large alpha integration worktree, and the next operator action is to split the worktree by `docs/reports/worktree-commit-plan.md`.
