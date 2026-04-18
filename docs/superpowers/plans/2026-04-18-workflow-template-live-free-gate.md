# Workflow Template Live-Free Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep shipped GitHub workflow templates explicitly aligned with QA-Z's live-free deterministic CI gate boundary.

**Architecture:** Add a raw-text workflow contract assertion beside the existing workflow-shape tests, then add matching comments to both protected workflows and sync README wording. No runtime command order or CLI behavior changes.

**Tech Stack:** Python, pytest, PyYAML, GitHub Actions YAML, Markdown.

---

### Task 1: Add Workflow Boundary RED Test

**Files:**
- Modify: `tests/test_github_workflow.py`

- [ ] **Step 1: Add raw-text boundary assertions**

Add these assertions inside `test_github_workflow_runs_deep_before_consumers_and_fails_last` after `workflow_text` is assigned:

```python
    assert "deterministic CI gate" in workflow_text
    assert "preserves local artifacts before applying the fast/deep verdict" in workflow_text
    assert "does not call live executors" in workflow_text
    assert "does not create branches, commits, pushes, or bot comments" in workflow_text
```

- [ ] **Step 2: Run focused test and confirm RED**

Run:

```bash
python -m pytest tests/test_github_workflow.py -q
```

Expected: failure because the workflow files do not yet include the boundary
phrases.

### Task 2: Add Workflow Boundary Text

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `templates/.github/workflows/vibeqa.yml`

- [ ] **Step 1: Add matching comments near the top of both workflows**

Add this comment block after the `name:` line:

```yaml
# QA-Z workflow templates are deterministic CI gates.
# This deterministic CI gate preserves local artifacts before applying the fast/deep verdict.
# This workflow does not call live executors.
# This workflow does not create branches, commits, pushes, or bot comments.
```

- [ ] **Step 2: Run focused test and confirm GREEN**

Run:

```bash
python -m pytest tests/test_github_workflow.py -q
```

Expected: all workflow tests pass.

### Task 3: Sync README Workflow Boundary

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the workflow paragraph**

In the README section describing the included CI workflow, add that it is a
deterministic CI gate and does not run executor bridges, ingest executor
results, perform autonomous repair, commit, push, or post GitHub bot comments.

- [ ] **Step 2: Run current-truth and workflow tests**

Run:

```bash
python -m pytest tests/test_current_truth.py tests/test_github_workflow.py -q
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
