# Repair Session Bridge Return Doc Sync Design

Date: 2026-04-18

## Context

Recent executor-bridge hardening made the bridge package more operator-friendly:

- non-JSON `qa-z executor-bridge` stdout now points to the result template,
  expected result artifact, copied safety package, safety rule count, and verify
  command
- executor-facing guides now remind operators to replace the scaffolded result
  template summary before ingest

README and artifact schema docs describe those contracts. `docs/repair-sessions.md`
still describes the older bridge flow and does not mention the stdout return
pointers or template placeholder guidance.

## Goal

Keep `docs/repair-sessions.md` aligned with the current bridge return path so a
reader following the repair-session workflow sees the same operator guidance as
README and the schema docs.

## Non-Goals

- Do not change CLI behavior.
- Do not change bridge manifests, result templates, ingest behavior, or dry-run
  behavior.
- Do not add live executor behavior, automatic edits, retries, commits, pushes,
  scheduling, or remote orchestration.

## Design

Add current-truth coverage that requires `docs/repair-sessions.md` to mention:

- `bridge stdout return pointers`
- `template placeholder guidance`

Then update the Executor Bridge section in `docs/repair-sessions.md` to state
that human stdout includes the bridge return pointers and that guides/stdout
tell operators to replace the scaffolded result summary before ingest.

## Test Strategy

1. Add current-truth assertions for the two phrases in `docs/repair-sessions.md`.
2. Run `python -m pytest tests/test_current_truth.py -q` and confirm RED.
3. Update `docs/repair-sessions.md`.
4. Run the current-truth test and confirm GREEN.
5. Run focused current-truth tests, full `python -m pytest`, and full
   `python -m qa_z benchmark --json`.
