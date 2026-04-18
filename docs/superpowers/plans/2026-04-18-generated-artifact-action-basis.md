# Generated Artifact Action Basis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make deferred cleanup compact evidence show the generated/runtime artifact evidence that explains its action hint.

**Architecture:** Add tests around `compact_backlog_evidence_summary()` for `triage_and_isolate_changes` items, then generalize the current area action-basis helper into a compact action-basis dispatcher. Keep the existing area behavior and add a generated/runtime evidence helper scoped to the deferred cleanup recommendation.

**Tech Stack:** Python standard library, pytest, existing QA-Z self-improvement helpers.

---

### Task 1: Pin Generated Action Basis

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Add generated action-basis test**

Add:

```python
def test_compact_evidence_summary_appends_generated_action_basis() -> None:
    item = {
        "id": "deferred_cleanup_gap-worktree-deferred-items",
        "recommendation": "triage_and_isolate_changes",
        "evidence": [
            {
                "source": "current_state",
                "path": "docs/reports/current-state-analysis.md",
                "summary": (
                    "report calls out deferred cleanup work or generated outputs "
                    "to isolate"
                ),
            },
            {
                "source": "generated_outputs",
                "path": "benchmarks/results/report.md",
                "summary": (
                    "generated benchmark outputs still present: "
                    "benchmarks/results/report.md, benchmarks/results/summary.json"
                ),
            },
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "current_state: report calls out deferred cleanup work or generated "
        "outputs to isolate; action basis: generated_outputs: generated "
        "benchmark outputs still present: benchmarks/results/report.md, "
        "benchmarks/results/summary.json"
    )
```

- [x] **Step 2: Add no-duplicate generated basis test**

Add:

```python
def test_compact_evidence_summary_does_not_duplicate_generated_primary() -> None:
    item = {
        "recommendation": "triage_and_isolate_changes",
        "evidence": [
            {
                "source": "generated_outputs",
                "summary": (
                    "generated benchmark outputs still present: "
                    "benchmarks/results/report.md"
                ),
            }
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "generated_outputs: generated benchmark outputs still present: "
        "benchmarks/results/report.md"
    )
```

- [x] **Step 3: Run RED tests**

```bash
python -m pytest tests/test_self_improvement.py::test_compact_evidence_summary_appends_generated_action_basis tests/test_self_improvement.py::test_compact_evidence_summary_does_not_duplicate_generated_primary -q
```

Expected: first test fails because generated evidence is not appended yet; second
test passes or stays unchanged.

### Task 2: Implement Generated Action Basis

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Add compact action-basis dispatcher**

Add:

```python
def compact_action_basis(item: dict[str, Any], primary_summary: str) -> str:
    area_basis = compact_area_action_basis(item, primary_summary)
    if area_basis:
        return area_basis
    return compact_generated_action_basis(item, primary_summary)
```

- [x] **Step 2: Add generated basis helper**

Add:

```python
def compact_generated_action_basis(
    item: dict[str, Any],
    primary_summary: str,
) -> str:
    if str(item.get("recommendation") or "") != "triage_and_isolate_changes":
        return ""
    if "generated_outputs:" in primary_summary or "runtime_artifacts:" in primary_summary:
        return ""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return ""
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        source = str(entry.get("source") or "artifact").strip() or "artifact"
        if source not in {"generated_outputs", "runtime_artifacts"}:
            continue
        summary = str(entry.get("summary") or "").strip()
        path = str(entry.get("path") or "").strip()
        if summary:
            return f"{source}: {summary}"
        if path:
            return f"{source}: {path}"
    return ""
```

- [x] **Step 3: Use dispatcher from compact summary**

Replace both calls to `compact_area_action_basis()` in
`compact_backlog_evidence_summary()` with `compact_action_basis()`.

- [x] **Step 4: Run GREEN tests**

```bash
python -m pytest tests/test_self_improvement.py::test_compact_evidence_summary_appends_generated_action_basis tests/test_self_improvement.py::test_compact_evidence_summary_does_not_duplicate_generated_primary tests/test_self_improvement.py::test_compact_evidence_summary_appends_area_action_basis -q
```

Expected: generated tests and existing area action-basis test pass.

### Task 3: Sync Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update docs**

Document that generated cleanup compact evidence may append `action basis:` with
`generated_outputs` or `runtime_artifacts` evidence.

- [x] **Step 2: Update truth assertions and snapshot count**

If pytest count changes, update `docs/reports/worktree-commit-plan.md` and the
matching current-truth assertion.

### Task 4: Verify Alpha Closure Gates

**Files:**
- Test only

- [x] **Step 1: Run focused checks**

```bash
python -m pytest tests/test_self_improvement.py tests/test_cli.py tests/test_current_truth.py -q
python -m qa_z self-inspect
python -m qa_z select-next
```

Expected: focused tests pass and deferred cleanup compact evidence can include
the generated action basis when generated artifacts are present.

- [x] **Step 2: Run full gate suite**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If formatting is needed, format only touched files and
rerun the full gate suite.
