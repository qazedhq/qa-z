# P11 Current-Truth Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sync QA-Z's shipped guidance and generated-artifact policy with the already-landed alpha behavior, then lock that truth in with focused tests.

**Architecture:** This pass is intentionally small. Add one narrow current-truth regression test module, make the smallest config and `.gitignore` edits needed to satisfy it, and keep the behavior surface otherwise unchanged.

**Tech Stack:** Python, pytest, Ruff, mypy, Markdown docs, Git ignore rules

---

### Task 1: Add current-truth regression tests

**Files:**
- Create: `tests/test_current_truth.py`
- Read: `src/qa_z/config.py`
- Read: `.gitignore`
- Read: `benchmark/README.md`

- [ ] **Step 1: Write the failing test module**

```python
from __future__ import annotations

from pathlib import Path

from qa_z.config import COMMAND_GUIDANCE


ROOT = Path(__file__).resolve().parents[1]


def test_command_guidance_matches_landed_review_and_repair_prompt_surface() -> None:
    review = COMMAND_GUIDANCE["review"]
    repair_prompt = COMMAND_GUIDANCE["repair-prompt"]

    assert "scaffolded, not fully implemented yet" not in review
    assert "scaffolded, not fully implemented yet" not in repair_prompt
    assert "review packet" in review
    assert "local artifacts" in review
    assert "repair packet" in repair_prompt
    assert "failed fast checks" in repair_prompt


def test_gitignore_treats_generated_benchmark_summary_and_report_as_local() -> None:
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "benchmarks/results/work/" in lines
    assert "benchmarks/results/summary.json" in lines
    assert "benchmarks/results/report.md" in lines
    assert "!benchmarks/fixtures/**/repo/.qa-z/**" in lines


def test_legacy_benchmark_readme_points_to_plural_benchmarks_directory() -> None:
    text = (ROOT / "benchmark" / "README.md").read_text(encoding="utf-8")

    assert "../benchmarks/" in text
    assert "historical placeholder" in text
```

- [ ] **Step 2: Run the new test file and verify it fails**

Run: `python -m pytest tests/test_current_truth.py -q`
Expected: FAIL because `COMMAND_GUIDANCE` still says `review` and `repair-prompt` are scaffolded, and `.gitignore` does not yet ignore the generated benchmark summary/report files.

### Task 2: Sync command guidance and benchmark ignore policy

**Files:**
- Modify: `src/qa_z/config.py`
- Modify: `.gitignore`

- [ ] **Step 1: Update the review guidance**

```python
"review": dedent(
    """
    qa-z review renders a deterministic review packet from local artifacts.

    Current responsibility:
    - render review packets from a contract or attached run artifacts
    - include fast-check context and sibling deep findings when available
    - emit human-readable Markdown plus machine-readable JSON
    """
).strip(),
```

- [ ] **Step 2: Update the repair-prompt guidance**

```python
"repair-prompt": dedent(
    """
    qa-z repair-prompt builds a deterministic repair packet from local artifacts.

    Current responsibility:
    - convert failed fast checks and blocking deep findings into repair artifacts
    - highlight affected files, validation commands, and next repair targets
    - emit human-readable Markdown plus machine-readable JSON
    """
).strip(),
```

- [ ] **Step 3: Update the benchmark generated-artifact ignore rules**

```gitignore
benchmarks/results/work/
benchmarks/results/summary.json
benchmarks/results/report.md
```

- [ ] **Step 4: Run the focused test file and verify it passes**

Run: `python -m pytest tests/test_current_truth.py -q`
Expected: PASS

### Task 3: Full validation and doc-truth confirmation

**Files:**
- Read: `README.md`
- Read: `docs/benchmarking.md`
- Read: `docs/reports/worktree-triage.md`

- [ ] **Step 1: Re-read the touched truth surfaces**

Confirm that:

- `README.md` still presents `review` and `repair-prompt` as working
- `docs/benchmarking.md` still treats `benchmarks/results/summary.json` and `benchmarks/results/report.md` as generated outputs
- `docs/reports/worktree-triage.md` still matches the `.gitignore` policy after the ignore update

- [ ] **Step 2: Run formatting, lint, types, and tests**

Run: `python -m ruff format --check .`
Expected: `... already formatted`

Run: `python -m ruff check .`
Expected: `All checks passed!`

Run: `python -m mypy src tests`
Expected: `Success: no issues found ...`

Run: `python -m pytest`
Expected: all tests pass

- [ ] **Step 3: Run the benchmark corpus**

Run: `python -m qa_z benchmark --json`
Expected: all fixtures pass and the summary still reports zero failed fixtures
