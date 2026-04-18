# Generated Versus Frozen Evidence Policy

QA-Z treats runtime evidence as useful, but not automatically source-like. This policy defines which generated artifacts stay local and which artifacts may be committed only when they are intentionally frozen as review evidence.

## Local Runtime State

Root `.qa-z/**` is generated runtime state. It contains local run, session, loop, executor bridge, executor-result, and self-inspection artifacts. It is ignored at the repository root and should stay local unless a future fixture or documentation task explicitly copies a small sample elsewhere.

`benchmarks/results/work/**` is disposable benchmark scratch output. The benchmark runner copies fixture repositories there before execution, and those workspaces should not be committed.

## Local By Default Benchmark Results

`benchmarks/results/summary.json` and `benchmarks/results/report.md` are generated benchmark outputs. They are local by default.

Commit these files only as intentional frozen evidence. A frozen benchmark result should be paired with surrounding documentation that explains why that exact result is being preserved, which command produced it, and what date or baseline it represents.

## Fixture-Local Evidence

`benchmarks/fixtures/**/repo/.qa-z/**` is allowed as fixture-local deterministic benchmark input. These files are not root runtime state; they are part of a committed test vector and should stay small enough for review.

## Self-Inspection Rule

Self-inspection treats the generated-artifact policy as explicit only when both surfaces are present:

- `.gitignore` covers root `.qa-z/`, `benchmarks/results/work/`, `benchmarks/results/summary.json`, and `benchmarks/results/report.md`
- this document describes the local by default and intentional frozen evidence rules

When both surfaces are present and no live runtime artifact paths are dirty, stale report language alone should not keep re-promoting generated-versus-frozen evidence policy work.

## Operator Checklist

Before source integration:

- do not stage root `.qa-z/**`
- do not stage `benchmarks/results/work/**`
- treat `benchmarks/results/summary.json` and `benchmarks/results/report.md` as local by default
- commit benchmark result files only as intentional frozen evidence with clear context
- keep fixture-local `.qa-z/**` only under `benchmarks/fixtures/**/repo/`
