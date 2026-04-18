# Self-Inspect Candidate Summaries Design

Date: 2026-04-18

## Purpose

Plain `qa-z self-inspect` currently reports artifact paths and a candidate count.
Operators must open `self_inspect.json` or run `qa-z backlog` to see what was
found. Now that `select-next` and `backlog` both show deterministic action
hints, the inspection step should also expose the top candidates in the same
operator language.

This pass adds concise top-candidate summaries to plain `qa-z self-inspect`
output. It keeps the JSON report shape unchanged and does not change scoring,
selection, backlog merge behavior, or any live-free boundary.

## Scope

- Add a pure renderer for plain self-inspection stdout.
- Show up to the top three candidates by `priority_score`, with candidate id as
  a stable tie-breaker.
- For each candidate, show id/title, recommendation, deterministic action hint,
  priority score, and compact evidence summary.
- Print `Top candidates: none` when no candidates were discovered.
- Keep `qa-z self-inspect --json` unchanged.
- Reuse existing `selected_task_action_hint()` and
  `compact_backlog_evidence_summary()` helpers so wording stays aligned with
  `backlog`, `select-next`, and loop plans.

## Non-Goals

- No new JSON fields.
- No change to candidate scoring or backlog merge.
- No automatic task selection.
- No code repair, live executor call, schedule, staging, commit, push, or GitHub
  posting.

## Behavior

Plain output becomes:

```text
qa-z self-inspect: wrote self-improvement artifacts
Self inspection: .qa-z/loops/latest/self_inspect.json
Backlog: .qa-z/improvement/backlog.json
Candidates: 3
Top candidates:
- worktree_risk-dirty-worktree: Reduce dirty worktree integration risk
  recommendation: reduce_integration_risk
  action: inspect the dirty worktree and separate generated artifacts, then rerun self-inspection
  priority score: 65
  evidence: git_status: modified=25; untracked=346; staged=0
```

The section is intentionally a summary. Operators can still use
`qa-z self-inspect --json` or `qa-z backlog --json` for full residue.

## Test Strategy

- Add a unit-style CLI rendering test for `render_self_inspect_stdout()`.
- Add or update a plain `self-inspect` CLI test to assert top-candidate detail.
- Verify the tests fail before implementation.
- Implement the minimal renderer and handler call.
- Run focused CLI/current-truth tests, then full alpha gates.

## Documentation

Update README, artifact schema, and current reports to state that plain
`self-inspect` now prints compact top-candidate summaries with action hints,
while the JSON artifact remains the authoritative full report.
