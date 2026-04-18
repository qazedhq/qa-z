# P59-P62 Operator Summary Clarity Design

## Goal

Make the human-facing `qa-z backlog` and `qa-z autonomy status` outputs focus on active work instead of making operators scan stale backlog residue or hidden session state.

## Why now

The latest loop already exposes richer action packets, but the plain-text backlog output still prints every open and closed item in one flat list, and autonomy status still hides open-session detail plus the title and recommendation behind the compact backlog ids.

## Scope

- keep JSON backlog and JSON autonomy status stable, using additive fields only
- make plain-text backlog output focus on open items and collapse closed history to a count
- enrich autonomy status top backlog items with title, recommendation, and compact evidence
- show open session details in plain-text autonomy status

## Non-goals

- no new backlog artifact schema version
- no filtering or mutation of stored backlog history
- no live execution
- no broad CLI redesign outside backlog and autonomy status

## Intended result

An operator can run `qa-z backlog` or `qa-z autonomy status` and immediately see the active work, the next recommendation, the relevant report or signal, and any open session pointers without digging through JSON first.
