# TypeScript Demo Live-Free Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the TypeScript example aligned with the landed fast-only, live-free QA-Z alpha boundary.

**Architecture:** Add focused README/config guards in the example tests, add a current-truth report guard, then update the TypeScript demo README and reports. No source, package, or CLI behavior changes.

**Tech Stack:** Python, pytest, PyYAML, Markdown.

---

### Task 1: Add Example Boundary RED Test

**Files:**
- Modify: `tests/test_examples.py`

- [ ] **Step 1: Import PyYAML**

Add:

```python
import yaml
```

- [ ] **Step 2: Add the TypeScript demo boundary test**

Add:

```python
def test_typescript_demo_readme_states_fast_only_live_free_boundary() -> None:
    demo = ROOT / "examples" / "typescript-demo"
    readme = (demo / "README.md").read_text(encoding="utf-8")
    config = yaml.safe_load((demo / "qa-z.yaml").read_text(encoding="utf-8"))

    assert [check["id"] for check in config["fast"]["checks"]] == [
        "ts_lint",
        "ts_type",
        "ts_test",
    ]
    assert config["checks"]["deep"] == []
    assert "TypeScript fast gate" in readme
    assert "fast-only demo" in readme
    assert "not a Next.js demo" in readme
    assert "does not configure TypeScript-specific deep automation" in readme
    assert "does not call live agents" in readme
    assert "does not run `executor-bridge` or `executor-result`" in readme
```

- [ ] **Step 3: Run focused test and confirm RED**

Run:

```bash
python -m pytest tests/test_examples.py -q
```

Expected: failure because the TypeScript demo README does not yet include the
new boundary text.

### Task 2: Add Report Current-Truth RED Test

**Files:**
- Modify: `tests/test_current_truth.py`

- [ ] **Step 1: Add report guard**

Add assertions to the report/template/example sync area:

```python
def test_reports_record_typescript_demo_live_free_boundary_sync() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "TypeScript demo live-free boundary" in current_state
    assert "TypeScript demo live-free boundary" in roadmap
```

- [ ] **Step 2: Run current-truth test and confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: failure because the reports do not yet mention this sync pass.

### Task 3: Update Example And Reports

**Files:**
- Modify: `examples/typescript-demo/README.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Update the TypeScript demo README**

Add a short boundary paragraph after the intro:

```markdown
It is a fast-only demo, not a Next.js demo. It does not configure
TypeScript-specific deep automation, does not call live agents, and does not run
`executor-bridge` or `executor-result`.
```

- [ ] **Step 2: Update reports**

Record that a TypeScript demo live-free boundary sync pass now keeps the
runnable TypeScript example aligned with the same alpha boundary.

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
