# Executor Bridge Stdout Return Pointers Design

Date: 2026-04-18

## Context

Executor bridge packages now include a complete machine-readable manifest, a
result template, executor-facing guides, copied safety artifacts, and a safety
rule count. The guide files expose enough detail once opened.

The non-JSON `qa-z executor-bridge` stdout is still sparse. It points to the
bridge directory, source session, handoff, and executor guide, but it does not
surface the bridge-local result template, expected result artifact, copied
safety package, safety rule count, or exact verification command. That leaves a
small operator gap at the moment immediately after package creation.

## Goal

Make the human stdout for `qa-z executor-bridge` a useful first handoff screen
without changing the manifest or JSON mode.

The stdout should include:

- bridge directory
- source session
- handoff path
- executor guide path
- result template path
- expected result artifact path
- copied safety package Markdown path
- safety rule count
- verify command

## Non-Goals

- Do not change `--json` output.
- Do not change bridge package layout.
- Do not change executor-result schema or ingest behavior.
- Do not add live executor behavior, automatic edits, retries, commits, pushes,
  scheduling, or remote orchestration.

## Design

Update `render_bridge_stdout()` in `src/qa_z/executor_bridge.py` to render
additional fields already present in the manifest:

```text
Result template: <return_contract.result_template_path>
Expected result: <return_contract.expected_result_artifact>
Safety package: <safety_package.policy_markdown>
Safety rule count: <bridge_safety_rule_count(manifest)>
Verify command: <formatted return_contract.verify_command>
```

The renderer should preserve the existing first line and existing path labels
so current operator muscle memory still works. If `verify_command` is absent,
omit that line rather than inventing a command.

## Documentation

Update README and artifact schema docs to describe the new bridge stdout return
pointers. Add a current-truth guard for the phrase `bridge stdout return
pointers`.

## Test Strategy

1. Add a CLI test for non-JSON `executor-bridge` stdout.
2. Confirm RED because stdout lacks result, safety, and verify pointers.
3. Update `render_bridge_stdout()`.
4. Confirm the focused CLI/bridge test passes.
5. Add current-truth docs guards and confirm RED.
6. Update README and schema docs, then confirm GREEN.
7. Run focused tests, full `python -m pytest`, and full
   `python -m qa_z benchmark --json`.
