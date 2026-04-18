# Closure-Aware Compact Evidence Priority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make human compact selected-task summaries prefer alpha closure readiness evidence over generic commit-isolation evidence.

**Architecture:** Keep backlog and selected-task artifacts unchanged. Add a small helper in `self_improvement.py` that chooses the most operator-useful evidence entry for compact summaries, with a narrow priority for closure-aware evidence and an existing-behavior fallback.

**Tech Stack:** Python, pytest, Markdown docs.

---

## Files

- Modify: `src/qa_z/self_improvement.py`
- Modify: `tests/test_self_improvement.py`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add RED Compact Summary Test

- [ ] **Step 1: Import the compact summary helper**

In `tests/test_self_improvement.py`, add `compact_backlog_evidence_summary` to the import from `qa_z.self_improvement`.

- [ ] **Step 2: Add the failing test**

Add this test near the loop-plan/select-next evidence tests:

```python
def test_compact_evidence_summary_prioritizes_alpha_closure_snapshot() -> None:
    item = {
        "id": "commit_isolation_gap-foundation-order",
        "evidence": [
            {
                "source": "current_state",
                "path": "docs/reports/current-state-analysis.md",
                "summary": "report calls out commit-order dependency or commit-isolation work",
            },
            {
                "source": "worktree_commit_plan",
                "path": "docs/reports/worktree-commit-plan.md",
                "summary": (
                    "alpha closure readiness snapshot pins full gate pass and "
                    "commit-split action"
                ),
            },
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "worktree_commit_plan: alpha closure readiness snapshot pins full gate "
        "pass and commit-split action"
    )
```

- [ ] **Step 3: Verify RED**

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_compact_evidence_summary_prioritizes_alpha_closure_snapshot -q
```

Expected: FAIL because compact summaries still use the first evidence item.

## Task 2: Implement Compact Evidence Priority

- [ ] **Step 1: Add helper functions**

Add these helpers before `compact_backlog_evidence_summary()`:

```python
def compact_evidence_priority(entry: dict[str, Any]) -> int:
    """Return a lower priority value for more useful compact evidence."""
    summary = str(entry.get("summary") or "").lower()
    if "alpha closure readiness snapshot" in summary:
        return 0
    return 1


def compact_evidence_entry(evidence: list[Any]) -> dict[str, Any] | None:
    """Pick the best evidence entry for one-line human summaries."""
    entries = [entry for entry in evidence if isinstance(entry, dict)]
    if not entries:
        return None
    return sorted(
        enumerate(entries),
        key=lambda pair: (compact_evidence_priority(pair[1]), pair[0]),
    )[0][1]
```

- [ ] **Step 2: Use the helper in compact summaries**

Update `compact_backlog_evidence_summary()`:

```python
    if not isinstance(evidence, list):
        return "none recorded"
    entry = compact_evidence_entry(evidence)
    if entry is None:
        return "none recorded"
    source = str(entry.get("source") or "artifact").strip() or "artifact"
    summary = str(entry.get("summary") or "").strip()
    path = str(entry.get("path") or "").strip()
    if summary:
        return f"{source}: {summary}"
    if path:
        return f"{source}: {path}"
    return "none recorded"
```

- [ ] **Step 3: Verify GREEN**

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_compact_evidence_summary_prioritizes_alpha_closure_snapshot -q
```

Expected: PASS.

## Task 3: Sync Reports

- [ ] **Step 1: Update current-state report**

Extend the worktree caveat text to say compact selected-task evidence now prioritizes closure-aware commit-isolation context.

- [ ] **Step 2: Update roadmap**

Extend the immediate rule or report-sync priority to mention compact selected-task evidence.

- [ ] **Step 3: Run focused tests**

Run:

```bash
python -m pytest tests/test_self_improvement.py tests/test_current_truth.py -q
```

Expected: PASS.

## Task 4: Full Verification

- [ ] **Step 1: Run full pytest**

Run:

```bash
python -m pytest
```

Expected: PASS.

- [ ] **Step 2: Run benchmark and static checks**

Run:

```bash
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```

Expected: all commands exit `0`.

## Commit Decision

Do not stage or commit. The current worktree remains a large alpha integration branch and should be split according to `docs/reports/worktree-commit-plan.md`.
