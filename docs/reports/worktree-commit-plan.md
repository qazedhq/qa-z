# QA-Z Worktree Commit Plan

Date: 2026-04-15
Branch: `codex/qa-z-bootstrap`

## Goal

Create reversible commit boundaries for the accumulated alpha worktree without
discarding meaningful work or bundling generated runtime artifacts into source commits.

This plan supersedes the earlier benchmark-first ordering. `src/qa_z/benchmark.py`
imports foundation modules that are not present in `HEAD`, so a benchmark-only first
commit would be broken. The corrected order is foundation first, benchmark second.

## Commit Rules

- Do not stage root `.qa-z/**`.
- Do not stage `benchmarks/results/work/**`.
- Do not stage `benchmarks/results/summary.json` or `benchmarks/results/report.md`
  unless the commit explicitly says it is freezing benchmark evidence.
- Keep fixture-local `.qa-z` summaries under `benchmarks/fixtures/**/repo/.qa-z/**`
  when they are benchmark inputs.
- Use `git add -p` for `src/qa_z/cli.py`, `README.md`,
  `docs/artifact-schema-v1.md`, and `docs/mvp-issues.md`; those files span multiple
  feature surfaces.
- Run targeted tests for each commit, then run the full validation checklist before
  tagging.

## Preflight

`tests/test_benchmark.py` has already been formatted once during triage, but it is
untracked in the current worktree. Do not create a standalone format-only commit for
that file unless it becomes tracked first.

Recommended benchmark preflight before Commit 2:

```bash
python -m ruff format tests/test_benchmark.py
python -m ruff format --check .
python -m ruff check .
```

Then include the formatted `tests/test_benchmark.py` in the benchmark commit.

## Corrected Commit Sequence

1. `feat: add runner repair and verification foundations`
2. `feat: expand benchmark coverage for typescript and deep policy cases`
3. `feat: add self-inspection backlog and task selection workflow`
4. `feat: add autonomy planning loops and loop artifacts`
5. `feat: add repair session workflow and verification publishing`
6. `feat: add executor bridge packaging for external repair workflows`
7. `docs: add worktree triage and commit plan reports`

## Import-Closure Finding

The direct `qa_z.benchmark` imports are:

- `qa_z.artifacts`
- `qa_z.config`
- `qa_z.repair_handoff`
- `qa_z.reporters.deep_context`
- `qa_z.reporters.repair_prompt`
- `qa_z.reporters.run_summary`
- `qa_z.reporters.sarif`
- `qa_z.runners.deep`
- `qa_z.runners.fast`
- `qa_z.runners.models`
- `qa_z.verification`

The benchmark-safe foundation closure, excluding `qa_z.benchmark` itself, is:

| State | Path |
| --- | --- |
| modified | `src/qa_z/artifacts.py` |
| modified | `src/qa_z/config.py` |
| untracked | `src/qa_z/diffing/models.py` |
| untracked | `src/qa_z/diffing/parser.py` |
| untracked | `src/qa_z/repair_handoff.py` |
| untracked | `src/qa_z/reporters/deep_context.py` |
| modified | `src/qa_z/reporters/repair_prompt.py` |
| modified | `src/qa_z/reporters/review_packet.py` |
| untracked | `src/qa_z/reporters/sarif.py` |
| untracked | `src/qa_z/runners/checks.py` |
| untracked | `src/qa_z/runners/deep.py` |
| modified | `src/qa_z/runners/fast.py` |
| modified | `src/qa_z/runners/models.py` |
| tracked-clean | `src/qa_z/runners/python.py` |
| untracked | `src/qa_z/runners/selection.py` |
| untracked | `src/qa_z/runners/selection_common.py` |
| untracked | `src/qa_z/runners/selection_deep.py` |
| untracked | `src/qa_z/runners/selection_typescript.py` |
| untracked | `src/qa_z/runners/semgrep.py` |
| modified | `src/qa_z/runners/subprocess.py` |
| untracked | `src/qa_z/runners/typescript.py` |
| untracked | `src/qa_z/verification.py` |

Add `src/qa_z/diffing/__init__.py` with this set for package completeness. Do not add
`src/qa_z/benchmark.py` until Commit 2.

## Commit 1: Runner, Repair, And Verification Foundations

Message:

```text
feat: add runner repair and verification foundations
```

Purpose:

Add the import-safe foundation that benchmark, deep QA, repair handoff, and
verification depend on. This commit should make the intermediate repository coherent
without introducing the benchmark corpus, self-improvement loops, repair sessions, or
executor bridge packaging.

Include whole files where possible:

- `src/qa_z/diffing/__init__.py`
- `src/qa_z/diffing/models.py`
- `src/qa_z/diffing/parser.py`
- `src/qa_z/repair_handoff.py`
- `src/qa_z/reporters/deep_context.py`
- `src/qa_z/reporters/sarif.py`
- `src/qa_z/runners/checks.py`
- `src/qa_z/runners/deep.py`
- `src/qa_z/runners/selection.py`
- `src/qa_z/runners/selection_common.py`
- `src/qa_z/runners/selection_deep.py`
- `src/qa_z/runners/selection_typescript.py`
- `src/qa_z/runners/semgrep.py`
- `src/qa_z/runners/typescript.py`
- `src/qa_z/verification.py`
- `src/qa_z/adapters/codex/repair_handoff.py` if repair-handoff adapter tests are included
- `src/qa_z/adapters/claude/repair_handoff.py` if repair-handoff adapter tests are included

Patch-add only foundation hunks from:

- `src/qa_z/artifacts.py`
- `src/qa_z/config.py`
- `src/qa_z/planner/contracts.py`
- `src/qa_z/reporters/repair_prompt.py`
- `src/qa_z/reporters/review_packet.py`
- `src/qa_z/reporters/run_summary.py`
- `src/qa_z/runners/fast.py`
- `src/qa_z/runners/models.py`
- `src/qa_z/runners/subprocess.py`
- `src/qa_z/adapters/codex/__init__.py`
- `src/qa_z/adapters/claude/__init__.py`
- `src/qa_z/cli.py`

`src/qa_z/cli.py` must not be added wholesale. Its current top-level imports include
benchmark, self-improvement, autonomy, repair session, and executor bridge modules.
For Commit 1, stage only the import and handler/parser hunks for:

- `deep`
- `repair-prompt`
- `verify`
- `review` run/deep context, if included

Do not stage CLI hunks for:

- `benchmark`
- `self-inspect`
- `select-next`
- `backlog`
- `autonomy`
- `repair-session`
- `executor-bridge`
- `github-summary`, unless its foundation-only rendering is intentionally included

Tests to include:

- `tests/test_diffing.py`
- `tests/test_fast_config.py`
- `tests/test_fast_selection.py`
- `tests/test_deep_run_resolution.py`
- `tests/test_deep_selection.py`
- `tests/test_semgrep_normalization.py`
- `tests/test_sarif_cli.py`
- `tests/test_sarif_reporter.py`
- `tests/test_subprocess_runner.py`
- `tests/test_repair_handoff.py`
- `tests/test_verification.py`
- `tests/test_plan_titles.py`, if planner contract metadata hunks are included
- foundation hunks from `tests/test_repair_prompt.py`, `tests/test_cli.py`, and
  `tests/test_artifact_schema.py`

Docs to patch-add only if they describe this foundation surface:

- README sections for fast/deep selection, repair handoff, SARIF, and verification
- `docs/artifact-schema-v1.md` sections for summary v2, deep findings, SARIF,
  repair packet/handoff, and verification artifacts
- `docs/mvp-issues.md` status for runner, deep, repair handoff, SARIF, and verification

Exclude:

- `src/qa_z/benchmark.py`
- `tests/test_benchmark.py`
- `benchmarks/**`
- `docs/benchmarking.md`
- `src/qa_z/self_improvement.py`
- `src/qa_z/autonomy.py`
- `src/qa_z/repair_session.py`
- `src/qa_z/executor_bridge.py`
- `src/qa_z/reporters/github_summary.py`, unless deliberately split as foundation
- `src/qa_z/reporters/verification_publish.py`
- `docs/reports/**`
- root `.qa-z/**`
- `benchmarks/results/**`

Targeted validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_diffing.py tests/test_fast_config.py tests/test_fast_selection.py tests/test_deep_run_resolution.py tests/test_deep_selection.py tests/test_semgrep_normalization.py tests/test_sarif_cli.py tests/test_sarif_reporter.py tests/test_subprocess_runner.py tests/test_repair_handoff.py tests/test_verification.py -q
python -m qa_z --help
python -c "import qa_z.repair_handoff; import qa_z.verification; import qa_z.runners.deep; import qa_z.reporters.sarif; import qa_z.reporters.deep_context"
```

Rollback boundary:

Reverting this commit should remove the new runner/deep/repair/verify foundation while
leaving older bootstrap commands coherent.

## Commit 2: Benchmark Coverage

Message:

```text
feat: expand benchmark coverage for typescript and deep policy cases
```

Purpose:

Add the benchmark runner, support helpers, TypeScript fixtures, and deep policy
fixtures on top of the foundation from Commit 1.

Include:

- `src/qa_z/benchmark.py`
- benchmark hunks from `src/qa_z/cli.py`
- `tests/test_benchmark.py`, patch-added if mixed-language P5-C is deferred
- `benchmarks/support/**`
- `benchmarks/fixtures/ts_lint_failure/**`
- `benchmarks/fixtures/ts_type_error/**`
- `benchmarks/fixtures/ts_test_failure/**`
- `benchmarks/fixtures/ts_multiple_fast_failures/**`
- `benchmarks/fixtures/ts_unchanged_candidate/**`
- `benchmarks/fixtures/ts_regressed_candidate/**`
- `benchmarks/fixtures/deep_severity_threshold_warn_filtered/**`
- `benchmarks/fixtures/deep_ignore_rule_suppressed/**`
- `benchmarks/fixtures/deep_exclude_paths_skipped/**`
- `benchmarks/fixtures/deep_grouped_findings_dedup/**`
- `benchmarks/fixtures/deep_filtered_vs_blocking_counts/**`
- `benchmarks/fixtures/deep_config_error_surface/**`
- `docs/benchmarking.md`, patch-added if mixed-language P5-C is deferred
- `.gitignore` hunks for fixture-local `.qa-z` and `benchmarks/results/work/`
- benchmark hunks from README, artifact schema, and MVP status docs

Exclude unless intentionally doing P5-C in this commit:

- `benchmarks/fixtures/mixed_all_resolved_candidate/**`
- `benchmarks/fixtures/mixed_partial_resolved_with_regression_candidate/**`
- `benchmarks/fixtures/mixed_py_resolved_ts_regressed_candidate/**`
- `benchmarks/fixtures/mixed_ts_resolved_py_regressed_candidate/**`
- `docs/superpowers/plans/2026-04-15-p5-c-mixed-language-benchmark.md`
- `docs/superpowers/specs/2026-04-15-p5-c-mixed-language-benchmark-design.md`

Always exclude:

- `benchmarks/results/summary.json`
- `benchmarks/results/report.md`
- `benchmarks/results/work/**`
- root `.qa-z/**`
- `docs/reports/**`

Targeted validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_benchmark.py -q
python -m qa_z benchmark --json
python -c "import qa_z.benchmark"
```

Rollback boundary:

Reverting this commit should remove benchmark measurement without affecting the
foundation commands from Commit 1.

## Commit 3: Self-Inspection Backlog

Message:

```text
feat: add self-inspection backlog and task selection workflow
```

Include:

- `src/qa_z/self_improvement.py`
- CLI hunks for `self-inspect`, `select-next`, and `backlog`
- `tests/test_self_improvement.py`
- relevant hunks from `tests/test_cli.py`
- `docs/superpowers/plans/2026-04-15-p6-a-self-inspection-backlog.md`
- README/schema/MVP hunks for self-inspection, backlog, selected tasks, and history

Validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_self_improvement.py tests/test_cli.py -q
```

## Commit 4: Autonomy Workflow

Message:

```text
feat: add autonomy planning loops and loop artifacts
```

Include:

- `src/qa_z/autonomy.py`
- CLI hunks for `autonomy --loops` and `autonomy status`
- `tests/test_autonomy.py`
- relevant hunks from `tests/test_cli.py`
- README/schema/MVP hunks for loop artifacts and autonomy outcomes
- `docs/repair-sessions.md` hunks that describe autonomy preparing sessions, if any

Validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_autonomy.py tests/test_cli.py -q
```

## Commit 5: Repair Session And Publishing

Message:

```text
feat: add repair session workflow and verification publishing
```

Include:

- `src/qa_z/repair_session.py`
- `src/qa_z/reporters/verification_publish.py`
- `src/qa_z/reporters/github_summary.py`
- CLI hunks for `repair-session` and `github-summary`
- `tests/test_repair_session.py`
- `tests/test_verification_publish.py`
- `tests/test_github_summary.py`
- `tests/test_github_workflow.py`
- relevant hunks from `tests/test_artifact_schema.py` and `tests/test_cli.py`
- `docs/repair-sessions.md`
- workflow hunks in `.github/workflows/ci.yml` and
  `templates/.github/workflows/vibeqa.yml` that publish summaries/upload artifacts
- README/schema/MVP hunks for repair sessions and publish summaries

Validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_repair_session.py tests/test_verification_publish.py tests/test_github_summary.py tests/test_github_workflow.py -q
```

## Commit 6: Executor Bridge

Message:

```text
feat: add executor bridge packaging for external repair workflows
```

Include:

- `src/qa_z/executor_bridge.py`
- CLI hunks for `executor-bridge`
- `tests/test_executor_bridge.py`
- relevant hunks from `tests/test_cli.py`
- README/schema/MVP/repair-session docs hunks for bridge artifacts

Validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_executor_bridge.py tests/test_cli.py -q
```

## Commit 7: Cleanup Reports

Message:

```text
docs: add worktree triage and commit plan reports
```

Include:

- `docs/reports/worktree-triage.md`
- `docs/reports/worktree-commit-plan.md`

Validation:

```bash
python -m pytest
```

## Alpha Closure Addendum

After the feature batches are staged, include the alpha closure cleanup in the
documentation/status commit:

- `docs/generated-vs-frozen-evidence-policy.md`
- `docs/superpowers/plans/2026-04-18-alpha-closure-gate-cleanup.md`
- final README/report/MVP wording updates, if any drift fixes were needed

Do not stage `benchmarks/results/**` or removed local `benchmarks/results-p12-*`
snapshots as source evidence.

## Alpha Release Closure Batch

Message:

```text
chore: freeze alpha release target and root qa gate
```

Purpose:

Close the release-prep work that sits outside the feature batches: the public
`v0.9.8-alpha` identifier, Python package version `0.9.8a0`, root Python-only
release gate, and final in-repository release notes.

Include whole files:

- `qa-z.yaml`
- `docs/releases/v0.9.8-alpha.md`
- `docs/superpowers/plans/2026-04-18-github-repository-release.md`

Patch-add only the release-target README hunks from:

- `README.md`

Patch-add only the version metadata hunks from:

- `pyproject.toml`

Patch-add only the root gate, release target, and closure-boundary guard hunks from:

- `tests/test_current_truth.py`
- `tests/test_github_workflow.py`

Patch-add any matching status-only wording from:

- `docs/reports/worktree-commit-plan.md`
- `docs/reports/worktree-triage.md`

Exclude:

- feature command, runner, benchmark, autonomy, repair-session, executor, and
  self-inspection implementation hunks
- generated root `.qa-z/**`
- generated `benchmarks/results/**`
- generated benchmark snapshot directories such as `benchmarks/results-*`

Targeted validation:

```bash
python -m pytest tests/test_current_truth.py tests/test_github_workflow.py -q
python -m qa_z fast --selection smart --json
python -m qa_z deep --selection smart --json
```

Rollback boundary:

Reverting this batch should unfreeze the public release target and remove the
root release gate without changing the already-split feature implementation
batches.

## Alpha Closure Readiness Snapshot

The latest full local gate pass for this accumulated alpha baseline is:

- `python -m pytest`: 341 passed
- `python -m qa_z benchmark --json`: 50/50 fixtures, overall_rate 1.0
- `python -m build --sdist --wheel`: passed, built `qa_z-0.9.8a0.tar.gz` and `qa_z-0.9.8a0-py3-none-any.whl`
- `python -m ruff check .`: pass
- `python -m ruff format --check .`: 126 files already formatted
- `python -m mypy src tests`: success across 82 source files

Human planning surfaces now keep this snapshot as the primary compact
commit-isolation evidence and append an `action basis:` suffix when area-bearing
`git_status` evidence explains the next action hint.
Treat the benchmark line as the benchmark summary `snapshot` field, not a
manually recomputed count, so alpha closure notes quote generated evidence.
Executor bridge stdout now also reports action-context package health and
missing action-context diagnostics when loop-prepared optional context paths are
copied or skipped.
Benchmark snapshot directories matching `benchmarks/results-*` are generated
runtime artifacts by default. Freeze them only when the commit explicitly says
they are intentional evidence and includes the surrounding context.
Deferred generated cleanup prepared actions now carry
`docs/generated-vs-frozen-evidence-policy.md` through `context_paths`, so
external handoffs keep the local-only versus intentional frozen evidence policy
beside the worktree triage reports.
Autonomy status and saved loop plans now mirror selected fallback families, so
repeated cleanup-family selection is visible without reopening `outcome.json`.
Loop-health prepared actions now carry selected task evidence paths through
`context_paths`, so fallback-diversity handoffs can point directly at
`.qa-z/loops/history.jsonl`.
Autonomy-created repair-session actions now preserve selected verification
evidence in `context_paths`, and executor bridge packages copy existing action
context files into `inputs/context/` while recording `inputs.action_context`.
The committed benchmark corpus now pins that path with
`executor_bridge_action_context_inputs` and pins missing optional action-context
guide/stdout diagnostics with `executor_bridge_missing_action_context_inputs`.
Deferred cleanup compact evidence can append an `action basis:` suffix with
`generated_outputs` or `runtime_artifacts` evidence so generated artifact cleanup
decisions stay visible in the human handoff.

This snapshot is evidence for commit splitting, not a source artifact to commit
blindly. `benchmarks/results/report.md` now carries its own `Generated Output Policy`
section, but `benchmarks/results/summary.json`,
`benchmarks/results/report.md`, and `benchmarks/results/work/**` still stay local
unless a commit explicitly freezes benchmark evidence with surrounding context.

The next operator action is to split the worktree by this commit plan, rerun the
targeted validation for each batch, and rerun the full validation checklist below
before tagging.

## Full Validation Before Tagging

Run after all selected commits are split and generated artifacts are excluded or
intentionally committed:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest
python -m qa_z benchmark --json
python -m qa_z --help
python -m qa_z self-inspect --help
python -m qa_z select-next --help
python -m qa_z autonomy --help
python -m qa_z executor-bridge --help
python -m qa_z repair-session --help
python -m qa_z github-summary --help
```

Use `v0.9.8-alpha` for the current release candidate now that the baseline includes
self-improvement, autonomy, executor bridge packaging, executor-result ingest, and
the live-free safety dry-run. Use `v0.10.0-alpha` only if the team wants a larger
reset point.
