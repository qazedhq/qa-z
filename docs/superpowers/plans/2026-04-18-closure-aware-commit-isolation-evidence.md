# Closure-Aware Commit-Isolation Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make self-inspection commit-isolation evidence mention the alpha closure readiness snapshot when that snapshot is present.

**Architecture:** Keep the existing self-inspection candidate contract unchanged. Add a small helper that detects closure-readiness text in `docs/reports/worktree-commit-plan.md` and rewrites only that evidence summary, then pin behavior with pytest.

**Tech Stack:** Python, pytest, Markdown reports.

---

## Files

- Modify: `src/qa_z/self_improvement.py`
- Modify: `tests/test_self_improvement.py`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add RED Self-Inspection Test

- [ ] **Step 1: Add a failing test**

Add this test near `test_self_inspection_promotes_deferred_cleanup_and_commit_isolation_gaps()` in `tests/test_self_improvement.py`:

```python
def test_self_inspection_uses_alpha_closure_snapshot_for_commit_isolation_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=3,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md"],
        untracked_paths=["docs/reports/worktree-commit-plan.md"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation.

        ## Alpha Closure Readiness Snapshot

        The latest full local gate pass for this accumulated alpha baseline is:

        - `python -m pytest`: 297 passed, 1 skipped
        - `python -m qa_z benchmark --json`: 47/47 fixtures, overall_rate 1.0

        The next operator action is to split the worktree by this commit plan.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="closure-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    isolation = next(
        item
        for item in report["candidates"]
        if item["id"] == "commit_isolation_gap-foundation-order"
    )

    assert isolation["recommendation"] == "isolate_foundation_commit"
    assert {
        evidence["summary"] for evidence in isolation["evidence"]
    } >= {
        "alpha closure readiness snapshot pins full gate pass and commit-split action",
        "dirty worktree still spans modified=3; untracked=1",
    }
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_self_inspection_uses_alpha_closure_snapshot_for_commit_isolation_evidence -q
```

Expected: FAIL because commit-isolation evidence still uses the generic commit-order summary.

## Task 2: Implement Closure-Aware Evidence Summary

- [ ] **Step 1: Add helper functions**

Add these helpers near `commit_isolation_evidence()` in `src/qa_z/self_improvement.py`:

```python
def alpha_closure_snapshot_is_present(text: str) -> bool:
    """Return whether a report pins the alpha closure gate snapshot."""
    lowered = text.lower()
    return all(
        term in lowered
        for term in (
            "alpha closure readiness snapshot",
            "latest full local gate pass",
            "split the worktree by this commit plan",
        )
    )


def closure_aware_commit_isolation_summary(path: Path, text: str) -> str | None:
    """Return a precise commit-isolation summary for closure-ready reports."""
    if path.name == "worktree-commit-plan.md" and alpha_closure_snapshot_is_present(
        text
    ):
        return (
            "alpha closure readiness snapshot pins full gate pass and "
            "commit-split action"
        )
    return None
```

- [ ] **Step 2: Route commit isolation through the helper**

Replace `commit_isolation_evidence()` with a loop that keeps existing matching behavior but uses the closure-aware summary when available:

```python
def commit_isolation_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect report evidence for commit-order isolation risk."""
    matches: list[dict[str, Any]] = []
    terms = (
        "commit order dependency",
        "corrected commit sequence",
        "foundation-before-benchmark",
        "commit split",
        "git add -p",
        "alpha closure readiness snapshot",
    )
    lowered_terms = tuple(term.lower() for term in terms)
    for source, path, text in report_documents(root):
        if source not in {"worktree_commit_plan", "current_state"}:
            continue
        lowered = text.lower()
        if any(term in lowered for term in lowered_terms):
            matches.append(
                {
                    "source": source,
                    "path": format_path(path, root),
                    "summary": closure_aware_commit_isolation_summary(path, text)
                    or "report calls out commit-order dependency or commit-isolation work",
                }
            )
    return matches
```

- [ ] **Step 3: Verify GREEN**

Run:

```bash
python -m pytest tests/test_self_improvement.py::test_self_inspection_uses_alpha_closure_snapshot_for_commit_isolation_evidence -q
```

Expected: PASS.

## Task 3: Sync Reports

- [ ] **Step 1: Update current-state report**

In `docs/reports/current-state-analysis.md`, extend the alpha closure readiness sentence to say self-inspection now carries closure-aware commit-isolation evidence.

- [ ] **Step 2: Update roadmap**

In `docs/reports/next-improvement-roadmap.md`, extend Priority 4 or the immediate rule to mention closure-aware commit-isolation evidence.

- [ ] **Step 3: Run focused tests**

Run:

```bash
python -m pytest tests/test_self_improvement.py tests/test_current_truth.py -q
```

Expected: PASS.

## Task 4: Full Verification

- [ ] **Step 1: Run full test suite**

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

Do not stage or commit. The current worktree remains a large alpha integration branch, and the next operator action remains splitting commits according to `docs/reports/worktree-commit-plan.md`.
