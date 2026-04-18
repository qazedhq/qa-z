# Planning Validation Command Hints Design

Date: 2026-04-18

## Purpose

The plain planning surfaces now share deterministic action hints across
`self-inspect`, `backlog`, `select-next`, and loop plans. The remaining operator
gap is that the surfaces still say what to do in prose but do not name the next
local QA-Z command that should refresh evidence after the work.

This pass adds deterministic validation command hints to those human surfaces.
It keeps JSON artifacts unchanged and does not execute the commands.

## Scope

- Add a pure helper that maps a selected or candidate backlog item to one
  validation command string.
- Render the command on plain `qa-z self-inspect`, `qa-z backlog`, and
  `qa-z select-next`.
- Render the command in `loop_plan.md`.
- Keep `--json` outputs and persisted selected/backlog/self-inspection artifacts
  stable.
- Preserve the live-free boundary: QA-Z prints commands for operators, but does
  not run repairs, stage, commit, push, schedule, or call a model.

## Command Mapping

Known recommendations map to the command most likely to refresh deterministic
evidence after the operator finishes the work:

- `add_benchmark_fixture`: `python -m qa_z benchmark --json`
- `reduce_integration_risk`: `python -m qa_z self-inspect`
- `isolate_foundation_commit`: `python -m qa_z self-inspect`
- `audit_worktree_integration`: `python -m qa_z self-inspect`
- `improve_fallback_diversity`: `python -m qa_z autonomy --loops 1`
- `stabilize_verification_surface`: `python -m qa_z verify --baseline-run <baseline> --candidate-run <candidate>`
- `create_repair_session`: `python -m qa_z repair-session status --session <session>`

Unknown recommendations fall back to `python -m qa_z self-inspect`.

## Output Shape

Plain command output uses:

```text
  validation: python -m qa_z self-inspect
```

Loop plans use Markdown code formatting:

```text
   - validation: `python -m qa_z self-inspect`
```

## Non-Goals

- No automatic command execution.
- No new JSON fields.
- No changes to scoring, selection, backlog merge, or autonomy packet creation.
- No live executor integration.

## Test Strategy

- Add helper tests for closure and benchmark recommendations.
- Extend CLI renderer tests for `self-inspect`, `backlog`, and `select-next`.
- Extend loop-plan test coverage.
- Verify the tests fail before implementation.
- Run focused tests, then full alpha gates.

## Documentation

Update README, artifact schema, and current reports to say human planning
surfaces now include deterministic validation command hints while JSON artifacts
remain unchanged.
