# Executor Result Template Placeholder Guidance Design

Date: 2026-04-18

## Context

`result_template.json` is intentionally a scaffold. It carries the placeholder
summary `Replace with executor outcome summary before ingest.`, and executor
result loading rejects that exact placeholder so a copied template cannot be
treated as completed evidence.

The bridge artifact schema documents that requirement, but the operator-facing
bridge guides and human stdout do not currently say it at the point where an
external executor is likely to act on the template.

## Goal

Expose the placeholder replacement rule in the operator-facing bridge surfaces:

- `executor_guide.md`
- `codex.md`
- `claude.md`
- non-JSON `qa-z executor-bridge` stdout

The guidance should say that the result template's placeholder summary must be
replaced before ingest or re-entry, without changing the executor result schema.

## Non-Goals

- Do not change `result_template.json` shape.
- Do not change executor-result ingest validation.
- Do not change JSON mode for `qa-z executor-bridge`.
- Do not add live executor behavior, automatic edits, retries, commits, pushes,
  scheduling, or remote orchestration.

## Design

Import `PLACEHOLDER_SUMMARY` into `src/qa_z/executor_bridge.py` and add a small
helper that returns a stable human sentence:

```text
Replace the placeholder summary before ingest: `Replace with executor outcome summary before ingest.`
```

Render that sentence in:

- `executor_guide.md` under `## Return Contract`
- `codex.md` and `claude.md` under their `## Return Contract`
- non-JSON stdout as `Template summary: replace placeholder before ingest`

This keeps the machine-readable contract unchanged while making the ingest-safe
step visible at the exact operator handoff points.

## Documentation

Update README and artifact schema docs to describe `template placeholder
guidance`. Add current-truth coverage so docs drift is caught.

## Test Strategy

1. Add bridge packaging assertions that guide, Codex, and Claude files mention
   placeholder summary replacement.
2. Add stdout assertions for the same condition.
3. Confirm focused RED.
4. Add renderer guidance and confirm focused GREEN.
5. Add current-truth docs guards, confirm RED, then update docs and confirm
   GREEN.
6. Run focused tests, full `python -m pytest`, and full
   `python -m qa_z benchmark --json`.
