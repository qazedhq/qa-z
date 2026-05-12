# QA-Z Worktree Commit Plan

Date: 2026-04-15
Branch: `codex/qa-z-bootstrap`

## Goal

Create reversible commit boundaries for the accumulated alpha worktree without
discarding meaningful work or bundling generated runtime artifacts into source commits.

This plan supersedes the earlier benchmark-first ordering. `src/qa_z/benchmark.py`
imports foundation modules that are not present in `HEAD`, so a benchmark-only first
commit would be broken. The corrected order is foundation first, benchmark second.

## Commit Rules

- Do not stage root `.qa-z/**`.
- Do not stage `benchmarks/results/work/**`.
- Do not stage `benchmarks/results/summary.json` or `benchmarks/results/report.md`
  unless the commit explicitly says it is freezing benchmark evidence.
- Keep fixture-local `.qa-z` summaries under `benchmarks/fixtures/**/repo/.qa-z/**`
  when they are benchmark inputs.
- Use `git add -p` for `src/qa_z/cli.py`,
  `src/qa_z/commands/command_registration.py`,
  `src/qa_z/commands/command_registry.py`,
  `src/qa_z/commands/execution.py`, `src/qa_z/commands/runtime.py`,
  `tests/test_command_registry_architecture.py`,
  `tests/test_execution_commands.py`, `tests/test_runtime_commands.py`,
  `README.md`, `docs/artifact-schema-v1.md`, and continuity report files under
  `docs/reports/`; those paths span multiple feature surfaces.
- Run targeted tests for each commit, then run the full validation checklist before
  tagging.

Before staging, run the deterministic dirty-path grouping helper:

```bash
python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting --output .qa-z/tmp/worktree-commit-plan.json
```

The helper reads `git status --short --untracked-files=all`, reports per-batch
changed paths, and keeps `generated_artifact_paths`,
`generated_local_only_paths`, `generated_local_by_default_paths`,
`cross_cutting_paths`, `shared_patch_add_paths`, `cross_cutting_groups`, report
paths, `unassigned_source_paths`, `product_decision_paths`,
`product_decision_groups`, `release_scope_decision_paths`, and
`release_scope_decision_groups` visible so source batches are not mixed with
generated release evidence or unapproved product/network surfaces by accident.
Its summary now also records `generated_local_only_count` and
`generated_local_by_default_count` plus `cross_cutting_group_count` and
`product_decision_path_count`, `release_scope_decision_path_count`,
`approved_alpha_support_path_count`, and `deferred_alpha_scope_path_count`, so
the same helper artifact separates stage-never runtime output from
local-by-default benchmark evidence, shared patch-add review groups, approved
operating-model support scope, and deferred product/network surfaces.
Known overlap paths now resolve more deterministically as well: executor fixture
trees are owned by the executor-return batch, verification/reporter seams fall
under the verification-and-publish batch, and only genuinely unmapped source
surfaces should continue to appear as `unassigned_source_paths`.
CLI, command-registry, live-repository, and report/runtime seams now also share
their own planning-and-runtime foundation batch, so those core local planning
surfaces can be staged together instead of leaking into the generic unassigned
bucket.
The alpha release closure batch now also absorbs artifact-smoke and
bundle-manifest helpers, keeping those release-proof support surfaces aligned
with the gate and preflight changes they validate.
A dedicated deep-runner foundation batch now owns the split `deep.py`,
`deep_policy.py`, `deep_runtime.py`, and `semgrep.py` surfaces plus their
direct architecture tests, while `src/qa_z/runners/models.py` remains
intentionally outside that batch because it is still a shared runner model
spine across fast, deep, verification, and reporting paths.
That shared spine now has its own `runner_contract_spine` batch so
`src/qa_z/runners/models.py` and its direct contract tests can move together
without being mislabeled as deep-only work, while `tests/test_fast_gate_environment.py`
rides with the planning/runtime foundation batch because it guards repo-level
pytest and mypy collection rather than runner behavior itself.
The remaining shared subprocess/tooling surfaces now also resolve more
deterministically: the current Ruff/tool-cache `pyproject.toml` delta plus
`src/qa_z/subprocess_env.py` ride with the planning/runtime foundation batch,
`src/qa_z/runners/subprocess.py` rides with the shared runner contract spine,
and `tests/test_release_script_environment.py` rides with the alpha release
closure batch because it guards the release/preflight/cleanup script lane.
Shared local operator command constants now ride with that same
planning/runtime foundation batch: keep `src/qa_z/operator_commands.py` and
`tests/test_operator_commands.py` together so strict worktree-plan and runtime
cleanup command surfaces stay synchronized across autonomy and task-selection
outputs.
If a future `pyproject.toml` change is purely release-version metadata, still
patch-add only the relevant hunks with the release-closure slice instead of
blindly staging the whole file.
For the stricter final staging audit, rerun it with
`--include-ignored --fail-on-generated` so ignored generated evidence becomes an
explicit `attention_required` reason instead of only an advisory count.
The strict helper output now also prints `Generated policy:` plus local-only
and local-by-default previews, which makes the remaining dirty generated roots
actionable without reopening the full JSON.
When you need to carry that strict audit forward as a local artifact, use
`--output .qa-z/tmp/worktree-commit-plan.json`; the helper now writes the JSON
payload before returning its non-zero `attention_required` exit code, so the
saved evidence survives even when generated artifacts still need review.
For long autonomy or release loops, add `--summary-only --json` when the next
operator only needs compact evidence. That payload omits full per-file `batches`
details while keeping `summary`, `attention_reasons`, `changed_batches`,
generated-path previews, `cross_cutting_paths`, `shared_patch_add_paths`,
`cross_cutting_groups`, `release_scope_decision_groups`,
`approved_alpha_support_groups`, `deferred_alpha_scope_groups`, unresolved
`product_decision_groups`, and repository context.
Each `changed_batches[]` item keeps the batch `message`, validation commands,
and compact staging guidance. When a batch has at most 20 included paths, the
summary preserves a complete `git_add_command` plus `git_add_command_text`;
larger batches keep only path previews plus `include_paths_truncated_count` so
operators do not mistake a partial preview for a complete staging command.
When a batch-filtered compact payload carries patch-add candidates, compact
staging guidance also includes `candidate_patch_add_count`,
`candidate_patch_add_paths`, `git_add_patch_command`, and
`git_add_patch_command_text` for complete small candidate sets.
If a filtered batch has no changed paths, the helper returns
`selected_batch_empty` and a `next_actions` hint to choose a changed batch or
rerun without `--batch`, rather than leaving an `attention_required` status with
no repair reason.
Batch-filtered top-level `attention_reasons` preserve every global blocker,
including unassigned or multi-batch paths; `selected_batch_summary.status` is
the field to read when the operator only needs the selected batch readiness.
Group payloads in summary-only output keep path previews and use
`paths_truncated_count` for oversized review groups instead of carrying full
path lists. They still preserve each group's `patch_command` argv array, so a
compact artifact remains directly actionable for review-surface patch-add
handoff without requiring the human renderer. `patch_command_text` carries the
same command as a copy/paste-friendly shell string with the helper's normal
path quoting, including whitespace and common shell separator characters.
Current compact strict snapshot on `2026-05-03` is still
`attention_required`, but now only because cross-cutting patch-add ownership is
still required: `changed_path_count=53`, `generated_artifact_count=0`,
`generated_local_only_count=0`, `generated_local_by_default_count=0`,
`cross_cutting_count=3`, `cross_cutting_group_count=3`,
`shared_patch_add_count=5`, `unassigned_source_path_count=0`, and
`multi_batch_path_count=0`. The compact payload now includes complete
cross-cutting `patch_command_text` strings plus complete small-batch
`git_add_command_text` strings, so the saved evidence can drive review-surface
patch-add handoff directly while the strict blocker remains intentionally
non-zero until a human chooses the relevant hunks.
`python scripts/runtime_artifact_cleanup.py` now mirrors that same split by
deriving cleanup candidates from the strict helper's generated-policy buckets:
apply mode clears all discovered local-only runtime roots, while benchmark roots
stay review-only local-by-default evidence until an operator decides whether to
keep them local or freeze them intentionally. The latest live cleanup
application deleted `13` local-only roots, left `7` local-by-default benchmark
roots in `review_local_by_default`, and reported `skipped_tracked=0`.
The L24 helper refresh also closed two commit-safety gaps in the batch output:
the runtime no longer trusts collapsed untracked directories, and the shared
command spine now stays patch-add only. The current non-strict helper refresh
shows `478` default porcelain entries versus `517` fully expanded changed
paths, `cross_cutting_count=12`, and `shared_patch_add_count=16`. Those
shared patch-add paths now include `src/qa_z/cli.py`,
`src/qa_z/commands/command_registration.py`,
`src/qa_z/commands/command_registry.py`, `src/qa_z/commands/execution.py`,
`src/qa_z/commands/runtime.py`, `tests/test_command_registry_architecture.py`,
`tests/test_execution_commands.py`, `tests/test_runtime_commands.py`, and the
four continuity reports. Do not stage those shared command/runtime surfaces
wholesale with `planning_runtime_foundation`; patch-add only the owning hunks.
Those shared paths now roll up into `cross_cutting_groups`, including
`public_docs_contract`, `command_router_spine`, `current_truth_guards`,
`command_surface_tests`, and `status_reports`, so an operator can patch-add by
review surface with a scoped `git add --patch` command instead of treating every
cross-cutting path as one flat list.
The helper now applies the explicit alpha release-scope decision to the five
known ownership groups instead of leaving them as generic unresolved product
decisions. `codex_operating_model` and `operating_model_validator` are approved
alpha support scope, while the Claude compatibility mirror plus Marketing/X
surface and tests are deferred out of the QA-Z alpha scope. For the current X
launch automation surface, `marketing/x/**` remains deferred because it can use
credentials, call X APIs, and mutate posting queue state when explicitly
enabled. Unknown future groups can still appear under `product_decision_paths`
with `product_decision_paths_present`, but the current five groups roll up into
`release_scope_decision_groups` and no longer block as unresolved.

| Group | Release scope | Evidence-backed action |
|---|---|---|
| `codex_operating_model` | `approved_alpha_support_scope` | Stage only with the operating-model support batch after validator and format proof. |
| `operating_model_validator` | `approved_alpha_support_scope` | Stage with the operating-model support batch after format and validator checks pass. |
| `claude_compatibility_mirror` | `deferred_out_of_alpha_scope` | Keep out of QA-Z alpha unless a compatibility release decision approves it. |
| `marketing_x_surface` | `deferred_out_of_alpha_scope` | Keep out of QA-Z alpha unless a product owner approves the credential-gated network surface. |
| `marketing_x_tests` | `deferred_out_of_alpha_scope` | Keep with Marketing/X only if that product surface is approved. |

## Alpha Release-Candidate Decision Packet - 2026-05-12

This packet refreshes the release-candidate boundary after the local alpha
closure commits, read-only remote proof, and the human-approved release
execution worktrain audit. Approval flags were absent, so the result is an
execution-ready packet, not a publish.

- Proof timestamp: `2026-05-12T14:33Z`.
- Source HEAD at proof time: `a3e5303933fe9b1bef03e2e915ce224e0cc4e1c1`.
- Branch at proof time: `main`.
- Remote target: `https://github.com/qazedhq/qa-z.git`.
- Remote `main` at proof time:
  `8f647619418b884afa3bef3d839326680bec70af`.
- Publish mode for this packet: `PROOF_ONLY`; approval flags
  `RELEASE_EXECUTION_APPROVED`, `PUSH_ALLOWED`, `TAG_ALLOWED`,
  `GITHUB_RELEASE_ALLOWED`, `PACKAGE_PUBLISH_ALLOWED`, and `DEPLOY_ALLOWED`
  were unset. No push, tag, GitHub release, package publish, deployment,
  credential use, destructive cleanup, or queue mutation was attempted.

Current local evidence:

- Strict worktree plan:
  `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`
  returned `status=ready` with `changed_batch_count=0`,
  `changed_path_count=25`, `product_decision_path_count=0`,
  `product_decision_group_count=0`, `cross_cutting_count=0`,
  `release_scope_decision_path_count=25`, and
  `deferred_alpha_scope_path_count=25`.
- Include-ignored worktree plan:
  `python scripts\worktree_commit_plan.py --include-ignored --summary-only --json`
  returned `status=ready` with `changed_path_count=16255`,
  `generated_artifact_count=37`, `generated_local_only_count=23`,
  `generated_local_by_default_count=14`, and the same `25` deferred
  out-of-alpha paths.
- Alpha gate:
  `python scripts\alpha_release_gate.py --quick --allow-dirty --json` returned
  `alpha release gate passed`, `27/27`, while remote checks stayed skipped.
- Literal no-argument skip-remote preflight:
  `python scripts\alpha_release_preflight.py --skip-remote --json` returned
  `release preflight failed` because the historical defaults still expect
  `codex/qa-z-bootstrap`, no configured `origin`, a clean worktree, and absent
  `v0.9.8-alpha`. That is a command-contract blocker for old copy/paste
  snippets, not a product regression.
- Current local no-remote preflight:
  `python scripts\alpha_release_preflight.py --skip-remote --expected-origin-url https://github.com/qazedhq/qa-z.git --expected-branch main --allow-dirty --skip-release-tag-check --json`
  returned `release preflight passed`, `6` passed, `4` skipped, and
  `release_path_state=local_only_remote_preflight`. Skip-remote local preflight remains separate from read-only remote proof, and its remote checks stayed skipped by design.
- Full local proof refresh:
  `python scripts\alpha_release_gate.py --quick --allow-dirty --json` carried
  the local proof bundle through `pytest` (`1601 passed`), Ruff check, Ruff
  format check, mypy (`533` source files), CLI help smoke, text hygiene, and
  worktree-plan evidence.

Read-only remote proof:

- `python scripts\alpha_release_preflight.py --repository-url https://github.com/qazedhq/qa-z.git --expected-origin-url https://github.com/qazedhq/qa-z.git --expected-branch main --skip-release-tag-check --allow-dirty --json`
  returned `release preflight passed`, `9` passed, `1` skipped,
  `repository_http_status=200`, `repository_visibility=public`,
  `repository_archived=false`, `repository_default_branch=main`,
  `remote_ref_count=24`, `remote_ref_head_count=5`,
  `remote_ref_tag_count=2`, and
  `release_path_state=blocked_remote_publish`.
- The same read-only preflight with `--allow-existing-refs` also passed the
  read checks, but still reported `release_path_state=blocked_remote_publish`
  because no publish action was approved and existing remote tags/refs need
  explicit release decisioning.
- `git ls-remote --refs origin` returned remote refs without credentials or
  mutation. Remote `main` is `8f647619418b884afa3bef3d839326680bec70af`; tags include
  `v0.9.8-alpha` and `v0.9.9-alpha`.
- GitHub API proof returned repository `qazedhq/qa-z`, `private=false`,
  `archived=false`, `default_branch=main`, release tags
  `v0.9.9-alpha,v0.9.8-alpha`, and `main_sha=8f647619418b884afa3bef3d839326680bec70af`.
- Latest read-only workflow proof for remote `main` is for
  `8f647619418b884afa3bef3d839326680bec70af`, not local
  `a3e5303933fe9b1bef03e2e915ce224e0cc4e1c1`: `CI`, `Public Raw Hygiene`,
  and `OpenSSF Scorecard` were completed successfully on the remote-visible
  SHA.
- `python scripts\check_public_raw_urls.py --repo qazedhq/qa-z --ref main --commit 8f647619418b884afa3bef3d839326680bec70af`
  passed for branch and exact-commit raw URLs.
- `python scripts\check_public_raw_urls.py --repo qazedhq/qa-z --ref main --commit a3e5303933fe9b1bef03e2e915ce224e0cc4e1c1`
  passed branch `main` URLs but failed exact-commit raw URLs with HTTP `404`,
  proving the local HEAD is not yet public on the remote.
- Local proof HEAD is 15 commits ahead of remote `main`, so this is not an
  empty-remote direct publish. Remote alpha readiness is partial: repository
  existence and readability are proven, but the current local proof SHA has not
  been pushed, CI-validated, tagged, released, or package-published.

Approval matrix:

| Action | Approved? | Executed? | Evidence / blocker |
|---|---:|---:|---|
| Read-only remote proof | Yes, safe read-only | Yes | GitHub API, `git ls-remote`, preflight, workflow API, and public raw checks captured. |
| Push | No | No | `PUSH_ALLOWED` unset; local HEAD is 15 commits ahead of remote `main`. |
| Tag | No | No | `TAG_ALLOWED` unset; existing tags `v0.9.8-alpha` and `v0.9.9-alpha` must not be reused. |
| GitHub release | No | No | `GITHUB_RELEASE_ALLOWED` unset; release requires approved tag, notes, and post-CI evidence. |
| Package publish | No | No | `PACKAGE_PUBLISH_ALLOWED` unset; `docs/package-publish-plan.md` keeps registry publishing for a later explicit plan. |
| Deploy | No | No | `DEPLOY_ALLOWED` unset; QA-Z alpha has no live service deployment lane. |

Push/tag/release/package publish: not executed in PROOF_ONLY mode.

Publish execution packet:

If a human approves a push later, run the proof commands again first:

```bash
git status --short -uall
python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting
python scripts\alpha_release_gate.py --quick --allow-dirty --json
python scripts\alpha_release_preflight.py --repository-url https://github.com/qazedhq/qa-z.git --expected-origin-url https://github.com/qazedhq/qa-z.git --expected-branch main --skip-release-tag-check --allow-dirty --json
```

The conservative push packet is a proof branch, not a direct default-branch
publish:

```bash
git push -u origin HEAD:codex/alpha-rc-<approved-sha>-20260512
git ls-remote --heads origin codex/alpha-rc-<approved-sha>-20260512
```

Direct `main` update needs separate explicit approval:

```bash
git push origin HEAD:main
```

After any approved push, capture remote CI and public raw proof for the pushed
SHA before any tag or release action:

```bash
python scripts\check_public_raw_urls.py --repo qazedhq/qa-z --ref main --commit <pushed-sha>
git ls-remote --refs origin
```

Only after remote CI and public raw proof pass on the pushed SHA may a release
operator choose a new approved tag. Do not reuse `v0.9.8-alpha` or
`v0.9.9-alpha`:

```bash
git tag -s <approved-alpha-tag> -m "QA-Z <approved-alpha-tag>"
git tag -v <approved-alpha-tag>
git push origin <approved-alpha-tag>
git ls-remote --tags origin <approved-alpha-tag>
```

If tag signing is not available and the release owner approves an annotated tag,
record the reason and use:

```bash
git tag -a <approved-alpha-tag> -m "QA-Z <approved-alpha-tag>"
git push origin <approved-alpha-tag>
```

GitHub release creation needs a separately approved tag and release body:

```bash
gh release create <approved-alpha-tag> --repo qazedhq/qa-z --title "QA-Z <approved-alpha-tag>" --notes-file <approved-release-notes.md> --prerelease
```

Package publishing is outside this alpha packet unless a separate package
release owner approves it. The minimum dry-run packet before any registry
publish is:

```bash
python -m build --sdist --wheel
python scripts\alpha_release_artifact_smoke.py --with-deps --json
python -m twine check dist/*
```

Package publish dry-run packet:

- Package metadata version is `0.9.8a0` in `pyproject.toml`.
- `PACKAGE_PUBLISH_ALLOWED` unset, so no PyPI, TestPyPI, npm, GitHub Packages,
  or package-registry publish is approved.
- Safe local-only dry-run commands:

```bash
python -m build --sdist --wheel
python scripts\alpha_release_artifact_smoke.py --with-deps --json
python -m twine check dist/*
```

- Expected dry-run evidence: built sdist and wheel names, artifact smoke JSON,
  `twine check` result, and confirmation that no upload command ran.
- Registry publish remains blocked until a release owner sets
  `RELEASE_EXECUTION_APPROVED=true` and `PACKAGE_PUBLISH_ALLOWED=true`, chooses
  TestPyPI or PyPI, confirms credentials out of band, and records the exact
  package URL/version after upload.
- Package rollback/yank policy is registry-owned. QA-Z must not imply a local
  command can undo a published package without following the selected
  registry's retention and yank rules.

Guard and timestamp hardening packet:

- `qa-z guard` now carries a `current_truth` verdict block when the latest
  self-inspection context is available.
- If `.qa-z/loops/latest/self_inspect.json` is stale for the backlog
  `updated_at` timestamp, guard returns `needs_review` instead of `merge_ok`
  even when fast and deep checks pass.
- Timestamp freshness now parses ISO-like timestamps as UTC instants. Missing or
  malformed self-inspection timestamps fail closed as stale when a backlog
  minimum exists, and timezone offsets such as `Z` and `+00:00` are compared by
  instant rather than lexically.
- Focused proof:

```bash
python -m pytest tests\test_guard_cli.py::test_guard_marks_stale_current_truth_context_as_needs_review tests\test_self_improvement_selection.py::test_selection_context_treats_missing_and_malformed_timestamps_as_stale tests\test_self_improvement_selection.py::test_selection_context_compares_timezone_offsets_by_instant -q
```

Rollback and incident packet:

- Local packet commit rollback: use `git revert <packet-commit>`; do not use
  `git reset` for shared release history.
- Mistaken proof branch push: if approved by a release owner, delete only the
  proof branch with
  `git push origin --delete codex/alpha-rc-<approved-sha>-20260512`.
- Mistaken direct `main` push: do not force-push by default. Open a rollback PR
  or run `git revert <bad-sha>` on a reviewed branch, then rerun the alpha gate
  and remote proof.
- Mistaken local tag before push: `git tag -d <approved-alpha-tag>`.
- Mistaken remote tag: only after human approval, run
  `git push origin :refs/tags/<approved-alpha-tag>` and record the deletion in
  release notes.
- Mistaken GitHub release: mark it draft or delete it through GitHub/`gh`
  only after release-owner approval; preserve notes and URLs in the incident
  record.
- Mistaken package publish: follow the registry owner's yank/unpublish policy;
  no package-registry publish has happened in this packet.
- Incident record must include actor, time, affected ref or artifact, command
  evidence, rollback command, validation rerun, and next approval owner.
- After any rollback, rerun:

```bash
git status --short -uall
python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting
python scripts\alpha_release_gate.py --quick --allow-dirty --json
python scripts\alpha_release_preflight.py --repository-url https://github.com/qazedhq/qa-z.git --expected-origin-url https://github.com/qazedhq/qa-z.git --expected-branch main --skip-release-tag-check --allow-dirty --json
```

Deferred Marketing/X packet:

- Deferred paths are `marketing/x/**` and `tests/test_x_automation.py`.
- Scope is deferred because the surface is product-owned marketing/network
  automation that can require X credentials, call X APIs, and mutate posting
  queue state when enabled.
- Do not stage Marketing/X source, tests, queue state, credentials, logs, or
  local runtime state for this QA-Z alpha candidate.
- Future approval requires an explicit product/network decision plus separate
  no-credential dry-run proof before any source staging, and live credentialed
  proof must remain a human/nonlocal release action.
- Later proof must show no accidental queue mutation, no credential leakage, and
  a reviewed boundary between content drafts, follow targets, local state, and
  any real X API call.

Deferred Claude compatibility mirror packet:

- Deferred paths are `.claude/**`.
- `.claude/**` is a compatibility mirror. Codex-native source of truth remains
  `.codex/agents/*.toml`, `.agents/skills/*/SKILL.md`, and `docs/agent/*.md`.
- Do not stage, delete, or promote `.claude/**` for this QA-Z alpha candidate
  unless a compatibility release decision says the mirror must be synchronized.
- Later proof must compare mirror contents against the Codex-native assets and
  identify the exact compatibility audience before `.claude/**` is staged.

Remote and publishing proof packet:

- Configured origin target is `qazedhq/qa-z`; local and read-only remote
  preflight both confirm that target.
- Remote repository checks and reachability are proven current as of the proof
  timestamp, but remote publish remains blocked by `PROOF_ONLY` approval
  boundaries, the non-empty remote state, and the fact that local
  `1f35eeb7c420842aad78f2bb10b0545a15412cbd` is not yet remote-visible.
- QA-Z local alpha RC readiness: `Yes` for the local proof packet.
- QA-Z remote alpha readiness: `Partial`; remote read proof is current, but the
  local proof SHA is not pushed and no current-SHA CI/public raw evidence exists.
- QA-Z release-execution readiness: `Partial`; exact push, tag, release,
  package, rollback, and incident packets are prepared, but approval flags are
  absent.
- Production readiness: `No`. Package registry publishing, deployment,
  production support policy, and human release approval remain outside this
  packet. Production readiness is not claimed.

The only normal staging candidates after this packet are tracked packet or
truth-surface edits that improve this decision evidence. The `25` deferred
out-of-alpha paths must remain untracked for the QA-Z alpha candidate unless
their owning release decision changes.

## Preflight

`tests/test_benchmark.py` has already been formatted once during triage, but it is
untracked in the current worktree. Do not create a standalone format-only commit for
that file unless it becomes tracked first.

Recommended benchmark preflight before Commit 2:

```bash
python -m ruff format tests/test_benchmark.py
python -m ruff format --check .
python -m ruff check .
```

Then include the formatted `tests/test_benchmark.py` in the benchmark commit.

## Corrected Commit Sequence

1. `feat: add runner repair and verification foundations`
2. `feat: expand benchmark coverage for typescript and deep policy cases`
3. `feat: add self-inspection backlog and task selection workflow`
4. `feat: add autonomy planning loops and loop artifacts`
5. `feat: add repair session workflow and verification publishing`
6. `feat: add executor bridge packaging for external repair workflows`
7. `docs: add worktree triage and commit plan reports`

## Import-Closure Finding

The direct `qa_z.benchmark` imports are:

- `qa_z.artifacts`
- `qa_z.config`
- `qa_z.repair_handoff`
- `qa_z.reporters.deep_context`
- `qa_z.reporters.repair_prompt`
- `qa_z.reporters.run_summary`
- `qa_z.reporters.sarif`
- `qa_z.runners.deep`
- `qa_z.runners.fast`
- `qa_z.runners.models`
- `qa_z.verification`

The benchmark-safe foundation closure, excluding `qa_z.benchmark` itself, is:

| State | Path |
| --- | --- |
| modified | `src/qa_z/artifacts.py` |
| modified | `src/qa_z/config.py` |
| untracked | `src/qa_z/diffing/models.py` |
| untracked | `src/qa_z/diffing/parser.py` |
| untracked | `src/qa_z/repair_handoff.py` |
| untracked | `src/qa_z/reporters/deep_context.py` |
| modified | `src/qa_z/reporters/repair_prompt.py` |
| modified | `src/qa_z/reporters/review_packet.py` |
| untracked | `src/qa_z/reporters/sarif.py` |
| untracked | `src/qa_z/runners/checks.py` |
| untracked | `src/qa_z/runners/deep.py` |
| modified | `src/qa_z/runners/fast.py` |
| modified | `src/qa_z/runners/models.py` |
| tracked-clean | `src/qa_z/runners/python.py` |
| untracked | `src/qa_z/runners/selection.py` |
| untracked | `src/qa_z/runners/selection_common.py` |
| untracked | `src/qa_z/runners/selection_deep.py` |
| untracked | `src/qa_z/runners/selection_typescript.py` |
| untracked | `src/qa_z/runners/semgrep.py` |
| modified | `src/qa_z/runners/subprocess.py` |
| untracked | `src/qa_z/runners/typescript.py` |
| untracked | `src/qa_z/verification.py` |

Add `src/qa_z/diffing/__init__.py` with this set for package completeness. Do not add
`src/qa_z/benchmark.py` until Commit 2.

## Commit 1: Runner, Repair, And Verification Foundations

Message:

```text
feat: add runner repair and verification foundations
```

Purpose:

Add the import-safe foundation that benchmark, deep QA, repair handoff, and
verification depend on. This commit should make the intermediate repository coherent
without introducing the benchmark corpus, self-improvement loops, repair sessions, or
executor bridge packaging.

Include whole files where possible:

- `src/qa_z/diffing/__init__.py`
- `src/qa_z/diffing/models.py`
- `src/qa_z/diffing/parser.py`
- `src/qa_z/repair_handoff.py`
- `src/qa_z/reporters/deep_context.py`
- `src/qa_z/reporters/sarif.py`
- `src/qa_z/runners/checks.py`
- `src/qa_z/runners/deep.py`
- `src/qa_z/runners/selection.py`
- `src/qa_z/runners/selection_common.py`
- `src/qa_z/runners/selection_deep.py`
- `src/qa_z/runners/selection_typescript.py`
- `src/qa_z/runners/semgrep.py`
- `src/qa_z/runners/typescript.py`
- `src/qa_z/verification.py`
- `src/qa_z/adapters/codex/repair_handoff.py` if repair-handoff adapter tests are included
- `src/qa_z/adapters/claude/repair_handoff.py` if repair-handoff adapter tests are included

Patch-add only foundation hunks from:

- `src/qa_z/artifacts.py`
- `src/qa_z/config.py`
- `src/qa_z/planner/contracts.py`
- `src/qa_z/reporters/repair_prompt.py`
- `src/qa_z/reporters/review_packet.py`
- `src/qa_z/reporters/run_summary.py`
- `src/qa_z/runners/fast.py`
- `src/qa_z/runners/models.py`
- `src/qa_z/runners/subprocess.py`
- `src/qa_z/adapters/codex/__init__.py`
- `src/qa_z/adapters/claude/__init__.py`
- `src/qa_z/cli.py`

`src/qa_z/cli.py` must not be added wholesale. Its current top-level imports include
benchmark, self-improvement, autonomy, repair session, and executor bridge modules.
For Commit 1, stage only the import and handler/parser hunks for:

- `deep`
- `repair-prompt`
- `verify`
- `review` run/deep context, if included

Do not stage CLI hunks for:

- `benchmark`
- `self-inspect`
- `select-next`
- `backlog`
- `autonomy`
- `repair-session`
- `executor-bridge`
- `github-summary`, unless its foundation-only rendering is intentionally included

Tests to include:

- `tests/test_diffing.py`
- `tests/test_fast_config.py`
- `tests/test_fast_selection.py`
- `tests/test_deep_run_resolution.py`
- `tests/test_deep_selection.py`
- `tests/test_semgrep_normalization.py`
- `tests/test_sarif_cli.py`
- `tests/test_sarif_reporter.py`
- `tests/test_subprocess_runner.py`
- `tests/test_repair_handoff.py`
- `tests/test_verification.py`
- `tests/test_plan_titles.py`, if planner contract metadata hunks are included
- foundation hunks from `tests/test_repair_prompt.py`, `tests/test_cli.py`, and
  `tests/test_artifact_schema.py`

Docs to patch-add only if they describe this foundation surface:

- README sections for fast/deep selection, repair handoff, SARIF, and verification
- `docs/artifact-schema-v1.md` sections for summary v2, deep findings, SARIF,
  repair packet/handoff, and verification artifacts
- `docs/mvp-issues.md` status for runner, deep, repair handoff, SARIF, and verification

Exclude:

- `src/qa_z/benchmark.py`
- `tests/test_benchmark.py`
- `benchmarks/**`
- `docs/benchmarking.md`
- `src/qa_z/self_improvement.py`
- `src/qa_z/autonomy.py`
- `src/qa_z/repair_session.py`
- `src/qa_z/executor_bridge.py`
- `src/qa_z/reporters/github_summary.py`, unless deliberately split as foundation
- `src/qa_z/reporters/verification_publish.py`
- `docs/reports/**`
- root `.qa-z/**`
- `benchmarks/results/**`

Targeted validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_diffing.py tests/test_fast_config.py tests/test_fast_selection.py tests/test_deep_run_resolution.py tests/test_deep_selection.py tests/test_semgrep_normalization.py tests/test_sarif_cli.py tests/test_sarif_reporter.py tests/test_subprocess_runner.py tests/test_repair_handoff.py tests/test_verification.py -q
python -m qa_z --help
python -c "import qa_z.repair_handoff; import qa_z.verification; import qa_z.runners.deep; import qa_z.reporters.sarif; import qa_z.reporters.deep_context"
```

Rollback boundary:

Reverting this commit should remove the new runner/deep/repair/verify foundation while
leaving older bootstrap commands coherent.

## Commit 2: Benchmark Coverage

Message:

```text
feat: expand benchmark coverage for typescript and deep policy cases
```

Purpose:

Add the benchmark runner, support helpers, TypeScript fixtures, and deep policy
fixtures on top of the foundation from Commit 1.

Include:

- `src/qa_z/benchmark.py`
- benchmark hunks from `src/qa_z/cli.py`
- `tests/test_benchmark.py`, patch-added if mixed-language P5-C is deferred
- `benchmarks/support/**`
- `benchmarks/fixtures/ts_lint_failure/**`
- `benchmarks/fixtures/ts_type_error/**`
- `benchmarks/fixtures/ts_test_failure/**`
- `benchmarks/fixtures/ts_multiple_fast_failures/**`
- `benchmarks/fixtures/ts_unchanged_candidate/**`
- `benchmarks/fixtures/ts_regressed_candidate/**`
- `benchmarks/fixtures/deep_severity_threshold_warn_filtered/**`
- `benchmarks/fixtures/deep_ignore_rule_suppressed/**`
- `benchmarks/fixtures/deep_exclude_paths_skipped/**`
- `benchmarks/fixtures/deep_grouped_findings_dedup/**`
- `benchmarks/fixtures/deep_filtered_vs_blocking_counts/**`
- `benchmarks/fixtures/deep_config_error_surface/**`
- `docs/benchmarking.md`, patch-added if mixed-language P5-C is deferred
- `.gitignore` hunks for fixture-local `.qa-z` and `benchmarks/results/work/`
- benchmark hunks from README, artifact schema, and MVP status docs

Exclude unless intentionally doing P5-C in this commit:

- `benchmarks/fixtures/mixed_all_resolved_candidate/**`
- `benchmarks/fixtures/mixed_partial_resolved_with_regression_candidate/**`
- `benchmarks/fixtures/mixed_py_resolved_ts_regressed_candidate/**`
- `benchmarks/fixtures/mixed_ts_resolved_py_regressed_candidate/**`
- `docs/superpowers/plans/2026-04-15-p5-c-mixed-language-benchmark.md`
- `docs/superpowers/specs/2026-04-15-p5-c-mixed-language-benchmark-design.md`

Always exclude:

- `benchmarks/results/summary.json`
- `benchmarks/results/report.md`
- `benchmarks/results/work/**`
- root `.qa-z/**`
- `docs/reports/**`

Targeted validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_benchmark.py -q
python -m qa_z benchmark --json
python -c "import qa_z.benchmark"
```

Rollback boundary:

Reverting this commit should remove benchmark measurement without affecting the
foundation commands from Commit 1.

## Commit 3: Self-Inspection Backlog

Message:

```text
feat: add self-inspection backlog and task selection workflow
```

Include:

- `src/qa_z/self_improvement.py`
- CLI hunks for `self-inspect`, `select-next`, and `backlog`
- `tests/test_self_improvement.py`
- relevant hunks from `tests/test_cli.py`
- `docs/superpowers/plans/2026-04-15-p6-a-self-inspection-backlog.md`
- README/schema/MVP hunks for self-inspection, backlog, selected tasks, and history

Validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_self_improvement.py tests/test_self_improvement_inspection.py tests/test_self_improvement_selection_output.py tests/test_repair_signal_inputs.py tests/test_artifact_consistency_discovery.py tests/test_cli.py -q
```

## Commit 4: Autonomy Workflow

Message:

```text
feat: add autonomy planning loops and loop artifacts
```

Include:

- `src/qa_z/autonomy.py`
- CLI hunks for `autonomy --loops` and `autonomy status`
- `tests/test_autonomy.py`
- relevant hunks from `tests/test_cli.py`
- README/schema/MVP hunks for loop artifacts and autonomy outcomes
- `docs/repair-sessions.md` hunks that describe autonomy preparing sessions, if any

Validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_autonomy.py tests/test_autonomy_action_cleanup.py tests/test_autonomy_action_context.py tests/test_cli.py -q
```

## Commit 5: Repair Session And Publishing

Message:

```text
feat: add repair session workflow and verification publishing
```

Include:

- `src/qa_z/repair_session.py`
- `src/qa_z/reporters/verification_publish.py`
- `src/qa_z/reporters/github_summary.py`
- CLI hunks for `repair-session` and `github-summary`
- `tests/test_repair_session.py`
- `tests/test_verification_publish_summary.py`
- `tests/test_verification_publish_session.py`
- `tests/test_verification_publish_architecture.py`
- `tests/test_verification_publish_helper_architecture.py`
- `tests/test_github_summary_render.py`
- `tests/test_github_summary_session.py`
- `tests/test_github_summary_deep.py`
- `tests/test_github_summary_architecture.py`
- `tests/test_github_workflow.py`
- relevant hunks from `tests/test_artifact_schema.py` and `tests/test_cli.py`
- `docs/repair-sessions.md`
- workflow hunks in `.github/workflows/ci.yml` and
  `templates/.github/workflows/vibeqa.yml` that publish summaries/upload artifacts
- README/schema/MVP hunks for repair sessions and publish summaries

Validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_repair_session.py tests/test_verification_publish_summary.py tests/test_verification_publish_session.py tests/test_verification_publish_architecture.py tests/test_verification_publish_helper_architecture.py tests/test_github_summary_render.py tests/test_github_summary_session.py tests/test_github_summary_deep.py tests/test_github_summary_architecture.py tests/test_github_workflow.py -q
```

## Commit 6: Executor Bridge

Message:

```text
feat: add executor bridge packaging for external repair workflows
```

Include:

- `src/qa_z/executor_bridge.py`
- CLI hunks for `executor-bridge`
- `tests/test_executor_bridge.py`
- relevant hunks from `tests/test_cli.py`
- README/schema/MVP/repair-session docs hunks for bridge artifacts

Validation:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest tests/test_executor_bridge.py tests/test_cli.py -q
```

## Commit 7: Cleanup Reports

Message:

```text
docs: add worktree triage and commit plan reports
```

Include:

- `docs/reports/worktree-triage.md`
- `docs/reports/worktree-commit-plan.md`

Validation:

```bash
python -m pytest
```

## Alpha Closure Addendum

After the feature batches are staged, include the alpha closure cleanup in the
documentation/status commit:

- `docs/generated-vs-frozen-evidence-policy.md`
- `docs/superpowers/plans/2026-04-18-alpha-closure-gate-cleanup.md`
- final README/report/MVP wording updates, if any drift fixes were needed

Do not stage `benchmarks/results/**` or removed local `benchmarks/results-p12-*`
snapshots as source evidence.

## Alpha Release Closure Batch

Message:

```text
chore: freeze alpha release target and root qa gate
```

Purpose:

Close the release-prep work that sits outside the feature batches: the public
`v0.9.8-alpha` identifier, Python package version `0.9.8a0`, root Python-only
release gate, and final in-repository release notes.

Include whole files:

- `qa-z.yaml`
- `docs/releases/v0.9.8-alpha.md`
- `docs/superpowers/plans/2026-04-18-github-repository-release.md`

Patch-add only the release-target README hunks from:

- `README.md`

Patch-add only the version metadata hunks from:

- `pyproject.toml`

Patch-add only the root gate, release target, and closure-boundary guard hunks from:

- `tests/test_current_truth.py`
- `tests/test_github_workflow.py`

Patch-add any matching status-only wording from:

- `docs/reports/worktree-commit-plan.md`
- `docs/reports/worktree-triage.md`

Exclude:

- feature command, runner, benchmark, autonomy, repair-session, executor, and
  self-inspection implementation hunks
- generated root `.qa-z/**`
- generated `benchmarks/results/**`
- generated benchmark snapshot directories such as `benchmarks/results-*`

Targeted validation:

```bash
python -m pytest tests/test_current_truth.py tests/test_github_workflow.py -q
python -m qa_z fast --selection smart --json
python -m qa_z deep --selection smart --json
python scripts/alpha_release_gate.py --quick --allow-dirty --json
```

Rollback boundary:

Reverting this batch should unfreeze the public release target and remove the
root release gate without changing the already-split feature implementation
batches.

## Alpha Closure Readiness Snapshot

The latest full local gate pass for this accumulated alpha baseline is:

- `python -m pytest`: 1212 passed
- `python -m qa_z benchmark --json`: 54/54 fixtures, overall_rate 1.0
- `python -m build --sdist --wheel`: passed, built `qa_z-0.9.8a0.tar.gz` and `qa_z-0.9.8a0-py3-none-any.whl`
- `python scripts/alpha_release_artifact_smoke.py --json`: passed, wheel and sdist metadata install smoke
- `python -m ruff check .`: pass
- `python -m ruff format --check .`: 519 files already formatted
- `python -m mypy src tests`: success across 507 source files

Human planning surfaces now keep this snapshot as the primary compact
commit-isolation evidence and append an `action basis:` suffix when area-bearing
`git_status` evidence explains the next action hint.
Treat the benchmark line as the benchmark summary `snapshot` field, not a
manually recomputed count, so alpha closure notes quote generated evidence.
Executor bridge stdout now also reports action-context package health and
missing action-context diagnostics when loop-prepared optional context paths are
copied or skipped.
Benchmark snapshot directories matching `benchmarks/results-*` are generated
runtime artifacts by default. Freeze them only when the commit explicitly says
they are intentional evidence and includes the surrounding context.
Deferred generated cleanup prepared actions now carry
`docs/generated-vs-frozen-evidence-policy.md` through `context_paths`, so
external handoffs keep the local-only versus intentional frozen evidence policy
beside the worktree triage reports.
Autonomy status and saved loop plans now mirror selected fallback families, so
repeated cleanup-family selection is visible without reopening `outcome.json`.
Loop-health prepared actions now carry selected task evidence paths through
`context_paths`, so fallback-diversity handoffs can point directly at
`.qa-z/loops/history.jsonl`.
Autonomy-created repair-session actions now preserve selected verification
evidence in `context_paths`, and executor bridge packages copy existing action
context files into `inputs/context/` while recording `inputs.action_context`.
The committed benchmark corpus now pins that path with
`executor_bridge_action_context_inputs` and pins missing optional action-context
guide/stdout diagnostics with `executor_bridge_missing_action_context_inputs`.
Deferred cleanup compact evidence can append an `action basis:` suffix with
`generated_outputs` or `runtime_artifacts` evidence so generated artifact cleanup
decisions stay visible in the human handoff.

This snapshot is evidence for commit splitting, not a source artifact to commit
blindly. `benchmarks/results/report.md` now carries its own `Generated Output Policy`
section, but `benchmarks/results/summary.json`,
`benchmarks/results/report.md`, and `benchmarks/results/work/**` still stay local
unless a commit explicitly freezes benchmark evidence with surrounding context.

The next operator action is to split the worktree by this commit plan, rerun the
targeted validation for each batch, and rerun the full validation checklist below
before tagging.

## Full Validation Before Tagging

Run after all selected commits are split and generated artifacts are excluded or
intentionally committed:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest
python -m qa_z benchmark --json
python -m qa_z --help
python -m qa_z self-inspect --help
python -m qa_z select-next --help
python -m qa_z autonomy --help
python -m qa_z executor-bridge --help
python -m qa_z repair-session --help
python -m qa_z github-summary --help
```

Use `v0.9.8-alpha` for the current release candidate now that the baseline includes
self-improvement, autonomy, executor bridge packaging, executor-result ingest, and
the live-free safety dry-run. Use `v0.10.0-alpha` only if the team wants a larger
reset point.
