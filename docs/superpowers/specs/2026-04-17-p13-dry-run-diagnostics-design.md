# P13 Dry-Run Diagnostics And Self-Inspection Bridge Design

## Goal

Make `qa-z executor-result dry-run` more actionable by exposing stable diagnostic fields and letting self-inspection consume that dry-run evidence directly instead of only re-deriving signals from raw history.

## Scope

Included:

- additive dry-run summary fields for stable reasoning and rule-status counts
- operator-facing report improvements that explain why a verdict is `clear`, `attention_required`, or `blocked`
- self-inspection support for session-local `dry_run_summary.json`
- backlog discovery for single-attempt blocked or no-op-warning cases that already show up in dry-run output

Excluded:

- retry scheduling or redispatch
- live executor work
- benchmark contract redesign
- changing backlog categories or scoring formulas broadly

## Why This Matters

After P10 and P12, QA-Z can:

- record session-local executor-result history
- evaluate that history against the frozen safety package
- benchmark `clear`, `attention_required`, and `blocked` dry-run outcomes

But one gap remains: self-inspection still mostly reasons from `history.json` directly. That misses some already-computed dry-run signals, especially single-attempt blocked states such as a completed attempt that remains verification-blocked.

## Design

### 1. Additive Dry-Run Summary Fields

Extend `dry_run_summary.json` with:

- `verdict_reason`
- `rule_status_counts`

`verdict_reason` should be a stable machine-readable explanation such as:

- `history_clear`
- `no_recorded_attempts`
- `manual_retry_review_required`
- `completed_attempt_not_verification_clean`
- `scope_validation_failed`
- `classification_conflict_requires_review`

`rule_status_counts` should expose:

- `clear`
- `attention`
- `blocked`

This stays additive and backward compatible with the current artifact schema version.

### 2. Report Clarity

The Markdown report should expose:

- the `verdict_reason`
- a compact rule-status count line

This keeps the operator-facing report aligned with the machine summary instead of requiring the reader to infer the top-level reason from the rule list manually.

### 3. Self-Inspection Bridge

Self-inspection should look for:

- `.qa-z/sessions/<session-id>/executor_results/history.json`
- `.qa-z/sessions/<session-id>/executor_results/dry_run_summary.json`

When dry-run data exists, self-inspection should:

- include the dry-run artifact as evidence
- enrich evidence summaries with dry-run verdict and signals
- promote certain dry-run findings even when the raw history is short

### 4. Candidate Rules

Keep the existing backlog categories, but make them dry-run aware:

1. `partial_completion_gap`
   - repeated partial attempts in history
   - or dry-run signal `repeated_partial_attempts`

2. `no_op_safeguard_gap`
   - repeated no-op style attempts
   - or dry-run signal `missing_no_op_explanation`
   - or dry-run signal `repeated_no_op_attempts`

3. `workflow_gap`
   - repeated rejected attempts
   - or dry-run verdict `blocked`
   - or dry-run signals such as `completed_verify_blocked`, `scope_validation_failed`, or `validation_conflict`

This lets self-inspection react to real friction that is already visible in dry-run output, even if the session has only one recorded attempt.

## Validation

- `python -m pytest tests/test_executor_result.py -q`
- `python -m pytest tests/test_self_improvement.py -q`
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy src tests`
- `python -m pytest`

## Expected Outcome

After P13, dry-run artifacts will stop being a side report that humans read separately. They will become a structured input to QA-Z's own next-task planning, and blocked single-attempt histories will no longer fall through the cracks.
