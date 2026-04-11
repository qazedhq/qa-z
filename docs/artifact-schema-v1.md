# QA-Z Artifact Schema v1

QA-Z v0.1.0-alpha writes deterministic artifacts that can be consumed by review and repair commands without invoking an LLM.

## Fast Summary

`qa-z fast` writes `summary.json` to:

```text
.qa-z/runs/<run-id>/fast/summary.json
```

Required top-level fields:

- `schema_version`: integer schema marker, currently `1`
- `mode`: runner mode, currently `fast`
- `contract_path`: repository-relative contract path, or `null`
- `project_root`: absolute project root used for the run
- `status`: `passed`, `failed`, `error`, or `unsupported`
- `started_at`: UTC timestamp
- `finished_at`: UTC timestamp
- `artifact_dir`: repository-relative fast artifact directory
- `checks`: ordered list of normalized check results
- `totals`: counts for `passed`, `failed`, `skipped`, and `warning`

Each check result includes:

- `id`: configured check id
- `tool`: executable name
- `command`: executed command argv
- `kind`: check category, such as `lint`, `format`, `typecheck`, or `test`
- `status`: `passed`, `failed`, `warning`, `skipped`, or `error`
- `exit_code`: process exit code, or `null` when no process completed
- `duration_ms`: elapsed runtime in milliseconds
- `stdout_tail`: captured stdout tail
- `stderr_tail`: captured stderr tail

Optional check fields:

- `message`: normalized QA-Z message
- `error_type`: normalized error category, such as `missing_tool`

## Fast Markdown Summary

`qa-z fast` writes `summary.md` next to `summary.json`. It is the human-readable companion for the same run and is not the source of truth for machine consumers.

## Per-Check JSON

`qa-z fast` writes one file per check to:

```text
.qa-z/runs/<run-id>/fast/checks/<check-id>.json
```

Each file uses the same check result shape embedded in `summary.json`.

## Repair Packet

`qa-z repair-prompt --from-run <run>` writes:

```text
.qa-z/runs/<run-id>/repair/packet.json
.qa-z/runs/<run-id>/repair/prompt.md
```

Required `packet.json` fields:

- `version`: integer repair packet schema marker, currently `1`
- `generated_at`: UTC timestamp
- `repair_needed`: boolean
- `run`: run context copied from the source summary
- `contract`: contract context used for the repair packet
- `failures`: ordered failed or errored checks with evidence
- `suggested_fix_order`: check ids in deterministic repair order
- `done_when`: completion criteria for the next repair loop
- `agent_prompt`: Markdown prompt body also written to `prompt.md`

Repair packets are generated from existing run artifacts. They do not rerun checks and they do not make LLM-only pass/fail judgments.
