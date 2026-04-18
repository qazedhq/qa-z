# Report Template Example Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sync QA-Z's public config example, downstream templates, example README, and report wording with the current alpha implementation.

**Architecture:** Keep this as a documentation and current-truth hardening pass. Runtime behavior should not change except the built-in bootstrap config text matching the public example. Tests should pin the intended wording and config shape.

**Tech Stack:** Python standard library, PyYAML in existing tests, pytest, Markdown, YAML.

---

### Task 1: Pin Config Example Truth

**Files:**
- Modify: `tests/test_current_truth.py`
- Modify: `src/qa_z/config.py`
- Modify: `qa-z.yaml.example`

- [ ] **Step 1: Write failing test**

Add a test that loads `qa-z.yaml.example` and asserts:

```python
example = yaml.safe_load((ROOT / "qa-z.yaml.example").read_text(encoding="utf-8"))
assert "deep" not in example.get("checks", {})
assert [check["id"] for check in example["deep"]["checks"]] == ["sg_scan"]
for unsupported in ("property", "mutation", "e2e_smoke"):
    assert unsupported not in public_text
assert EXAMPLE_CONFIG == public_text
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -k example_config -q
```

Expected: fail because the legacy placeholder `checks.deep` list is still present.

- [ ] **Step 3: Update config text**

Remove only the unsupported `checks.deep` list from `src/qa_z/config.py` and `qa-z.yaml.example`. Keep `checks.selection.max_changed_files` because fast and deep selection still read it as a fallback.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -k example_config -q
```

Expected: pass.

### Task 2: Pin Template And Example Truth

**Files:**
- Modify: `tests/test_current_truth.py`
- Modify: `tests/test_examples.py`
- Modify: `templates/AGENTS.md`
- Modify: `templates/CLAUDE.md`
- Modify: `templates/.claude/skills/qa-guard/SKILL.md`
- Modify: `examples/nextjs-demo/README.md`

- [ ] **Step 1: Write failing tests**

Add tests that assert:

```python
assert "qa-z deep" in template_text
assert "repair-session" in template_text
assert "executor-bridge" in template_text
assert "does not call live agents" in template_text.lower()
assert "not wired" in nextjs_readme.lower()
assert "examples/typescript-demo" in nextjs_readme
assert "Stryker" not in nextjs_readme
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -k templates -q
python -m pytest tests/test_examples.py -k nextjs -q
```

Expected: fail until template/example docs are synced.

- [ ] **Step 3: Update templates and Next.js README**

Make the templates name landed QA-Z commands and preserve the live-free boundary. Update the Next.js placeholder to point to the TypeScript fast demo and avoid unlanded deep-tool claims.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -k templates -q
python -m pytest tests/test_examples.py -k nextjs -q
```

Expected: pass.

### Task 3: Sync Reports

**Files:**
- Modify: `tests/test_current_truth.py`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Add current-truth assertions**

Assert the reports mention template/example sync as a landed first pass while preserving ongoing maintenance.

- [ ] **Step 2: Update reports**

Update Priority 4 language so it no longer reads as untouched work. Keep the remaining scope focused on future drift prevention.

- [ ] **Step 3: Run current-truth tests**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

### Task 4: Validate

**Files:**
- All touched files

- [ ] **Step 1: Run targeted tests**

Run:

```bash
python -m pytest tests/test_cli.py tests/test_current_truth.py tests/test_examples.py tests/test_github_workflow.py -q
```

Expected: pass.

- [ ] **Step 2: Run full tests**

Run:

```bash
python -m pytest
```

Expected: pass.

- [ ] **Step 3: Run full benchmark**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: all committed benchmark fixtures pass.
