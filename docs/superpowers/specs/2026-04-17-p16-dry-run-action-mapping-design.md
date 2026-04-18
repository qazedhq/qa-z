# P16 Dry-Run Action Mapping Design

## Goal

Make autonomy action packets more specific when selected backlog items come from dry-run safety evidence, so blocked or attention dry-run findings point operators at the right local command instead of a generic workflow note.

## Scope

Included:

- signal-aware autonomy action mapping for dry-run blocked and attention candidates
- session-aware `executor-result dry-run` command suggestions when evidence contains a session id
- focused autonomy tests

Excluded:

- new backlog categories
- live executor work
- retry scheduling
- GitHub publishing changes

## Design

### 1. Blocked Dry-Run Actions

When a selected task carries `executor_dry_run_blocked`, autonomy should emit:

- action type: `executor_safety_review_plan`
- commands including `python -m qa_z executor-result dry-run --session <session-id>` when the session can be recovered from evidence
- a next recommendation that explicitly mentions resolving blocked safety findings

### 2. Attention Dry-Run Actions

When a selected task carries `executor_dry_run_attention`, autonomy should emit:

- action type: `executor_safety_followup_plan`
- commands including `python -m qa_z executor-result dry-run --session <session-id>` when available
- a next recommendation that explicitly mentions reviewing attention signals before another retry

### 3. Fallback Behavior

If no session id can be recovered, keep the command template generic:

- `python -m qa_z executor-result dry-run --session <session>`

Existing workflow-gap mapping remains the fallback for tasks that do not carry dry-run severity signals.
