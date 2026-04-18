# P6-A Self-Inspection Backlog Implementation Plan

Goal: add an artifact-driven self-inspection and improvement backlog layer for QA-Z.

## Scope

- Add `src/qa_z/self_improvement.py` for local artifact discovery, scoring, backlog merge, task selection, loop plan rendering, and loop history append.
- Add `qa-z self-inspect`, `qa-z backlog`, and `qa-z select-next` as thin CLI adapters.
- Document the new artifacts in README, artifact schema, and MVP issue tracking.
- Keep this slice artifact-only: no live model calls, no remote orchestration, and no automatic source edits.

## Evidence Sources

- `benchmarks/results/summary.json` for failed benchmark fixtures and aggregate benchmark failures.
- `.qa-z/runs/**/verify/summary.json` for verification regressions or incomplete candidate evidence.
- README and artifact-schema mismatch checks for narrow docs/schema drift.

## Validation

- `python -m pytest tests/test_self_improvement.py tests/test_cli.py -q`
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy src tests`
- `python -m pytest`
