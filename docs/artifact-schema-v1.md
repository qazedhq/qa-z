# QA-Z Artifact Schema v1

QA-Z writes deterministic artifacts that can be consumed by review, repair, verification, and benchmark commands without invoking an LLM.

## Run Summary

`qa-z fast` writes:

```text
.qa-z/runs/<run-id>/fast/summary.json
.qa-z/runs/<run-id>/fast/summary.md
```

`qa-z deep` writes:

```text
.qa-z/runs/<run-id>/deep/summary.json
.qa-z/runs/<run-id>/deep/summary.md
.qa-z/runs/<run-id>/deep/results.sarif
```

Required top-level `summary.json` fields:

- `schema_version`: integer schema marker. Legacy summaries use `1`; selection-aware summaries use `2`.
- `mode`: runner mode, usually `fast` or `deep`
- `contract_path`: repository-relative contract path, or `null`
- `project_root`: absolute project root used for the run
- `status`: `passed`, `failed`, `error`, or `unsupported`
- `started_at`: UTC timestamp
- `finished_at`: UTC timestamp
- `checks`: ordered list of normalized check results
- `totals`: counts for `passed`, `failed`, `skipped`, and `warning`

Optional top-level fields:

- `artifact_dir`: repository-relative artifact directory
- `contract_title`: title extracted from the active contract
- `message`: normalized runner message
- `selection`: selection metadata for schema v2 summaries
- `policy`: runner policy metadata, such as Semgrep policy controls

Each check result includes:

- `id`: configured check id
- `tool`: executable name
- `command`: executed command argv
- `kind`: check category, such as `lint`, `format`, `typecheck`, `test`, or `static-analysis`
- `status`: `passed`, `failed`, `warning`, `skipped`, or `error`
- `exit_code`: process exit code, or `null` when no process completed
- `duration_ms`: elapsed runtime in milliseconds
- `stdout_tail`: captured stdout tail
- `stderr_tail`: captured stderr tail
- `execution_mode`: `full`, `targeted`, `skipped`, or `null`
- `target_paths`: paths selected for this check
- `selection_reason`: compact reason for the execution mode
- `high_risk_reasons`: reasons that escalated selection to full execution

Optional check fields:

- `message`: normalized QA-Z message
- `error_type`: normalized error category, such as `missing_tool`
- `findings_count`: total normalized deep findings
- `blocking_findings_count`: findings that block the deep verdict
- `filtered_findings_count`: findings ignored by policy
- `filter_reasons`: count by filter reason
- `severity_summary`: count by severity
- `grouped_findings`: deduplicated finding buckets
- `findings`: active normalized findings
- `policy`: check-specific policy metadata

## Selection Metadata

Schema v2 summaries may include `selection`:

- `mode`: requested mode, usually `full` or `smart`
- `input_source`: source used for changed-file detection, such as `cli_diff`, `contract`, or `none`
- `changed_files`: normalized changed-file records
- `high_risk_reasons`: reasons the run escalated to a full scan
- `selected_checks`: all selected check ids
- `full_checks`: selected checks run without path targeting
- `targeted_checks`: selected checks run against target paths
- `skipped_checks`: checks skipped by selection policy

Legacy v1 summaries without `schema_version` or `selection` still load as schema version `1`.

## Per-Check JSON

`qa-z fast` and `qa-z deep` write one file per check to:

```text
.qa-z/runs/<run-id>/<mode>/checks/<check-id>.json
```

Each file uses the same check result shape embedded in `summary.json`.

## Deep Findings

The built-in Semgrep deep check normalizes Semgrep JSON into the check result fields above. Active findings use:

- `rule_id`
- `severity`
- `path`
- `line`
- `message`
- optional `metadata`

Grouped findings use:

- `rule_id`
- `severity`
- `path`
- `count`
- `representative_line`
- `message`

Severity policy lives under the check `policy` object. `fail_on_severity` determines which severities block the deep verdict.

## SARIF

`qa-z deep` writes SARIF 2.1.0 to:

```text
.qa-z/runs/<run-id>/deep/results.sarif
```

The SARIF log is derived from normalized active findings. When only grouped findings are available, QA-Z emits one representative SARIF result per group. SARIF run properties include:

- `qa_z_mode`
- `qa_z_status`
- `qa_z_schema_version`
- `qa_z_artifact_dir`, when available
- `qa_z_contract_path`, when available

## Review Packet

`qa-z review --from-run <run>` can write:

```text
.qa-z/runs/<run-id>/review/review.md
.qa-z/runs/<run-id>/review/review.json
```

The JSON packet includes contract context, run status, selection metadata, executed checks, failed checks, priority order, and optional deep finding context from a sibling deep summary.

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
- `run`: source run context, including optional `selection`
- `contract`: contract context used for the repair packet
- `failures`: ordered failed or errored fast checks with evidence
- `suggested_fix_order`: check ids in deterministic repair order, plus `sg_scan` when blocking deep findings exist
- `done_when`: completion criteria for the next repair loop
- `agent_prompt`: Markdown prompt body also written to `prompt.md`
- `deep`: optional deep finding context

Repair packets are generated from existing run artifacts. They do not rerun checks and they do not make LLM-only pass/fail judgments.

## Repair Handoff

`qa-z repair-prompt` also writes:

```text
.qa-z/runs/<run-id>/repair/handoff.json
.qa-z/runs/<run-id>/repair/codex.md
.qa-z/runs/<run-id>/repair/claude.md
```

`handoff.json` has:

- `kind`: `qa_z.repair_handoff`
- `schema_version`: `1`
- `generated_at`
- `project`
- `provenance`
- `repair.repair_needed`
- `repair.targets`
- `repair.affected_files`
- `repair.objectives`
- `constraints.must_follow`
- `constraints.non_goals`
- `validation.commands`
- `validation.success_criteria`
- `workflow.suggested_steps`

Handoff artifacts are local files. They package evidence and validation commands; they do not call an external model.

## Verification Artifacts

`qa-z verify` writes by default under the candidate run:

```text
.qa-z/runs/<candidate-run-id>/verify/summary.json
.qa-z/runs/<candidate-run-id>/verify/compare.json
.qa-z/runs/<candidate-run-id>/verify/report.md
```

`summary.json` has:

- `kind`: `qa_z.verify_summary`
- `schema_version`: `1`
- `repair_improved`
- `verdict`: `improved`, `unchanged`, `mixed`, `regressed`, or `verification_failed`
- `blocking_before`
- `blocking_after`
- `resolved_count`
- `remaining_issue_count`
- `new_issue_count`
- `regression_count`
- `not_comparable_count`

`compare.json` has:

- `kind`: `qa_z.verify_compare`
- `schema_version`: `1`
- baseline and candidate run ids
- baseline and candidate fast/deep status
- `verdict`
- categorized `fast_checks`
- categorized `deep_findings`
- aggregate `summary`

Verification compares deterministic artifacts only. It does not infer repair success from style or LLM judgment.


## Benchmark Summary

`qa-z benchmark` writes:

```text
benchmarks/results/summary.json
benchmarks/results/report.md
benchmarks/results/work/
```

Required `summary.json` fields:

- `kind`: `qa_z.benchmark_summary`
- `schema_version`: integer schema marker, currently `1`
- `fixtures_total`
- `fixtures_passed`
- `fixtures_failed`
- `overall_rate`
- `snapshot`: compact text such as `22/22 fixtures, overall_rate 1.0`
- `category_rates`: pass-rate buckets for detection, handoff, verify, artifact, and policy evidence
- `failed_fixtures`: fixture names with mismatched expectations
- `fixtures`: per-fixture results with `name`, `passed`, `failures`, `categories`, `actual`, and `artifacts`

Benchmark artifacts are deterministic local evidence. `benchmarks/results/work/` is scratch output and should not be committed. `summary.json` and `report.md` are generated outputs; commit them only as intentional frozen evidence with surrounding context.
