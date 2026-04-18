# Executor Operator Diagnostics Plan

Date: 2026-04-17

## Phase 1: Pin The Contract With Tests

- Add dry-run logic tests for `operator_summary` and `recommended_actions`.
- Cover repeated partial, scope validation, validation conflict plus no-op gaps,
  completed verification blocking, and no recorded attempts.
- Add integration assertions for CLI dry-run output and persisted reports.

## Phase 2: Propagate Through Session Surfaces

- Include dry-run operator diagnostics in `repair-session status` human output.
- Include the same fields in `repair-session status --json`.
- Preserve the fields in completed session `summary.json` and `outcome.md`.
- Keep old materialized dry-run summaries valid by treating missing fields as
  optional.

## Phase 3: Publish Surface Parity

- Extend `SessionPublishSummary` with operator summary and recommended actions.
- Prefer completed session summary fields, falling back to synthesized dry-run
  summaries when needed.
- Render the fields in GitHub-summary-facing Markdown.

## Phase 4: Documentation Sync

- Update README dry-run and GitHub-summary sections.
- Update artifact schema docs for the new fields.
- Update current-state and roadmap reports so operator diagnostics is recorded
  as a first pass rather than a missing surface.
- Add current-truth assertions for the docs.

## Phase 5: Verification

- Run targeted tests around dry-run, repair-session, publish, and current-truth.
- Run `python -m pytest`.
- Run the benchmark corpus.
