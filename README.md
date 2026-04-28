# QA-Z ⚡

**Codex-first QA control plane for coding-agent workflows.**

QA-Z turns code changes into **QA contracts**, runs deterministic checks, and produces review / repair / verification artifacts that humans and coding agents can act on.

[![CI](https://github.com/qazedhq/qa-z/actions/workflows/ci.yml/badge.svg)](https://github.com/qazedhq/qa-z/actions/workflows/ci.yml)
![Status](https://img.shields.io/badge/status-alpha-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![QA](https://img.shields.io/badge/QA-contract--first-purple)
![Release](https://img.shields.io/badge/release-v0.9.8--alpha-brightgreen)

---

## ✨ What is QA-Z?

Most coding agents are built to **write code**.

QA-Z is built to answer the next question:

> **Should this change be merged — and if not, what should the agent fix next?**

QA-Z gives your repo a local, deterministic QA layer that can:

- 🧾 generate QA contracts from issues, specs, and diffs
- ⚡ run fast checks for Python and TypeScript projects
- 🔎 run Semgrep-backed deep checks
- 🧠 produce review packets and repair prompts
- 🛠️ package repair sessions for Codex, Claude, or human operators
- ✅ verify whether a repair actually improved the result
- 📦 emit GitHub summaries, SARIF, benchmark reports, and local artifacts

---

## 🚀 Quickstart

Install QA-Z locally:

```bash
python -m pip install -e .[dev]
```

Check the CLI:

```bash
python -m qa_z --help
```

Initialize a repo:

```bash
python -m qa_z init --profile python --with-agent-templates --with-github-workflow
```

Validate the config:

```bash
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

Run the fast gate:

```bash
python -m qa_z fast --selection smart --diff changes.diff
```

Run the deep gate:

```bash
python -m qa_z deep --selection smart --diff changes.diff
```

Generate a review packet:

```bash
python -m qa_z review --from-run latest
```

Generate an agent-ready repair prompt:

```bash
python -m qa_z repair-prompt --from-run latest --adapter codex
```

---

## 🧭 Core workflow

```text
init
  ↓
plan
  ↓
fast
  ↓
deep
  ↓
review
  ↓
repair-prompt
  ↓
external repair
  ↓
verify
  ↓
github-summary
```

QA-Z does **not** edit your code by itself.

It creates the contracts, evidence, prompts, and verification artifacts that make external repair work safer and easier to review.

---

## 🧩 Command surface

| Command | What it does |
| --- | --- |
| `qa-z init` | Create starter QA-Z config and optional templates |
| `qa-z doctor` | Validate config shape and launch readiness |
| `qa-z plan` | Generate a QA contract from issue/spec/diff input |
| `qa-z fast` | Run deterministic fast checks |
| `qa-z deep` | Run configured Semgrep deep checks |
| `qa-z review` | Render a review packet from run artifacts |
| `qa-z repair-prompt` | Generate Codex / Claude / handoff repair prompts |
| `qa-z repair-session` | Package a local repair workflow |
| `qa-z verify` | Compare baseline and candidate run artifacts |
| `qa-z github-summary` | Render GitHub Actions summary Markdown |
| `qa-z benchmark` | Run seeded QA-Z benchmark fixtures |
| `qa-z self-inspect` | Inspect QA-Z artifacts and surface improvement tasks |
| `qa-z select-next` | Select the next evidence-backed improvement task |
| `qa-z backlog` | Refresh or inspect the improvement backlog |
| `qa-z autonomy` | Run deterministic local planning loops |
| `qa-z executor-bridge` | Package a loop/session for an external executor |
| `qa-z executor-result` | Ingest and audit external executor results |

---

## ⚡ Fast checks

QA-Z can run configured fast checks and store the results under `.qa-z/runs/`.

Typical checks include:

- Python lint, format, typecheck, and tests
- TypeScript lint, typecheck, and tests
- full or smart diff-aware selection
- strict no-tests policy support
- JSON and Markdown artifacts

Example:

```bash
python -m qa_z fast --json
python -m qa_z fast --selection smart --diff changes.diff
```

---

## 🔎 Deep checks

QA-Z deep checks currently focus on Semgrep-backed static analysis.

Deep runs can:

- attach to the latest fast run
- run standalone into a chosen output directory
- target changed source/test files in smart mode
- escalate risky or ambiguous changes to a full scan
- emit normalized findings and SARIF

Example:

```bash
python -m qa_z deep --from-run latest
python -m qa_z deep --sarif-output qa-z.sarif
```

Default SARIF output:

```text
.qa-z/runs/<run-id>/deep/results.sarif
```

---

## 🛠️ Repair workflow

QA-Z turns failed checks and blocking deep findings into repair-ready artifacts.

```bash
python -m qa_z repair-prompt --from-run latest --adapter codex
```

Generated artifacts include:

```text
.qa-z/runs/<run-id>/repair/handoff.json
.qa-z/runs/<run-id>/repair/codex.md
.qa-z/runs/<run-id>/repair/claude.md
```

These files are designed for:

- Codex
- Claude
- a human reviewer
- another external coding executor

QA-Z itself does **not** call live model APIs.

---

## ✅ Verification

After a repair, QA-Z can compare a baseline run with a candidate run.

```bash
python -m qa_z verify \
  --baseline-run .qa-z/runs/baseline \
  --candidate-run .qa-z/runs/candidate
```

Possible verdicts:

- `improved`
- `unchanged`
- `mixed`
- `regressed`
- `verification_failed`

---

## 📦 Artifacts

QA-Z is artifact-first.

Most outputs are written under:

```text
.qa-z/
```

Common artifact surfaces:

| Path | Purpose |
| --- | --- |
| `.qa-z/runs/` | Fast/deep run evidence |
| `.qa-z/sessions/` | Local repair sessions |
| `.qa-z/executor/` | External executor bridge packages |
| `.qa-z/executor-results/` | Returned executor result ingest artifacts |
| `.qa-z/improvement/` | Self-inspection and backlog artifacts |
| `.qa-z/loops/` | Autonomy planning loop artifacts |

Root `.qa-z/**` is local by default and should normally stay out of release commits.

---

## 🧪 Validation status

Current alpha validation evidence:

```text
ruff check src tests scripts: passed
ruff format --check src tests scripts: 519 files already formatted
mypy src tests: passed across 507 source files
pytest: 1212 passed
alpha release gate: 29/29 passed
artifact smoke: wheel and sdist passed
artifact forbidden scan: 0 forbidden files
GitHub Actions: test success, qa-z success
```

Release tag:

```text
v0.9.8-alpha
```

---

## 🧱 What QA-Z is not

QA-Z is intentionally **not**:

- ❌ a coding agent
- ❌ an autonomous code editor
- ❌ a live Codex or Claude runtime
- ❌ a queue, scheduler, or remote orchestrator
- ❌ an LLM-only judge replacing deterministic checks
- ❌ a tool that commits, pushes, or posts GitHub comments by itself

QA-Z is the QA layer around those workflows.

---

## 🗺️ Roadmap

Near-term roadmap:

- 🧪 broader TypeScript deep QA automation
- 🔐 multi-engine security checks
- 🧬 property, mutation, smoke, and e2e test integrations
- 🧾 richer GitHub Checks / annotation support
- 📊 stronger benchmark realism for mixed Python + TypeScript repos
- 🛡️ tighter release evidence and artifact hygiene flows

---

## 📚 Docs

Useful starting points:

```text
docs/artifact-schema-v1.md
docs/repair-sessions.md
docs/pre-live-executor-safety.md
docs/generated-vs-frozen-evidence-policy.md
qa-z.yaml.example
examples/typescript-demo/
```

---

## 💡 Positioning

QA-Z is not another coding agent.

It is the **QA control plane** that helps coding agents reach production quality with:

- traceable contracts
- executable checks
- reviewable evidence
- actionable repair feedback
- deterministic verification

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
