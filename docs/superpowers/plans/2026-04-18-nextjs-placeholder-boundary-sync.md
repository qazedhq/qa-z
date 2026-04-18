# Next.js Placeholder Boundary Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pin the Next.js placeholder as README-only, non-runnable, and live-free until a real deterministic Next.js demo lands.

**Architecture:** This is a current-truth hardening pass. Tests enforce the placeholder contract; docs then describe the same boundary across the example README, MVP issue list, current-state report, and roadmap.

**Tech Stack:** Python pytest, Markdown docs.

---

### Task 1: Pin Placeholder Expectations

**Files:**
- Modify: `tests/test_examples.py`
- Modify: `tests/test_current_truth.py`

- [ ] **Step 1: Extend the example test**

In `test_nextjs_demo_readme_is_honest_placeholder`, assert that `examples/nextjs-demo` contains only `README.md` and that the README contains:

```python
assert "placeholder-only" in readme
assert "not a runnable Next.js project" in readme
assert "does not include `package.json`" in readme
assert "does not include `qa-z.yaml`" in readme
assert "does not call live agents" in readme
assert "does not run `executor-bridge` or `executor-result`" in readme
```

- [ ] **Step 2: Add report/MVP current-truth assertions**

Add a current-truth test requiring `docs/mvp-issues.md`, `docs/reports/current-state-analysis.md`, and `docs/reports/next-improvement-roadmap.md` to mention `Next.js placeholder live-free boundary`.

- [ ] **Step 3: Verify RED**

Run:

```bash
python -m pytest tests/test_examples.py::test_nextjs_demo_readme_is_honest_placeholder tests/test_current_truth.py::test_reports_record_nextjs_placeholder_live_free_boundary_sync -q
```

Expected: fail because the placeholder README and report docs do not yet include the new boundary wording.

### Task 2: Sync The Example And Docs

**Files:**
- Modify: `examples/nextjs-demo/README.md`
- Modify: `docs/mvp-issues.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Update the placeholder README**

State that the directory is placeholder-only, not runnable, contains no `package.json` or `qa-z.yaml`, points to `examples/typescript-demo`, and does not call live agents or run executor bridge/result commands.

- [ ] **Step 2: Update MVP Issue 11**

Add a status note that the FastAPI demo is dependency-light and runnable, the TypeScript demo is fast-only and runnable, and the Next.js directory remains a placeholder-only example until real project files and deterministic commands exist.

- [ ] **Step 3: Update current-state and roadmap docs**

Name the `Next.js placeholder live-free boundary` pass alongside the existing TypeScript and FastAPI example sync passes.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python -m pytest tests/test_examples.py::test_nextjs_demo_readme_is_honest_placeholder tests/test_current_truth.py::test_reports_record_nextjs_placeholder_live_free_boundary_sync -q
```

Expected: pass.

### Task 3: Full Verification

**Files:**
- Read verification output only.

- [ ] **Step 1: Run example/current-truth tests**

```bash
python -m pytest tests/test_examples.py tests/test_current_truth.py -q
```

Expected: pass.

- [ ] **Step 2: Run full tests**

```bash
python -m pytest
```

Expected: all tests pass with the repository's expected skipped test count.

- [ ] **Step 3: Run benchmark**

```bash
python -m qa_z benchmark --json
```

Expected: all committed benchmark fixtures pass.
