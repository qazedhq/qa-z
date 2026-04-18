# QA-Z Worktree Triage

Date: 2026-04-15
Branch: `codex/qa-z-bootstrap`

## Summary

This worktree is an accumulated alpha integration state, not a small feature diff.
No changes were staged during this triage pass.

- Tracked modified files: 25
- Untracked file paths: 193
- `git status --short` entries: 75, because Git collapses several untracked directories
- Last committed base: `3501a2a docs: define semgrep deep vertical slice`
- Tags found locally: none

The dirty state contains useful implementation work across fast/deep selection,
TypeScript checks, Semgrep normalization, repair handoff, verification, repair
sessions, benchmark coverage, self-improvement planning, autonomy, executor bridge
packaging, docs, schema, tests, examples, and generated benchmark output.

This pass did not delete or commit any existing work.

## Category Counts

Tracked modified files:

| Category | Count |
| --- | ---: |
| Core product code | 12 |
| Tests / fixtures / benchmark corpus | 4 |
| Docs / schema / plans | 4 |
| Config / tooling / schema example | 5 |

Untracked files:

| Category | Count |
| --- | ---: |
| Core product code | 24 |
| Tests / fixtures / benchmark corpus | 151 |
| Docs / schema / plans / examples | 16 |
| Local runtime outputs | 2 |

Ignored generated/local state observed outside Git:

- `.qa-z/**`
- `benchmarks/results/work/**`
- cache directories such as `.mypy_cache/`, `.pytest_cache/`, and `.ruff_cache/`

## Tracked Modified Files

| Path | Category | Estimated stage | Handling |
| --- | --- | --- | --- |
| `.github/workflows/ci.yml` | Config / tooling | Deep/SARIF/GitHub workflow | Split with workflow integration docs or final docs sync |
| `.gitignore` | Generated artifact policy | Benchmark/runtime policy | Keep with benchmark corpus or artifact policy commit |
| `README.md` | Docs / user surface | Alpha status sync | Keep for final docs sync after feature batches |
| `benchmark/README.md` | Docs | Legacy benchmark docs | Review during docs sync |
| `docs/artifact-schema-v1.md` | Schema docs | P3-P6 artifact surface | Keep with schema sync, or split with owning feature if easy |
| `docs/mvp-issues.md` | Roadmap/status docs | Alpha status through v0.9.2 | Keep as roadmap/status sync |
| `pyproject.toml` | Config / tooling | Test discovery | Keep with test/tooling commit or docs sync |
| `qa-z.yaml.example` | Config surface | Fast/deep/TypeScript/Semgrep config | Keep with config surface changes |
| `src/qa_z/adapters/claude/__init__.py` | Core adapter | Repair handoff adapter export | Keep with repair handoff batch |
| `src/qa_z/adapters/codex/__init__.py` | Core adapter | Repair handoff adapter export | Keep with repair handoff batch |
| `src/qa_z/artifacts.py` | Core artifact loading | Latest run manifest and contract context | Keep with runner/repair foundation |
| `src/qa_z/cli.py` | Core CLI wiring | Cross-cutting command surface | Split by command hunks only if safe |
| `src/qa_z/config.py` | Core config | Fast/deep/selection config | Keep with runner foundation |
| `src/qa_z/planner/contracts.py` | Core planner | Diff/title/context metadata | Keep with runner foundation |
| `src/qa_z/reporters/repair_prompt.py` | Core reporter | Deep-aware repair prompt/handoff context | Keep with repair handoff batch |
| `src/qa_z/reporters/review_packet.py` | Core reporter | Deep-aware review packet | Keep with repair handoff/deep reporter batch |
| `src/qa_z/reporters/run_summary.py` | Core reporter | Run summary output | Keep with runner foundation |
| `src/qa_z/runners/fast.py` | Core runner | Smart selection/check execution | Keep with runner foundation |
| `src/qa_z/runners/models.py` | Core models | v2 run/check/selection models | Keep with runner foundation |
| `src/qa_z/runners/subprocess.py` | Core runner | Subprocess output preservation | Keep with runner foundation |
| `templates/.github/workflows/vibeqa.yml` | Config / workflow template | CI QA-Z workflow | Keep with workflow/docs sync |
| `tests/test_artifact_schema.py` | Tests | Schema coverage | Keep with schema/docs batch |
| `tests/test_cli.py` | Tests | CLI behavior | Split by command group where practical |
| `tests/test_repair_prompt.py` | Tests | Repair/review prompt behavior | Keep with repair handoff batch |
| `tests/test_subprocess_runner.py` | Tests | Subprocess/no-tests behavior | Keep with runner foundation |

## Untracked Core Product Code

| Path | Estimated stage | Handling |
| --- | --- | --- |
| `src/qa_z/adapters/claude/repair_handoff.py` | Repair handoff | Keep with repair handoff batch |
| `src/qa_z/adapters/codex/repair_handoff.py` | Repair handoff | Keep with repair handoff batch |
| `src/qa_z/autonomy.py` | P6-B autonomy | Keep with autonomy batch |
| `src/qa_z/benchmark.py` | P5 benchmark runner | Keep with benchmark batch |
| `src/qa_z/diffing/__init__.py` | Runner foundation | Keep with runner foundation |
| `src/qa_z/diffing/models.py` | Runner foundation | Keep with runner foundation |
| `src/qa_z/diffing/parser.py` | Runner foundation | Keep with runner foundation |
| `src/qa_z/executor_bridge.py` | P6-C executor bridge | Keep with executor bridge batch |
| `src/qa_z/repair_handoff.py` | Repair handoff | Keep with repair handoff batch |
| `src/qa_z/repair_session.py` | Repair session | Keep with repair session batch |
| `src/qa_z/reporters/deep_context.py` | Deep reporter context | Keep with runner/repair reporter batch |
| `src/qa_z/reporters/github_summary.py` | GitHub summary | Keep with publish/session batch |
| `src/qa_z/reporters/sarif.py` | SARIF | Keep with deep/SARIF batch |
| `src/qa_z/reporters/verification_publish.py` | Verification publish | Keep with verification/session batch |
| `src/qa_z/runners/checks.py` | Runner foundation | Keep with runner foundation |
| `src/qa_z/runners/deep.py` | Deep runner | Keep with deep runner batch |
| `src/qa_z/runners/selection.py` | Smart selection | Keep with runner foundation |
| `src/qa_z/runners/selection_common.py` | Smart selection | Keep with runner foundation |
| `src/qa_z/runners/selection_deep.py` | Deep selection | Keep with deep runner batch |
| `src/qa_z/runners/selection_typescript.py` | TypeScript selection | Keep with TypeScript runner batch |
| `src/qa_z/runners/semgrep.py` | Semgrep normalization | Keep with deep runner batch |
| `src/qa_z/runners/typescript.py` | TypeScript checks | Keep with TypeScript runner batch |
| `src/qa_z/self_improvement.py` | P6-A self-improvement | Keep with self-improvement batch |
| `src/qa_z/verification.py` | Post-repair verification | Keep with verification batch |

## Untracked Tests

| Path | Estimated stage | Handling |
| --- | --- | --- |
| `tests/test_autonomy.py` | P6-B autonomy | Keep with autonomy batch |
| `tests/test_benchmark.py` | P5 benchmark | Keep with benchmark batch; format before staging the benchmark commit because the file is untracked |
| `tests/test_deep_run_resolution.py` | Deep runner | Keep with deep runner batch |
| `tests/test_deep_selection.py` | Deep selection | Keep with deep runner batch |
| `tests/test_diffing.py` | Runner foundation | Keep with runner foundation |
| `tests/test_executor_bridge.py` | P6-C executor bridge | Keep with executor bridge batch |
| `tests/test_fast_config.py` | Fast/TypeScript config | Keep with runner foundation |
| `tests/test_fast_selection.py` | Fast smart selection | Keep with runner foundation |
| `tests/test_github_summary.py` | GitHub summary | Keep with publish/session batch |
| `tests/test_github_workflow.py` | Workflow template | Keep with workflow/docs sync |
| `tests/test_plan_titles.py` | Planner contracts | Keep with runner foundation |
| `tests/test_repair_handoff.py` | Repair handoff | Keep with repair handoff batch |
| `tests/test_repair_session.py` | Repair session | Keep with repair session batch |
| `tests/test_sarif_cli.py` | SARIF/deep CLI | Keep with deep/SARIF batch |
| `tests/test_sarif_reporter.py` | SARIF reporter | Keep with deep/SARIF batch |
| `tests/test_self_improvement.py` | P6-A self-improvement | Keep with self-improvement batch |
| `tests/test_semgrep_normalization.py` | Semgrep normalization | Keep with deep runner batch |
| `tests/test_verification.py` | Verification | Keep with verification batch |
| `tests/test_verification_publish.py` | Verification publish | Keep with publish/session batch |

## Benchmark Corpus And Fixtures

The untracked benchmark corpus is meaningful source material, not local trash.
Keep `benchmarks/fixtures/**`, `benchmarks/support/**`, and fixture-local `.qa-z`
summaries that are used as seeded inputs.

| Group | Fixture directories |
| --- | --- |
| Python fast detection | `py_lint_failure`, `py_test_failure`, `py_type_error` |
| TypeScript fast detection | `ts_lint_failure`, `ts_type_error`, `ts_test_failure`, `ts_multiple_fast_failures` |
| Verification outcomes | `improved_candidate`, `unchanged_candidate`, `regressed_candidate`, `ts_unchanged_candidate`, `ts_regressed_candidate` |
| Mixed-language verification | `mixed_all_resolved_candidate`, `mixed_partial_resolved_with_regression_candidate`, `mixed_py_resolved_ts_regressed_candidate`, `mixed_ts_resolved_py_regressed_candidate` |
| Semgrep/deep detection | `semgrep_eval`, `semgrep_hardcoded_secret`, `semgrep_shell_true` |
| Deep policy behavior | `deep_config_error_surface`, `deep_exclude_paths_skipped`, `deep_filtered_vs_blocking_counts`, `deep_grouped_findings_dedup`, `deep_ignore_rule_suppressed`, `deep_severity_threshold_warn_filtered` |
| Cross-run integration | `fast_and_deep_blocking` |

Support files to keep with the benchmark batch:

- `benchmarks/support/bin/semgrep`
- `benchmarks/support/bin/semgrep.cmd`
- `benchmarks/support/fake_semgrep.py`
- `benchmarks/support/fast_check.py`

Generated benchmark result files observed:

- `benchmarks/results/summary.json`
- `benchmarks/results/report.md`

These two files are generated by `python -m qa_z benchmark --json`. Treat them as
local runtime evidence unless the project explicitly wants to commit a frozen
benchmark evidence snapshot. The work directory under `benchmarks/results/work/**`
is ignored and should remain local only.

## Docs, Plans, And Examples

Untracked docs and historical planning artifacts:

- `docs/benchmarking.md`
- `docs/repair-sessions.md`
- `docs/superpowers/plans/2026-04-12-github-summary-surface.md`
- `docs/superpowers/plans/2026-04-14-p5-a-typescript-benchmark-fixtures.md`
- `docs/superpowers/plans/2026-04-15-p5-c-mixed-language-benchmark.md`
- `docs/superpowers/plans/2026-04-15-p6-a-self-inspection-backlog.md`
- `docs/superpowers/specs/2026-04-15-p5-c-mixed-language-benchmark-design.md`

The `docs/superpowers/**` files should remain historical design records. They
should not be treated as current product truth unless README, schema docs, tests,
and CLI behavior agree.

Untracked TypeScript demo example:

- `examples/typescript-demo/README.md`
- `examples/typescript-demo/eslint.config.js`
- `examples/typescript-demo/issue.md`
- `examples/typescript-demo/package.json`
- `examples/typescript-demo/qa-z.yaml`
- `examples/typescript-demo/spec.md`
- `examples/typescript-demo/src/invoice.ts`
- `examples/typescript-demo/tests/invoice.test.ts`
- `examples/typescript-demo/tsconfig.json`

Keep the example only if TypeScript fast-check support is included in the alpha
baseline. Otherwise defer the entire `examples/typescript-demo/**` directory.

## Generated Artifact Policy

| Path | Policy | Reason |
| --- | --- | --- |
| `.qa-z/**` at repository root | Ignore/local only | Runtime run/session/loop/executor state |
| `.qa-z/runs/local-verify/**` | Ignore/local only | Local verification output currently present |
| `.qa-z/sessions/**` | Ignore/local only | Local repair workflow state |
| `.qa-z/loops/**` | Ignore/local only | Local self-improvement/autonomy state |
| `.qa-z/executor/**` | Ignore/local only | Local executor bridge packages |
| `benchmarks/results/work/**` | Ignore/local only | Benchmark scratch workspaces |
| `benchmarks/results/summary.json` | Local only by default | Generated benchmark summary; commit only as intentional frozen evidence |
| `benchmarks/results/report.md` | Local only by default | Generated benchmark report; commit only as intentional frozen evidence |
| `benchmarks/fixtures/**/repo/.qa-z/**` | Keep as fixture input | Seeded baseline/candidate summaries used by tests/benchmark |
| `benchmarks/fixtures/**/repo/.qa-z-benchmark/**` | Keep as fixture input | Seeded fake Semgrep output for deterministic benchmark fixtures |
| `benchmarks/support/**` | Keep as benchmark source | Shared fake tooling for deterministic benchmark execution |

The current `.gitignore` already ignores root `.qa-z/`, re-allows fixture-local
`.qa-z` data under `benchmarks/fixtures/**/repo/.qa-z/**`, and ignores
`benchmarks/results/work/`, `benchmarks/results/report.md`, and
`benchmarks/results/summary.json`.

## Logical Implementation Batches

### Batch 0: Runner, Repair, And Verification Foundation

Fast/deep runner evidence plus repair-handoff and verification foundation. This batch
must precede the benchmark commit because `src/qa_z/benchmark.py` imports these
modules directly or through their closure.

- `src/qa_z/diffing/**`
- `src/qa_z/repair_handoff.py`
- `src/qa_z/reporters/deep_context.py`
- `src/qa_z/reporters/repair_prompt.py`
- `src/qa_z/reporters/review_packet.py`
- `src/qa_z/reporters/sarif.py`
- `src/qa_z/runners/checks.py`
- `src/qa_z/runners/fast.py`
- `src/qa_z/runners/models.py`
- `src/qa_z/runners/selection*.py`
- `src/qa_z/runners/semgrep.py`
- `src/qa_z/runners/typescript.py`
- `src/qa_z/runners/deep.py`
- `src/qa_z/verification.py`
- relevant hunks from `src/qa_z/artifacts.py`, `src/qa_z/config.py`,
  `src/qa_z/runners/subprocess.py`, and `src/qa_z/cli.py`
- matching tests for diffing, fast/deep selection, Semgrep, SARIF, subprocess,
  repair handoff, and verification behavior

### Batch 1: Benchmark Coverage

Benchmark runner and deterministic corpus:

- `src/qa_z/benchmark.py`
- `benchmarks/fixtures/**`
- `benchmarks/support/**`
- `tests/test_benchmark.py`
- `docs/benchmarking.md`
- `.gitignore` fixture/local result policy

The mixed-language verification fixtures are already present in the dirty tree.
If P5-C should remain a future line, split the `mixed_*` fixtures and P5-C plan/spec
into a deferred patch instead of committing them with P5-A/P5-B.

### Batch 2: Self-Improvement Backlog

Evidence-backed planning without code edits or live model calls:

- `src/qa_z/self_improvement.py`
- related CLI wiring for `self-inspect`, `select-next`, and `backlog`
- `tests/test_self_improvement.py`
- relevant artifact schema and roadmap docs

### Batch 3: Autonomy Workflow

Repeatable local planning loops:

- `src/qa_z/autonomy.py`
- related CLI wiring for `autonomy`
- `tests/test_autonomy.py`
- autonomy loop/outcome schema and docs hunks

### Batch 4: Repair Session And Publishing

Repair-session orchestration and GitHub/publish summaries:

- `src/qa_z/adapters/*/repair_handoff.py`
- `src/qa_z/repair_session.py`
- `src/qa_z/reporters/github_summary.py`
- `src/qa_z/reporters/verification_publish.py`
- related tests for repair session, publish summaries, GitHub summary, and workflow

### Batch 5: Executor Bridge

External executor packaging:

- `src/qa_z/executor_bridge.py`
- related CLI wiring for `executor-bridge`
- `tests/test_executor_bridge.py`
- executor bridge schema/docs updates

### Batch 6: Cleanup Reports And Residual Docs

Cleanup reports plus residual docs/examples after implementation batches:

- `README.md`
- `docs/artifact-schema-v1.md`
- `docs/mvp-issues.md`
- `docs/repair-sessions.md`
- `docs/reports/**`
- `qa-z.yaml.example`
- `.github/workflows/ci.yml`
- `templates/.github/workflows/vibeqa.yml`
- `examples/typescript-demo/**`
- residual docs-only plan files

## Deferred Or Unknown Items

No untracked paths were found in an obviously unrelated top-level location. However,
the following should not be blindly bundled:

- `benchmarks/results/summary.json` and `benchmarks/results/report.md`: generated by benchmark runs; defer unless intentionally freezing sample evidence.
- Root `.qa-z/**`: local runtime state, ignored, should not be staged.
- `benchmarks/results/work/**`: local benchmark scratch state, ignored, should not be staged.
- `tests/test_benchmark.py`: `ruff format --check` reports it needs formatting, but the file is untracked. Handle before staging the benchmark commit; do not create a standalone format-only commit unless the file becomes tracked first.
- P5-C mixed-language benchmark files: already present. Either split into a dedicated P5-C commit or defer as the next work line.
- `benchmark/README.md`: legacy singular benchmark doc. Confirm whether it should survive beside `docs/benchmarking.md`.
- LF/CRLF warnings from Git on modified files: avoid unnecessary line-ending churn during split commits.

## Validation Results

Required validation run on 2026-04-15:

| Command | Exit | Result |
| --- | ---: | --- |
| `python -m ruff format --check .` | 1 | Failed: `tests\test_benchmark.py` would be reformatted; 96 files already formatted |
| `python -m ruff check .` | 0 | Passed: all checks passed |
| `python -m mypy src tests` | 0 | Passed: no issues found in 73 source files |
| `python -m pytest` | 0 | Passed: 174 passed, 1 skipped in 14.96s |
| `python -m qa_z benchmark --json` | 0 | Passed: 26 fixtures passed, 0 failed, overall rate 1.0 |

Targeted CLI smoke checks:

| Command | Exit | Result |
| --- | ---: | --- |
| `python -m qa_z --help` | 0 | Command surface includes core and alpha commands |
| `python -m qa_z self-inspect --help` | 0 | Help rendered |
| `python -m qa_z select-next --help` | 0 | Help rendered |
| `python -m qa_z autonomy --help` | 0 | Help rendered |
| `python -m qa_z executor-bridge --help` | 0 | Help rendered |
| `python -m qa_z repair-session --help` | 0 | Help rendered |
| `python -m qa_z github-summary --help` | 0 | Help rendered |

## Immediate Worktree Guidance

1. Do not stage generated root `.qa-z/**` or `benchmarks/results/work/**`.
2. Keep `benchmarks/results/summary.json` and `benchmarks/results/report.md`
   local by default unless intentionally freezing sample evidence.
3. Format `tests/test_benchmark.py` before the benchmark commit. Because it is untracked, this is a benchmark-commit preflight step rather than a clean standalone format-only commit.
4. Split current dirty work into the batches above before tagging an alpha baseline.
5. Treat `v0.9.8-alpha` as the release candidate for the broader accumulated
   runner, benchmark, autonomy, executor bridge, executor-result ingest, and
   live-free dry-run surface; use `v0.10.0-alpha` only if the team wants a larger
   reset point.
