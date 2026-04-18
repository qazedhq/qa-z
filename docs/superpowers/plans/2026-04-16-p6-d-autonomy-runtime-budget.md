# P6-D Autonomy Runtime Budget Implementation Plan

Goal: add local autonomy planning loops that repeatedly run self-inspection and task selection while recording per-loop outcome artifacts and runtime-budget evidence.

## Scope

- Add `src/qa_z/autonomy.py` for local inspect/select/plan/record loops.
- Add `qa-z autonomy` and `qa-z autonomy status` CLI surfaces.
- Persist loop-local artifacts under `.qa-z/loops/<loop-id>/` and latest mirrors under `.qa-z/loops/latest/`.
- Record runtime target, elapsed, remaining, minimum-loop, and budget-met fields in summary, outcome, and history surfaces.
- Keep the workflow artifact-only: no live model calls, no remote orchestration, no external repair dispatch, and no source edits.

## Validation

- `python -m pytest tests/test_autonomy.py tests/test_cli.py -q`
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy src tests`
- `python -m pytest`
