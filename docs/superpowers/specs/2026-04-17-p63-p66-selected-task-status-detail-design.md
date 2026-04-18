# P63-P66 Selected Task Status Detail Design

## Goal

Make `qa-z autonomy status` self-contained by carrying compact details for the latest selected tasks, not just their ids.

## Why now

`autonomy status` already shows richer prepared actions and current backlog-top-item summaries, but the selected task list itself is still only ids. That leaves a semantic gap: the latest loop selection comes from `selected_tasks.json`, while the backlog-top list comes from the current backlog and may diverge later.

## Scope

- add additive `latest_selected_task_details` to autonomy status JSON
- derive those details from the stored latest `selected_tasks.json` artifact
- reflect the compact details in the human-readable status output
- keep existing selected task ids and backlog-top-item summaries intact

## Non-goals

- no new loop artifacts
- no backlog mutation
- no live execution
- no removal of existing status fields

## Intended result

Operators can read `qa-z autonomy status --json` or the plain-text status view and see what the latest loop actually selected, with title, category, recommendation, evidence summary, and selection score, even if the live backlog later changes.
