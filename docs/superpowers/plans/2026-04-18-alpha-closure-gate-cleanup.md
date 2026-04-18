# Alpha Closure Gate Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current feature-complete alpha worktree into a committable alpha-closure state by clearing format/type gates, resolving generated evidence snapshots, validating the live-free baseline, and staging the work through existing commit boundaries.

**Architecture:** Treat this as a closure pass, not a feature pass. Keep production behavior unchanged unless verification exposes a real regression; the only expected code edit is test typing cleanup, plus mechanical formatter output and source-control hygiene. Use deterministic gates as the acceptance contract.

**Tech Stack:** Python, pytest, Ruff, mypy, QA-Z CLI benchmark runner, Git, PowerShell on Windows.

---

## Files

- Modify: `tests/test_executor_dry_run_logic.py`
- Modify by formatter only: `src/qa_z/autonomy.py`
- Modify by formatter only: `src/qa_z/benchmark.py`
- Modify by formatter only: `src/qa_z/executor_bridge.py`
- Modify by formatter only: `src/qa_z/executor_dry_run_logic.py`
- Modify by formatter only: `src/qa_z/repair_session.py`
- Modify by formatter only: `src/qa_z/self_improvement.py`
- Modify by formatter only: `tests/test_autonomy.py`
- Modify by formatter only: `tests/test_benchmark.py`
- Modify by formatter only: `tests/test_current_truth.py`
- Modify by formatter only: `tests/test_executor_bridge.py`
- Modify by formatter only: `tests/test_self_improvement.py`
- Modify by formatter only: `tests/test_verification_publish.py`
- Remove local generated snapshot directories: `benchmarks/results-p12-blocked/`
- Remove local generated snapshot directories: `benchmarks/results-p12-partial/`
- Review for final truth sync: `README.md`
- Review for final truth sync: `docs/reports/current-state-analysis.md`
- Review for final truth sync: `docs/reports/next-improvement-roadmap.md`
- Review for final truth sync: `docs/mvp-issues.md`
- Review for final truth sync: `docs/generated-vs-frozen-evidence-policy.md`
- Review for final truth sync: `docs/reports/worktree-commit-plan.md`
- Review for final truth sync: `qa-z.yaml.example`

## Task 1: Fix Test Typing Closure

- [ ] **Step 1: Confirm the current mypy failure**

Run:

```bash
python -m mypy src tests
```

Expected: FAIL with these four errors in `tests/test_executor_dry_run_logic.py`:

```text
tests\test_executor_dry_run_logic.py:109: error: Value of type "object" is not indexable  [index]
tests\test_executor_dry_run_logic.py:146: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]
tests\test_executor_dry_run_logic.py:232: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]
tests\test_executor_dry_run_logic.py:299: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]
```

- [ ] **Step 2: Update the test helper type**

Change the top of `tests/test_executor_dry_run_logic.py` from:

```python
from qa_z.executor_dry_run_logic import (
    DRY_RUN_ONLY_RULE_IDS,
    DRY_RUN_RULE_IDS,
    build_dry_run_summary,
    evaluate_rules,
)
from qa_z.executor_safety import EXECUTOR_SAFETY_RULE_IDS, executor_safety_package


def build_summary(attempts: list[dict[str, object]]) -> dict[str, object]:
    """Build a dry-run summary with compact stable defaults."""
    return build_dry_run_summary(
        session_id="session-one",
        history_path=".qa-z/sessions/session-one/executor_results/history.json",
        report_path=".qa-z/sessions/session-one/executor_results/dry_run_report.md",
        safety_package_id="pre_live_executor_safety_v1",
        attempts=attempts,
    )
```

to:

```python
from typing import Any

from qa_z.executor_dry_run_logic import (
    DRY_RUN_ONLY_RULE_IDS,
    DRY_RUN_RULE_IDS,
    build_dry_run_summary,
    evaluate_rules,
)
from qa_z.executor_safety import EXECUTOR_SAFETY_RULE_IDS, executor_safety_package


def build_summary(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a dry-run summary with compact stable defaults."""
    return build_dry_run_summary(
        session_id="session-one",
        history_path=".qa-z/sessions/session-one/executor_results/history.json",
        report_path=".qa-z/sessions/session-one/executor_results/dry_run_report.md",
        safety_package_id="pre_live_executor_safety_v1",
        attempts=attempts,
    )
```

- [ ] **Step 3: Verify the focused test still passes**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -q
```

Expected: PASS.

- [ ] **Step 4: Verify mypy clears**

Run:

```bash
python -m mypy src tests
```

Expected: PASS with:

```text
Success: no issues found in 82 source files
```

## Task 2: Apply Ruff Formatting

- [ ] **Step 1: Confirm the formatter surface**

Run:

```bash
python -m ruff format --check .
```

Expected: FAIL listing these 12 files:

```text
src\qa_z\autonomy.py
src\qa_z\benchmark.py
src\qa_z\executor_bridge.py
src\qa_z\executor_dry_run_logic.py
src\qa_z\repair_session.py
src\qa_z\self_improvement.py
tests\test_autonomy.py
tests\test_benchmark.py
tests\test_current_truth.py
tests\test_executor_bridge.py
tests\test_self_improvement.py
tests\test_verification_publish.py
```

- [ ] **Step 2: Run the formatter**

Run:

```bash
python -m ruff format .
```

Expected: Ruff reformats only Python files and exits successfully.

- [ ] **Step 3: Verify formatting**

Run:

```bash
python -m ruff format --check .
```

Expected: PASS with all files already formatted.

- [ ] **Step 4: Verify lint remains clean**

Run:

```bash
python -m ruff check .
```

Expected: PASS.

## Task 3: Resolve Generated P12 Snapshot Directories

- [ ] **Step 1: Confirm snapshot directory classification**

Run:

```powershell
Get-ChildItem -LiteralPath 'benchmarks' -Force | Select-Object Name, PSIsContainer | Format-Table -AutoSize
```

Expected: output includes:

```text
fixtures
results
results-p12-blocked
results-p12-partial
support
```

Run:

```bash
git status --ignored --short benchmarks/results benchmarks/results-p12-blocked benchmarks/results-p12-partial
```

Expected:

```text
?? benchmarks/results-p12-blocked/
?? benchmarks/results-p12-partial/
!! benchmarks/results-p12-blocked/work/executor_dry_run_completed_verify_blocked/repo/.qa-z/
!! benchmarks/results-p12-partial/work/executor_dry_run_repeated_partial_attention/repo/.qa-z/
!! benchmarks/results/
```

- [ ] **Step 2: Keep fixture evidence and discard generated snapshots**

Classify `benchmarks/results-p12-blocked/` and `benchmarks/results-p12-partial/` as local generated benchmark snapshots, not frozen evidence. The committed evidence remains the fixture corpus under `benchmarks/fixtures/**`, the benchmark expectations, and the policy text in `docs/generated-vs-frozen-evidence-policy.md`.

- [ ] **Step 3: Verify the delete targets are inside the workspace**

Run:

```powershell
Resolve-Path -LiteralPath 'benchmarks/results-p12-blocked', 'benchmarks/results-p12-partial'
```

Expected:

```text
F:\JustTyping\benchmarks\results-p12-blocked
F:\JustTyping\benchmarks\results-p12-partial
```

- [ ] **Step 4: Remove only those generated snapshot directories**

Run:

```powershell
Remove-Item -LiteralPath 'benchmarks/results-p12-blocked', 'benchmarks/results-p12-partial' -Recurse
```

Expected: command exits successfully and does not touch `benchmarks/fixtures/`, `benchmarks/support/`, or `benchmarks/results/`.

- [ ] **Step 5: Verify generated snapshots are gone**

Run:

```powershell
Test-Path -LiteralPath 'benchmarks/results-p12-blocked'
Test-Path -LiteralPath 'benchmarks/results-p12-partial'
```

Expected:

```text
False
False
```

- [ ] **Step 6: Verify Git no longer sees the untracked snapshots**

Run:

```bash
git status --ignored --short benchmarks/results benchmarks/results-p12-blocked benchmarks/results-p12-partial
```

Expected:

```text
!! benchmarks/results/
```

## Task 4: Final Current-Truth Review

- [ ] **Step 1: Confirm the alpha baseline language**

Review these files:

```text
README.md
docs/reports/current-state-analysis.md
docs/reports/next-improvement-roadmap.md
docs/mvp-issues.md
```

Expected: each file says the alpha baseline is local and deterministic, with no live executor, no remote orchestration, and no autonomous code editing.

- [ ] **Step 2: Confirm generated evidence policy language**

Review:

```text
docs/generated-vs-frozen-evidence-policy.md
.gitignore
```

Expected:

```text
.qa-z/
benchmarks/results/work/
benchmarks/results/summary.json
benchmarks/results/report.md
```

are local-generated surfaces, while `benchmarks/fixtures/**/repo/.qa-z/**` is allowed only as fixture-local deterministic input.

- [ ] **Step 3: Confirm config and template examples do not overclaim**

Review:

```text
qa-z.yaml.example
templates/AGENTS.md
templates/CLAUDE.md
templates/.claude/skills/qa-guard/SKILL.md
templates/.github/workflows/vibeqa.yml
examples/fastapi-demo/README.md
examples/nextjs-demo/README.md
examples/typescript-demo/README.md
```

Expected: examples and templates describe deterministic local gates and repair handoff surfaces only; they do not claim live executor automation, remote orchestration, branch mutation, commit/push behavior, or GitHub bot comments.

- [ ] **Step 4: Apply only drift fixes found during review**

If any reviewed file contradicts the expected language, edit that file to use this wording:

```text
QA-Z's current alpha baseline is a local deterministic QA control plane. It can package repair evidence for external agents and ingest executor-result artifacts, but it does not run live model execution, remote orchestration, autonomous code editing, branch mutation, commit/push automation, or GitHub bot actions.
```

Expected: no documentation change is made when the reviewed files already preserve that boundary.

## Task 5: Run Alpha Closure Gates

- [ ] **Step 1: Run the full test suite**

Run:

```bash
python -m pytest
```

Expected: PASS with 294 passed and 1 skipped, or the updated count if new tests were intentionally added during this closure pass.

- [ ] **Step 2: Run the benchmark corpus**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: PASS with 46/46 fixtures and `overall_rate` equal to `1.0`.

- [ ] **Step 3: Run lint**

Run:

```bash
python -m ruff check .
```

Expected: PASS.

- [ ] **Step 4: Run format check**

Run:

```bash
python -m ruff format --check .
```

Expected: PASS.

- [ ] **Step 5: Run type check**

Run:

```bash
python -m mypy src tests
```

Expected: PASS.

- [ ] **Step 6: Capture the closure evidence**

Record the exact command results in the final implementation summary. Do not commit `benchmarks/results/summary.json`, `benchmarks/results/report.md`, or `benchmarks/results/work/**` unless a separate frozen-evidence commit is explicitly created with surrounding documentation.

## Task 6: Stage Through Existing Commit Boundaries

- [ ] **Step 1: Re-read the existing commit plan**

Run:

```powershell
Get-Content -LiteralPath 'docs/reports/worktree-commit-plan.md'
```

Expected: the plan still names this commit order:

```text
feat: add runner repair and verification foundations
feat: expand benchmark coverage for typescript and deep policy cases
feat: add self-inspection backlog and task selection workflow
feat: add autonomy planning loops and loop artifacts
feat: add repair session workflow and verification publishing
feat: add executor bridge packaging for external repair workflows
docs: add worktree triage and commit plan reports
```

- [ ] **Step 2: Update the commit plan only if the current worktree requires it**

If the final closure pass adds this plan file and the generated evidence policy file is still uncommitted, append this exact section to `docs/reports/worktree-commit-plan.md`:

```markdown
## Alpha Closure Addendum

After the feature batches are staged, include the alpha closure cleanup in the documentation/status commit:

- `docs/generated-vs-frozen-evidence-policy.md`
- `docs/superpowers/plans/2026-04-18-alpha-closure-gate-cleanup.md`
- final README/report/MVP wording updates, if any drift fixes were needed

Do not stage `benchmarks/results/**` or removed local `benchmarks/results-p12-*` snapshots as source evidence.
```

Expected: no commit-plan change is made when an equivalent alpha-closure note already exists.

- [ ] **Step 3: Stage the foundation commit using patch selection**

Run:

```bash
git add src/qa_z/diffing src/qa_z/repair_handoff.py src/qa_z/reporters/deep_context.py src/qa_z/reporters/sarif.py src/qa_z/runners/checks.py src/qa_z/runners/deep.py src/qa_z/runners/selection.py src/qa_z/runners/selection_common.py src/qa_z/runners/selection_deep.py src/qa_z/runners/selection_typescript.py src/qa_z/runners/semgrep.py src/qa_z/runners/typescript.py src/qa_z/verification.py tests/test_diffing.py tests/test_fast_config.py tests/test_fast_selection.py tests/test_deep_run_resolution.py tests/test_deep_selection.py tests/test_semgrep_normalization.py tests/test_sarif_cli.py tests/test_sarif_reporter.py tests/test_verification.py tests/test_plan_titles.py
git add -p src/qa_z/artifacts.py src/qa_z/config.py src/qa_z/planner/contracts.py src/qa_z/reporters/repair_prompt.py src/qa_z/reporters/review_packet.py src/qa_z/reporters/run_summary.py src/qa_z/runners/fast.py src/qa_z/runners/models.py src/qa_z/runners/subprocess.py src/qa_z/cli.py tests/test_repair_prompt.py tests/test_cli.py tests/test_artifact_schema.py README.md docs/artifact-schema-v1.md docs/mvp-issues.md
```

Expected: only runner, deep, repair handoff, SARIF, and verification foundation hunks are staged.

- [ ] **Step 4: Validate and commit the foundation batch**

Run:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_diffing.py tests/test_fast_config.py tests/test_fast_selection.py tests/test_deep_run_resolution.py tests/test_deep_selection.py tests/test_semgrep_normalization.py tests/test_sarif_cli.py tests/test_sarif_reporter.py tests/test_verification.py tests/test_plan_titles.py -q
git commit -m "feat: add runner repair and verification foundations"
```

Expected: all validation commands pass before the commit is created.

- [ ] **Step 5: Stage and commit the remaining batches in order**

Use `docs/reports/worktree-commit-plan.md` as the authoritative file list for each remaining batch. For each batch, run the targeted tests named in that plan and then commit with the exact message from Step 1.

Expected commit order:

```text
feat: expand benchmark coverage for typescript and deep policy cases
feat: add self-inspection backlog and task selection workflow
feat: add autonomy planning loops and loop artifacts
feat: add repair session workflow and verification publishing
feat: add executor bridge packaging for external repair workflows
docs: add worktree triage and commit plan reports
```

- [ ] **Step 6: Run final post-commit validation**

Run:

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
git status --short
```

Expected: all gates pass, benchmark remains 46/46 with `overall_rate` `1.0`, and `git status --short` shows no source changes other than intentionally ignored generated runtime artifacts.

## Self-Review

Spec coverage:

- Alpha 기준선 고정 is covered by Task 4 and Task 5.
- Generated vs Frozen Evidence Policy is covered by Task 3 and Task 4.
- Loop Health / Empty-loop Hardening is preserved as maintenance scope by Task 4 and Task 5.
- Mixed-surface Benchmark Breadth is validated by Task 5 and staged through Task 6.
- Report / Template / Example Sync is covered by Task 4.
- Executor Operator Diagnostics is validated by Task 1, Task 5, and the benchmark corpus in Task 6.
- Alpha Closure is covered by Tasks 1 through 6.

Placeholder scan:

- No task contains deferred implementation language.
- Every command step includes an expected result.
- The only conditional edit is bounded to a specific replacement sentence or a specific commit-plan addendum.

Type consistency:

- `build_summary()` returns `dict[str, Any]`, matching `build_dry_run_summary()` and allowing typed access to nested summary values in the test assertions.
- Generated snapshot paths are consistently treated as local generated output, while fixture-local `.qa-z` remains committed benchmark input.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-18-alpha-closure-gate-cleanup.md`.

Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
