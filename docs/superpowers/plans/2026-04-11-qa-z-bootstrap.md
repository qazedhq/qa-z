# QA-Z Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap the `QA-Z` repository with public docs, a runnable Python CLI skeleton, integration templates, and verification tests.

**Architecture:** The bootstrap keeps the product promise in docs while adding a thin Python package that stabilizes command names early. `init` performs meaningful setup work now, and the rest of the command set returns structured guidance until the deeper control-plane engine is implemented.

**Tech Stack:** Python 3.10+, argparse, pathlib, pytest, GitHub Actions, Markdown, YAML examples

---

### Task 1: Create Repository Foundation

**Files:**
- Create: `F:/JustTyping/.gitignore`
- Create: `F:/JustTyping/LICENSE`
- Create: `F:/JustTyping/README.md`
- Create: `F:/JustTyping/AGENTS.md`
- Create: `F:/JustTyping/qa-z.yaml.example`
- Create: `F:/JustTyping/docs/mvp-issues.md`

- [ ] **Step 1: Create the foundational docs and ignore rules**

```text
Create a root README that defines QA-Z as a QA control plane, add Apache-2.0 licensing, and include a `.gitignore` that ignores Python caches, virtual environments, and local worktree folders.
```

- [ ] **Step 2: Add the agent operating contract**

```markdown
Write `AGENTS.md` to encode the repo's contribution rules: contract-first thinking, deterministic gates, TDD for code changes, and required verification commands.
```

- [ ] **Step 3: Add the example policy file and MVP backlog**

```yaml
project:
  name: qa-z
  languages:
    - python
    - typescript
```

Run: `git diff --stat`
Expected: the repo shows the new documentation files as uncommitted additions

### Task 2: Build the Minimal Python Package With TDD

**Files:**
- Create: `F:/JustTyping/pyproject.toml`
- Create: `F:/JustTyping/src/qa_z/__init__.py`
- Create: `F:/JustTyping/src/qa_z/__main__.py`
- Create: `F:/JustTyping/src/qa_z/cli.py`
- Create: `F:/JustTyping/src/qa_z/config.py`
- Create: `F:/JustTyping/tests/test_cli.py`

- [ ] **Step 1: Write failing tests for CLI surface**

```python
def test_parser_registers_core_subcommands():
    parser = build_parser()
    subcommands = parser._subparsers._group_actions[0].choices
    assert {"init", "plan", "fast", "deep", "review", "repair-prompt"} <= set(subcommands)
```

- [ ] **Step 2: Run the tests to confirm RED**

Run: `python -m pytest`
Expected: import or symbol failures because the package does not exist yet

- [ ] **Step 3: Implement the package minimally**

```python
def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
```

- [ ] **Step 4: Re-run tests to confirm GREEN**

Run: `python -m pytest`
Expected: all CLI tests pass

### Task 3: Add Internal Package Boundaries

**Files:**
- Create: `F:/JustTyping/src/qa_z/planner/__init__.py`
- Create: `F:/JustTyping/src/qa_z/contracts/__init__.py`
- Create: `F:/JustTyping/src/qa_z/runners/__init__.py`
- Create: `F:/JustTyping/src/qa_z/reporters/__init__.py`
- Create: `F:/JustTyping/src/qa_z/adapters/__init__.py`
- Create: `F:/JustTyping/src/qa_z/adapters/codex/__init__.py`
- Create: `F:/JustTyping/src/qa_z/adapters/claude/__init__.py`
- Create: `F:/JustTyping/src/qa_z/plugins/__init__.py`
- Create: `F:/JustTyping/src/qa_z/plugins/python/__init__.py`
- Create: `F:/JustTyping/src/qa_z/plugins/typescript/__init__.py`
- Create: `F:/JustTyping/src/qa_z/plugins/security/__init__.py`
- Create: `F:/JustTyping/qa/contracts/README.md`

- [ ] **Step 1: Create package placeholders**

```python
"""Reserved for future QA-Z planner orchestration logic."""
```

- [ ] **Step 2: Create the contracts workspace placeholder**

```markdown
# QA Contracts

Generated and curated QA contracts live here.
```

- [ ] **Step 3: Verify package discovery still works**

Run: `python -m pytest`
Expected: the earlier CLI tests remain green

### Task 4: Add Templates, Workflows, and Examples

**Files:**
- Create: `F:/JustTyping/templates/AGENTS.md`
- Create: `F:/JustTyping/templates/CLAUDE.md`
- Create: `F:/JustTyping/templates/.claude/skills/qa-guard/SKILL.md`
- Create: `F:/JustTyping/templates/.github/workflows/vibeqa.yml`
- Create: `F:/JustTyping/.github/codex/prompts/review.md`
- Create: `F:/JustTyping/.github/workflows/ci.yml`
- Create: `F:/JustTyping/.github/workflows/codex-review.yml`
- Create: `F:/JustTyping/examples/fastapi-demo/README.md`
- Create: `F:/JustTyping/examples/nextjs-demo/README.md`
- Create: `F:/JustTyping/benchmark/README.md`

- [ ] **Step 1: Create downstream integration templates**

```markdown
Ship AGENTS and CLAUDE templates that teach downstream repos how to run QA-Z as a quality gate instead of a code generator.
```

- [ ] **Step 2: Create repo automation**

```yaml
name: CI
on:
  push:
  pull_request:
```

- [ ] **Step 3: Add examples and benchmark placeholders**

```markdown
Describe what each example repo will demonstrate and how the benchmark corpus will be used later.
```

- [ ] **Step 4: Verify everything still passes**

Run: `python -m pytest`
Expected: all tests pass with 0 failures

### Task 5: Local Verification

**Files:**
- Modify: `F:/JustTyping/tests/test_cli.py`

- [ ] **Step 1: Install the package in editable mode**

Run: `python -m pip install -e .`
Expected: editable install succeeds

- [ ] **Step 2: Run the test suite**

Run: `python -m pytest`
Expected: all tests pass

- [ ] **Step 3: Smoke test the CLI**

Run: `python -m qa_z --help`
Expected: help output lists the six core commands

- [ ] **Step 4: Smoke test project initialization**

Run: `python -m qa_z init`
Expected: `qa-z.yaml` and `qa/contracts/README.md` are created or reported as already present

