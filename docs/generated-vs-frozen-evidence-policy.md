# Generated Versus Frozen Evidence Policy

QA-Z treats runtime evidence as useful, but not automatically source-like. This policy defines which generated artifacts stay local and which artifacts may be committed only when they are intentionally frozen as review evidence.

## Local Runtime State

Root `.qa-z/**` is generated runtime state. It contains local run, session, loop, executor bridge, executor-result, and self-inspection artifacts. It is ignored at the repository root and should stay local unless a future fixture or documentation task explicitly copies a small sample elsewhere.

Some tool caches also stay local. For example, `mypy.ini` pins the mypy cache
to `$TEMP/qa-z-mypy-cache` on Windows so compiled mypy can type-check this
workspace without crashing on a workspace-local cache path, and `pyproject.toml`
pins Ruff to `~/AppData/Local/Temp/qa-z-ruff-cache` so direct `ruff` runs do
not depend on a broken workspace-local cache location.

Other generated tool outputs are local-only runtime artifacts: `build/**`,
`dist/**`, `src/qa_z.egg-info/**`, and cache trees such as `__pycache__/`,
`.pytest_cache/`, `.mypy_cache/`, `.mypy_cache_safe/`, `.ruff_cache/`, and
`.ruff_cache_safe/`.
These are operator/runtime artifacts, not review evidence, and should not be
treated as intentionally freezable benchmark evidence.

Literal `%TEMP%/**` directories, root `/tmp_*` scratch files or directories,
and benchmark lock probes under `/benchmarks/minlock-*` are also local-only
runtime artifacts. They can appear when a Windows command uses CMD-style
environment syntax in PowerShell, for example `%TEMP%/qa-z-...`, or when a local
probe leaves scratch output behind, and should be cleaned rather than reviewed
as source-like repository changes.

`benchmarks/results/work/**` is disposable benchmark scratch output. The benchmark runner copies fixture repositories there before execution, and those workspaces should not be committed.

## Local By Default Benchmark Results

`benchmarks/results/summary.json` and `benchmarks/results/report.md` are generated benchmark outputs. They are local by default.

Snapshot directories matching `benchmarks/results-*` are also local-by-default benchmark evidence. They stay local unless an operator intentionally freezes one as evidence with surrounding context that explains the exact command, date, and reason it is being kept.

Commit these files only as intentional frozen evidence. A frozen benchmark result should be paired with surrounding documentation that explains why that exact result is being preserved, which command produced it, and what date or baseline it represents.
`python scripts/runtime_artifact_cleanup.py` reports these benchmark paths as review-only local-by-default roots, and `--apply` deletes only local-only runtime artifacts automatically. Cleanup discovery now reuses the same generated-policy roots that the strict worktree helper reports, so `build/**`, `dist/**`, `src/qa_z.egg-info/**`, cache trees such as `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.mypy_cache_safe/`, `.ruff_cache/`, `.ruff_cache_safe/`, literal `%TEMP%/**` scratch roots, root `.qa-z/**`, and `benchmarks/results/work/**` can all surface as deterministic local-only cleanup candidates without widening benchmark evidence deletion. Local-by-default benchmark results stay review-only until an operator decides whether they remain local or are intentionally frozen as evidence.

## Fixture-Local Evidence

`benchmarks/fixtures/**/repo/.qa-z/**` is allowed as fixture-local deterministic benchmark input. These files are not root runtime state; they are part of a committed test vector and should stay small enough for review.

## Self-Inspection Rule

Self-inspection treats the generated-artifact policy as explicit only when both surfaces are present:

- `.gitignore` covers root `.qa-z/`, safe cache roots `.mypy_cache_safe/` and `.ruff_cache_safe/`, literal `%TEMP%/` workspace scratch roots, root `/tmp_*` scratch probes, `/benchmarks/minlock-*` benchmark lock probes, `benchmarks/results/work/`, `benchmarks/results-*`, `benchmarks/results/summary.json`, and `benchmarks/results/report.md`
- this document describes the local by default and intentional frozen evidence rules

When both surfaces are present and no live runtime artifact paths are dirty, stale report language alone should not keep re-promoting generated-versus-frozen evidence policy work.

## Operator Checklist

Before source integration:

- preview policy-managed cleanup roots with `python scripts/runtime_artifact_cleanup.py --json`
- apply cleanup only when the dry-run output looks correct with `python scripts/runtime_artifact_cleanup.py --apply --json`
- the cleanup script reports `benchmarks/results/**` and `benchmarks/results-*` as review-only local-by-default roots and does not auto-delete them in apply mode
- `--apply` deletes only local-only runtime artifacts automatically
- the cleanup script skips candidate roots that still contain tracked files so intentional frozen evidence is not deleted, and JSON/human output includes a `reason` for `review_local_by_default`, `skipped_tracked`, `planned`, and `deleted` roots
- do not stage root `.qa-z/**`
- do not stage literal `%TEMP%/**` workspace scratch roots
- do not stage root `/tmp_*` scratch probes
- do not stage `/benchmarks/minlock-*` benchmark lock probes
- do not stage `benchmarks/results/work/**`
- do not stage local snapshot directories matching `benchmarks/results-*` unless they are intentionally frozen evidence
- treat `benchmarks/results/summary.json` and `benchmarks/results/report.md` as local by default
- commit benchmark result files only as intentional frozen evidence with clear context
- keep fixture-local `.qa-z/**` only under `benchmarks/fixtures/**/repo/`
