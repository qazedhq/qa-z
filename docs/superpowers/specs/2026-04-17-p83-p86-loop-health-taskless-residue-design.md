# P83-P86 Loop Health Taskless Residue Design

## Goal

Make autonomy loop history more explicit when no task survives selection by
classifying every taskless loop as blocked and preserving the reason plus simple
before/after backlog counts.

## Problem

QA-Z already stops repeated `blocked_no_candidates` loops, but taskless loops
can still appear with `selected_tasks=[]` and a softer `completed` state when
inspection closed stale backlog items mid-loop. That makes loop history harder
to interpret and weakens loop-health follow-up.

## Scope

- Treat any taskless autonomy loop as `blocked_no_candidates`.
- Preserve additive `selection_gap_reason`.
- Preserve additive `backlog_open_count_before_inspection` and
  `backlog_open_count_after_inspection`.
- Mirror that residue in `outcome.json`, `history.jsonl`, `loop_plan.md`, and
  `qa-z autonomy status`.

## Non-Goals

- No new executor behavior.
- No backlog-scoring redesign.
- No probabilistic retry logic or scheduler changes.

## Validation

- Focused autonomy tests first.
- README/schema/current-truth sync.
- Full repo validation plus a real `qa-z autonomy --loops 1 --json` spot-check.
