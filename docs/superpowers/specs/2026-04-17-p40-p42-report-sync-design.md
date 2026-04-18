# P40-P42 Report Sync Design

## Goal

Bring report-style planning documents back into line with the landed executor-history and dry-run provenance baseline so self-inspection stops reseeding stale follow-up work.

## Problem

`docs/reports/current-state-analysis.md` and `docs/reports/next-improvement-roadmap.md` still describe older executor-contract and ingest work as if it were the main next priority. Self-inspection reads those reports as grounded evidence, so stale wording can keep creating avoidable backlog noise.

## Scope

- rewrite current-state gaps around loop health, evidence policy, benchmark breadth, and operator diagnostics
- reorder the roadmap around active work instead of already-landed executor contract milestones
- add current-truth coverage so the reports do not drift back silently

## Non-goals

- no CLI changes
- no backlog scoring changes
- no worktree cleanup execution

## Result

Self-inspection remains report-aware, but the reports point at today’s real follow-up layers instead of replaying already-completed milestones.
