# Executor Bridge Guide Safety Count Design

Date: 2026-04-18

## Context

Executor bridge manifests now expose `safety_package.rule_count`, derived from
the copied safety package's ordered `rule_ids`. That makes the machine-readable
bridge contract easier to audit.

The operator-facing bridge guides still only point at `executor_safety.md`.
Someone reading `executor_guide.md`, `codex.md`, or `claude.md` must open
another file or inspect `bridge.json` to confirm how many frozen safety rules
were copied into the package.

## Goal

Expose the safety package rule count in every executor-facing bridge guide:

- `executor_guide.md`
- `codex.md`
- `claude.md`

The value must come from the bridge manifest's existing `safety_package`
summary. It should stay additive, deterministic, and live-free.

## Non-Goals

- Do not change the executor safety package schema.
- Do not change the bridge manifest schema beyond the already-landed
  `safety_package.rule_count`.
- Do not change rule ids, rule text, or safety package layout.
- Do not add live executor behavior, retries, scheduling, commits, pushes, or
  remote orchestration.

## Design

Add a small renderer helper in `src/qa_z/executor_bridge.py` that reads the
manifest safety package and returns a displayable count. Prefer
`safety_package.rule_count` when present, and fall back to `len(rule_ids)` for
defensive rendering of older in-memory shapes.

Render this line in the human bridge guide's `## Safety Package` section:

```text
- Safety rule count: `<count>`
```

Render the same count near the safety package path in both executor-specific
wrappers:

```text
- Safety rule count: `<count>`
```

This keeps the machine-readable manifest as the source of truth while making the
operator-facing documents easier to audit.

## Documentation

Update the public bridge description and artifact schema docs so they state that
executor-facing guides include the safety rule count.

Add current-truth coverage for `guide safety rule count` so future docs drift is
caught.

## Test Strategy

1. Add assertions to the bridge packaging test that `executor_guide.md`,
   `codex.md`, and `claude.md` contain the expected safety rule count.
2. Run the focused bridge test and confirm RED because the guide text is absent.
3. Add the renderer helper and guide lines.
4. Run the focused bridge test and confirm GREEN.
5. Add current-truth docs guards and confirm RED.
6. Update docs and confirm GREEN.
7. Run focused tests, full `python -m pytest`, and full
   `python -m qa_z benchmark --json`.
