# Self-Inspect Candidate Summaries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make plain `qa-z self-inspect` show compact top-candidate summaries with deterministic action hints.

**Architecture:** Add `render_self_inspect_stdout()` in `src/qa_z/cli.py` beside the existing backlog and select-next renderers. It reads the already produced self-inspection report and paths, then reuses `selected_task_action_hint()` and `compact_backlog_evidence_summary()` for top candidate detail without changing JSON artifacts.

**Tech Stack:** Python standard library, pytest, existing QA-Z CLI rendering helpers.

---

### Task 1: Pin Plain Self-Inspect Candidate Output

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Import the renderer in tests**

Update:

```python
from qa_z.cli import build_parser, main, render_select_next_stdout
```

to include `render_self_inspect_stdout`.

- [ ] **Step 2: Add the failing renderer test**

Add:

```python
def test_render_self_inspect_stdout_surfaces_top_candidate_details(tmp_path: Path) -> None:
    output = render_self_inspect_stdout(
        {
            "candidates": [
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "recommendation": "reduce_integration_risk",
                    "priority_score": 65,
                    "evidence": [
                        {
                            "source": "git_status",
                            "summary": "modified=25; untracked=346; staged=0",
                        }
                    ],
                }
            ]
        },
        self_inspection_path=tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json",
        backlog_path=tmp_path / ".qa-z" / "improvement" / "backlog.json",
        root=tmp_path,
    )

    assert "Top candidates:" in output
    assert "- worktree_risk-dirty-worktree: Reduce dirty worktree integration risk" in output
    assert "recommendation: reduce_integration_risk" in output
    assert (
        "action: inspect the dirty worktree and separate generated artifacts, "
        "then rerun self-inspection" in output
    )
    assert "priority score: 65" in output
    assert "evidence: git_status: modified=25; untracked=346; staged=0" in output
```

- [ ] **Step 3: Add the empty-candidate expectation**

Add a small assertion or separate test that `render_self_inspect_stdout()` prints:

```text
Top candidates:
- none
```

when `candidates` is empty.

- [ ] **Step 4: Run RED tests**

```bash
python -m pytest tests/test_cli.py::test_render_self_inspect_stdout_surfaces_top_candidate_details tests/test_cli.py::test_render_self_inspect_stdout_handles_no_candidates -q
```

Expected: fail because the renderer does not exist yet.

### Task 2: Implement Self-Inspect Renderer

**Files:**
- Modify: `src/qa_z/cli.py`

- [ ] **Step 1: Add the renderer**

Add:

```python
def render_self_inspect_stdout(
    report: dict[str, Any],
    *,
    self_inspection_path: Path,
    backlog_path: Path,
    root: Path,
) -> str:
    candidates = [
        item for item in report.get("candidates", []) if isinstance(item, dict)
    ]
    lines = [
        "qa-z self-inspect: wrote self-improvement artifacts",
        f"Self inspection: {format_relative_path(self_inspection_path, root)}",
        f"Backlog: {format_relative_path(backlog_path, root)}",
        f"Candidates: {len(candidates)}",
        "Top candidates:",
    ]
    if not candidates:
        lines.append("- none")
    top_candidates = sorted(
        candidates,
        key=lambda item: (-int_value(item.get("priority_score")), str(item.get("id"))),
    )
    for item in top_candidates[:3]:
        lines.extend(
            [
                f"- {item.get('id')}: {item.get('title', item.get('id', 'untitled'))}",
                f"  recommendation: {item.get('recommendation', '')}",
                f"  action: {selected_task_action_hint(item)}",
                f"  priority score: {item.get('priority_score', 0)}",
                f"  evidence: {compact_backlog_evidence_summary(item)}",
            ]
        )
    return "\n".join(lines)
```

- [ ] **Step 2: Use the renderer from `handle_self_inspect()`**

Replace the inline `"\n".join(...)` block with:

```python
print(
    render_self_inspect_stdout(
        report,
        self_inspection_path=paths.self_inspection_path,
        backlog_path=paths.backlog_path,
        root=root,
    )
)
```

- [ ] **Step 3: Run GREEN tests**

Run the same focused pytest command. Expected: pass.

### Task 3: Sync Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Update README planning paragraph**

State that human `qa-z self-inspect` now prints top candidate summaries with
recommendation, action hint, priority score, and compact evidence.

- [ ] **Step 2: Update artifact schema**

Document that `self_inspect.json` remains the full report and the plain command
prints only the top three candidates.

- [ ] **Step 3: Update reports**

Mention that self-inspect, backlog, and select-next now share deterministic
action-hint wording across the planning handoff surfaces.

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
python -m ruff format --check --no-cache .
python -m mypy src tests
```

- [ ] **Step 3: Smoke the command**

```bash
python -m qa_z self-inspect
```

Expected: plain output includes `Top candidates:` with action hints and no live
execution, staging, commit, push, or code repair occurs.
