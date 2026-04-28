# QA-Z Artifact Schema v1/v2

QA-Z writes deterministic artifacts that can be consumed by review and repair commands without invoking an LLM.

`summary.json` v1 remains loadable when `schema_version` is missing or set to `1`. New fast and deep runner writes use `schema_version: 2`; fast and deep summaries include selection metadata when selection is resolved. Deep `sg_scan` checks may also include Semgrep finding metadata.

## Latest Run Manifest

Each successful `qa-z fast` artifact write updates:

```text
.qa-z/runs/latest-run.json
```

The manifest contains:

- `run_dir`: repository-relative path to the latest run directory when the run lives under the repository, or an absolute path otherwise

Follow-up commands such as `qa-z review --from-run latest`, `qa-z repair-prompt --from-run latest`, `qa-z github-summary --from-run latest`, and `qa-z deep` prefer this manifest. If it points at stale data, QA-Z falls back to scanning the configured runs directory for `*/fast/summary.json`. `qa-z deep` consumes the manifest for attachment but does not update it.

## Fast And Deep Summaries

`qa-z fast` writes `summary.json` to:

```text
.qa-z/runs/<run-id>/fast/summary.json
```

`qa-z deep` writes `summary.json` to:

```text
.qa-z/runs/<run-id>/deep/summary.json
```

Required top-level fields:

- `schema_version`: integer schema marker; v2 writers emit `2`
- `mode`: runner mode, currently `fast` or `deep`
- `contract_path`: repository-relative contract path, or `null`
- `project_root`: absolute project root used for the run
- `status`: `passed`, `failed`, `error`, or `unsupported`
- `started_at`: UTC timestamp
- `finished_at`: UTC timestamp
- `artifact_dir`: repository-relative runner artifact directory
- `selection`: v2 selection metadata object, or `null`
- `policy`: optional deep policy metadata when the runner records policy-driven behavior
- `run_resolution`: optional deep metadata describing whether the run attached to an existing fast run or wrote a standalone deep run
- `checks`: ordered list of normalized check results
- `totals`: counts for `passed`, `failed`, `skipped`, and `warning`

The v2 `selection` object includes:

- `mode`: `full` or `smart`
- `input_source`: `cli_diff`, `contract`, or `none`
- `changed_files`: structured changed-file entries
- `high_risk_reasons`: reasons that forced full execution
- `selected_checks`: checks selected for execution
- `full_checks`: checks run in full mode
- `targeted_checks`: checks run against target paths
- `skipped_checks`: checks skipped by selection

Each changed-file entry includes:

- `path`: current repository-relative path
- `old_path`: previous path for modified/deleted/renamed files, or `null`
- `status`: `added`, `modified`, `deleted`, or `renamed`
- `additions`: added line count from the diff
- `deletions`: deleted line count from the diff
- `language`: `python`, `typescript`, `markdown`, `toml`, `yaml`, `json`, or `other`
- `kind`: `source`, `test`, `config`, `docs`, or `other`

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
- `execution_mode`: v2 execution mode, `full`, `targeted`, `skipped`, or `null`
- `target_paths`: v2 target paths used for targeted execution
- `selection_reason`: v2 human-readable selection reason, or `null`
- `high_risk_reasons`: v2 reasons that forced full execution for this check

Optional check fields:

- `message`: normalized QA-Z message
- `error_type`: normalized error category, such as `missing_tool`
- `findings_count`: total Semgrep finding count before suppression for `sg_scan`
- `blocking_findings_count`: Semgrep findings that match `semgrep.fail_on_severity` after suppression
- `filtered_findings_count`: Semgrep findings removed by path or rule suppression
- `filter_reasons`: filtered finding counts keyed by reason, currently `excluded_path` or `ignored_rule`
- `severity_summary`: active Semgrep finding counts keyed by severity after suppression
- `grouped_findings`: deduped Semgrep findings grouped by `rule_id`, `path`, and `severity`
- `findings`: active normalized Semgrep findings with `rule_id`, `severity`, `path`, `line`, and `message`
- `scan_warning_count`: non-blocking Semgrep scan-quality warning count, such as taint-analysis timeouts
- `scan_warnings`: normalized Semgrep scan-quality warnings with `error_type`, `severity`, `message`, and optional `path`/`line`
- `policy`: Semgrep policy used by the check, including `config`, `fail_on_severity`, `ignore_rules`, and `exclude_paths`

When `sg_scan` is configured, `qa-z deep` runs Semgrep, parses JSON from stdout, applies configured path/rule suppression, groups active findings, and marks the check `failed` only when at least one active finding matches `semgrep.fail_on_severity`. Findings below the threshold remain visible in artifacts and summaries without blocking the run. Semgrep scan-quality warnings remain non-blocking but are surfaced through `scan_warning_count`, `scan_warnings`, and summary-level `diagnostics.scan_quality` instead of being available only in stdout tails. In smart-selection mode, docs-only changes produce a skipped `sg_scan`, source/test changes append target paths to the configured Semgrep command, and high-risk or ambiguous changes run the configured full command. If Semgrep fails before producing valid JSON, QA-Z still writes `summary.json`, `summary.md`, and the per-check artifact with subprocess evidence; invalid custom Semgrep config is reported as an `error`. When no deep checks are configured, deep writes an empty `checks` list with `status: passed` as a skeleton artifact.

Deep v2 summaries include `run_resolution` with:

- `source`: `latest`, `from_run`, `output_dir`, or `new_run`
- `attached_to_fast_run`: `true` when deep evidence was written beside a fast run
- `run_dir`: repository-relative or absolute run directory
- `deep_dir`: repository-relative or absolute deep artifact directory
- `fast_summary_path`: source fast summary path when attached, otherwise `null`

Deep v2 summaries may also include `diagnostics.scan_quality` when non-blocking
scanner warnings were observed:

- `status`: currently `warning`
- `warning_count`: aggregate warning count across deep checks
- `warning_types`: unique warning types such as `Fixpoint timeout`
- `warning_paths`: unique warning paths when Semgrep reports file-level context
- `check_ids`: deep check ids that emitted scan-quality warnings
- `warning_paths`: unique normalized paths associated with warnings
- `check_ids`: deep check ids that emitted scan-quality warnings

## Markdown Summary

`qa-z fast` and `qa-z deep` write `summary.md` next to `summary.json`. It is the human-readable companion for the same run and is not the source of truth for machine consumers.

## Per-Check JSON

`qa-z fast` writes one file per check to:

```text
.qa-z/runs/<run-id>/fast/checks/<check-id>.json
```

`qa-z deep` writes one file per executed check to:

```text
.qa-z/runs/<run-id>/deep/checks/<check-id>.json
```

Each file uses the same check result shape embedded in `summary.json`. A configured Semgrep run writes `deep/checks/sg_scan.json`; a skeleton deep run without checks still creates the `deep/checks/` directory without per-check files.

## SARIF

`qa-z deep` writes a SARIF 2.1.0 artifact to:

```text
.qa-z/runs/<run-id>/deep/results.sarif
```

Passing `--sarif-output <path>` writes an additional copy at that path. SARIF output is additive; `summary.json`, `summary.md`, and per-check JSON keep their existing shapes.

The SARIF reporter consumes normalized deep findings already present on `RunSummary.checks`. For current Semgrep-backed `sg_scan` checks, each active finding becomes one SARIF result with:

- `ruleId`: normalized `rule_id`
- `level`: `error` for `ERROR`/high severities, `warning` for warning/medium severities, `note` for info/low severities, and `warning` for unknown values
- `message.text`: normalized finding message, or the rule id when no message exists
- `locations[].physicalLocation.artifactLocation.uri`: slash-normalized repository-relative path when available
- `locations[].physicalLocation.region.startLine`: normalized line number when available
- `properties`: QA-Z check id, check status, and original severity

If an artifact only contains `grouped_findings` and no active `findings`, QA-Z emits one representative SARIF result per group using `representative_line` and records `qa_z_grouped_count` in result properties. Empty deep runs still produce valid SARIF with an empty `results` list.

## Repair Packet

`qa-z repair-prompt --from-run <run>` writes:

```text
.qa-z/runs/<run-id>/repair/packet.json
.qa-z/runs/<run-id>/repair/prompt.md
.qa-z/runs/<run-id>/repair/handoff.json
.qa-z/runs/<run-id>/repair/codex.md
.qa-z/runs/<run-id>/repair/claude.md
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

Optional repair fields:

- `deep`: compact sibling deep summary context when `.qa-z/runs/<run-id>/deep/summary.json` exists, including Semgrep finding counts, severity summary, highest severity, affected files, target paths, and top findings

Repair packets are generated from existing run artifacts. They do not rerun checks and they do not make LLM-only pass/fail judgments. If blocking deep findings exist, `repair_needed` becomes `true` even when fast checks passed; non-blocking deep findings remain visible in summaries without becoming repair requirements.

## Repair Handoff

`handoff.json` is the normalized executor-facing repair contract. It is generated from the same fast summary, optional sibling deep summary, and contract context used by `packet.json`, but it separates core data from adapter presentation text.

Required top-level fields:

- `kind`: stable artifact kind, currently `qa_z.repair_handoff`
- `schema_version`: integer handoff schema marker, currently `1`
- `generated_at`: UTC timestamp copied from the repair packet generation
- `project`: repository context QA-Z knows, including the source summary mode and project root
- `provenance`: source artifact pointers, including run directory, fast summary path, optional deep summary path, contract path, source status, and run timestamps
- `repair`: normalized repair requirements
- `constraints`: required constraints and non-goals for executor safety
- `validation`: exact commands and success criteria for the post-repair verification loop
- `workflow`: suggested deterministic workflow steps

The `repair` object includes:

- `repair_needed`: boolean carried from the repair packet
- `targets`: ordered repair targets selected from failed fast checks and blocking deep findings
- `affected_files`: first-seen ordered file list derived from selected targets
- `objectives`: concise repair objectives derived from selected targets

Each repair target includes:

- `id`: stable target id, such as `check:py_type` or `deep:<rule_id>:<path>`
- `source`: `fast_check` or `deep_finding`
- `severity`: `blocking` for failed fast checks or the normalized deep finding severity
- `title`: short target label
- `rationale`: QA-Z evidence summary or finding message
- `objective`: concise repair objective
- `affected_files`: target-specific file list

Optional target fields:

- `command`: recheck command for failed fast checks
- `evidence`: captured stdout/stderr tail for failed fast checks
- `location`: path or path:line for deep findings
- `occurrences`: grouped finding count when available

Deep repair targets are selected from blocking findings only. When grouped findings are present, QA-Z uses grouped findings and filters them by `semgrep.fail_on_severity`; non-blocking grouped findings remain visible in other summaries but are not handoff repair targets. When grouped findings are absent, QA-Z applies the same blocking-severity filter to top findings.

The `validation.commands` list includes failed fast check commands when available, then `python -m qa_z fast`. If blocking deep findings are selected, it also includes `python -m qa_z deep --from-run latest`. The handoff does not run these commands and does not decide success through an LLM.

`codex.md` and `claude.md` render the same normalized handoff data. `codex.md` is action-oriented for Codex-style execution. `claude.md` is more explanatory and emphasizes constraints, non-goals, and workflow. Both are deterministic Markdown artifacts; neither invokes a live vendor API.

## Repair Session

`qa-z repair-session start --baseline-run <run>` creates a local workflow directory:

```text
.qa-z/sessions/<session-id>/
  session.json
  executor_guide.md
  executor_safety.json
  executor_safety.md
  handoff/
    packet.json
    prompt.md
    handoff.json
    codex.md
    claude.md
  executor_results/
    history.json
    attempts/
      <attempt-id>.json
    dry_run_summary.json
    dry_run_report.md
```

The handoff files use the same repair packet and handoff schemas documented above, but they are written under the session so a full repair loop can be inspected from one directory. `executor_guide.md` is a human-readable guide for an external executor. `executor_safety.json` and `executor_safety.md` freeze the same pre-live safety boundary for both repair sessions and executor bridges. None of these files imply live Codex or Claude API execution.

`session.json` is the machine-readable state manifest. Required top-level fields:

- `kind`: stable artifact kind, currently `qa_z.repair_session`
- `schema_version`: integer schema marker, currently `1`
- `session_id`: session directory id
- `session_dir`: repository-relative session directory when possible
- `state`: current workflow state
- `created_at` and `updated_at`: UTC timestamps
- `baseline_run_dir`: baseline run directory used as the pre-repair evidence
- `baseline_fast_summary_path`: baseline fast summary artifact
- `baseline_deep_summary_path`: baseline deep summary artifact, or `null`
- `handoff_dir`: session-local handoff directory
- `handoff_artifacts`: paths for `packet.json`, `prompt.md`, `handoff.json`, `codex.md`, and `claude.md`
- `executor_guide_path`: session-local executor guide
- `safety_artifacts`: paths for `executor_safety.json` and `executor_safety.md`
- `candidate_run_dir`: post-repair candidate run directory, or `null` before verification
- `verify_dir`: session-local verification directory, or `null` before verification
- `verify_artifacts`: paths for verification `summary.json`, `compare.json`, and `report.md`
- `outcome_path`: session `outcome.md`, or `null` before verification
- `summary_path`: session `summary.json`, or `null` before verification
- `provenance`: compact baseline status, contract path, and repair-needed metadata
- `executor_result_path`: latest ingested executor result artifact, or `null`
- `executor_result_status`: latest ingested executor result status, or `null`
- `executor_result_validation_status`: latest reported executor validation status, or `null`
- `executor_result_bridge_id`: bridge id that produced the latest ingested result, or `null`

Current session creation moves directly to `waiting_for_external_repair` after the handoff artifacts and executor guide are written. A successful comparison writes the verification and outcome artifacts, then updates the state to `completed`. The additional states `created`, `handoff_ready`, `candidate_generated`, `verification_complete`, and `failed` are reserved for future recovery and diagnosis.

The `executor_results/` directory becomes meaningful after `qa-z executor-result ingest` or `qa-z executor-result dry-run`. It is reserved at the session level so the latest accepted result, readable attempt history, and dry-run audit can stay co-located with the owning repair session.

`qa-z repair-session verify --session <session> --rerun` creates a candidate run under `.qa-z/sessions/<session-id>/candidate` by reusing the existing deterministic fast, deep, and review paths before running verification. `--candidate-run <run>` compares an existing candidate instead. By default, session verification writes:

```text
.qa-z/sessions/<session-id>/verify/summary.json
.qa-z/sessions/<session-id>/verify/compare.json
.qa-z/sessions/<session-id>/verify/report.md
.qa-z/sessions/<session-id>/outcome.md
.qa-z/sessions/<session-id>/summary.json
```

The session-level `summary.json` is a workflow index, not a replacement for `verify/compare.json`. It contains:

- `kind`: stable artifact kind, currently `qa_z.repair_session_summary`
- `schema_version`: integer schema marker, currently `1`
- `session_id`, `state`, `baseline_run_dir`, `candidate_run_dir`, `verify_dir`, and `outcome_path`
- `verdict`: verification verdict
- `repair_improved`: `true` only for `improved`
- `blocking_before` and `blocking_after`
- `resolved_count`
- `remaining_issue_count`
- `new_issue_count`
- `regression_count`
- `not_comparable_count`
- `next_recommendation`: deterministic workflow recommendation such as `merge candidate`, `inspect regressions`, `reject repair`, `rerun needed`, or `continue repair`
- `executor_dry_run_verdict` and `executor_dry_run_reason`: optional session-local dry-run context copied from `executor_results/dry_run_summary.json` when present, or synthesized from readable executor history when the dry-run summary is missing
- `executor_dry_run_source`: optional provenance marker, currently `materialized` or `history_fallback`, so callers can tell whether the dry-run residue came from `dry_run_summary.json` or synthesized history
- `executor_dry_run_attempt_count`: optional dry-run attempt count preserved for completed repair-session summaries, including the history-only fallback path
- `executor_dry_run_history_signals`: optional stable history-residue signal ids copied from the session-local dry-run summary or synthesized from `executor_results/history.json`
- `executor_dry_run_operator_decision`: optional primary operator action id copied from `operator_decision`
- `executor_dry_run_operator_summary`: optional one-line operator diagnostic copied from `operator_summary`
- `executor_dry_run_recommended_actions`: optional ordered action objects copied from `recommended_actions`

Repair sessions do not edit files, call live model APIs, create remote jobs, schedule work, comment on GitHub, commit, or push. They only connect existing local handoff and verification mechanisms into one auditable directory.

## Executor Safety Package

`qa-z repair-session start` writes a shared pre-live executor safety package to:

```text
.qa-z/sessions/<session-id>/executor_safety.json
.qa-z/sessions/<session-id>/executor_safety.md
```

`executor_safety.json` has:

- `kind`: stable artifact kind, currently `qa_z.executor_safety`
- `schema_version`: integer schema marker, currently `1`
- `package_id`: stable contract id, currently `pre_live_executor_safety_v1`
- `status`: currently `pre_live_only`
- `summary`: concise statement of the frozen boundary
- `rules`: ordered rule objects with `id`, `category`, `requirement`, and `enforced_by`
- `non_goals`: explicit exclusions such as no live API execution, no remote orchestration, and no automatic code edits
- `enforcement_points`: current QA-Z surfaces that point at or enforce the package

The current rule ids are:

- `no_op_requires_explanation`
- `retry_boundary_is_manual`
- `mutation_scope_limited`
- `unrelated_refactors_prohibited`
- `verification_required_for_completed`
- `outcome_classification_must_be_honest`

`executor_safety.md` is the operator-facing companion for the same package. It is explanatory text only; the JSON artifact is the machine-readable source of truth.

## Repair Verification

`qa-z verify --baseline-run <run> --candidate-run <run>` compares an existing pre-repair baseline run with an existing post-repair candidate run. `qa-z verify --baseline-run <run> --rerun` first creates a candidate run with the existing deterministic `fast` and `deep` runners, then compares it. Verification does not edit files, call Codex or Claude, run a scheduler, or make LLM-only judgments.

By default, verification writes artifacts under the candidate run:

```text
.qa-z/runs/<candidate-run-id>/verify/summary.json
.qa-z/runs/<candidate-run-id>/verify/compare.json
.qa-z/runs/<candidate-run-id>/verify/report.md
```

`compare.json` is the machine-readable source of truth. Required top-level fields:

- `kind`: stable artifact kind, currently `qa_z.verify_compare`
- `schema_version`: integer schema marker, currently `1`
- `baseline_run_id`: baseline run directory name
- `candidate_run_id`: candidate run directory name
- `baseline`: baseline run directory and observed fast/deep statuses
- `candidate`: candidate run directory and observed fast/deep statuses
- `verdict`: one of `improved`, `unchanged`, `mixed`, `regressed`, or `verification_failed`
- `fast_checks`: fast check deltas grouped by verification category
- `deep_findings`: deep finding deltas grouped by verification category
- `summary`: numeric aggregate counts used for verdict derivation

The verification categories are:

- `resolved`: a previously blocking fast check or deep finding no longer blocks
- `still_failing`: a previously blocking fast check or deep finding still blocks
- `regressed`: previously non-blocking comparable evidence became blocking
- `newly_introduced`: a candidate-only blocking fast check or deep finding appeared
- `skipped_or_not_comparable`: evidence was skipped, missing from one side, or otherwise cannot prove improvement

Fast checks are matched by check id and compare status, exit code, and kind. `failed` and `error` are blocking. `passed` and `warning` are non-blocking. Skipped checks are recorded as not comparable without automatically making the whole verification fail.

Deep findings are matched conservatively. Active findings use `source`, `rule_id`, normalized path, line, and normalized message as the strict identity; relaxed matching drops message text but keeps source, rule, path, and line. Grouped findings use the same source/rule/path identity and treat the representative line as display metadata for relaxed matching. QA-Z does not do broad fuzzy matching or infer root causes. Blocking deep findings are determined by the same `fail_on_severity` policy recorded in deep artifacts, defaulting to `ERROR`.

One-sided deep artifacts are not comparable. If only the baseline or only the candidate has a sibling `deep/summary.json`, verification records `deep:summary` in `skipped_or_not_comparable` and returns `verification_failed`. If neither run has deep artifacts, verification compares the fast evidence as a fast-only run.

`summary.json` is a compact numeric view of the comparison:

- `kind`: stable artifact kind, currently `qa_z.verify_summary`
- `schema_version`: integer schema marker, currently `1`
- `repair_improved`: `true` only for the `improved` verdict
- `verdict`: final verdict string
- `blocking_before`: baseline blocking fast checks plus blocking deep findings
- `blocking_after`: candidate blocking fast checks plus blocking deep findings
- `resolved_count`: resolved fast checks plus resolved deep findings
- `new_issue_count`: newly introduced and regressed blocking evidence
- `regression_count`: comparable evidence that became blocking
- `not_comparable_count`: skipped or non-comparable fast/deep evidence

`report.md` is the human-readable companion. It lists baseline and candidate run ids, final verdict, aggregate counts, fast-check categories, deep-finding categories, and a short reproduction note.

Verdict derivation is deterministic:

- `improved`: at least one blocker resolved and no new or regressed blockers were found
- `unchanged`: no blockers resolved and no new or regressed blockers were found
- `mixed`: at least one blocker resolved and at least one new or regressed blocker was found
- `regressed`: new or regressed blockers were found and no blockers resolved
- `verification_failed`: required run evidence is missing, invalid, or not comparable enough to evaluate the repair

## Review Packet Artifacts

`qa-z review --from-run <run> --output-dir <dir>` writes:

```text
<dir>/review.md
<dir>/review.json
```

`review.md` is the human-readable packet. `review.json` contains the same run-aware contract, selection, executed-check, failed-check, and priority-order context in machine-readable form. When sibling deep artifacts exist, review output includes a Deep Findings section with finding count, severity summary, affected files, selection mode, and top Semgrep findings.

## GitHub Summary

`qa-z github-summary --from-run <run> --output <path>` writes compact Markdown for GitHub Actions Job Summary:

```text
.qa-z/runs/<run-id>/github-summary.md
```

The GitHub summary is intentionally not a raw failure dump. It includes the overall fast and deep statuses, selection mode, fast totals, failed checks, changed files, selection groups, optional Deep QA findings, and pointers to the fast summary, review packet, and repair prompt artifacts.

When verification or repair-session outcome artifacts are available, `github-summary` also appends a concise repair outcome section. The section can come from:

- `<run>/verify/summary.json`, `<run>/verify/compare.json`, and `<run>/verify/report.md`
- a repair-session manifest whose `candidate_run_dir` matches the source run
- an explicit `--from-session <session>` argument

The publish summary model normalizes:

- baseline and candidate run ids when available
- final verification verdict
- resolved blocker count
- remaining blocker count
- regression count
- PR-friendly recommendation
- short artifact paths for session, verify summary, verify compare, verify report, outcome, and handoff artifacts

When the source is a repair session, the publish summary may also carry additive executor dry-run residue: verdict, verdict reason, dry-run source (`materialized` or `history_fallback`), attempt count, history-signal ids, operator decision, operator summary, and recommended actions. If session `summary.json` is missing but `verify/` artifacts still exist, QA-Z falls back to those verification artifacts without dropping readable dry-run residue from `executor_results/history.json`.

Recommendation mapping is deterministic and uses only recorded verdicts:

- `improved`: `safe_to_review`
- `mixed`: `review_required`
- `regressed`: `do_not_merge`
- `verification_failed`: `rerun_required`
- `unchanged`: `continue_repair`

The shipped GitHub workflows upload `deep/results.sarif` with `github/codeql-action/upload-sarif@v3`. GitHub turns uploaded SARIF results into code scanning alerts and pull request annotations when the repository permits `security-events: write`. QA-Z does not yet emit standalone `::warning` workflow commands or Checks API annotations.

TypeScript fast checks use the same v2 shape as Python checks. A targeted TypeScript lint or test entry records `execution_mode: targeted`, the resolved `eslint` or `vitest run` command, and the selected `target_paths`.

When the source run includes v2 selection metadata, `qa-z review --from-run` and `qa-z repair-prompt` carry that selection context forward so the next human or agent can see why each check was run, targeted, or skipped. Missing deep summaries are treated as fast-only runs; broken deep summaries are artifact errors.

## Benchmark Summary

`qa-z benchmark` runs seeded fixtures and writes:

```text
benchmarks/results/summary.json
benchmarks/results/report.md
```

The benchmark runner copies each fixture repository into `benchmarks/results/work/` before execution. That work directory is generated and disposable.

Generated benchmark output policy is defined in `docs/generated-vs-frozen-evidence-policy.md`. `benchmarks/results/summary.json` and `benchmarks/results/report.md` are local by default and should be committed only as intentional frozen evidence with surrounding documentation. Root `.qa-z/**` stays local, while `benchmarks/fixtures/**/repo/.qa-z/**` is allowed when it is fixture-local deterministic input.

`summary.json` has:

- `kind`: stable artifact kind, currently `qa_z.benchmark_summary`
- `schema_version`: integer schema marker, currently `1`
- `fixtures_total`, `fixtures_passed`, and `fixtures_failed`
- `overall_rate`: fixture-level pass rate
- `snapshot`: compact generated benchmark result text such as `52/52 fixtures, overall_rate 1.0`, derived from `fixtures_passed`, `fixtures_total`, and `overall_rate`
- `category_rates`: detection, handoff, verify, and artifact pass rates
- `failed_fixtures`: fixture names with at least one mismatch
- `fixtures`: per-fixture result records with `actual` observed fields, `failures`, category statuses, and artifact pointers

The generated `report.md` repeats `snapshot` near the top so human closure notes can quote generated benchmark evidence instead of recomputing counts.

Benchmark results are comparisons against fixture `expected.json` contracts. They do not replace fast, deep, repair, or verify artifacts, and they do not call live executors.

Deep benchmark contracts may assert Semgrep scan-quality diagnostics with `scan_warning_count`, `scan_warnings`-derived fields such as `scan_warning_types_present`, summary-level `scan_quality`, and fixtures such as `deep_scan_warning_diagnostics` and `deep_scan_warning_multi_source_diagnostics`; these warnings remain non-blocking and do not replace finding counts.

Fixture contracts may execute the local executor return path through `run.executor_result` and compare the resulting `expect_executor_result` section. That path creates a repair session, packages an executor bridge, ingests a `qa_z.executor_result` artifact, and may attach verification evidence through the same `candidate_run` or `rerun` hints used outside the benchmark.

## Alpha Release Gate Evidence

`scripts/alpha_release_gate.py --json --output dist/alpha-release-gate.json`
writes a local generated release-readiness artifact. It is publish evidence, not
a committed runtime contract, unless an operator intentionally freezes it with
surrounding release notes.

The top-level gate JSON includes:

- `summary`, `exit_code`, `generated_at`, `check_count`, `passed_count`, `failed_count`, and `failed_checks`
- `checks`: ordered command results with `name`, `label`, `status`, `exit_code`, `stdout_tail`, and `stderr_tail`
- `worktree_commit_plan`: the gate command name for
  `python scripts/worktree_commit_plan.py --include-ignored --json`, which
  checks commit-split grouping and ignored generated evidence before publish
- `preflight_output`: the nested preflight artifact path when `--output` is used
- `worktree_plan_output`: the nested worktree commit-plan artifact path when
  `--output` or `--worktree-plan-output` is used
- optional `worktree_plan_attention_reasons`: top-level copy of strict worktree
  plan blockers when the worktree commit-plan gate check fails
- `strict_worktree_plan`: whether the gate ran the worktree commit-plan helper
  with both `--fail-on-generated` and `--fail-on-cross-cutting`
- `preflight_failed_checks`, `next_actions`, and optional `next_commands` when
  nested preflight failures include or synthesize repair guidance
- optional `evidence_consistency_errors`: deterministic release-evidence mismatches
  such as benchmark snapshot mismatches, a `worktree generated artifact split mismatch`,
  or a `worktree generated artifact policy split mismatch` that add a
  `release_evidence_consistency` failed check
- `evidence.pytest.passed`: the pytest pass count extracted from the direct pytest gate
- optional `evidence.pytest.skipped`: the pytest skipped count extracted from the direct pytest gate, when present
- `evidence.deep.status`: the deep command status from the `qa-z deep --json` artifact
- `evidence.deep.scan_quality_status`: non-blocking deep scan-quality status, when present
- `evidence.deep.scan_quality_warning_count`: non-blocking deep scan-quality warning count, when present
- `evidence.deep.scan_quality_warning_types`: normalized scan-quality warning types, when present
- optional `evidence.deep.scan_quality_warning_paths`: normalized scan-quality
  warning paths when present
- optional `evidence.deep.scan_quality_check_ids`: deep check ids that emitted
  scan-quality warnings when present
- `evidence.benchmark.snapshot`: compact benchmark result text such as `52/52 fixtures, overall_rate 1.0`
- `evidence.benchmark.fixtures_passed`, `fixtures_failed`, `fixtures_total`, and `overall_rate`
- optional `evidence.local_preflight.repository_target`: copied nested preflight
  GitHub owner/repository target when that payload recorded a canonical target
- optional `evidence.local_preflight.expected_origin_target`: copied nested
  preflight origin target when that payload recorded a canonical target
- optional `evidence.local_preflight.repository_url`: copied nested preflight
  repository URL when canonical target extraction is unavailable
- optional `evidence.local_preflight.expected_origin_url`: copied nested
  expected origin URL when canonical target extraction is unavailable
- optional `evidence.local_preflight.origin_state`: copied nested preflight
  origin state such as `missing` or `configured`
- optional `evidence.local_preflight.actual_origin_url`: copied nested
  preflight actual origin URL when the repository has a configured `origin`
- optional `evidence.local_preflight.actual_origin_target`: copied nested
  canonical GitHub repository target for the configured `origin` when it can be
  derived
- optional `evidence.local_preflight.remote_path`: copied nested preflight
  remote publish-path decision such as `direct_publish`, `release_pr`, or
  `blocked`
- optional `evidence.local_preflight.release_path_state`: copied nested
  publish-state classifier such as `remote_direct_publish`,
  `remote_release_pr`, `local_only_bootstrap_origin`,
  `local_only_remote_preflight`, `blocked_existing_refs`,
  `blocked_existing_tag`, `blocked_origin_alignment`,
  `blocked_repository`, or `blocked_remote_access`
- optional `evidence.local_preflight.remote_readiness`: copied nested
  preflight readiness classifier such as `needs_origin_bootstrap`,
  `ready_for_remote_checks`, or `needs_release_pr_path`
- optional `evidence.local_preflight.publish_strategy`: copied nested
  next-step publish strategy such as `push_default_branch`, `push_release_branch`,
  `remote_preflight`, or `bootstrap_origin`
- optional `evidence.local_preflight.publish_checklist_count`: copied nested
  count of post-push publish checklist items when the remote path already knows
  the next CI/PR/origin-bootstrap/tagging milestones; compact human Evidence prints this as
  `publish_checklist_count` / `checklist=`
- optional `evidence.local_preflight.remote_blocker`: copied nested preflight
  blocker classifier such as `repository_missing`, `origin_present`, or
  `origin_mismatch`
- optional `evidence.local_preflight.remote_ref_count`: copied nested count of
  remote refs observed during the publish-path decision when the remote was not
  empty
- optional `evidence.local_preflight.remote_ref_head_count`: copied nested
  count of `refs/heads/*` refs observed during the publish-path decision
- optional `evidence.local_preflight.remote_ref_tag_count`: copied nested count
  of `refs/tags/*` refs observed during the publish-path decision
- optional `evidence.local_preflight.remote_ref_kinds`: copied nested list of
  remote ref kinds such as `heads` or `tags`
- optional `evidence.local_preflight.remote_ref_sample`: copied nested sample
  of remote refs observed during the publish-path decision
- optional `evidence.local_preflight.skip_remote`,
  `evidence.local_preflight.allow_existing_refs`, and
  `evidence.local_preflight.allow_dirty`: copied nested preflight mode flags
- optional `evidence.local_preflight.tracked_generated_artifact_count`: copied
  nested count of tracked generated roots surfaced by preflight
- optional `evidence.local_preflight.generated_local_only_tracked_count`:
  copied nested count of tracked local-only runtime artifacts roots
- optional `evidence.local_preflight.generated_local_by_default_tracked_count`:
  copied nested count of tracked local-by-default benchmark evidence roots
- optional `evidence.gate_failures.<check>.kind`: deterministic gate-local
  blocker classifier for known environment-sensitive failures such as
  `mypy_internal_error`, `semgrep_x509_store_failure`,
  `benchmark_results_lock`, `offline_build_dependency_failure`, or
  `bundle_path_locked`
- optional `evidence.gate_failures.<check>.summary`: compact operator-facing
  explanation paired with that blocker kind
- optional top-level `environment_failure_count` and `product_failure_count`:
  counts of failed gate checks that were classified as environment/toolchain
  blockers versus unclassified product/QA failures
- when known blocker kinds are present, the gate also appends deterministic
  `next_actions` and `next_commands` telling operators which rerun or cleanup
  command should unblock the release path next
- every failed check in `checks[]` now records `failure_scope=environment|product`;
  known environment blockers also attach `failure_kind` and `failure_summary`
  directly to the failed check entry so human triage can distinguish local
  runtime/tooling blockers from product regressions without reopening JSON
- `evidence.worktree_commit_plan.status`: commit-plan helper status
- `evidence.worktree_commit_plan.changed_batch_count`,
  optional `evidence.worktree_commit_plan.unchanged_batch_count`,
  `generated_artifact_count`, optional `generated_artifact_file_count`,
  optional `generated_artifact_dir_count`, optional
  `generated_local_only_count`, optional `generated_local_by_default_count`,
  `cross_cutting_count`, optional `cross_cutting_group_count`,
  `unassigned_source_path_count`, `multi_batch_path_count`, and
  `next_action_count`: compact
  source/generated commit-split diagnostics from
  `scripts/worktree_commit_plan.py --include-ignored --json`
- optional `evidence.worktree_commit_plan.kind`: copied worktree commit-plan
  artifact kind, currently `qa_z.worktree_commit_plan`, when present
- optional `evidence.worktree_commit_plan.schema_version`: copied worktree
  commit-plan schema marker, when present
- optional `evidence.worktree_commit_plan.output_path`: copied nested helper
  `output_path`, when the helper artifact recorded where it was written
- optional `evidence.worktree_commit_plan.branch`: copied worktree commit-plan
  repository branch context, when the helper artifact recorded it
- optional `evidence.worktree_commit_plan.head`: copied worktree commit-plan
  repository head context, when the helper artifact recorded it
- optional `evidence.worktree_commit_plan.attention_reasons`: machine-readable
  strict worktree plan blockers such as `generated_artifacts_present`
- optional `evidence.worktree_commit_plan.attention_reason_count`: count of
  strict worktree plan blockers summarized from `attention_reasons`
- optional `evidence.worktree_commit_plan.strict_mode`: copied strict audit
  flags from the worktree commit-plan artifact
- worktree commit-plan `next_actions` are promoted to top-level `next_actions`
  when that gate check fails, matching the existing preflight repair guidance
- `release_evidence_consistency` fails with a `worktree patch-add group mismatch`
  when compact `cross_cutting_group_count` exceeds
  `shared_patch_add_count`, because every patch-add review group must be backed
  by at least one shared patch-add candidate
- nested preflight `next_commands` are promoted to top-level `next_commands`
  when deterministic repair commands are available

The human gate renderer prints the same evidence under `Evidence:` when these
fields are present. Semgrep scan-quality warning counts are diagnostic and may
vary between local runs; release docs should say the warnings are surfaced
without pinning a specific count.
When nested preflight target metadata is available, compact gate Evidence also
prints `target=`, optional `origin=`, optional `origin_state=`, optional
`origin_current_target=`, optional `origin_current=`, `path=`, optional
`readiness=`, optional `blocker=`, optional `refs=`, optional `head_refs=`,
optional `tag_refs=`, optional `ref_kinds=`, and `ref_sample=`,
optional `next_actions=` and `next_commands=` counts, optional
`tracked_generated=`, optional `tracked_local_only=`, optional
`tracked_local_by_default=`, and `mode=` fields next to the preflight summary
instead of forcing operators to open the nested preflight JSON. When canonical
target extraction is unavailable, the same line falls back to `target_url=` and
`origin_url=` so raw
repository/origin context is still visible.
When worktree commit-plan repository provenance is available, human Evidence
also prints `branch=` and `head=` and normalizes detached checkouts to
`branch=detached`.
If an older benchmark artifact has only counters, the gate synthesizes the same
benchmark `snapshot` from `fixtures_passed`, `fixtures_total`, and
`overall_rate`. Benchmark evidence counters and the benchmark `snapshot` must
agree; otherwise the gate appends `release_evidence_consistency` to
`failed_checks` instead of letting contradictory release evidence pass as
publish-ready. That failure also adds `next_actions` guidance to rerun the
alpha release gate and inspect the benchmark JSON before publishing.

The nested preflight artifact referenced by `preflight_output` keeps the same
deterministic fields documented in release docs: `repository_url`, optional
`repository_target`, optional `repository_probe_state`, optional `repository_probe_basis`, optional `repository_probe_generated_at`, optional `repository_probe_freshness`, optional `repository_probe_age_hours`, optional `repository_http_status`, optional `repository_visibility`, optional `repository_archived`, optional `repository_default_branch`, `expected_repository`, `expected_origin_url`, optional
`expected_origin_target`, `expected_branch`, `expected_tag`, `skip_remote`,
`allow_existing_refs`, `allow_dirty`, `check_count`, `passed_count`,
`failed_count`, `skipped_count`, `failed_checks`, `remote_path`, optional
`release_path_state`, optional
`remote_readiness`, optional `publish_strategy`, optional `publish_checklist`, optional `remote_blocker`, optional `origin_state`,
optional `actual_origin_url`, optional `actual_origin_target`, optional
`remote_ref_count`, optional `remote_ref_head_count`, optional
`remote_ref_tag_count`, optional `remote_ref_kinds`, optional
`remote_ref_sample`, optional `tracked_generated_artifact_count`, optional
`tracked_generated_artifact_paths`, optional
`generated_local_only_tracked_count`, optional
`generated_local_only_tracked_paths`, optional
`generated_local_by_default_tracked_count`, optional
`generated_local_by_default_tracked_paths`, `checks`, optional
`next_actions`, optional `next_commands`, and
`generated_at`. Human preflight output prints the same target/origin/mode
decision context under compact `Target:`, `Origin:`, `Mode:`, and `Decision:`
lines before the per-check status list, includes the actual configured origin
URL when known, prints `Next commands:` when those repair commands are present,
and prints `Publish checklist:` when a successful remote path has explicit
post-push follow-up milestones.

## Worktree Commit Plan Evidence

`scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json`
prints deterministic commit-splitting evidence for the current dirty worktree,
can persist that payload as a local runtime artifact, and remains an operator
planning artifact rather than a staging operation.

The JSON includes:

- `kind`: `qa_z.worktree_commit_plan`
- `schema_version`: integer schema marker, currently `1`
- `generated_at`: UTC timestamp for the helper run
- optional `output_path`: path written by `--output`, when the CLI wrote this
  payload to disk
- optional `repository`: `branch` and `head` context when the payload is emitted
  from the CLI against a live git worktree
- `status`: `ready` or `attention_required`
- `strict_mode`: active strict audit flags, currently `fail_on_generated` and
  `fail_on_cross_cutting`
- optional `attention_reasons`: machine-readable reasons that made the plan
  require attention, such as `generated_artifacts_present`
- `summary`: compact counts for batches, changed paths, generated artifacts,
  cross-cutting paths, `cross_cutting_group_count`, `report_path_count`,
  multi-batch paths, and unassigned source paths, plus `batch_count`,
  `changed_path_count`, `unchanged_batch_count`,
  `generated_artifact_file_count`, `generated_artifact_dir_count`,
  `generated_local_only_count`, `generated_local_by_default_count`,
  `shared_patch_add_count`, and `attention_reason_count`
- `batches`: ordered commit-plan batches with `id`, `title`, commit `message`,
  `validation_commands`, `changed_count`, and `changed_paths`
- `batches[].staging_plan`: machine-readable staging guidance with
  `include_paths`, `candidate_patch_add_paths`, `exclude_path_count`, and
  `validation_commands`
- `batches[].staging_plan.git_add_command` and
  `batches[].staging_plan.git_add_patch_command`: argv-style staging guidance
  for whole-file and patch-add review
- `generated_artifact_paths`: local generated or ignored evidence such as
  `.qa-z/**`, `benchmarks/results/**`, `benchmarks/results-*`, `dist/**`,
  `build/**`, egg-info, cache, or `__pycache__` paths
- `generated_local_only_paths`: generated artifact paths that should stay local
  unless a fixture or documentation task intentionally freezes a small sample,
  such as root `.qa-z/**`, caches, `dist/**`, `build/**`, or
  `benchmarks/results/work/**`
- `generated_local_by_default_paths`: generated artifact paths that are still
  local by default but may be intentionally frozen with surrounding context,
  such as `benchmarks/results/summary.json`, `benchmarks/results/report.md`, or
  snapshot directories matching `benchmarks/results-*`
- `cross_cutting_paths`: files such as `README.md`, `docs/artifact-schema-v1.md`,
  and current-truth tests that should be patch-added with the feature batch they
  describe
- `report_paths`: local report files under `docs/reports/**`
- `shared_patch_add_paths`: ordered patch-add candidate list combining
  cross-cutting paths and report paths for selected-batch staging follow-through
- `cross_cutting_groups`: operator-sized shared patch-add groups, currently
  `public_docs_contract`, `command_router_spine`, `current_truth_guards`,
  `command_surface_tests`, `status_reports`, or
  `unclassified_cross_cutting`; each group records `path_count`, `paths`, and a
  scoped `patch_command`
- `multi_batch_paths`: paths that match more than one batch and need an explicit
  owner unless a known owner override applies
- `unassigned_source_paths`: source-like paths that no commit batch owns yet
- `next_actions`: deterministic operator guidance for generated, multi-batch,
  cross-cutting, or unassigned paths

`--batch <id>` keeps the same top-level contract while narrowing `batches` to one
selected batch. `--include-ignored` includes ignored generated artifacts from
`git status --short --ignored`, which is useful before source staging.
`--fail-on-generated` adds `generated_artifacts_present` to `attention_reasons`
and returns `attention_required` when generated evidence exists.
`--fail-on-cross-cutting` adds `cross_cutting_paths_present` when cross-cutting
docs, tests, or report paths require patch-add ownership. Human output prints
`Strict mode:` when either strict flag is active and `Attention reasons:` when
attention blockers are present. Attention reasons are de-duplicated in human
output.
Next actions are de-duplicated in human output.
Next commands are de-duplicated in human output.
Human output prints `Batches: changed=` when changed and unchanged batch counts
are available.
Human output prints `Generated artifacts:` with `files=` and `dirs=` when
generated artifact split counts are available.
Human output prints `Report paths:` when report drift is present.
Human output prints `Report preview:` with the first dirty report paths.
Batch-filtered output includes `selected_batch_summary.include_path_count`,
`selected_batch_summary.patch_add_candidate_count`, and
`selected_batch_summary.generated_exclude_count`; human output prints those as
`Selected staging:`.
Human output prints `Shared patch-add paths:`, `Shared patch-add preview:`, and
`Cross-cutting groups:` when cross-cutting or report paths still need patch-add
review. Each group prints a scoped `patch command:` so operators can patch-add
one review surface at a time. Alpha release gate evidence copies
`cross_cutting_group_count` and human gate output prints it as
`patch_add_groups=` when present.
`--summary-only` keeps `cross_cutting_groups` compact by preserving group ids,
titles, `path_count`, and path previews, but omitting full `patch_command`
arrays; oversized group path lists add `paths_truncated_count`.
Batch-filtered human output prints `Selected batch:` and
`Global attention reasons:` when those fields are present.
Strict batch filters preserve
generated_artifacts_present as a global blocker, and batch filters preserve
cross_cutting_paths_present as a global blocker, while using
`selected_batch_summary.status`, `selected_batch_summary.attention_reason_count`,
and `global_attention_reason_count` for the selected batch's local status and
global blocker count.
batch filters preserve generated_artifacts_present and
cross_cutting_paths_present in strict mode.
Helper output write failures return exit code `2` with deterministic stderr
instead of a traceback.

## Runtime Artifact Cleanup Evidence

`scripts/runtime_artifact_cleanup.py --json` previews policy-managed generated
runtime artifact cleanup, and `--apply --json` deletes only untracked
local-only roots while leaving local-by-default benchmark evidence in review.

The JSON includes:

- `kind`: `qa_z.runtime_artifact_cleanup`
- `schema_version`: integer schema marker, currently `1`
- `generated_at`: UTC timestamp for the helper run
- `repo_root`: absolute repository root used for cleanup planning
- `mode`: `dry-run` or `apply`
- `candidates`: ordered cleanup candidates discovered from the same
  generated-policy buckets as the worktree commit-plan helper
- `candidates[].path`: repository-relative candidate root
- `candidates[].kind`: `directory` or `file`
- `candidates[].policy_bucket`: `local_only` or `local_by_default`
- `candidates[].status`: `planned`, `deleted`, `skipped_tracked`, or
  `review_local_by_default`
- `candidates[].reason`: repair-oriented explanation for the chosen status,
  such as tracked paths preventing deletion or benchmark evidence requiring
  operator review
- `candidates[].tracked_paths`: tracked git paths under the candidate root when
  cleanup skipped deletion for safety
- `counts`: status rollup with `planned`, `review_local_by_default`,
  `skipped_tracked`, and `deleted`

Human output prints the same mode, status counts, candidate paths, `reason`
text, and tracked-path preview so cleanup decisions remain reviewable without
opening the JSON artifact.

## Self-Improvement Artifacts

`qa-z self-inspect` reads existing local QA-Z evidence and writes:

```text
.qa-z/loops/latest/self_inspect.json
.qa-z/improvement/backlog.json
```

The self-inspection pass is a planning layer. It does not edit files, call Codex or Claude APIs, run remote jobs, or create autonomous repair loops. Candidate tasks must be grounded in local artifacts or repository files, such as benchmark summaries, verification summaries, repair-session manifests, stored executor-result artifacts, session-local executor-result history artifacts, publish companion artifacts, README/schema docs, committed benchmark fixture contracts, report files under `docs/reports/`, recent loop history, and local worktree signals such as modified/untracked/staged counts plus generated benchmark result files where those files exist.

When self-inspection evidence is derived from executor dry-run residue, candidate evidence summaries keep the same dry-run provenance inline as `source=materialized` or `source=history_fallback`. That keeps backlog review auditable even when the operator only reads `self_inspect.json` or `backlog.json`. benchmark-gap evidence preserves the generated benchmark `snapshot` from `benchmarks/results/summary.json`, so failed-fixture backlog entries can show the fixture failure together with the overall benchmark pass-rate line.

For legacy benchmark summaries that predate `snapshot`, benchmark-gap evidence synthesizes the same compact text from `fixtures_passed`, `fixtures_total`, and `overall_rate` when those fields are present.
If a failed benchmark summary has only aggregate failure counts and no per-fixture details, self-inspection creates a summary-level benchmark-gap item instead of dropping the failure evidence.

Plain `qa-z self-inspect` output is an operator summary over this artifact. It prints artifact paths, total candidate count, and up to three top candidates with title, recommendation, deterministic action hint, deterministic validation command hint, priority score, and compact evidence summary. `qa-z self-inspect --json` remains the full machine-readable report.

Self-inspection JSON includes a top-level `live_repository` object so candidate decisions can be compared against the live state that produced them:

- `modified_count`, `untracked_count`, and `staged_count`: git dirty-worktree counts from `git status --short`
- `runtime_artifact_count`: count of dirty local-only runtime artifact paths after excluding local-by-default benchmark result evidence
- `benchmark_result_count`: count of local-by-default benchmark evidence present under `benchmarks/results/` and dirty snapshot roots matching `benchmarks/results-*`
- `dirty_benchmark_result_count`: subset of `benchmark_result_count` that is currently dirty in `git status`
- `release_evidence_count`: count of dirty generated alpha release gate/preflight evidence files under `dist/`
- `current_branch`: current branch name from live git state when available
- `current_head`: current `HEAD` revision from live git state when available
- `generated_artifact_policy_explicit`: whether `.gitignore` and `docs/generated-vs-frozen-evidence-policy.md` cover the generated-artifact contract
- `dirty_area_summary`: compact area counts such as `benchmark:6, source:6, docs:5`; dirty benchmark result evidence stays in the `benchmark` bucket instead of inflating `runtime_artifact`
- `backlog_reseeded`: whether inspection had to repopulate an empty backlog from fresh structural evidence
- `reseeded_candidate_ids`: concrete candidate ids written back into the backlog during that reseed pass; the report may still list a synthetic `backlog_reseeding_gap` diagnostic candidate, but `backlog.json` keeps only the concrete follow-up items when they exist

Dirty-worktree candidate evidence keeps the existing `git_status` source but now includes deterministic repository-area counts, for example `areas=benchmark:271, docs:160, source:42`, before the compact sample path list. The counts are derived from dirty modified plus untracked paths and do not add a new artifact schema field.
When `areas=` is present on a dirty-worktree item, human action hints use the first one or two rendered areas to name the first triage surface, for example `triage benchmark and docs changes first`. Without area evidence, the generic dirty-worktree action hint remains unchanged.
When a loop-health item with recommendation `improve_fallback_diversity` carries `recent_fallback_family=<family>` evidence, the human action hint now tells operators to surface a non-`<family>` fallback family before selecting more work from that same family. This keeps `self-inspect`, `backlog`, `select-next`, and `loop_plan.md` aligned without changing the JSON candidate shape.
Commit-isolation candidates also reuse `areas=` when their existing `git_status` evidence is present. The `isolate_foundation_commit` human action hint can then name the first one or two dirty areas to isolate into the foundation split, while the machine-readable candidate shape remains unchanged.
Deferred cleanup and commit-isolation candidates now rely on dirty generated-artifact pressure rather than the mere presence of local benchmark summaries. `benchmark_result_count` stays as operator context, while `dirty_benchmark_result_count` explains whether those artifacts are actually contributing live cleanup pressure. When the current inspection also knows the live `HEAD` revision, those structural report seeds require an explicit report `Head:` line before they are treated as fresh enough to reopen backlog work.
When the generated-artifact ignore rules and policy document are already explicit, live runtime artifact paths can still justify `artifact_hygiene_gap` or `runtime_artifact_cleanup_gap`, but they do not reopen `evidence_freshness_gap` on their own. That keeps cleanup work actionable without re-labeling the policy itself as ambiguous. In that explicit-policy state, `runtime_artifact_cleanup_gap` now scores above the broader `artifact_hygiene_gap`, so the next operator clears policy-managed runtime artifacts before revisiting longer-lived source/evidence separation work.

`self_inspect.json` has:

- `kind`: stable artifact kind, currently `qa_z.self_inspection`
- `schema_version`: integer schema marker, currently `1`
- `loop_id`: stable id for this inspection pass
- `generated_at`: UTC timestamp
- `backlog_reseeded`: whether inspection had to repopulate an empty backlog from structural evidence during this pass
- `reseeded_candidate_ids`: concrete candidate ids that were persisted into `backlog.json` during that reseed
- `live_repository`: compact live git/generated-artifact state used by this inspection pass
- `evidence_sources`: unique artifact paths used by generated candidates
- `candidates`: candidate backlog items before long-term merge

Each candidate includes:

- `id`: stable category-prefixed id
- `title`: short actionable task title
- `category`: one of the practical backlog categories, such as `benchmark_gap`, `verify_regression`, `executor_result_gap`, `schema_drift`, `docs_drift`, `session_gap`, `coverage_gap`, `artifact_consistency`, `workflow_gap`, `integration_gap`, `provenance_gap`, `partial_completion_gap`, `no_op_safeguard_gap`, `worktree_risk`, `commit_isolation_gap`, `artifact_hygiene_gap`, `runtime_artifact_cleanup_gap`, `deferred_cleanup_gap`, `evidence_freshness_gap`, `backlog_reseeding_gap`, or `autonomy_selection_gap`
- `evidence`: ordered artifact references with `source`, `path`, and a compact summary
- `impact`, `likelihood`, `confidence`, and `repair_cost`: integer scoring inputs
- `priority_score`: deterministic score
- `recommendation`: deterministic next action, such as `add_benchmark_fixture`, `stabilize_verification_surface`, `resume_executor_repair`, `triage_executor_failure`, `inspect_executor_no_op`, `sync_contract_and_docs`, `audit_executor_contract`, `harden_executor_result_freshness`, `harden_partial_completion_handling`, `harden_executor_no_op_safeguards`, `audit_worktree_integration`, `reduce_integration_risk`, `triage_and_isolate_changes`, `isolate_foundation_commit`, `separate_runtime_from_source_artifacts`, `clarify_generated_vs_frozen_evidence_policy`, `improve_backlog_reseeding`, `improve_empty_loop_handling`, `improve_fallback_diversity`, or `create_repair_session`
- `signals`: evidence tags used for scoring bonuses
- `recurrence_count`: number of times the item has been observed after backlog merge

`backlog.json` has:

- `kind`: stable artifact kind, currently `qa_z.improvement_backlog`
- `schema_version`: integer schema marker, currently `1`
- `updated_at`: UTC timestamp for the latest merge
- `items`: persistent backlog items

Backlog items use the same candidate fields plus:

- `status`: current queue state, currently `open` for observed candidates, `closed` for stale open items that were not re-observed on the latest inspection pass, or another workflow-managed state such as `selected` or `in_progress`
- `first_seen_at`: first UTC timestamp when the candidate was recorded
- `last_seen_at`: latest UTC timestamp when the candidate was observed
- `closed_at`: optional UTC timestamp when a stale `open` item was automatically closed
- `closure_reason`: optional reason for automatic closure, currently `not_observed_in_latest_inspection`

When self-inspection had to repopulate an empty backlog from fresh structural evidence, `backlog.json` persists the concrete candidates and does not keep a synthetic `backlog_reseeding_gap` item open alongside them.

Priority scoring is deterministic:

```text
priority_score = (impact * likelihood * confidence) - repair_cost
```

The current bonuses are:

- benchmark failure evidence: `+2`
- `mixed` or `regressed` verification evidence: `+2`
- docs/schema drift evidence: `+1`
- executor validation failure evidence: `+2`
- executor no-op safety evidence: `+1`
- executor failed-result evidence: `+1`
- mixed-surface benchmark realism gap: `+2`
- recent empty-loop chain: `+2`
- repeated fallback-family reuse: `+2`
- worktree integration risk: `+1`
- large dirty worktree signal: `+2`
- commit-order dependency signal: `+2`
- deferred cleanup recurrence: `+1`
- generated artifact policy ambiguity: `+1`
- policy-managed runtime artifacts still present under an explicit policy: `+2`
- service-readiness gap: `+2`
- roadmap gap not yet represented in backlog: `+2`
- recurrence count of 2 or more: `+1`
- regression-prevention signal: `+1`

`qa-z select-next` reads `.qa-z/improvement/backlog.json` and writes:

```text
.qa-z/loops/latest/selected_tasks.json
.qa-z/loops/latest/loop_plan.md
.qa-z/loops/history.jsonl
```

`selected_tasks.json` has:

- `kind`: stable artifact kind, currently `qa_z.selected_tasks`
- `schema_version`: integer schema marker, currently `1`
- `loop_id`: selected loop id
- `generated_at`: UTC timestamp
- `source_backlog`: backlog artifact path
- `source_self_inspection`: latest self-inspection artifact path when it supplied live repository context
- `source_self_inspection_loop_id` and `source_self_inspection_generated_at`: provenance copied from that self-inspection artifact when present
- `live_repository`: compact live git/generated-artifact snapshot copied from the latest self-inspection pass when present
- `selected_tasks`: the top 1 to 3 open backlog items sorted by selection priority score and stable tie-breakers

Each selected task may include:

- `selection_penalty`: small immediate-reselection penalty derived from the last two loop-history entries
- `selection_penalty_reasons`: compact reasons such as exact-task reselection, category reselection, fallback-family reselection, or current-batch fallback-family reselection
- `selection_priority_score`: `priority_score` after the selection penalty is applied

The plain-text `qa-z select-next` output now mirrors compact selected-task details for operators:

- live repository context when the latest self-inspection artifact supplied it
- selected task id plus title
- `recommendation`
- deterministic action hint derived from `recommendation`
- deterministic validation command hint derived from `recommendation`
- `selection_priority_score`, or `priority_score` when no additive selection score is present
- optional `selection_penalty` plus `selection_penalty_reasons`
- compact evidence summary derived from the selected task evidence

`loop_plan.md` is a human-readable companion for an external executor. It repeats the selected task ids, categories, recommendations, deterministic action hints, deterministic validation command hints, scores, evidence, and latest live repository context when available. When selection residue exists, `loop_plan.md` now also mirrors `selection_priority_score`, plus `selection_penalty` and `selection_penalty_reasons`, so the persisted plan keeps the same selection diversity context visible on the operator CLI surfaces. When no task was selected, `loop_plan.md` now also mirrors `selection_gap_reason` plus open backlog counts before and after inspection, so taskless loops keep their loop-health residue visible too. It explicitly states that QA-Z is selecting work, not calling live model APIs or repairing code by itself.

`history.jsonl` appends one JSON object per selection loop. Each line has:

- `kind`: stable artifact kind, currently `qa_z.loop_history_entry`
- `schema_version`: integer schema marker, currently `1`
- `loop_id` and `created_at`
- `selected_tasks`: selected backlog item ids
- `selected_categories`: selected backlog categories when they are known at selection time
- `selected_fallback_families`: selected fallback families such as `cleanup`, `loop_health`, `workflow_remediation`, `docs_sync`, or `benchmark_expansion`
- `evidence_used`: unique evidence paths for the selected tasks
- `source_self_inspection`, `source_self_inspection_loop_id`, `source_self_inspection_generated_at`, and `live_repository`: latest self-inspection path, provenance, and compact live repository snapshot when selection had that context
- `resulting_session_id`: `null` until a later workflow creates and records a session
- `verify_verdict`: `null` until a later workflow records verification results
- `benchmark_delta`: `null` until a later workflow records benchmark movement
- `next_candidates`: remaining open backlog item ids after selection

When `qa-z autonomy` runs, it reuses the same selection path and then enriches the matching history line with:

- `prepared_actions`: action types prepared for the selected tasks
- `outcome_path`: per-loop autonomy outcome artifact path
- `state`: final autonomy loop state
- `state_transitions`: recorded loop-state transitions such as `empty_backlog_detected`, `reseeded`, `fallback_selected`, or `blocked_no_candidates`
- `backlog_open_count_before_inspection` and `backlog_open_count_after_inspection`
- optional `selection_gap_reason` when no task survived selection
- `next_recommendations`: compact next steps derived from prepared actions

When `qa-z executor-result ingest` records a bridge-backed result, it may further enrich the matching history line with:

- `executor_result_status`
- `executor_ingest_status`
- `executor_result_path`
- `executor_validation_status`
- `executor_changed_files`
- `executor_verification_hint`
- `executor_verify_resume_status`
- updated `verify_verdict` when the ingest step also ran verification
- updated `next_recommendations`

## Autonomy Workflow Artifacts

`qa-z autonomy --loops N` connects self-inspection, backlog merge, task selection, next-action planning, optional local repair-session preparation, outcome recording, and history updates. It is a workflow preparation layer. It does not edit files, call Codex or Claude APIs, run remote jobs, schedule daemons, commit, push, or post GitHub comments.

Optional runtime-budget controls make the run persist until a minimum elapsed wall-clock target is satisfied:

- `--min-runtime-hours`: minimum total runtime budget before the run may finish
- `--min-loop-seconds`: minimum wall-clock duration to spend in each loop before advancing

If repeated loops end in `blocked_no_candidates`, QA-Z stops after a small deterministic cap instead of spinning empty loops for the rest of the runtime budget. Taskless loops now classify as `blocked_no_candidates` even when self-inspection closed stale open items during the loop, and the same recent-history penalty used by `select-next` also applies inside autonomy so identical fallback tasks, categories, or fallback families do not immediately repeat when comparable alternatives exist.

Each loop writes a stable directory:

```text
.qa-z/loops/<loop-id>/
  self_inspect.json
  selected_tasks.json
  loop_plan.md
  outcome.json
```

The latest loop is mirrored under:

```text
.qa-z/loops/latest/
  self_inspect.json
  selected_tasks.json
  loop_plan.md
  outcome.json
  autonomy_summary.json
```

`autonomy_summary.json` has:

- `kind`: stable artifact kind, currently `qa_z.autonomy_summary`
- `schema_version`: integer schema marker, currently `1`
- `generated_at`: UTC timestamp for the autonomy run
- `run_started_at` and `finished_at`
- `loops_requested` and `loops_completed`
- `latest_loop_id`
- `runtime_target_seconds`, `runtime_elapsed_seconds`, and `runtime_remaining_seconds`
- `runtime_budget_met`: whether the minimum runtime budget has been satisfied
- `min_loop_seconds`
- `stop_reason`: why the autonomy run stopped, such as `requested_loops_and_runtime_met` or `repeated_blocked_no_candidates`
- `consecutive_blocked_loops`: number of blocked taskless loops at the end of the run
- `created_session_ids`: repair sessions created during the run
- `outcomes`: embedded loop outcome objects

`outcome.json` has:

- `kind`: stable artifact kind, currently `qa_z.autonomy_outcome`
- `schema_version`: integer schema marker, currently `1`
- `loop_id` and `generated_at`
- `loop_started_at` and `loop_finished_at`
- `loop_elapsed_seconds`
- `cumulative_elapsed_seconds`
- `runtime_target_seconds` and `runtime_remaining_seconds`
- `runtime_budget_met`
- `min_loop_seconds`
- `state`: final state, such as `completed`, `fallback_selected`, or `blocked_no_candidates`
- `state_transitions`: observed workflow states such as `inspected`, `selected`, `empty_backlog_detected`, `reseeded`, `fallback_selected`, `blocked_no_candidates`, `session_prepared`, `awaiting_repair`, `recorded`, and `completed`
- `selected_task_ids`
- `selected_fallback_families`: fallback families represented by the selected tasks
- `source_self_inspection`, `source_self_inspection_loop_id`, `source_self_inspection_generated_at`, and `live_repository`: loop-local self-inspection path, provenance, and compact live repository snapshot copied through the selected-task artifact when available
- `backlog_open_count_before_inspection` and `backlog_open_count_after_inspection`
- optional `selection_gap_reason`: additive taskless-loop classification such as `no_open_backlog_after_inspection`
- `loop_health`: compact loop-health summary with `classification`, `selected_count`, `taskless`, `fallback_selected`, `selection_gap_reason`, `backlog_open_count_before_inspection`, `backlog_open_count_after_inspection`, `stale_open_items_closed`, `blocked_chain_length`, `blocked_chain_remaining_until_stop`, `blocked_chain_loop_ids`, and `summary`
- `evidence_used`: selected task evidence paths
- `verification_evidence`: selected verification summaries observed by the loop
- `actions_prepared`: deterministic action packets
- `created_session_ids`
- `next_recommendations`
- `artifacts`: per-loop artifact paths

Prepared actions are deterministic translations from selected task categories:

- `benchmark_gap` and `coverage_gap`: `benchmark_fixture_plan`
- `policy_gap`: `policy_fixture_plan`
- `docs_drift` and `schema_drift`: `docs_sync_plan`
- `backlog_reseeding_gap` and `autonomy_selection_gap`: `loop_health_plan`
- `workflow_gap`, `integration_gap`, `provenance_gap`, `partial_completion_gap`, and `no_op_safeguard_gap`: `workflow_gap_plan`
- `worktree_risk`, `commit_isolation_gap`, `artifact_hygiene_gap`, `runtime_artifact_cleanup_gap`, `deferred_cleanup_gap`, and `evidence_freshness_gap`: `integration_cleanup_plan`
- `artifact_consistency`: `artifact_consistency_plan`
- `session_gap`: `repair_session_followup`
- `verify_regression`: `repair_session` when `verify/compare.json` identifies a baseline run and session creation succeeds; otherwise `verification_stabilization_plan`

Each prepared action includes:

- `type`, `task_id`, `title`, `commands`, and `next_recommendation`
- optional `session_id` and `baseline_run` when the action creates or resumes a repair session
- optional `context_paths`: additive local evidence pointers for recommendation-aware packets, such as `.qa-z/loops/history.jsonl`, `.qa-z/loops/<loop-id>/self_inspect.json`, `docs/generated-vs-frozen-evidence-policy.md`, `docs/reports/worktree-triage.md`, `docs/reports/worktree-commit-plan.md`, or `docs/reports/current-state-analysis.md`

Recommendation-aware worktree and integration packets now keep the existing action types but narrow their follow-up guidance:

- loop-health recommendations such as `improve_fallback_diversity` keep the `loop_health_plan` type but carry selected task evidence paths, loop-local self-inspection, and report references through `context_paths`
- cleanup recommendations such as `reduce_integration_risk` or `isolate_foundation_commit` attach stable commands like `git status --short`, `python scripts/runtime_artifact_cleanup.py --json`, `python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json`, and `python -m qa_z self-inspect --json`, and now also carry loop-local self-inspection through `context_paths`
- runtime-artifact cleanup packets that keep the `triage_and_isolate_changes` recommendation add `python scripts/runtime_artifact_cleanup.py --apply --json` and change `next_recommendation` to clear policy-managed runtime artifacts before rerunning self-inspection
- `audit_worktree_integration` keeps the `workflow_gap_plan` type but carries the current-state, worktree-triage, and worktree-commit reports plus loop-local self-inspection through `context_paths`
- deferred generated cleanup through `triage_and_isolate_changes` keeps the `integration_cleanup_plan` type but carries `docs/generated-vs-frozen-evidence-policy.md` and `scripts/runtime_artifact_cleanup.py` through `context_paths` alongside worktree triage and commit-plan reports

That means cleanup and workflow prepared actions also carry loop-local self-inspection, so later bridge, release, or operator surfaces can recover the exact self-inspection artifact that produced the worktree-oriented recommendation instead of relying on a newer `latest` file.

For repair-session actions, QA-Z calls the existing local `repair-session` creation path and records the created `session_id`, `session_dir`, `handoff_dir`, `executor_guide`, and baseline run. Autonomy-created repair-session actions now preserve loop-local self-inspection plus selected verification evidence in `context_paths`, so the next bridge package can copy both `.qa-z/loops/<loop-id>/self_inspect.json` and the selected verify summary when those files exist. It does not run the external repair, create a candidate, or verify the candidate inside `qa-z autonomy`.

`qa-z autonomy status` reads local artifacts and returns:

- latest loop id and state
- latest selected task ids
- `latest_selected_fallback_families`: additive copy of the latest outcome `selected_fallback_families` list, used for repeated fallback-family diagnostics
- `latest_live_repository`: compact live repository context from the stored latest selected-task artifact or outcome when available
- `latest_selected_task_details`: additive compact copies of the latest selected task entries as they were written to `selected_tasks.json`, including `id`, `title`, `category`, `recommendation`, `evidence_summary`, optional `selection_priority_score`, and optional `selection_penalty` and `selection_penalty_reasons`
- `latest_prepared_actions`: additive compact copies of the latest prepared action packets, including `type`, `task_id`, `next_recommendation`, optional `commands`, optional `context_paths`, and any session-specific pointers
- `latest_next_recommendations`: additive compact next-step list copied from the latest loop outcome
- optional `latest_selection_gap_reason`
- `latest_backlog_open_count_before_inspection` and `latest_backlog_open_count_after_inspection`
- `latest_loop_health`: compact copy of the latest outcome `loop_health`
- loops completed in the latest autonomy run
- latest runtime target, elapsed, remaining, and budget-met state
- latest loop elapsed seconds and configured minimum loop seconds
- open repair-session count and compact session pointers
- latest observed verification verdict
- top open backlog items, each with compact `title`, `recommendation`, and `evidence_summary`

The status command reads local files only and does not advance loop state. The plain-text status output now also mirrors open session details plus the latest selected-task details, latest prepared action type, next step, commands, `context_paths`, selected fallback families, live repository context, and compact backlog-top-item summaries when that data exists. When present on the stored selected-task artifact, the status view also mirrors `selection_penalty` and `selection_penalty_reasons` so fallback diversity residue stays visible after the loop finishes. When `runtime_target_seconds` is zero, the human runtime line explicitly says `no minimum budget` instead of rendering an `elapsed/0 seconds` fraction.

autonomy loop plans now also mirror selected-task evidence alongside ids, categories, recommendations, action hints, validation command hints, priority scores, selected fallback families, latest live repository context, and any selection residue, so the saved `loop_plan.md` remains self-contained for the next operator. When the latest loop was taskless, the plain-text status output also mirrors `selection_gap_reason`, `loop_health`, and the before/after open backlog counts so operators can tell whether the backlog started empty or was emptied during inspection. The `loop_health.summary` field is also copied into human loop plans and status output.

`qa-z backlog --json` still prints the full backlog artifact. The plain-text `qa-z backlog` view is intentionally operator-focused: it keeps open or active items first, prints each item's title, recommendation, deterministic action hint, deterministic validation command hint, and compact evidence summary, and collapses closed history to a count instead of replaying the entire backlog residue.

When the open item is the dirty-worktree risk candidate, that compact evidence mirrors the same area-count summary from self-inspection so backlog review and selected-task planning point at the same integration surfaces.
The action hint on those human surfaces also reuses the same area evidence, so backlog, selection stdout, and loop plans keep the same first triage target without adding a new machine-readable field.
For commit-isolation items, the same area evidence informs the human action hint even when compact evidence prioritizes the alpha closure snapshot. When that happens, the compact human summary can append an `action basis:` suffix with the area-bearing `git_status` summary. Consumers that need the full detail should read the unchanged `evidence` array from the JSON artifact.
Paths under `benchmarks/results/` and sibling snapshot directories matching `benchmarks/results-*` are treated as local-by-default benchmark result evidence for dirty-worktree classification. They stay visible through `benchmark_result_paths` and `dirty_benchmark_result_count`, not `runtime_artifact_paths`, unless a commit intentionally freezes them as evidence with surrounding context. The `triage_and_isolate_changes` action hint now names that local-only versus intentional frozen evidence decision while keeping the JSON recommendation id unchanged. For `runtime_artifact_cleanup_gap`, the same recommendation id now tells operators to clear policy-managed runtime artifacts before source integration and to keep frozen evidence only when intentional.
When a `triage_and_isolate_changes` item has secondary `generated_outputs` or `runtime_artifacts` evidence but compact evidence leads with a report summary, the human compact summary can append that secondary evidence as `action basis:`. This is presentation-only; the unchanged JSON `evidence` array remains the source of truth.
The matching autonomy prepared action also carries `docs/generated-vs-frozen-evidence-policy.md` through `context_paths`, so external operators receive the policy context with the deterministic cleanup packet.

`qa-z backlog --json` prints the current `backlog.json` shape. If no backlog exists yet, it prints an empty backlog object rather than inventing candidates.

## Executor Bridge Artifacts

`qa-z executor-bridge` packages an existing autonomy-prepared repair session or a manually-created repair session for an external executor. It is a local bridge contract only. It does not call Codex or Claude APIs, edit files, run queues, schedule jobs, create branches, commit, push, post GitHub comments, or apply executor results.

Supported sources:

```bash
python -m qa_z executor-bridge --from-loop <loop-id>
python -m qa_z executor-bridge --from-session .qa-z/sessions/<session-id>
```

The command writes:

```text
.qa-z/executor/<bridge-id>/
  bridge.json
  result_template.json
  executor_guide.md
  codex.md
  claude.md
  inputs/
    autonomy_outcome.json   # only for loop-sourced bridges
    session.json
    handoff.json
    context/
      001-summary.json       # copied action context, when provided
    executor_safety.json
    executor_safety.md
```

`bridge.json` has:

- `kind`: stable artifact kind, currently `qa_z.executor_bridge`
- `schema_version`: integer schema marker, currently `1`
- `bridge_id` and `created_at`
- `status`: currently `ready_for_external_executor`
- `source_loop_id`: loop id when sourced from autonomy, otherwise `null`
- `source_session_id`
- `source_self_inspection`, `source_self_inspection_loop_id`, `source_self_inspection_generated_at`, and `live_repository`: source self-inspection path, provenance, and compact live repository context copied from the source autonomy outcome when present
- `selected_task_ids`
- `prepared_action_type`
- `baseline_run_dir`
- `session_dir`
- `handoff_path`
- `handoff_paths`: original session-local handoff, Codex, Claude, and executor guide pointers
- `bridge_dir`
- `inputs`: bridge-local copied input artifact paths, including optional `action_context` copy records and `action_context_missing` skipped context paths
- `validation_commands`: exact argv arrays the external executor should run after editing
- `safety_package`: copied safety package summary with `package_id`, `status`, copied policy paths, ordered rule ids, and safety rule count
- `non_goals`: executor safety boundaries such as no unrelated refactors, no broadened scope, no weakened checks, no live API calls from QA-Z, and no commit/push/GitHub bot behavior
- `safety_constraints`: short operational guardrails for scoped execution
- `return_contract`: expected post-repair handoff back to QA-Z
- `evidence_summary`: compact loop/session/handoff context

The return contract records:

- `expected_next_step`: currently `run repair-session verify after edits`
- `candidate_worktree`: candidate edits happen in the repository working tree outside QA-Z
- `repair_notes`: optional external executor notes may live outside QA-Z
- `verify_command`: primary validation command
- `expected_result_artifact`: bridge-local `result.json` path the external executor should write before re-entry
- `result_template_path`: bridge-local `result_template.json` path with the expected executor-result shape
- `verification_hint_default`: default post-edit QA-Z verification mode, currently `rerun`
- `expected_verify_artifacts`: session-local `verify/summary.json`, `verify/compare.json`, and `verify/report.md`
- `partial_completion`: instruction to preserve evidence and report remaining failures when validation cannot pass

`result_template.json` is a machine-readable starter payload for the expected `qa_z.executor_result` artifact. It uses the owning bridge id, session id, optional loop id, bridge validation commands, and the default verification hint as scaffolding. The placeholder summary must be replaced before ingestion.

When a loop-sourced repair-session action carries `context_paths`, the bridge copies existing file inputs under the repository root into `inputs/context/` with deterministic ordinal filenames. `inputs.action_context` records each `source_path` and bridge-local `copied_path`; `inputs.action_context_missing` records missing, non-file, or out-of-root context paths without failing the bridge package.

`executor_guide.md` is the human-readable bridge guide. It explains why the work was selected, the live repository context that shaped selection when available, what to fix, where to look, how the copied safety package constrains the work, which bridge-local action context inputs were copied, the guide safety rule count, how to validate, how to fill the result template, and how to return control to QA-Z.

`codex.md` and `claude.md` are bridge-specific executor-facing wrappers around the same session, handoff, safety-package inputs, copied action context inputs, live repository context, and guide safety rule count. They do not invoke either executor. They are files for an external operator or tool to consume.

The non-JSON CLI output includes bridge stdout return pointers for the result template, expected result artifact, copied safety package, safety rule count, live repository context when present, and verification command. The guides and stdout include template placeholder guidance so the scaffolded result summary is replaced before ingest. JSON output remains the full manifest.

## Executor Result Ingest

`qa-z executor-result ingest --result <path>` is the return path from an external executor back into QA-Z. It validates a structured result manifest, checks freshness and provenance against the source bridge, session, and ingest reference time, rejects `changed_files` outside the bridge handoff `repair.affected_files`, stores accepted results under the session, and follows the declared verification hint only when verify-resume preconditions pass.

The command reads a `qa_z.executor_result` artifact. Required top-level fields are:

- `kind`: stable artifact kind, currently `qa_z.executor_result`
- `schema_version`: integer schema marker, currently `1`
- `bridge_id`
- `source_session_id`
- `source_loop_id`: optional loop id when the bridge was created from autonomy
- `created_at`
- `status`: one of `completed`, `partial`, `failed`, `no_op`, or `not_applicable`
- `summary`: concise executor outcome summary
- `verification_hint`: one of `rerun`, `candidate_run`, or `skip`
- `candidate_run_dir`: required when `verification_hint` is `candidate_run`
- `changed_files`: ordered list of changed-file entries
- `validation`: validation status, commands, and optional per-command results
- `notes`: optional short free-form notes

Each changed-file entry includes:

- `path`
- `status`: `added`, `modified`, `deleted`, `renamed`, or `unknown`
- `old_path`: optional previous path for renames
- `summary`: optional concise note

The validation object includes:

- `status`: `passed`, `failed`, or `not_run`
- `commands`: ordered argv arrays the executor used or deferred
- `results`: optional command result entries

Each validation result entry includes:

- `command`
- `status`
- `exit_code`
- `summary`

Every ingest attempt with a readable `qa_z.executor_result` payload writes:

```text
.qa-z/executor-results/<result-id>/ingest.json
.qa-z/executor-results/<result-id>/ingest_report.md
```

`ingest.json` records:

- `kind`: stable artifact kind, currently `qa_z.executor_result_ingest`
- `schema_version`: integer schema marker, currently `1`
- `result_id`: stable ingest record id derived from the bridge id and result timestamp
- `bridge_id`, `session_id`, and `source_loop_id`
- `source_self_inspection`, `source_self_inspection_loop_id`, `source_self_inspection_generated_at`, and `live_repository`: source bridge context copied from the loop-sourced executor bridge when present
- `result_status`: executor-reported status
- `ingest_status`: one of `accepted`, `accepted_with_warning`, `accepted_partial`, `accepted_no_op`, `rejected_stale`, `rejected_mismatch`, or `rejected_invalid`
- `stored_result_path`: accepted session-local result path, or `null`
- `session_state`: updated session state when the result was stored, or `null`
- `verification_hint`
- `verification_triggered`
- `verification_verdict`
- `verify_summary_path`
- `warnings`: conservative ingest warnings such as missing timestamps, future-dated or conflicting validation evidence, weak no-op explanations, missing candidate runs, or suspicious completed results without changed files
- `freshness_check`: freshness status, reason, bridge/session/result timestamps, the `ingested_at` reference time, details, and warnings
- `provenance_check`: provenance status, reason, and details
- `verify_resume_status`: one of `ready_for_verify`, `ingested_with_warning`, `verify_blocked`, `stale_result`, or `mismatch_detected`
- `backlog_implications`: structural follow-up candidates derived from freshness, mismatched provenance, partial, weak no-op, or validation-consistency gaps
- `next_recommendation`
- `ingest_artifact_path` and `ingest_report_path`

`ingest_report.md` mirrors source self-inspection provenance in a `Source Context` section when any source field is present, and mirrors live repository details in a `Live Repository Context` section when the bridge supplied them. Non-JSON `qa-z executor-result ingest` stdout prints the ingest report path, then mirrors source self-inspection, source loop, source generation time, live repository context, freshness and provenance status, warnings, and backlog implication categories so the first operator-facing surface carries the same provenance as JSON and Markdown.

When ingestion is accepted, QA-Z stores the result at:

```text
.qa-z/sessions/<session-id>/executor_result.json
```

Every readable executor-result attempt whose owning session can be resolved also writes:

```text
.qa-z/sessions/<session-id>/executor_results/history.json
.qa-z/sessions/<session-id>/executor_results/attempts/<attempt-id>.json
```

`history.json` records:

- `kind`: stable artifact kind, currently `qa_z.executor_result_history`
- `schema_version`: integer schema marker, currently `1`
- `session_id`
- `updated_at`
- `attempt_count`
- `latest_attempt_id`
- `attempts`: ordered attempt summaries

Each attempt summary includes:

- `attempt_id`
- `recorded_at`
- `bridge_id`
- `source_loop_id`
- `source_self_inspection`, `source_self_inspection_loop_id`, `source_self_inspection_generated_at`, and `live_repository`: source bridge context copied from the ingest summary when present
- `result_status`
- `ingest_status`
- `verify_resume_status`
- `verification_hint`
- `verification_triggered`
- `verification_verdict`
- `validation_status`
- `warning_ids`
- `backlog_categories`
- `changed_files_count`
- `notes_count`
- `attempt_path`
- `ingest_artifact_path`
- `ingest_report_path`
- `freshness_status` and optional `freshness_reason`
- `provenance_status` and optional `provenance_reason`

When no prior history exists but the session already has a stored legacy `executor_result.json`, QA-Z backfills a single readable attempt into `history.json` before appending newer attempts.

The ingest step may also:

- update `session.json` with the latest executor-result status and bridge pointer
- move the session state to `candidate_generated` or `failed` before verification
- run the existing `repair-session verify` flow only when the result is fresh enough, validation evidence is consistent enough, provenance checks pass, and the verify-resume state is `ready_for_verify` or `ingested_with_warning`
- update `.qa-z/loops/history.jsonl` when the result came from an autonomy loop, including `executor_ingest_status` and `executor_verify_resume_status`
- leave a rejected or verify-blocked result outside the session while still preserving the ingest artifact and report under `.qa-z/executor-results/`

`qa-z executor-result dry-run --session <session>` evaluates the recorded session history against the frozen pre-live safety package and writes:

```text
.qa-z/sessions/<session-id>/executor_results/dry_run_summary.json
.qa-z/sessions/<session-id>/executor_results/dry_run_report.md
```

`dry_run_summary.json` records:

- `kind`: stable artifact kind, currently `qa_z.executor_result_dry_run`
- `schema_version`: integer schema marker, currently `1`
- `session_id`
- `history_path`
- `safety_package_id`
- `summary_source`: provenance for this dry-run summary, currently `materialized` for the persisted artifact written by `qa-z executor-result dry-run`
- `evaluated_attempt_count`
- `latest_attempt_id`
- `latest_result_status`
- `latest_ingest_status`
- `verdict`: currently `clear`, `attention_required`, or `blocked`
- `verdict_reason`: stable machine-readable reason for the current verdict
- `history_signals`
- `operator_decision`: deterministic primary action id for operator-facing surfaces, aligned with the first `recommended_actions` entry
- `operator_summary` and `recommended_actions`: deterministic operator-facing summary plus ordered action objects derived from the same history signals; blocked mixed-history summaries may keep verification blockers primary while still carrying adjacent validation-conflict or retry-pressure residue
- `rule_status_counts`: counts for `clear`, `attention`, and `blocked` rule outcomes
- `rule_evaluations`: ordered rule outcomes with `id`, `status`, and `summary`
- `next_recommendation`
- `report_path`

Human `qa-z executor-result dry-run` output mirrors the same dry-run summary contract with `Source:`, `Why:`, ordered `Rule counts: clear=..., attention=..., blocked=...`, `Decision:`, `Diagnostic:`, and `Action <id>:` lines before `Next:`. The action id comes from each recommended action object, so operator-facing text and JSON stay aligned.

The dry-run rule catalog is the seven-rule runtime audit set emitted by
`rule_evaluations`. It extends the frozen safety package by combining the six
frozen pre-live rules from the executor safety rule catalog with the
dry-run-only `executor_history_recorded` rule, which marks empty recorded
history as attention instead of pretending that no attempts are clear evidence.

The dry-run is live-free: it does not invoke an external executor, mutate code, or schedule retries. It audits the full recorded session history plus the latest attempt against the current frozen safety rules.

When `dry_run_summary.json` is missing but `executor_results/history.json` is present and readable, repair-session status, completed session summaries, publish summaries, GitHub summaries, and self-inspection may synthesize the same dry-run residue in memory. Those additive surfaces expose the provenance as `executor_dry_run_source: history_fallback` instead of pretending the materialized dry-run artifact exists. Self-inspection evidence summaries also keep that provenance inline through `source=history_fallback`, while materialized dry-run evidence keeps `source=materialized`. Human `repair-session status` output also keeps the same source visible through an `Executor dry-run source:` line and mirrors operator guidance through `Executor dry-run decision:`, `Executor dry-run diagnostic:`, and an action line.
