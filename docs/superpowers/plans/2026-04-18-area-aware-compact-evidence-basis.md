# Area-Aware Compact Evidence Basis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep alpha closure evidence primary while showing the dirty-area evidence that explains area-aware commit-isolation action hints.

**Architecture:** Add tests around `compact_backlog_evidence_summary()`, then add a narrow helper in `src/qa_z/self_improvement.py` that appends an `action basis:` suffix only when secondary evidence contains `areas=` and the primary compact line does not. Documentation explains the additive human-output behavior without changing JSON contracts.

**Tech Stack:** Python standard library, pytest, existing QA-Z self-improvement helpers.

---

### Task 1: Pin Area-Aware Compact Evidence

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Add action-basis compact evidence test**

Add:

```python
def test_compact_evidence_summary_appends_area_action_basis() -> None:
    item = {
        "id": "commit_isolation_gap-foundation-order",
        "evidence": [
            {
                "source": "worktree_commit_plan",
                "path": "docs/reports/worktree-commit-plan.md",
                "summary": (
                    "alpha closure readiness snapshot pins full gate pass and "
                    "commit-split action"
                ),
            },
            {
                "source": "git_status",
                "path": ".",
                "summary": (
                    "dirty worktree still spans modified=3; untracked=1; "
                    "areas=docs:2, source:1"
                ),
            },
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "worktree_commit_plan: alpha closure readiness snapshot pins full gate "
        "pass and commit-split action; action basis: git_status: dirty worktree "
        "still spans modified=3; untracked=1; areas=docs:2, source:1"
    )
```

- [x] **Step 2: Add no-duplicate compact evidence test**

Add:

```python
def test_compact_evidence_summary_does_not_duplicate_primary_area_summary() -> None:
    item = {
        "evidence": [
            {
                "source": "git_status",
                "summary": "modified=1; areas=docs:1",
            }
        ]
    }

    assert compact_backlog_evidence_summary(item) == (
        "git_status: modified=1; areas=docs:1"
    )
```

- [x] **Step 3: Run RED tests**

```bash
python -m pytest tests/test_self_improvement.py::test_compact_evidence_summary_appends_area_action_basis tests/test_self_improvement.py::test_compact_evidence_summary_does_not_duplicate_primary_area_summary -q
```

Expected: first test fails because compact evidence does not append `action basis:` yet; second test passes or remains unchanged.

### Task 2: Implement Compact Action Basis

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Add secondary basis helper**

Add a helper near `compact_backlog_evidence_summary()`:

```python
def compact_area_action_basis(
    item: dict[str, Any],
    primary_summary: str,
) -> str:
    if "areas=" in primary_summary:
        return ""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return ""
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        summary = str(entry.get("summary") or "").strip()
        if "areas=" not in summary:
            continue
        source = str(entry.get("source") or "artifact").strip() or "artifact"
        return f"{source}: {summary}"
    return ""
```

- [x] **Step 2: Append basis in compact summary**

After the primary compact summary is built, append:

```python
basis = compact_area_action_basis(item, compact_summary)
if basis:
    return f"{compact_summary}; action basis: {basis}"
return compact_summary
```

- [x] **Step 3: Run GREEN tests**

```bash
python -m pytest tests/test_self_improvement.py::test_compact_evidence_summary_appends_area_action_basis tests/test_self_improvement.py::test_compact_evidence_summary_does_not_duplicate_primary_area_summary -q
```

Expected: both tests pass.

### Task 3: Sync Operator Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update user-facing docs**

Document that compact human evidence can append `action basis:` when the primary
evidence is closure-oriented but action guidance depends on dirty-area evidence.

- [x] **Step 2: Update truth snapshot if pytest count changes**

If new tests change the full pytest count, update the alpha closure readiness
snapshot and the matching current-truth assertion.

### Task 4: Verify Alpha Closure Gates

**Files:**
- Test only

- [x] **Step 1: Run focused checks**

```bash
python -m pytest tests/test_self_improvement.py tests/test_cli.py tests/test_current_truth.py -q
python -m qa_z self-inspect
python -m qa_z select-next
```

Expected: focused tests pass, and selected-task output can show a compact
evidence line whose primary closure snapshot is followed by `action basis:`.

- [x] **Step 2: Run full gate suite**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If formatting changes are required, format only the
files touched in this plan and rerun the full gate suite.
