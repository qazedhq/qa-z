# P71-P74 Autonomy Selection Penalty Visibility Design

## Goal

Keep the latest autonomy status view aligned with the richer selected-task
residue already available from `selected_tasks.json` and the human
`qa-z select-next` output.

## Problem

After P67-P70, operators can see selection penalties and penalty reasons on
`qa-z select-next`, but `qa-z autonomy status` still drops that same residue
from `latest_selected_task_details`. That makes the post-loop status view less
informative than the selection surface that produced it.

## Scope

- Preserve additive `selection_penalty` and `selection_penalty_reasons` on
  `latest_selected_task_details`.
- Render that residue in human `qa-z autonomy status` output when present.
- Keep the autonomy status contract additive and backward compatible.

## Non-Goals

- No changes to selection scoring.
- No new loop artifacts.
- No changes to prepared action logic or executor flows.

## Validation

- Targeted autonomy/status tests first.
- README/schema/current-truth sync.
- Full repository validation afterwards.
