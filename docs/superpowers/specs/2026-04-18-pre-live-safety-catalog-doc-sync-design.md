# Pre-Live Safety Catalog Doc Sync Design

Date: 2026-04-18

## Context

QA-Z now has two explicit safety-related catalogs:

- the six-rule frozen executor safety package catalog
- the seven-rule dry-run audit catalog, which extends the frozen package with
  the dry-run-only `executor_history_recorded` rule

README, benchmarking docs, and artifact schema docs already mention the executor
safety rule catalog, dry-run rule catalog, and safety rule count. The dedicated
`docs/pre-live-executor-safety.md` document still describes the frozen rules,
but it does not name the catalog relationship or the safety rule count. It also
says dry-run evaluates against the frozen rules without clarifying the
dry-run-only history-presence extension.

## Goal

Make `docs/pre-live-executor-safety.md` the clear source-of-truth companion for
the current safety catalog model:

- name the executor safety rule catalog
- state that it is the six-rule frozen pre-live set
- state that bridge manifests and guides expose a safety rule count
- state that the dry-run rule catalog extends the frozen package with
  `executor_history_recorded`

## Non-Goals

- Do not change executor safety package schema.
- Do not change rule ids or dry-run behavior.
- Do not change bridge manifests, result templates, ingest behavior, or
  verification behavior.
- Do not add live executor behavior, automatic edits, retries, commits, pushes,
  scheduling, or remote orchestration.

## Design

Add current-truth coverage requiring `docs/pre-live-executor-safety.md` to
contain:

- `executor safety rule catalog`
- `six-rule frozen pre-live set`
- `safety rule count`
- `dry-run rule catalog`
- `executor_history_recorded`

Then update the document's Package, Frozen Rules, and Live-Free Dry-Run sections
with a short explanation of the catalog relationship. Keep the existing rule
list intact.

## Test Strategy

1. Add current-truth assertions for the pre-live safety document.
2. Run `python -m pytest tests/test_current_truth.py -q` and confirm RED.
3. Update `docs/pre-live-executor-safety.md`.
4. Run the current-truth test and confirm GREEN.
5. Run full `python -m pytest` and full `python -m qa_z benchmark --json`.
