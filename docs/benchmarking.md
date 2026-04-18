# QA-Z Benchmarking

The QA-Z benchmark corpus is a small seeded evaluation set for checking whether the current control plane behaves consistently across fast checks, deep findings, repair handoff generation, and post-repair verification.

It is not a live repair loop. It does not call Codex, Claude, remote APIs, queues, or schedulers. Fixtures either run deterministic local QA-Z flows or compare pre-seeded run artifacts.

## Running The Benchmark

Run the committed corpus from the repository root:

```bash
python -m qa_z benchmark
```

The command writes:

```text
benchmarks/results/summary.json
benchmarks/results/report.md
benchmarks/results/work/
```

`summary.json` is the machine-readable source of truth and includes a compact `snapshot` string such as `50/50 fixtures, overall_rate 1.0`. `report.md` is the human-readable companion and repeats the same snapshot. `work/` contains isolated copies of fixture repositories and generated QA-Z artifacts; it is disposable generated output.

The generated-versus-frozen evidence policy lives in `docs/generated-vs-frozen-evidence-policy.md`. `benchmarks/results/summary.json` and `benchmarks/results/report.md` are local by default and should be committed only as intentional frozen evidence with surrounding context. `benchmarks/results/work/` remains local scratch output. The generated `report.md` repeats this policy and labels category rows as `covered` or `not covered`; selected-fixture runs can leave unrelated categories uncovered even when the selected fixtures pass.

Useful variants:

```bash
python -m qa_z benchmark --json
python -m qa_z benchmark --fixture semgrep_eval
python -m qa_z benchmark --fixtures-dir benchmarks/fixtures --results-dir benchmarks/results
```

The exit code is `0` only when every selected fixture passes its expected-result contract.

## Fixture Layout

Each fixture lives under `benchmarks/fixtures/<name>/`:

```text
benchmarks/
  fixtures/
    py_type_error/
      expected.json
      repo/
        qa-z.yaml
        qa/contracts/contract.md
        src/app.py
```

The runner copies `repo/` into `benchmarks/results/work/<name>/repo` before execution, then injects shared helpers from `benchmarks/support/`. Fixtures should stay small and intentional; they are test vectors, not demo applications.

## Expected Contract

`expected.json` declares which QA-Z flows to run and which outcomes must be observed. List expectations use subset matching so fixtures can assert important evidence without becoming brittle.

Example:

```json
{
  "name": "semgrep_eval",
  "run": {
    "fast": true,
    "deep": true,
    "repair_handoff": true
  },
  "expect_fast": {
    "status": "passed",
    "failed_checks": [],
    "schema_version": 2
  },
  "expect_deep": {
    "status": "failed",
    "blocking_findings_min": 1,
    "rule_ids": ["python.lang.security.audit.eval"],
    "schema_version": 2
  },
  "expect_handoff": {
    "repair_needed": true,
    "target_sources": ["deep_finding"],
    "affected_files": ["src/app.py"],
    "validation_command_ids": ["qa-z-fast", "qa-z-deep"],
    "schema_version": 1
  }
}
```

Supported expectation sections:

- `expect_fast`: fast run status, schema version, failed check ids, blocking failed check ids
- `expect_deep`: deep run status, schema version, finding counts, blocking/filtered/grouped count thresholds, rule ids, filter reasons, policy metadata, and config-error surfacing
- `expect_handoff`: repair-needed flag, target ids, target sources, affected files, validation command ids, schema version
- `expect_verify`: verdict, schema version, blocking before/after, resolved count, remaining issue count, new issue count, regression count
- `expect_executor_bridge`: bridge kind, schema version, source loop/session ids, prepared action type, action context source paths, copied bridge-local paths, missing context paths/count, copied-file existence, copied-context guide/stdout visibility, and missing-context guide/stdout visibility
- `expect_executor_result`: result status, ingest status, session state, verification hint/trigger, recommendation, warning ids, backlog implication categories, and freshness or provenance reasons when needed
- `expect_executor_dry_run`: dry-run verdict, verdict reason, evaluated-attempt count, latest result/ingest status, dry-run summary provenance, history signals, rule-id buckets, rule-status counts, operator decision, operator summary, recommended action ids/summaries, and next recommendation aliases

Numeric keys ending in `_min` or `_max` are threshold checks. Other scalar keys are exact checks.

Mixed-surface realism fixtures also use a few additive aliases instead of introducing a second contract format:

- `remaining_issue_count_min` asserts conservative unchanged or partial outcomes without relying only on `blocking_after`
- `expected_ingest_status` compares against the normalized executor-result ingest classification
- `expected_recommendation` compares against the recorded next operator action
- `warning_ids_absent`, `backlog_categories`, and `freshness_reason` let fixtures assert ingest realism without matching full ingest reports
- `action_context_paths`, `action_context_copied_paths`, `action_context_count`, `action_context_missing`, `action_context_missing_count`, `action_context_files_exist`, `guide_mentions_action_context`, `guide_mentions_missing_action_context`, `stdout_mentions_action_context`, and `stdout_mentions_missing_action_context` let executor bridge fixtures pin bridge-local action context copying plus guide/stdout missing-context diagnostics without matching the entire bridge manifest
- `expected_source` compares against the materialized dry-run `summary_source` field without renaming the underlying artifact key
- `attention_rule_ids`, `blocked_rule_ids`, `clear_rule_ids`, `attention_rule_count`, `blocked_rule_count`, `clear_rule_count`, `history_signals`, `operator_decision`, `operator_summary`, `recommended_action_ids`, and `recommended_action_summaries` let dry-run fixtures pin the important safety signals and operator guidance without copying whole reports

For deep policy fixtures, `rule_ids_present` and `rule_ids_absent` compare against the normalized active or grouped findings that remain after ignore-rule and exclude-path policy is applied. Filtered findings are still counted in `findings_count` and `filtered_findings_count`, but their rule ids are not retained in the final active `rule_ids` list. Use `expect_config_error: true` when a fixture must prove an invalid Semgrep configuration surfaces as an execution error instead of looking like a clean no-finding run.

## Initial Corpus

The corpus covers these high-signal cases:

- `py_type_error`
- `py_test_failure`
- `py_lint_failure`
- `ts_lint_failure`
- `ts_type_error`
- `ts_test_failure`
- `ts_multiple_fast_failures`
- `mixed_py_resolved_ts_regressed_candidate`
- `mixed_ts_resolved_py_regressed_candidate`
- `mixed_all_resolved_candidate`
- `mixed_partial_resolved_with_regression_candidate`
- `mixed_fast_handoff_functional_worktree_cleanup`
- `mixed_fast_deep_handoff_dual_surface`
- `mixed_fast_deep_handoff_ts_lint_python_deep`
- `mixed_fast_deep_handoff_py_lint_ts_test_dual_deep`
- `executor_bridge_action_context_inputs`
- `executor_bridge_missing_action_context_inputs`
- `mixed_docs_schema_sync_maintenance_candidate`
- `executor_result_partial_mixed_verify_candidate`
- `executor_result_no_op_with_justification_candidate`
- `executor_dry_run_clear_verified_completed`
- `executor_dry_run_repeated_partial_attention`
- `executor_dry_run_completed_verify_blocked`
- `executor_dry_run_validation_noop_operator_actions`
- `executor_dry_run_repeated_rejected_operator_actions`
- `executor_dry_run_repeated_noop_operator_actions`
- `executor_dry_run_blocked_mixed_history_operator_actions`
- `executor_dry_run_empty_history_operator_actions`
- `executor_dry_run_scope_validation_operator_actions`
- `executor_dry_run_missing_noop_explanation_operator_actions`
- `executor_dry_run_mixed_attention_operator_actions`
- `mixed_cleanup_only_worktree_risk_candidate`
- `semgrep_eval`
- `semgrep_shell_true`
- `semgrep_hardcoded_secret`
- `deep_severity_threshold_warn_filtered`
- `deep_ignore_rule_suppressed`
- `deep_exclude_paths_skipped`
- `deep_grouped_findings_dedup`
- `deep_filtered_vs_blocking_counts`
- `deep_config_error_surface`
- `fast_and_deep_blocking`
- `unchanged_candidate`
- `improved_candidate`
- `regressed_candidate`
- `ts_unchanged_candidate`
- `ts_regressed_candidate`

The fast fixtures use deterministic helper commands so the benchmark is not coupled to local `ruff`, `mypy`, `pytest`, `eslint`, `tsc`, or `vitest` behavior. The Semgrep fixtures use a deterministic local `semgrep` stand-in that emits normalized Semgrep JSON, which exercises QA-Z deep normalization without requiring Semgrep to be installed.

## TypeScript Fast Fixtures

TypeScript benchmark fixtures reuse the same expected-result contract as Python fixtures. Do not add a TypeScript-only expectation section unless the runner starts producing language-specific artifact fields.

A minimal TypeScript fast fixture should configure one or more explicit checks in `repo/qa-z.yaml`:

```json
{
  "project": {"name": "ts-type-error", "languages": ["typescript"]},
  "contracts": {"output_dir": "qa/contracts"},
  "fast": {
    "output_dir": ".qa-z/runs",
    "fail_on_missing_tool": true,
    "checks": [
      {
        "id": "ts_type",
        "enabled": true,
        "run": [
          "python",
          ".qa-z-benchmark/fast_check.py",
          "fail",
          "src/invoice.ts(1,14): error TS2322"
        ],
        "kind": "typecheck"
      }
    ]
  },
  "deep": {"checks": []}
}
```

The expected contract stays language neutral:

```json
{
  "name": "ts_type_error",
  "run": {
    "fast": true,
    "repair_handoff": true
  },
  "expect_fast": {
    "status": "failed",
    "blocking_failed_checks": ["ts_type"],
    "schema_version": 2
  },
  "expect_handoff": {
    "repair_needed": true,
    "target_sources": ["fast_check"],
    "affected_files": ["src/invoice.ts"],
    "validation_command_ids": ["check:ts_type", "qa-z-fast"],
    "schema_version": 1
  }
}
```

Use `ts_lint`, `ts_type`, and `ts_test` for the built-in TypeScript fast-check surface. Multi-failure fixtures should assert the aggregated `target_ids` and the deduplicated `target_sources`, but should avoid brittle assumptions about generated Markdown text.

Verification fixtures can seed TypeScript summaries under `.qa-z/runs/baseline/fast/summary.json` and `.qa-z/runs/candidate/fast/summary.json`. The seeded set covers `unchanged` and `regressed` TypeScript candidate verdicts, while the mixed-language verification fixtures cover cross-language `improved` and `mixed` outcomes.

## Mixed-Language Verification Fixtures

Mixed-language verification fixtures use pre-seeded fast summaries for repositories that declare both Python and TypeScript. They protect the post-repair verdict logic when a candidate changes one language while affecting the other.

The current mixed set covers:

- Python blocker resolved while TypeScript regresses: `mixed`
- TypeScript blocker resolved while Python regresses: `mixed`
- Python and TypeScript blockers both resolved: `improved`
- one blocker resolved, one remains, and another check regresses: `mixed`

Keep these fixtures verification-focused. They should not execute local Python or TypeScript tools, and they should not introduce deep findings unless the comparison behavior itself needs a deep mixed-language guard.

## Mixed-Surface Realism Fixtures

Mixed-surface realism fixtures extend the seeded verification set with more service-repository style combinations:

- executed fast plus repair handoff coverage where a functional fix also carries worktree cleanup context
- executed mixed Python/TypeScript fast failures plus Semgrep-backed deep findings in one repair handoff: `mixed_fast_deep_handoff_dual_surface`
- executed TypeScript lint evidence plus Python Semgrep-backed deep evidence in one repair handoff: `mixed_fast_deep_handoff_ts_lint_python_deep`
- executed Python lint evidence plus TypeScript test evidence plus dual Python/TypeScript deep findings in one repair handoff: `mixed_fast_deep_handoff_py_lint_ts_test_dual_deep`
- bridge-local action context copying from a loop-prepared repair session into `inputs/context/`: `executor_bridge_action_context_inputs`
- missing action-context guide and stdout diagnostics for optional context paths that cannot be copied: `executor_bridge_missing_action_context_inputs`
- docs/schema maintenance that stays functionally `unchanged`
- partial executor-result ingest that still points at mixed verify evidence
- justified `no_op` executor returns that avoid the missing-explanation warning while remaining functionally `unchanged`
- cleanup-only worktree risk reduction that does not masquerade as a functional repair
- future-dated executor-result rejection that protects ingest-time freshness checks
- completed executor-result acceptance with validation-evidence conflict that blocks automatic verify resume

These fixtures stay deterministic. They either execute the existing local fast and handoff paths with helper commands or compare pre-seeded run artifacts. They do not claim live executor orchestration, hidden network calls, or LLM-based maintenance scoring.

## Executor Dry-Run Fixtures

Executor dry-run fixtures seed session-local executor-result history and then run `qa-z executor-result dry-run` through the benchmark harness. They protect the live-free safety layer without introducing live retries, agents, queues, or code mutation.

The initial set covers:

- `executor_dry_run_clear_verified_completed`: one accepted completed attempt that is not blocked by verification
- `executor_dry_run_repeated_partial_attention`: repeated partial attempts that should surface manual retry attention
- `executor_dry_run_completed_verify_blocked`: a completed attempt whose recorded history still blocks deterministic completion
- `executor_dry_run_validation_noop_operator_actions`: validation-conflict plus missing no-op explanation history that pins operator summary and recommended action residue
- `executor_dry_run_repeated_rejected_operator_actions`: repeated rejected ingest attempts that pin the rejected-result inspection action
- `executor_dry_run_repeated_noop_operator_actions`: repeated no-op outcomes that pin the repeated no-op pattern action and repeated no-op rule attention through `retry_boundary_is_manual`
- `executor_dry_run_blocked_mixed_history_operator_actions`: blocked completion history combined with repeated partial attempts and validation conflict, proving the blocked verdict stays primary while secondary operator actions remain visible
- `executor_dry_run_empty_history_operator_actions`: no recorded attempts yet, proving dry-run materializes empty history, marks `executor_history_recorded` as empty-history rule attention, and tells the operator to ingest an executor result before relying on safety evidence
- `executor_dry_run_scope_validation_operator_actions`: scope-validation failure history that blocks mutation-scope safety and pins the scope-drift inspection action
- `executor_dry_run_missing_noop_explanation_operator_actions`: missing no-op explanation history that pins the no-op explanation action and matching next recommendation

These fixtures are counted under the existing `policy` benchmark category because they check frozen safety-policy interpretation, not a second execution engine.

Together, all committed executor dry-run fixtures pin `operator_decision`,
`operator_summary`, `recommended_action_ids`, and `recommended_action_summaries` in
`expected.json`, so clear, attention, blocked, repeated rejected, repeated
no-op, blocked mixed-history, empty-history, and scope-validation cases all
protect operator guidance as well as verdict/rule-count behavior.
Every committed executor dry-run fixture now also pins complete dry-run rule buckets through
`clear_rule_ids`, `attention_rule_ids`, and `blocked_rule_ids`, so a missing,
renamed, or re-bucketed rule cannot hide behind unchanged counts.
The dry-run rule catalog is exported from `qa_z.executor_dry_run_logic` as the
seven-rule runtime audit set. It extends the frozen safety package by combining
the six-rule executor safety rule catalog with
`executor_history_recorded`, which exists only to make empty recorded history
auditable at the dry-run layer.
The attention fixtures also pin action-aligned next recommendations for
validation conflicts, missing no-op explanations, repeated no-op outcomes, and
retry-pressure histories.
Repeated no-op rule attention is also pinned at the rule-count level, so the
manual retry-review verdict cannot drift away from `retry_boundary_is_manual`.
Empty-history rule attention is pinned the same way: `no_recorded_attempts`
maps to `executor_history_recorded`, so the ingest-result recommendation has a
matching rule bucket.

## Deep Policy Fixtures

Deep policy fixtures protect how QA-Z applies Semgrep policy after raw findings are available. They are not a claim that QA-Z has multiple deep engines or broad security automation; they are regression guards for the existing Semgrep normalization and benchmark comparison path.

The current policy set covers:

- severity thresholds: warning findings can remain active without blocking when `fail_on_severity` is `ERROR`
- ignored rules: configured `semgrep.ignore_rules` findings are filtered and absent from active rule ids
- excluded paths: `deep.selection.exclude_paths` and check-level Semgrep excludes remove findings from active results
- grouping and dedupe: repeated findings with the same rule, path, and severity become one grouped handoff target
- filtered vs blocking counts: raw, filtered, grouped, and blocking counts stay distinguishable
- config errors: invalid Semgrep config is reported as `status: error` with `semgrep_config_error`

A minimal policy expectation can stay additive inside `expect_deep`:

```json
{
  "name": "deep_ignore_rule_suppressed",
  "run": {
    "deep": true
  },
  "expect_deep": {
    "status": "passed",
    "blocking_findings_count": 0,
    "filtered_findings_count_min": 1,
    "rule_ids_absent": ["generic.secrets.security.detected-private-key"],
    "schema_version": 2
  }
}
```

When adding policy fixtures, prefer one small Semgrep JSON payload under `repo/.qa-z-benchmark/semgrep.json` and an explicit `repo/qa-z.yaml` policy. Avoid exact matches on human-readable messages unless the message itself is the contract under test.

## Adding A Fixture

1. Create `benchmarks/fixtures/<name>/expected.json`.
2. Add a minimal `repo/qa-z.yaml` with only the checks required for the case.
3. Add a small contract under `repo/qa/contracts/contract.md`.
4. Add only the source, test, seeded `.qa-z/runs`, or `.qa-z-benchmark/semgrep.json` files needed by the expected flows.
5. Run `python -m qa_z benchmark --fixture <name>`.
6. Run `python -m pytest tests/test_benchmark.py`.

Keep expectations explicit enough to catch contract drift, but tolerant enough that unrelated artifact details do not break the benchmark.

## Reading Results

`summary.json` reports:

- compact `snapshot` text for closure notes and generated reports
- fixture totals and overall pass rate
- category pass rates for detection, handoff, verification, artifact, and policy checks
- per-fixture pass/fail state
- precise failure reasons
- the actual observed fast/deep/handoff/verify fields used for comparison

`report.md` gives the same information in Markdown for humans.

## Future Work

Future benchmark expansion should add more cross-language edge cases as bugs are found, more Semgrep policy combinations, deeper worktree and integration cleanup combinations, richer operator-facing dry-run diagnostics, and artifact stability expectations for additional reporters. Live executor benchmarking belongs after deterministic orchestration exists; it should not be mixed into this local corpus runner.
