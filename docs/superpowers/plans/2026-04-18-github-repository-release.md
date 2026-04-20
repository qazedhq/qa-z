# GitHub Repository Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare QA-Z for a clean public GitHub alpha release from the current `codex/qa-z-bootstrap` integration branch.

**Architecture:** Treat the current branch as an accumulated alpha integration state, not one feature diff. Preserve deterministic quality gates, split source changes into reviewable batches, keep generated runtime evidence local by default, then tag only after README, CI, config, tests, and benchmark evidence agree.

**Tech Stack:** Python 3.10+, setuptools, pytest, ruff, mypy, PyYAML, Semgrep for deep QA, optional Node/ESLint/TypeScript/Vitest only for TypeScript demo and mixed-project fixtures.

---

## Current Readiness Snapshot

Verified on 2026-04-20 from `F:\JustTyping`:

- `python -m pytest`: passed through `python -m qa_z fast --selection smart --json`, `359 passed`
- `python -m ruff format --check .`: passed, `130 files already formatted`
- `python -m ruff check .`: passed
- `python -m mypy src tests`: passed, `84 source files`
- `python -m qa_z fast --selection smart --json`: passed with Python-only root checks
- `python -m qa_z deep --selection smart --json`: passed after installing Semgrep locally; root scan is scoped to `src` and `tests`
- `python -m qa_z benchmark --json`: passed, `50/50 fixtures, overall_rate 1.0`
- `python -m build --sdist --wheel`: passed, built `qa_z-0.9.8a0.tar.gz` and `qa_z-0.9.8a0-py3-none-any.whl`
- `python scripts/alpha_release_artifact_smoke.py --json`: passed, wheel and sdist metadata install smoke
- `python -m qa_z --help`: command surface renders all current alpha commands

Known release blockers:

- The root `qa-z.yaml` gate mismatch is repaired: root fast no longer requires `eslint`, `tsc`, or `vitest`, and root deep no longer scans intentionally vulnerable benchmark fixtures.
- The tracked worktree is clean after the release-readiness commits. Ignored local caches, root `.qa-z/**`, and `benchmarks/results/**` remain local generated artifacts.
- Release target frozen: Git tag `v0.9.8-alpha` and Python package `0.9.8a0`.
- Publish blocker: local Git has no configured `origin` remote, so Task 6 cannot push or open the release PR until the intended GitHub repository target is configured.

## Files And Surfaces To Touch

- Release config: `qa-z.yaml` if the repository should run Python-only root gates, or CI commands if root gates should use a specific config.
- CI: `.github/workflows/ci.yml`
- Package metadata: `pyproject.toml`
- Public docs: `README.md`, `docs/artifact-schema-v1.md`, `docs/mvp-issues.md`
- Release reports: `docs/reports/current-state-analysis.md`, `docs/reports/next-improvement-roadmap.md`, `docs/reports/worktree-commit-plan.md`
- Generated artifact policy: `.gitignore`, `docs/generated-vs-frozen-evidence-policy.md`
- Source/test batches already listed in `docs/reports/worktree-commit-plan.md`
- Optional GitHub polish: `CONTRIBUTING.md`, issue templates, release notes, repository description/topics

## Task 1: Freeze The Release Target

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `docs/mvp-issues.md`
- Create or modify: `docs/releases/v0.9.8-alpha.md` if release notes are kept in-repo

- [x] **Step 1: Choose the public release identifier**

Recommended Git tag: `v0.9.8-alpha`.

Recommended Python package version if publishing a package later: `0.9.8a0`.

Use `v0.1.0-alpha` only if the README is intentionally rewritten back to the smaller bootstrap scope.

- [x] **Step 2: Align package metadata and docs**

If choosing `v0.9.8-alpha`, update:

```toml
[project]
version = "0.9.8a0"
```

Then make README, MVP roadmap, and release notes refer to the same alpha tag.

- [x] **Step 3: Validate version consistency**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass. If it fails, update current-truth docs or tests together.

## Task 2: Fix The Root QA-Z Gate Mismatch

**Files:**
- Create: `qa-z.yaml`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Test: `tests/test_github_workflow.py`
- Test: `tests/test_current_truth.py`

- [x] **Step 1: Decide root gate scope**

Recommended for this Python package repository: root `qa-z.yaml` should run Python fast checks plus Semgrep deep checks. Keep TypeScript checks in `qa-z.yaml.example`, `examples/typescript-demo/qa-z.yaml`, and benchmark fixtures.

- [x] **Step 2: Add a root release config**

Create `qa-z.yaml` with Python-only root checks:

```yaml
project:
  name: qa-z
  languages:
    - python
  roots:
    - src
    - tests

contracts:
  sources:
    - issue
    - pull_request
    - spec
    - diff
  output_dir: qa/contracts

fast:
  default_contract: latest
  output_dir: ".qa-z/runs"
  strict_no_tests: false
  fail_on_missing_tool: true
  selection:
    default_mode: "full"
    full_run_threshold: 40
  checks:
    - id: py_lint
      enabled: true
      run: ["ruff", "check", "."]
      kind: "lint"
    - id: py_format
      enabled: true
      run: ["ruff", "format", "--check", "."]
      kind: "format"
    - id: py_type
      enabled: true
      run: ["mypy", "src", "tests"]
      kind: "typecheck"
    - id: py_test
      enabled: true
      run: ["pytest", "-q"]
      kind: "test"
      no_tests: "warn"

deep:
  fail_on_missing_tool: true
  selection:
    default_mode: "full"
    full_run_threshold: 15
    exclude_paths:
      - dist/**
      - build/**
      - coverage/**
      - "**/*.generated.*"
  checks:
    - id: sg_scan
      enabled: true
      run: ["semgrep", "--json"]
      kind: "static-analysis"
      semgrep:
        config: "auto"
        fail_on_severity:
          - ERROR
        ignore_rules: []

reporters:
  markdown: true
  json: true
  sarif: true
  github_annotations: false
  repair_packet: true

adapters:
  codex:
    enabled: true
    instructions_file: AGENTS.md
  claude:
    enabled: true
    instructions_file: CLAUDE.md
```

- [x] **Step 3: Re-run the root gates**

Install Semgrep for local validation:

```bash
python -m pip install semgrep
```

Run:

```bash
python -m qa_z fast --selection smart --json
python -m qa_z deep --selection smart --json
```

Expected: root QA-Z gates pass or fail only on real project findings, not missing TypeScript tools.

- [x] **Step 4: Keep CI aligned**

In `.github/workflows/ci.yml`, keep installing Semgrep for deep QA. Do not require root Node dependencies unless a root `package.json` is intentionally added.

Run:

```bash
python -m pytest tests/test_github_workflow.py tests/test_current_truth.py -q
```

Expected: workflow tests and current-truth checks pass.

## Task 3: Split The Accumulated Worktree Into Reviewable Commits

**Files:**
- Follow: `docs/reports/worktree-commit-plan.md`
- Do not stage: root `.qa-z/**`
- Do not stage by default: `benchmarks/results/summary.json`, `benchmarks/results/report.md`, `benchmarks/results/work/**`

- [x] **Step 1: Confirm no generated runtime artifacts are staged**

Run:

```bash
git status --short
```

Expected: root `.qa-z/**` and `benchmarks/results/work/**` do not appear as staged source changes.

- [x] **Step 2: Commit foundation first**

Commit message:

```bash
git commit -m "feat: add runner repair and verification foundations"
```

Use the file grouping from `docs/reports/worktree-commit-plan.md`.

Validation before commit:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_diffing.py tests/test_fast_config.py tests/test_fast_selection.py tests/test_deep_run_resolution.py tests/test_deep_selection.py tests/test_semgrep_normalization.py tests/test_sarif_cli.py tests/test_sarif_reporter.py tests/test_subprocess_runner.py tests/test_repair_handoff.py tests/test_verification.py -q
```

- [x] **Step 3: Commit benchmark coverage**

Commit message:

```bash
git commit -m "feat: expand benchmark coverage for typescript and deep policy cases"
```

Validation before commit:

```bash
python -m pytest tests/test_benchmark.py -q
python -m qa_z benchmark --json
```

- [x] **Step 4: Commit planning and autonomy layers**

Commit messages:

```bash
git commit -m "feat: add self-inspection backlog and task selection workflow"
git commit -m "feat: add autonomy planning loops and loop artifacts"
```

Validation before each commit:

```bash
python -m pytest tests/test_self_improvement.py tests/test_autonomy.py tests/test_cli.py -q
```

- [x] **Step 5: Commit repair-session, publishing, and executor bridge**

Commit messages:

```bash
git commit -m "feat: add repair session workflow and verification publishing"
git commit -m "feat: add executor bridge packaging for external repair workflows"
```

Validation before each commit:

```bash
python -m pytest tests/test_repair_session.py tests/test_verification_publish.py tests/test_github_summary.py tests/test_executor_bridge.py tests/test_cli.py -q
```

- [x] **Step 6: Commit docs, examples, templates, and release reports last**

Commit message:

```bash
git commit -m "docs: align alpha release docs and examples"
```

Validation before commit:

```bash
python -m pytest tests/test_current_truth.py tests/test_examples.py tests/test_github_workflow.py -q
```

Completion evidence from the local commit history:

- `7d39e3e feat: add runner repair and verification foundations`
- `001e719 feat: expand benchmark coverage for typescript and deep policy cases`
- `a32e7fc feat: add self-inspection backlog and task selection workflow`
- `112b98e feat: add autonomy planning loops and loop artifacts`
- `ee4a4e1 feat: add repair session workflow and verification publishing`
- `a52d01e feat: add executor bridge packaging for external repair workflows`
- `0427add docs: add worktree triage and commit plan reports`

Follow-up release-readiness commits after the split added executor-result safety,
public GitHub readiness templates, refreshed validation evidence, and local PR and
release-note drafts. The tracked worktree is clean; ignored `.qa-z/**`,
`benchmarks/results/**`, and local caches remain generated artifacts.

## Task 4: Add Public GitHub Repository Readiness Files

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/pull_request_template.md`
- Optional create: `SECURITY.md`

- [x] **Step 1: Add contribution workflow**

Document:

- install: `python -m pip install -e .[dev]`
- full Python validation: `python -m ruff format --check .`, `python -m ruff check .`, `python -m mypy src tests`, `python -m pytest`
- QA-Z validation: `python -m qa_z fast --selection smart --json`, `python -m qa_z deep --selection smart --json`, `python -m qa_z benchmark --json`
- generated artifact policy: root `.qa-z/**` and benchmark result workspaces stay local

- [x] **Step 2: Add issue and PR templates**

Keep templates short and contract-oriented:

- expected behavior
- observed deterministic evidence
- command run
- artifact paths
- environment

- [x] **Step 3: Validate docs are linked**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: current-truth tests pass after any README or policy links are added.

## Task 5: Final Release Candidate Validation

**Files:**
- No code changes expected

- [x] **Step 1: Run full deterministic validation**

Run:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest
python -m qa_z fast --selection smart --json
python -m qa_z deep --selection smart --json
python -m qa_z benchmark --json
python -m build --sdist --wheel
```

Expected:

- ruff format/check pass
- mypy passes
- pytest reports all tests passing with the known skip
- fast/deep pass under the release root config
- benchmark reports `50/50 fixtures, overall_rate 1.0` or a deliberately updated snapshot with matching docs/tests

- [x] **Step 2: Run CLI smoke checks**

Run:

```bash
python -m qa_z --help
python -m qa_z init --help
python -m qa_z plan --help
python -m qa_z fast --help
python -m qa_z deep --help
python -m qa_z review --help
python -m qa_z repair-prompt --help
python -m qa_z repair-session --help
python -m qa_z verify --help
python -m qa_z github-summary --help
python -m qa_z benchmark --help
python -m qa_z self-inspect --help
python -m qa_z select-next --help
python -m qa_z backlog --help
python -m qa_z autonomy --help
python -m qa_z executor-bridge --help
python -m qa_z executor-result --help
```

Expected: every help command exits `0`.

- [x] **Step 3: Confirm worktree cleanliness**

Run:

```bash
git status --short
```

Expected: no unstaged release changes except intentionally local ignored artifacts.

## Task 6: Publish The GitHub Release

**Files:**
- Git metadata and GitHub release page

- [ ] **Step 1: Push the release branch**

Run:

```bash
git push origin codex/qa-z-bootstrap
```

- [ ] **Step 2: Open a release PR**

PR title:

```text
Release QA-Z v0.9.8-alpha
```

PR body must include:

- scope summary
- exact validation commands and results
- known non-goals: no live Codex/Claude execution, no autonomous code editing, no remote orchestration, no GitHub bot comments
- generated artifact policy
- benchmark snapshot

Local draft prepared while publish is blocked:

- `docs/releases/v0.9.8-alpha-pr.md`
- `docs/releases/v0.9.8-alpha-github-release.md`
- `docs/releases/v0.9.8-alpha-publish-handoff.md`

- [ ] **Step 3: Merge after CI passes**

Required CI evidence:

- `test` job passes
- `qa-z` job passes
- SARIF upload is attempted and may continue-on-error only for permission-related code scanning issues

- [ ] **Step 4: Tag the release**

Run:

```bash
git tag -a v0.9.8-alpha -m "QA-Z v0.9.8-alpha"
git push origin v0.9.8-alpha
```

- [ ] **Step 5: Create GitHub release notes**

Use the PR validation evidence and keep the wording alpha-honest:

- deterministic fast/deep QA
- review and repair artifacts
- repair sessions and verification
- benchmark corpus
- self-inspection and autonomy planning
- executor bridge and result ingest
- live-free safety dry-run
- explicit non-goals

Local draft prepared while publish is blocked:

- `docs/releases/v0.9.8-alpha-github-release.md`
- `docs/releases/v0.9.8-alpha-publish-handoff.md`

## Task 7: Post-Release Follow-Up

**Files:**
- Modify: `docs/reports/next-improvement-roadmap.md`
- Optional modify: `docs/mvp-issues.md`

- [ ] **Step 1: Record release baseline**

Add the final tag, CI run link, and validation snapshot to the roadmap or release notes.

- [ ] **Step 2: Start the next work only after baseline is clean**

Recommended next priorities:

1. mixed-surface benchmark breadth
2. report/template/example current-truth sync
3. executor operator diagnostics depth
4. generated versus frozen evidence policy maintenance
5. loop-health clarity maintenance

- [ ] **Step 3: Keep live execution deferred**

Do not begin live Codex/Claude execution until deterministic handoff, verification, publishing, bridge, ingest, and safety contracts remain stable on the release branch.
