# Worktree Area Evidence Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic repository-area counts to dirty-worktree self-inspection evidence.

**Architecture:** Add focused helper functions in `src/qa_z/self_improvement.py` beside the existing live worktree helpers. `discover_worktree_risk_candidates()` will append one `areas=` segment to the existing `git_status` evidence summary when dirty paths are present. Tests will exercise both the helper and the end-to-end self-inspection candidate.

**Tech Stack:** Python standard library, pytest, existing QA-Z self-inspection code.

---

### Task 1: Pin Worktree Area Classification

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Import the classifier**

Add `classify_worktree_path_area` to the existing import from
`qa_z.self_improvement`.

- [x] **Step 2: Add classifier tests**

Add this test:

```python
def test_classify_worktree_path_area_uses_stable_repository_buckets() -> None:
    assert classify_worktree_path_area(".github/workflows/ci.yml") == "workflow"
    assert classify_worktree_path_area("src/qa_z/cli.py") == "source"
    assert classify_worktree_path_area("tests/test_cli.py") == "tests"
    assert classify_worktree_path_area("docs/reports/current-state-analysis.md") == "docs"
    assert classify_worktree_path_area("README.md") == "docs"
    assert classify_worktree_path_area("benchmarks/fixtures/example/expected.json") == "benchmark"
    assert classify_worktree_path_area("benchmark/README.md") == "benchmark"
    assert classify_worktree_path_area("examples/fastapi-demo/README.md") == "examples"
    assert classify_worktree_path_area("templates/AGENTS.md") == "templates"
    assert classify_worktree_path_area("pyproject.toml") == "config"
    assert classify_worktree_path_area(".qa-z/loops/latest/outcome.json") == "runtime_artifact"
    assert classify_worktree_path_area("scripts/local-tool.py") == "other"
```

- [x] **Step 3: Run RED classifier test**

```bash
python -m pytest tests/test_self_improvement.py::test_classify_worktree_path_area_uses_stable_repository_buckets -q
```

Expected: fail because the helper is not defined yet.

### Task 2: Pin Dirty Worktree Evidence Summary

**Files:**
- Modify: `tests/test_self_improvement.py`

- [x] **Step 1: Extend the dirty-worktree test**

In `test_self_inspection_promotes_dirty_worktree_risk_from_live_signals`, add
dirty paths across docs and source areas and assert:

```python
assert "areas=docs:2, source:2" in candidate["evidence"][0]["summary"]
```

- [x] **Step 2: Run RED evidence test**

```bash
python -m pytest tests/test_self_improvement.py::test_self_inspection_promotes_dirty_worktree_risk_from_live_signals -q
```

Expected: fail because `areas=` is not rendered yet.

### Task 3: Implement Area Summary

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [x] **Step 1: Add helper functions**

Add:

```python
def classify_worktree_path_area(path_text: str) -> str:
    normalized = path_text.replace("\\", "/").lstrip("./")
    if is_runtime_artifact_path(normalized):
        return "runtime_artifact"
    if normalized.startswith(".github/workflows/"):
        return "workflow"
    if normalized.startswith("src/"):
        return "source"
    if normalized.startswith("tests/"):
        return "tests"
    if normalized == "README.md" or normalized.startswith("docs/"):
        return "docs"
    if normalized.startswith("benchmarks/") or normalized.startswith("benchmark/"):
        return "benchmark"
    if normalized.startswith("examples/"):
        return "examples"
    if normalized.startswith("templates/"):
        return "templates"
    if normalized in {".gitignore", "pyproject.toml", "qa-z.yaml.example"}:
        return "config"
    return "other"


def worktree_area_summary(paths: list[str], *, limit: int = 5) -> str:
    counts: dict[str, int] = {}
    for path in paths:
        if not str(path).strip():
            continue
        area = classify_worktree_path_area(str(path))
        counts[area] = counts.get(area, 0) + 1
    if not counts:
        return ""
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{area}:{count}" for area, count in ordered[:limit])
```

- [x] **Step 2: Render area summary**

In `discover_worktree_risk_candidates()`, build `dirty_paths` once from modified
plus untracked paths. Append:

```python
area_summary = worktree_area_summary(dirty_paths)
if area_summary:
    summary += "; areas=" + area_summary
```

before the `sample=` segment.

- [x] **Step 3: Run GREEN tests**

```bash
python -m pytest tests/test_self_improvement.py::test_classify_worktree_path_area_uses_stable_repository_buckets tests/test_self_improvement.py::test_self_inspection_promotes_dirty_worktree_risk_from_live_signals -q
```

Expected: both pass.

### Task 4: Sync Documentation And Verify

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [x] **Step 1: Update docs**

Document that dirty-worktree evidence summaries include deterministic area
counts while artifact shapes and live-free boundaries remain unchanged.

- [x] **Step 2: Run focused verification**

```bash
python -m pytest tests/test_self_improvement.py tests/test_cli.py tests/test_current_truth.py -q
python -m qa_z self-inspect
```

Expected: tests pass and the top dirty-worktree evidence includes `areas=`.

- [x] **Step 3: Run full verification**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If the pytest count changes, update the alpha closure
snapshot and matching truth test before the final full pytest run.
