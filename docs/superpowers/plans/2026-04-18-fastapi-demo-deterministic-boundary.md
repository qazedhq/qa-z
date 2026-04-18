# FastAPI Demo Deterministic Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the FastAPI-shaped Python example aligned with QA-Z's deterministic fast/repair-prompt, live-free alpha boundary.

**Architecture:** Add focused README/config guards in the example tests, add a current-truth report guard, then update the FastAPI demo README and reports. No source, config, or CLI behavior changes.

**Tech Stack:** Python, pytest, PyYAML, Markdown.

---

### Task 1: Add Example Boundary RED Test

**Files:**
- Modify: `tests/test_examples.py`

- [ ] **Step 1: Add the FastAPI demo boundary test**

Add:

```python
def test_fastapi_demo_readme_states_dependency_light_deterministic_boundary() -> None:
    demo = ROOT / "examples" / "fastapi-demo"
    readme = (demo / "README.md").read_text(encoding="utf-8")
    config = yaml.safe_load((demo / "qa-z.yaml").read_text(encoding="utf-8"))
    failing_config = yaml.safe_load(
        (demo / "qa-z.failing.yaml").read_text(encoding="utf-8")
    )

    assert [check["id"] for check in config["fast"]["checks"]] == [
        "py_lint",
        "py_format",
        "py_test",
    ]
    assert [check["id"] for check in failing_config["fast"]["checks"]] == [
        "py_lint",
        "py_format",
        "py_test_bug_demo",
    ]
    assert config["checks"]["deep"] == []
    assert failing_config["checks"]["deep"] == []
    assert "dependency-light" in readme
    assert "works without installing a web server" in readme
    assert "deterministic fast and repair-prompt demo" in readme
    assert "does not configure deep checks" in readme
    assert "does not call live agents" in readme
    assert "does not run `repair-session`, `executor-bridge`, or `executor-result`" in readme
```

- [ ] **Step 2: Run focused test and confirm RED**

Run:

```bash
python -m pytest tests/test_examples.py -q
```

Expected: failure because the FastAPI demo README does not yet include the new
boundary text.

### Task 2: Add Report Current-Truth RED Test

**Files:**
- Modify: `tests/test_current_truth.py`

- [ ] **Step 1: Add report guard**

Add:

```python
def test_reports_record_fastapi_demo_deterministic_boundary_sync() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "FastAPI demo deterministic boundary" in current_state
    assert "FastAPI demo deterministic boundary" in roadmap
```

- [ ] **Step 2: Run current-truth test and confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: failure because the reports do not yet mention this sync pass.

### Task 3: Update Example And Reports

**Files:**
- Modify: `examples/fastapi-demo/README.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Update the FastAPI demo README**

Add a short boundary paragraph after the intro:

```markdown
It is a deterministic fast and repair-prompt demo. It does not configure deep checks, does not call live agents, and does not run `repair-session`, `executor-bridge`, or `executor-result`.
```

- [ ] **Step 2: Update reports**

Record that a FastAPI demo deterministic boundary sync pass now keeps the
runnable Python example aligned with the same alpha boundary.

- [ ] **Step 3: Run focused tests and confirm GREEN**

Run:

```bash
python -m pytest tests/test_examples.py tests/test_current_truth.py -q
```

Expected: both suites pass.

### Task 4: Full Verification

**Files:**
- No additional edits.

- [ ] **Step 1: Run full pytest**

Run:

```bash
python -m pytest
```

Expected: full test suite passes.

- [ ] **Step 2: Run benchmark**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: all benchmark fixtures pass with `overall_rate` equal to `1.0`.
