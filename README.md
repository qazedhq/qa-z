QA-Z
> A deterministic QA control plane for coding agents.
![Status](https://img.shields.io/badge/status-alpha-orange)
![Release](https://img.shields.io/badge/release-v0.9.8--alpha-blue)
![Model agnostic](https://img.shields.io/badge/model--agnostic-yes-brightgreen)
QA-Z helps teams answer the question every coding-agent workflow eventually reaches:
Should this change be merged, and if not, what exactly should the agent fix next?
It turns issue/spec/diff context into QA contracts, runs deterministic fast and deep checks, and emits review, repair, verification, GitHub summary, and SARIF artifacts that humans or external agents can act on.
---
Why QA-Z?
Coding agents are good at changing code. Production teams still need traceable evidence.
QA-Z is designed to be:
QA-first: focused on merge readiness, not code generation.
Contract-first: every run can be tied back to explicit QA intent.
Deterministic-gated: pass/fail comes from executable checks, not LLM judgment.
Repair-oriented: failures become actionable repair packets.
Model-agnostic: works with Codex, Claude, human operators, or any external executor.
QA-Z is not another coding agent. It does not edit code, call live model APIs, create branches, push commits, or post GitHub comments by itself.
---
What it does
QA-Z can:
initialize a repository QA scaffold;
generate QA contracts from issue, spec, and diff inputs;
run deterministic Python and TypeScript fast checks;
run Semgrep-backed deep checks with SARIF output;
produce review packets and repair prompts from run artifacts;
package local repair sessions and executor handoffs;
ingest external executor results and verify candidate runs against baselines;
render compact GitHub Actions summaries;
run a seeded benchmark corpus for release confidence;
inspect QA-Z artifacts and select evidence-backed improvement tasks.
---
Quickstart
Install from source:
```bash
python -m pip install -e .[dev]
```
Inspect the CLI:
```bash
python -m qa_z --help
```
Initialize a repository:
```bash
python -m qa_z init --profile python --with-agent-templates
python -m qa_z doctor
```
Create a QA contract:
```bash
python -m qa_z plan \
  --title "Protect billing auth guard" \
  --issue issue.md \
  --spec spec.md \
  --diff changes.diff
```
Run QA gates:
```bash
python -m qa_z fast --selection smart --diff changes.diff
python -m qa_z deep --selection smart --diff changes.diff
```
Generate review and repair artifacts:
```bash
python -m qa_z review --from-run latest
python -m qa_z repair-prompt --from-run latest --adapter codex
```
Verify a candidate repair:
```bash
python -m qa_z verify \
  --baseline-run .qa-z/runs/baseline \
  --candidate-run .qa-z/runs/candidate
```
If the `qa-z` console script is on your PATH, you can use `qa-z ...` instead of `python -m qa_z ...`.
---
Core workflow
```text
init
  -> plan
  -> fast
  -> deep
  -> review
  -> repair-prompt
  -> repair-session start
  -> external repair
  -> executor-result ingest
  -> verify
  -> github-summary
```
QA-Z keeps each step local and artifact-driven. The external repair step can be performed by a human, Codex, Claude, or another executor.
---
Command overview
Goal	Command
Bootstrap a repo	`qa-z init`
Validate config	`qa-z doctor`
Create QA contracts	`qa-z plan`
Run fast deterministic checks	`qa-z fast`
Run Semgrep-backed deep checks	`qa-z deep`
Render review packets	`qa-z review`
Generate repair prompts	`qa-z repair-prompt`
Create local repair sessions	`qa-z repair-session`
Compare baseline and candidate runs	`qa-z verify`
Render GitHub Actions summaries	`qa-z github-summary`
Run benchmark fixtures	`qa-z benchmark`
Inspect QA-Z evidence	`qa-z self-inspect`
Maintain/select backlog work	`qa-z backlog`, `qa-z select-next`
Prepare autonomy planning loops	`qa-z autonomy`
Package external executor handoffs	`qa-z executor-bridge`
Ingest external executor results	`qa-z executor-result`
---
Artifacts
QA-Z writes local artifacts under `.qa-z/` so later commands can reason from evidence instead of re-parsing terminal output.
Common outputs include:
```text
.qa-z/runs/<run-id>/summary.json
.qa-z/runs/<run-id>/summary.md
.qa-z/runs/<run-id>/deep/results.sarif
.qa-z/runs/<run-id>/review/packet.json
.qa-z/runs/<run-id>/repair/handoff.json
.qa-z/sessions/<session-id>/manifest.json
.qa-z/sessions/<session-id>/verify/compare.json
.qa-z/executor/<bridge-id>/bridge.json
.qa-z/executor-results/<result-id>/ingest.json
```
Root `.qa-z/**`, build outputs, caches, and benchmark result work directories are local by default and should not be committed unless intentionally frozen as evidence.
---
Deep checks and SARIF
`qa-z deep` runs configured `sg_scan` Semgrep checks when Semgrep is available on `PATH`.
It supports:
full or smart selection;
severity thresholds;
suppression policy;
grouped findings;
normalized JSON summaries;
SARIF 2.1.0 output for GitHub code scanning.
Default SARIF path:
```text
.qa-z/runs/<run-id>/deep/results.sarif
```
You can also write a stable SARIF path:
```bash
python -m qa_z deep --sarif-output qa-z.sarif
```
---
CI usage
QA-Z includes workflow templates for deterministic CI gates.
A typical CI flow runs:
```bash
python -m qa_z fast --selection smart --json
python -m qa_z deep --selection smart --json
python -m qa_z review --from-run latest
python -m qa_z repair-prompt --from-run latest
python -m qa_z github-summary --from-run latest
```
Deep findings can be uploaded as SARIF when the repository grants GitHub code-scanning permissions.
---
Alpha release gate
For QA-Z's own release checks:
```bash
python -m pytest
python scripts/alpha_release_gate.py --json
python scripts/alpha_release_artifact_smoke.py --with-deps --json
```
Current alpha validation baseline:
`pytest`: `1212 passed`
`ruff check`: passed
`ruff format --check`: passed
`mypy`: passed across `507` source files
alpha release gate: `29/29` passed
wheel/sdist install smoke: passed
artifact forbidden-file scan: `0` forbidden files
---
Status
QA-Z is currently in public alpha.
Implemented alpha scope:
local deterministic QA gates;
contract generation;
fast/deep run artifacts;
review and repair packets;
local repair sessions;
executor bridge packaging;
executor-result ingest;
post-repair verification;
GitHub summary and SARIF output;
benchmark and self-inspection workflows.
Not included in this alpha:
autonomous code editing;
live Codex or Claude execution;
remote queues, schedulers, or daemons;
automatic commits, pushes, or GitHub bot comments;
package-registry publishing.
---
Roadmap
Near-term priorities:
keep release evidence and docs synchronized;
expand deterministic benchmark coverage only where it adds unique evidence;
improve GitHub annotation surfaces beyond SARIF;
add more deep-check engines beyond Semgrep;
continue hardening executor-result safety and verification workflows.
Longer-term ideas:
property, mutation, and smoke-test deep checks;
richer PR annotations;
multi-engine security automation;
optional live executor integrations with strict safety boundaries.
---
Repository map
```text
docs/                 design notes, schemas, release notes, and workflow docs
qa/contracts/         QA contract workspace
src/qa_z/             Python package and CLI implementation
templates/            Codex, Claude, and workflow templates
.github/workflows/    repository CI workflows
examples/             Python and TypeScript demos
benchmarks/           seeded benchmark fixtures and support helpers
scripts/              release, smoke, and repository hygiene helpers
```
---
Learn more
Start with:
`qa-z.yaml.example` for the full public config shape;
`docs/artifact-schema-v1.md` for artifact fields;
`docs/repair-sessions.md` for local repair-session behavior;
`docs/pre-live-executor-safety.md` for executor safety boundaries;
`docs/releases/v0.9.8-alpha.md` for release notes.
---
Detailed operator contract index
<details>
<summary>Current-truth maintenance anchors</summary>

These anchors keep the public README aligned with the detailed schema, release
handoff, and current-truth guard tests without making the quickstart depend on
every internal operator field.

- `qa-z.yaml.example` is the authoritative full public example config.
- The root `qa-z.yaml` is Python-only for the repository release gate; TypeScript
  examples live in `qa-z.yaml.example`, examples, and benchmarks.
- `docs/generated-vs-frozen-evidence-policy.md` defines local-only runtime
  artifacts, local-by-default benchmark evidence, and intentional frozen
  evidence.
- Generated-artifact preflight checks keep root `.qa-z/**`,
  `benchmarks/results/work/**`, `build/**`, `dist/**`, and cache output local by
  default.
- `python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json`
  records worktree commit-plan evidence including `unassigned_source_paths`,
  `generated_artifact_paths`, `generated_local_only_paths`,
  `generated_local_by_default_paths`, `cross_cutting_paths`, `changed_batches`,
  `shared_patch_add_paths`, `cross_cutting_groups`, and repository context.
- Gate JSON stores `evidence.worktree_commit_plan`; strict audits use
  `--strict-worktree-plan` with `--fail-on-generated --fail-on-cross-cutting`.
- `generated_local_only_count`, `generated_local_by_default_count`,
  `batch_count`, `attention_reason_count`, `global_attention_reason_count`,
  `attention_reasons`, `strict_worktree_plan`, "Global attention reasons:",
  "Attention reasons:", "Attention reasons are de-duplicated", "Next actions
  are de-duplicated", and "Next commands are de-duplicated" are expected
  operator evidence fields.
- The worktree helper also reports "worktree generated artifact split mismatch",
  "worktree patch-add group mismatch", and `generated_exclude_count`.
- `reduce_integration_risk` prepared actions are tied to the worktree
  commit-plan path rather than generic cleanup.
- Report-only deferred cleanup wording is not enough; live git or runtime
  artifact evidence is required before cleanup candidates reopen.
- `.benchmark.lock` protects benchmark results-dir writes.
- `--from-run` and `--output-dir` cannot be combined for `qa-z deep`.
- Deep scan diagnostics include `scan_warning_count`,
  `scan_quality_warning_count`, and `scan_quality_warning_paths`.
- Benchmark coverage includes `mixed_fast_deep_handoff_dual_surface`.
- Executor dry-run fixtures include
  `executor_dry_run_validation_noop_operator_actions`,
  `executor_dry_run_repeated_rejected_operator_actions`,
  `executor_dry_run_validation_conflict_repeated_rejected_operator_actions`,
  `executor_dry_run_repeated_noop_operator_actions`,
  `executor_dry_run_blocked_mixed_history_operator_actions`,
  `executor_dry_run_empty_history_operator_actions`,
  `executor_dry_run_scope_validation_operator_actions`, and
  `executor_dry_run_missing_noop_explanation_operator_actions`.
- Self-inspection records `backlog_reseeded` and concrete reseed candidate ids.
- GitHub summary supports session candidate resolution:
  `python -m qa_z github-summary --from-session .qa-z/sessions/<session-id>`.
- Session dry-run verdict, reason, source, attempt counts, and history signals
  remain visible for executor-result handoff.
- The generated workflow template is a deterministic CI gate and does not run
  `executor-bridge`.
- README repository map honesty:
  `examples/                 runnable Python and TypeScript demos plus placeholder examples`.
- Near-term roadmap anchors:
  1. Preserve generated versus frozen evidence policy as artifact surfaces evolve.
  2. Maintain loop-health summary clarity as autonomy surfaces grow.
  3. Deepen operator-facing executor diagnostics selectively as new mixed-history combinations add unique residue, without adding live execution.
  4. Broaden mixed-surface benchmark realism only where a new deterministic slice adds unique evidence.
  5. Keep report, template, and example surfaces in current-truth sync as maintenance so they do not drift.
- Remote/repository probe placeholders remain documented as `repo_probe=...`,
  `repo_probe_basis=last_known`, `repo_probe_at=...`,
  `repo_probe_freshness=...`, `repo_probe_age_hours=...`, `repo_http=...`,
  `repo_visibility=...`, `repo_archived=yes|no`, and
  `repo_default_branch=...`.

Exact current-truth anchors:

```text
If `--from-session` is given without an explicit `--from-run`, QA-Z now follows that session's `candidate_run_dir`
intentional frozen evidence
`reseeded_candidate_ids`
--results-dir
session dry-run verdict, reason, source, attempt counts, and history signals
report-only deferred cleanup wording
local-only runtime artifacts
run_resolution
scan_warnings
mixed_fast_deep_handoff_ts_lint_python_deep
operator summary
rejected-result inspection ahead of partial retry review
root deep scan is scoped to `src` and `tests`
The excerpt below shows the intended policy shape:
3. Broaden operator diagnostics and mixed-history depth only where a new deterministic dry-run slice adds unique evidence.
does not run `executor-bridge`
generated-artifact preflight
--summary-only --json
public_docs_contract
command_router_spine
current_truth_guards
cross_cutting_group_count
whichever run currently owns `latest`
Cleanup JSON and human output now include a `reason`
synthetic `backlog_reseeding_gap`
exit code `2`
operator summary and recommended actions
Integration-gap candidates
tracked generated roots
deep_scan_warning_diagnostics
mixed_fast_deep_handoff_py_lint_ts_test_dual_deep
validation conflicts and retry pressure still need review
TypeScript checks remain covered by `qa-z.yaml.example`
5. Keep report, template, and example current-truth sync as maintenance so the alpha docs stay exact.
post GitHub bot comments
strict_mode
worktree patch-add group mismatch
batch_count
generated_exclude_count
Global attention reasons:
attention_reason_count
global_attention_reason_count
Attention reasons:
Attention reasons are de-duplicated
Next actions are de-duplicated
Next commands are de-duplicated
attention_reasons
strict_worktree_plan
review-only local-by-default roots
parallel benchmark runs use .benchmark.lock; one benchmark run owns --results-dir or exits with exit code `2`
synthesizes the same residue from `executor_results/history.json`
git_status
deep_scan_warning_multi_source_diagnostics
mixed_fast_deep_scan_warning_fast_only
safety rule count
gate JSON summarizes pytest, deep, and benchmark evidence
command_surface_tests
benchmark_workflow_templates
release_continuity
helper-derived policy roots
marks the dry-run source as history fallback
audit_worktree_integration
warning checks
executor_bridge_action_context_inputs
guide safety rule count
optional pytest skipped count
status_reports
older benchmark artifact has only counters
contradictory benchmark totals
worktree generated artifact split mismatch
inspect `python -m qa_z benchmark --json`
preflight_failed_checks, next_actions, and next_commands
gate JSON deduplicates promoted attention reasons, next_actions, and
gate reads nested preflight output file when stdout is not JSON
gate reads nested worktree commit-plan output file when stdout is not JSON
gate supplements partial preflight stdout from the output file
gate synthesizes dirty-worktree guidance from failed_checks
human-readable gate output prints Next actions
human-readable gate output prints Evidence
origin_state=
origin_current_target=
origin_current=
refs=
ref_sample=
actual_origin_target
repository_http_status
repository_probe_state
repository_probe_generated_at
repository_visibility
repository_archived
repository_default_branch
remote_ref_count
remote_ref_head_count
remote_ref_tag_count
remote_ref_kinds
publish_strategy
publish_checklist
release_path_state
publish_strategy=push_default_branch
publish_strategy=push_release_branch
publish_strategy=remote_preflight
publish_strategy=bootstrap_origin
ready_for_remote_checks
configured but no `--expected-origin-url` was supplied
preflight:
artifact smoke:
bundle manifest:
build:
cli help:
warning_types=
warning_paths=
warning_checks=
human-readable gate Evidence prints unchanged_batches
human-readable gate Evidence prints batches and changed_paths
human-readable gate Evidence prints generated_files and generated_dirs
reports=
human-readable gate Evidence prints output=
human-readable gate output prints Artifacts
human-readable gate output prints Worktree plan attention
human-readable gate Evidence prints strict=fail_on_generated
human-readable gate output prints `Generated at:`
summary_source: materialized
live_repository
artifact paths
executor_bridge_missing_action_context_inputs
bridge stdout return pointers
release_evidence_consistency
paths_truncated_count
`Rule counts: clear=..., attention=..., blocked=...`
current_branch
missing action-context guide and stdout diagnostics
template placeholder guidance
python scripts/worktree_commit_plan.py --include-ignored --json
patch_add_groups=
shared_patch_add_count=
changed_paths=
`Action <id>:` lines
current_head
ingest stdout diagnostics
operator summary and recommended action residue
gate JSON promotes preflight_failed_checks,
git_add_command
git_add_patch_command
candidate_patch_add_paths
validation_commands
self-inspection now synthesizes the same dry-run residue from that history
dirty_benchmark_result_count
four executed mixed fast plus deep handoff fixtures
ordered `Action <id>:` lines for recommended actions
`origin_state=`
`origin_current_target=`
`origin_current=`
`refs=`
`ref_sample=`
batch filters preserve generated_artifacts_present
batch filters preserve cross_cutting_paths_present
candidate evidence summaries also preserve dry-run provenance as `source=materialized` or `source=history_fallback`
branch=detached
`actual_origin_target`
`repository_http_status`
`repository_probe_state`
`repository_probe_generated_at`
`repository_visibility`
`repository_archived`
`repository_default_branch`
output write failures return exit code `2`
filters runtime-artifact policy gaps through the live ignore policy
dirty_area_summary
`remote_ref_count`
`remote_ref_head_count`
`remote_ref_tag_count`
`remote_ref_kinds`
`remote_ref_sample`
`publish_strategy`
`publish_checklist`
`release_path_state`
`publish_strategy=push_default_branch`
`publish_strategy=push_release_branch`
`publish_strategy=remote_preflight`
`publish_strategy=bootstrap_origin`
closes it instead of leaving stale work permanently selectable
Live repository:
Dirty worktree failures now recommend committing, stashing
they no longer reopen `evidence_freshness_gap` by themselves
`runtime_artifact_cleanup_gap` now outranks the broader `artifact_hygiene_gap`
within-batch fallback-family penalty
recommendation-specific commands plus additive `context_paths`
`python scripts/runtime_artifact_cleanup.py --json`
`python scripts/runtime_artifact_cleanup.py --apply --json`
Deferred generated cleanup packets
`docs/generated-vs-frozen-evidence-policy.md` through `context_paths`
`scripts/runtime_artifact_cleanup.py` through `context_paths`
`latest_prepared_actions` and `latest_next_recommendations` fields
Human `qa-z backlog` output now focuses on open or active items
prints the backlog `Updated:` timestamp
`latest_selected_task_details`, derived directly from the stored latest `selected_tasks.json`
Human `qa-z select-next` output now echoes each selected task's title,
selection score, penalty reasons, and compact evidence summary
selection penalty and its reasons
surface a non-cleanup fallback family before selecting more cleanup work
loop plans now mirror selection score and penalty residue
autonomy loop plans now mirror selected-task evidence summaries
selected fallback families
`latest_selected_fallback_families`
Loop-health packets
loop-history evidence
Autonomy-created repair-session packets
loop-local self-inspection plus selected verification evidence
cleanup and workflow packets now also carry loop-local self-inspection
bridge-local action context inputs
action-context package health
missing action-context diagnostics
non-JSON stdout mirrors source self-inspection, source loop
freshness/provenance checks, warnings, and backlog implications
`selection_gap_reason` plus open backlog counts before and after inspection
`loop_health` summary
blocked no-candidate chain
blocked no-candidate loop ids
`stop_reason`
no minimum budget
treated as local-by-default benchmark result evidence in live repository signals and self-inspection
stay in the `benchmark` bucket for `dirty_area_summary`
not as local-only runtime cleanup pressure
normalize back to the intended repository URL
Set --repository-url to https://github.com/qazedhq/qa-z.git
python scripts/alpha_release_gate.py --include-remote
python scripts/alpha_release_gate.py --json --output dist/alpha-release-gate.json
dist/alpha-release-gate.preflight.json
dist/alpha-release-gate.worktree-plan.json
include `generated_at`
preflight output also print `Generated at:`
check_count, passed_count, failed_count,
skipped_count, failed_checks
canonicalized repository/origin targets
`Target:`
`Origin:`
`Mode:`
`Decision:`
`target=`
`path=`
`blocker=`
`mode=`
`target_url=`
`origin_url=`
schemeless `github.com/owner/repo.git`
benchmarks/results-*
--expected-origin-url
CLI help smoke checks
action basis:
intentional frozen evidence
`generated_outputs` or `runtime_artifacts`
clear policy-managed runtime artifacts before source integration
benchmark-gap evidence preserves the generated benchmark `snapshot`
legacy benchmark summaries
summary-level benchmark-gap item
generated alpha release evidence count
```

</details>
---
Positioning
QA-Z is the QA layer for coding-agent workflows.
It helps agents, reviewers, and CI systems move from “the code changed” to “the change is tested, reviewed, repairable, and ready to evaluate.”
