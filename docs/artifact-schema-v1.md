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

## Repair Session Artifacts

`qa-z repair-session start --baseline-run <run>` writes:

```text
.qa-z/sessions/<session-id>/session.json
.qa-z/sessions/<session-id>/executor_guide.md
.qa-z/sessions/<session-id>/handoff/packet.json
.qa-z/sessions/<session-id>/handoff/prompt.md
.qa-z/sessions/<session-id>/handoff/handoff.json
.qa-z/sessions/<session-id>/handoff/codex.md
.qa-z/sessions/<session-id>/handoff/claude.md
```

`session.json` has:

- `kind`: `qa_z.repair_session`
- `schema_version`: `1`
- `session_id`
- `state`
- `baseline_run`
- `candidate_run`
- `session_dir`
- `handoff_dir`
- `executor_guide_path`
- `verify_summary_path`
- `verify_compare_path`
- `verify_report_path`
- `outcome_path`
- `verdict`
- `created_at`
- `updated_at`

`qa-z repair-session verify --session <session> --candidate-run <run>` writes:

```text
.qa-z/sessions/<session-id>/verify/summary.json
.qa-z/sessions/<session-id>/verify/compare.json
.qa-z/sessions/<session-id>/verify/report.md
.qa-z/sessions/<session-id>/summary.json
.qa-z/sessions/<session-id>/outcome.md
```

The session-level `summary.json` has:

- `kind`: `qa_z.repair_session_summary`
- `schema_version`: `1`
- `session_id`
- `state`
- `baseline_run`
- `candidate_run`
- `verdict`
- `repair_improved`
- `blocking_before`
- `blocking_after`
- `resolved_count`
- `remaining_issue_count`
- `new_issue_count`
- `regression_count`
- `not_comparable_count`
- paths to the nested verification artifacts

Repair sessions only package local artifacts and record the deterministic return path. They do not dispatch remote workers or call live models.

## Executor Bridge Artifacts

`qa-z executor-bridge --from-session <session>` writes:

```text
.qa-z/executor/<bridge-id>/bridge.json
.qa-z/executor/<bridge-id>/executor_guide.md
.qa-z/executor/<bridge-id>/codex.md
.qa-z/executor/<bridge-id>/claude.md
.qa-z/executor/<bridge-id>/inputs/session.json
.qa-z/executor/<bridge-id>/inputs/handoff.json
```

When the bridge is created from a loop outcome with a `repair_session` action, it also copies:

```text
.qa-z/executor/<bridge-id>/inputs/autonomy_outcome.json
```

`bridge.json` has:

- `kind`: `qa_z.executor_bridge`
- `schema_version`: `1`
- `bridge_id`
- `created_at`
- `status`: `ready_for_external_executor`
- `source_loop_id`
- `source_session_id`
- `selected_task_ids`
- `baseline_run`
- `session_dir`
- `handoff_dir`
- `bridge_dir`
- `inputs`
- `handoff_paths`
- `validation_commands`
- `safety_constraints`
- `non_goals`
- `return_contract`
- `evidence_summary`

Executor bridge artifacts package local evidence for an outside human or coding agent. They do not call Codex or Claude, mutate code, schedule work, commit, push, or post GitHub comments.

## Verification Publish Summary

`qa-z github-summary` can render local run, verify, or repair-session evidence for GitHub Actions job summaries:

```text
qa-z github-summary --from-run latest
qa-z github-summary --from-verify .qa-z/runs/<run-id>/verify/summary.json
qa-z github-summary --from-session <session-id>
```

When rendering verification evidence as JSON, the output has:

- `kind`: `qa_z.verification_publish_summary`
- `schema_version`: `1`
- `source_type`: `verify` or `repair_session`
- `source_path`
- `session_id`, when available
- `verdict`
- `repair_improved`
- `resolved_count`
- `remaining_issue_count`
- `new_issue_count`
- `regression_count`
- `not_comparable_count`
- `recommendation`

`github-summary` is a local renderer for `$GITHUB_STEP_SUMMARY`. It does not post comments, labels, checks, or annotations through the GitHub API.

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
## Self-Inspection And Backlog Artifacts

`qa-z self-inspect` writes:

```text
.qa-z/loops/latest/self_inspect.json
.qa-z/improvement/backlog.json
```

`self_inspect.json` has:

- `kind`: `qa_z.self_inspection`
- `schema_version`: integer schema marker, currently `1`
- `generated_at`
- `loop_id`
- `artifact_only`: always `true` for this local planning surface
- `candidates_total`
- `candidates`: deterministic improvement candidates with ids, categories, recommendations, priority scores, signals, and evidence
- `evidence_sources`: compact source/path pairs used during inspection
- `backlog_path`
- `summary.open_backlog_items`

`backlog.json` has:

- `kind`: `qa_z.improvement_backlog`
- `schema_version`: integer schema marker, currently `1`
- `generated_at`
- `items`: backlog entries with stable ids, status, first/last seen timestamps, recurrence counts, priority scores, recommendations, signals, and evidence
- `summary`: total, open, and closed item counts

Backlog priority is deterministic. It combines impact, likelihood, confidence, repair cost, recurrence, and grounded artifact bonuses such as benchmark failures or verification regressions. Missing optional artifacts do not create fabricated evidence.

## Selected Task And Loop Memory Artifacts

`qa-z select-next` writes:

```text
.qa-z/loops/latest/selected_tasks.json
.qa-z/loops/latest/loop_plan.md
.qa-z/loops/history.jsonl
```

`selected_tasks.json` has:

- `kind`: `qa_z.selected_tasks`
- `schema_version`: integer schema marker, currently `1`
- `generated_at`
- `loop_id`
- `selection_limit`: requested count clamped from `1` through `3`
- `selected_count`
- `selected_tasks`: selected backlog entries with rank, category, recommendation, priority score, evidence, action hint, validation command, and compact evidence
- `artifact_only`: always `true`

`loop_plan.md` is a human-readable local plan derived from selected tasks. `history.jsonl` appends one `qa_z.loop_history_entry` JSON object per selection with selected task ids, selected categories, evidence paths, and pointers to the latest selected-task and loop-plan artifacts.

Self-improvement artifacts prepare local deterministic work. They do not call live model APIs, invoke remote orchestration, or edit source code.
## Autonomy Loop Artifacts

`qa-z autonomy` writes one directory per local planning loop and mirrors the latest loop:

```text
.qa-z/loops/<loop-id>/self_inspect.json
.qa-z/loops/<loop-id>/selected_tasks.json
.qa-z/loops/<loop-id>/loop_plan.md
.qa-z/loops/<loop-id>/outcome.json
.qa-z/loops/latest/autonomy_summary.json
.qa-z/loops/latest/outcome.json
```

`autonomy_summary.json` has:

- `kind`: `qa_z.autonomy_summary`
- `schema_version`: integer schema marker, currently `1`
- `generated_at`, `run_started_at`, and `finished_at`
- `loops_requested` and `loops_completed`
- `latest_loop_id`
- `runtime_target_seconds`, `runtime_elapsed_seconds`, `runtime_remaining_seconds`, and `runtime_budget_met`
- `min_loop_seconds`
- `stop_reason`
- `outcomes`: embedded per-loop outcome objects

`outcome.json` has:

- `kind`: `qa_z.autonomy_outcome`
- `schema_version`: integer schema marker, currently `1`
- `loop_id`
- `generated_at`
- `state`: `completed` or `blocked_no_candidates`
- `state_transitions`
- `selected_task_ids`
- `evidence_used`
- `actions_prepared`: deterministic local action packets with type, task id, next recommendation, and commands
- `next_recommendations`
- `artifacts`: paths for loop-local self-inspection, selected tasks, loop plan, and outcome
- runtime fields after summary enrichment: `loop_elapsed_seconds`, `cumulative_elapsed_seconds`, `runtime_target_seconds`, `runtime_remaining_seconds`, `min_loop_seconds`, and `runtime_budget_met`

`qa-z autonomy status` reports a compact `qa_z.autonomy_status` view derived from the latest summary, latest outcome, latest selected tasks, and current backlog. Autonomy loops are local planning artifacts only. They do not start live executors, call model APIs, mutate source files, or perform remote orchestration.
