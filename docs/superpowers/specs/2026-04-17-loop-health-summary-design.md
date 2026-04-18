# Loop Health Summary Design

## Goal

Make autonomy taskless-loop evidence readable from the saved outcome, history, plan, and status surfaces without requiring operators to mentally combine several scattered fields.

## Problem

Autonomy already records `selection_gap_reason` plus open backlog counts before and after inspection. That protects against silent empty loops, but the evidence is still too low-level. Operators have to infer whether a loop was genuinely empty, whether self-inspection closed stale backlog residue, whether fallback work was selected, or whether the run stopped early because repeated blocked loops exhausted useful work.

## Chosen Approach

Add a compact `loop_health` object to each autonomy outcome and mirror it into loop history and status.

The object will contain:

- `classification`: `selected`, `fallback_selected`, or `taskless`
- `selected_count`
- `taskless`
- `fallback_selected`
- `selection_gap_reason`
- `backlog_open_count_before_inspection`
- `backlog_open_count_after_inspection`
- `stale_open_items_closed`
- `summary`

`run_autonomy` will also write a summary-level `stop_reason`:

- `requested_loops_and_runtime_met`
- `repeated_blocked_no_candidates`

This keeps the existing fields for compatibility while giving operators one deterministic place to read loop health.

## Alternatives Considered

### Only Improve Text Rendering

Human output would improve, but JSON consumers would still need to infer meaning from scattered fields.

### Add A Separate Loop Health Artifact

That would be heavier than needed. The existing `outcome.json`, history line, and status object are the right surfaces for this alpha hardening pass.

### Compact Object In Existing Artifacts

This is the selected path. It is additive, deterministic, and small.

## Data Flow

`run_autonomy_loop()` computes `loop_health` after selection state is known. It writes the object into `outcome.json`, passes it into `render_autonomy_loop_plan()`, mirrors it into the latest outcome, and then `update_history_entry()` copies it into `.qa-z/loops/history.jsonl`.

`load_autonomy_status()` exposes the latest object as `latest_loop_health`. `render_autonomy_status()` prints its classification and summary before the existing selected-task detail section.

`run_autonomy()` records why the run stopped. If repeated `blocked_no_candidates` loops hit the deterministic cap before the runtime budget is met, the summary says `stop_reason: repeated_blocked_no_candidates`.

## Non-Goals

- no new command
- no live executor behavior
- no change to selection scoring
- no change to the blocked-loop cap
- no deletion or cleanup of existing loop history

## Tests

Add tests that prove:

- empty-evidence loops write `loop_health.classification == taskless`
- stale-backlog closures report `stale_open_items_closed`
- history and status preserve the latest loop-health object
- human status and loop plan render the compact loop-health summary
- autonomy summary records `stop_reason == repeated_blocked_no_candidates` when the blocked-loop cap stops the run early
