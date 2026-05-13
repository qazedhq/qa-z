# Work Slice Ledger

Append one entry per meaningful improvement slice. Do not use this ledger to turn blocked work into completed work.

## Template
- Date:
- Repo:
- Lane:
- User-facing flow:
- Slice type: Flow / Contract / Evidence / Cleanup
- Before:
- Root cause:
- Change made:
- Validation run:
- Evidence:
- Gate delta:
- User impact:
- Remaining blocker:
- Next safe slice:

## 2026-05-12 Operating Model Scaffold
- Repo: JustTyping
- Lane: agent operating model
- Slice type: Cleanup
- Change made: Added Claude-style role files, repeatable skills, and agent docs so QA-Z improvement means judgment, benchmark, repair-prompt, or current-truth improvement instead of target-repo coding.
- Validation run: structural file presence and markdown diff checks.
- Gate delta: no release gate changed; this is workflow scaffolding only.
- Next safe slice: use the scaffold for risk model, benchmark fixture, repair prompt, or current-truth drift work.


## 2026-05-12 V4 Product-Code Handoff
- Repo: JustTyping
- Lane: agent operating model -> real product/code slice handoff
- Slice type: Cleanup / Evidence
- Change made: Added `docs/agent/next-real-slices.md`, `product-code-slice` skill, safer validation checks, and guardrails so the next broad request moves from scaffolding to one code/test/runtime/evidence slice.
- Validation run: `python scripts/validate-agent-operating-model.py`
- Gate delta: no product release gate changed; this prevents future docs-only improvement loops.
- User impact: the next Codex run has a concrete first real slice instead of another operating-model edit.
- Remaining blocker: actual product code/test changes must be performed inside the full repository checkout.
- Next safe slice: choose the first applicable item in `docs/agent/next-real-slices.md` and validate it.


## 2026-05-12 Stale Select-Next Provenance Guard
- Repo: JustTyping
- Lane: current truth -> self-inspect/select-next -> recommended QA slice
- User-facing flow: `qa-z select-next` selected-task output
- Slice type: Contract / Evidence
- Before: `selected_tasks.json` could copy latest self-inspection provenance without marking that the backlog had been updated after that self-inspection.
- Root cause: selection context only checked whether `.qa-z/loops/latest/self_inspect.json` existed and had live repository context; it did not compare the self-inspection timestamp to backlog `updated_at`.
- Change made: `select-next` now marks stale self-inspection provenance, emits a copyable `select-next --refresh` command, mirrors that truth in `loop_plan.md` and history, and avoids copying old live repository context into selected-task artifacts.
- Validation run: `python -m pytest tests/test_loop_health_signal_inputs.py tests/test_self_improvement_selection.py tests/test_cli.py -q`; `python -m ruff check src\qa_z\operator_commands.py src\qa_z\selection_context.py src\qa_z\self_improvement_selection.py src\qa_z\commands\planning_output.py src\qa_z\task_selection_render.py src\qa_z\improvement_state.py tests\test_loop_health_signal_inputs.py tests\test_self_improvement_selection.py tests\test_cli.py`; `python -m mypy src\qa_z\operator_commands.py src\qa_z\selection_context.py src\qa_z\self_improvement_selection.py src\qa_z\commands\planning_output.py src\qa_z\task_selection_render.py src\qa_z\improvement_state.py`; `python scripts\validate-agent-operating-model.py`.
- Evidence: targeted tests assert stale provenance fields, refresh commands, `loop_plan.md` and history propagation, and omission of stale `live_repository`.
- Gate delta: selected-task artifacts are more honest about stale current-truth context; release readiness is not closed by this local slice.
- User impact: operators get an explicit refresh command before acting on a selected task whose self-inspection context trails the backlog.
- Remaining blocker: unrelated dirty/untracked work remains user-owned, including operating assets and marketing/X files.
- Next safe slice: repair prompt handoff completeness or benchmark lock/results-dir evidence, after the dirty-source boundary is decided.


## 2026-05-12 Release Scope Split Evidence
- Repo: JustTyping
- Lane: dirty worktree -> worktree commit plan -> alpha release gate
- User-facing flow: `scripts/worktree_commit_plan.py` and `scripts/alpha_release_gate.py --quick --allow-dirty --json`
- Slice type: Evidence / Contract
- Before: release-gate worktree evidence collapsed untracked operating assets and credential-gated `marketing/x/**` launch automation into vague unassigned source paths or left the product/network boundary to external notes.
- Root cause: the commit-plan helper had source, generated, cross-cutting, and report buckets but no product-decision bucket for paths that are source-like yet need explicit release ownership before staging.
- Change made: the worktree commit plan now reports `product_decision_paths`, `product_decision_path_count`, and `product_decision_paths_present`; marketing/X local state stays local-only generated evidence, while marketing/X source and operating-model assets are visible as product-decision paths. Alpha gate evidence and human output now preserve `product_decision_path_count`.
- Validation run: `python -m pytest tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_output.py tests\test_worktree_commit_plan_cli.py tests\test_worktree_commit_plan_filtering.py tests\test_alpha_release_gate_evidence.py::test_alpha_release_gate_extracts_real_worktree_commit_plan_payload tests\test_alpha_release_gate_evidence.py::test_alpha_release_gate_evidence_preserves_cross_cutting_group_count tests\test_alpha_release_gate_render.py::test_alpha_release_gate_human_output_prints_worktree_strict_mode -q`; `python -m ruff check scripts\worktree_commit_plan_support.py scripts\alpha_release_gate_evidence.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_output.py tests\test_alpha_release_gate_evidence.py tests\test_alpha_release_gate_render.py`; `python -m ruff format --check scripts\worktree_commit_plan_support.py scripts\alpha_release_gate_evidence.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_output.py tests\test_alpha_release_gate_evidence.py tests\test_alpha_release_gate_render.py`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts\worktree_commit_plan.py --include-ignored --json`.
- Evidence: current strict summary reports `unassigned_source_path_count=0`, `product_decision_path_count=50`, `cross_cutting_count=2`, and attention reasons `product_decision_paths_present` plus `cross_cutting_paths_present`; include-ignored output also reports `marketing/x/.state/` as local-only generated evidence.
- Gate delta: unassigned-source blocker is reduced to zero and the remaining release blocker is now explicit product/release ownership plus cross-cutting patch-add review, not ambiguous dirty source.
- User impact: a QA-Z operator can now separate the stale select-next guard slice from operating-model and X launch automation surfaces before staging or release-gate review.
- Remaining blocker: product owner must decide whether operating assets and `marketing/x/**` belong in this release or a separate non-QA-Z/network surface; `ruff format --check .` remains blocked by user-owned `scripts/validate-agent-operating-model.py`.
- Next safe slice: either make the product-decision split concrete through an approved staging/commit decision, or add the direct guard-level stale-current-truth canary once release-scope ownership is decided.


## 2026-05-12 Product-Decision Ownership Groups
- Repo: JustTyping
- Lane: product-decision ownership -> worktree commit plan -> alpha release gate
- User-facing flow: `scripts/worktree_commit_plan.py` and `scripts/alpha_release_gate.py --quick --allow-dirty --json`
- Slice type: Evidence / Contract
- Before: product-decision paths were visible but still one generic 50-path release blocker, and `scripts/validate-agent-operating-model.py` blocked global Ruff format.
- Root cause: the worktree commit-plan helper grouped ordinary batches and cross-cutting patch-add paths, but it did not group product-decision paths by ownership surface.
- Change made: the worktree commit plan now emits `product_decision_groups` and `product_decision_group_count`, separating Codex-native operating-model assets, Claude compatibility mirrors, Marketing/X network automation, the operating-model validator, and Marketing/X tests. Alpha gate evidence preserves `product_decision_group_count`, and the operating-model validator was Ruff-formatted without changing semantics.
- Validation run: targeted worktree-plan/current-truth tests; final validation commands are recorded in the sprint closeout.
- Evidence: current strict summary reports `unassigned_source_path_count=0`, `product_decision_path_count=50`, `product_decision_group_count=5`, `cross_cutting_count=2`, and attention reasons `product_decision_paths_present` plus `cross_cutting_paths_present`.
- Gate delta: the Ruff format blocker is resolved; the alpha gate remains blocked on worktree ownership until a human approves or defers the five product-decision groups and patch-adds the cross-cutting files.
- User impact: operators can now make a concrete release-scope decision by group instead of reopening a flat 50-path list.
- Remaining blocker: human release owner must decide whether the operating-model package and Marketing/X surface belong in this alpha release; cross-cutting schema/current-truth/report hunks still need patch-add ownership.
- Next safe slice: after the release-scope decision, rerun the strict worktree plan and alpha gate; if still blocked only by stale-guard proof, add the direct guard-level stale-current-truth canary.


## 2026-05-12 Alpha Release-Candidate Decision Packet
- Repo: JustTyping
- Lane: local alpha gate -> release-candidate decision packet -> deferred scope
- User-facing flow: worktree commit plan, alpha release gate, and release preflight operator handoff
- Slice type: Evidence / Cleanup
- Before: four tracked truth files were still modified, Marketing/X and Claude mirror scope remained untracked, and remote/publishing proof was intentionally not run.
- Root cause: the local alpha gate was green, but release-candidate status still needed one durable packet that separated local readiness from deferred product/network and compatibility surfaces.
- Change made: closed the four tracked truth files in `c6fac96`, then added a release-candidate packet to `docs/reports/worktree-commit-plan.md` covering the strict plan, include-ignored plan, alpha gate, local no-remote preflight, deferred Marketing/X scope, deferred Claude compatibility mirror, and required remote proof command.
- Validation run: `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts\worktree_commit_plan.py --include-ignored --summary-only --json`; `python scripts\alpha_release_gate.py --quick --allow-dirty --json`; `python scripts\alpha_release_preflight.py --skip-remote --expected-origin-url https://github.com/qazedhq/qa-z.git --expected-branch main --allow-dirty --skip-release-tag-check --json`.
- Evidence: strict plan returned `ready`, `changed_batch_count=0`, `product_decision_path_count=0`, and `cross_cutting_count=0`; include-ignored plan returned `ready` with `deferred_alpha_scope_path_count=25`; alpha gate returned `27/27`; local preflight returned `release_path_state=local_only_remote_preflight`.
- Gate delta: tracked modified truth files moved from dirty to committed; deferred out-of-alpha scope remains visible and uncommitted; production readiness is still not claimed.
- User impact: a maintainer can review the alpha release-candidate boundary without confusing local green gates with remote, publish, Marketing/X, or Claude mirror approval.
- Remaining blocker: remote proof, package publishing, deployment, and any Marketing/X or Claude mirror promotion require explicit human/nonlocal approval.
- Next safe slice: add one local regression that locks release-candidate truth-surface consistency without staging deferred Marketing/X or `.claude/**`.


## 2026-05-12 Alpha RC Remote/Publishing Proof Packet
- Repo: JustTyping
- Lane: alpha RC local proof -> read-only remote proof -> publish decision packet
- User-facing flow: worktree commit plan, alpha release preflight, alpha gate, and release-candidate handoff
- Slice type: Evidence / Contract
- Before: the RC packet intentionally stopped at local proof; remote repository checks, publish decisioning, and freshness regression were not yet captured in the tracked truth surface.
- Root cause: the local alpha RC state was green, but maintainers still needed a timestamped source-head packet that separated skip-remote preflight from read-only remote proof and kept publish actions blocked in `PROOF_ONLY`.
- Change made: refreshed `docs/reports/worktree-commit-plan.md` with source HEAD, proof timestamp, local/remote preflight evidence, remote ref counts, non-empty remote state, publish approval boundaries, deferred Marketing/X and Claude mirror proof requirements, and final skeptical readiness labels.
- Validation run: `python -m pytest tests\test_current_truth_worktree_commit_plan.py -q`; strict/final gates recorded in the worktrain closeout.
- Evidence: local preflight passed with `6` passed / `4` skipped; read-only remote preflight passed with `9` passed / `1` skipped, `repository_http_status=200`, `repository_visibility=public`, `remote_ref_count=24`, and `release_path_state=blocked_remote_publish`; `git ls-remote --refs origin` listed remote `main` plus `v0.9.8-alpha` and `v0.9.9-alpha`.
- Gate delta: remote existence and reachability moved from unproven to read-only proven; publishing remains intentionally unexecuted; production readiness remains `No`.
- User impact: a maintainer can now decide push/tag/release/package next steps from one tracked packet without confusing local green proof, read-only remote proof, and publish approval.
- Remaining blocker: human approval is required for push, tag, GitHub release, and package publish; deferred Marketing/X and `.claude/**` remain untracked and out of alpha.
- Next safe slice: after human publish approval, push an approved proof branch and capture remote CI plus public raw evidence on the pushed SHA.


## 2026-05-12 Human-Approved Alpha Release Execution Packet
- Repo: JustTyping
- Lane: release approval -> remote proof -> execution-or-packet handoff -> rollback packet
- User-facing flow: worktree commit plan, alpha release preflight, public raw proof, and release operator handoff
- Slice type: Evidence / Cleanup
- Before: the RC remote proof packet showed the repository was public and reachable, but the packet still carried the earlier source HEAD, ahead count, and no dedicated rollback/incident command packet.
- Root cause: no release execution approval flags were present, so the safe next improvement was not a push or tag; it was a current execution packet that makes the approval boundary and rollback path exact.
- Change made: refreshed `docs/reports/worktree-commit-plan.md` with the current HEAD `1f35eeb`, explicit empty approval flags, the literal preflight command's legacy-default failure, current local/remote proof, remote-main CI/public raw evidence, current-HEAD raw 404 proof, exact push/tag/release/package packets, rollback/incident commands, and final skeptical readiness labels.
- Validation run: `python -m pytest tests\test_current_truth_worktree_commit_plan.py -q`; broader release gates are recorded in the worktrain closeout.
- Evidence: strict plan stayed `ready`; alpha gate stayed `27/27`; remote repository proof stayed `repository_http_status=200`; public raw proof passed for remote `main` at `8f647619418b884afa3bef3d839326680bec70af`; public raw proof for local `1f35eeb` exact URLs failed with HTTP `404`, proving the current local SHA is not yet public.
- Gate delta: remote alpha readiness remains `Partial`, but the next human action is now exact and rollback-ready instead of a generic approval blocker.
- User impact: a maintainer can approve or reject push, tag, GitHub release, package publish, and rollback steps from one tracked packet without accidentally promoting deferred Marketing/X or `.claude/**` scope.
- Remaining blocker: push/tag/GitHub release/package/deploy actions still require explicit human approval flags and fresh post-action evidence.
- Next safe slice: if approval is granted, push the current approved `HEAD` to
  an approved proof branch and capture remote CI plus exact-commit public raw
  proof for the pushed SHA.


## 2026-05-12 Alpha RC Deep Release Hardening Worktrain
- Repo: JustTyping
- Lane: release execution packet -> package dry-run packet -> guard current-truth hardening
- User-facing flow: release operator handoff, `qa-z guard`, and `qa-z select-next`
- Slice type: Evidence / Contract
- Before: the RC packet referenced the previous local proof SHA and ahead count, package publishing was approval-blocked but not dry-run packetized, the current preflight handoff still advertised a bare historical command as if it were current proof, and guard could return `merge_ok` while latest self-inspection context was stale for the backlog.
- Root cause: local RC proof advanced to `a3e5303` without a matching truth-surface refresh, and self-inspection freshness used string comparison instead of parsed timestamp instants.
- Change made: refreshed `docs/reports/worktree-commit-plan.md`, `docs/package-publish-plan.md`, and `docs/releases/v0.9.8-alpha-publish-handoff.md` with current HEAD proof, package dry-run/upload blockers, explicit current preflight command, and rollback/yank notes. Added guard `current_truth` verdict handling so stale self-inspection produces `needs_review`, and changed selection-context freshness to parse ISO-like timestamps as UTC instants while failing closed on missing or malformed timestamps.
- Validation run: focused current-truth packet tests, guard stale-current-truth canary, and selection timestamp edge tests passed; broader closeout gates are recorded in the worktrain final report.
- Evidence: current local HEAD is `a3e5303933fe9b1bef03e2e915ce224e0cc4e1c1`, remote `main` is `8f647619418b884afa3bef3d839326680bec70af`, and the local branch is `15` commits ahead. Remote-main public raw proof passed; current-HEAD exact public raw proof failed with HTTP `404`, proving current HEAD is not remote-visible.
- Gate delta: release execution readiness is more exact but remains approval-blocked; guard verdicts now avoid treating stale current-truth context as merge-ready.
- User impact: maintainers can approve push/tag/release/package work from a current packet and can trust `qa-z guard` to ask for review when its local current-truth context trails the backlog.
- Remaining blocker: push, tag, GitHub release, package publish, deploy, and current-HEAD remote CI/public raw proof require explicit approval and post-action evidence.
- Next safe slice: after this packet commit, run the final validation stack and leave the top human action as approving a proof-branch push for the current HEAD.


## 2026-05-13 Commit-Safe Proof-Head And Current-Truth Guard Hardening
- Repo: JustTyping
- Lane: release truth validator -> proof-head lifecycle -> guard current-truth -> alpha gate/preflight CLI smoke
- User-facing flow: alpha release packet validation, `qa-z guard`, `scripts/alpha_release_preflight.py --json --output ...`, and `scripts/alpha_release_gate.py --quick --allow-dirty --json`
- Slice type: Contract / Evidence / Flow
- Before: the release truth validator could validate the live packet only against the current `HEAD`, proof-branch commands used moving `HEAD` refspecs, package dry-run validation did not prove upload commands stayed out of the safe dry-run section, missing or wrong-kind self-inspection could disappear from guard current-truth context, the alpha gate skipped `qa-z doctor --help`, and preflight/gate `--output` write failures surfaced as raw exceptions.
- Root cause: release packet truth checks were string-contract based around a pre-commit proof packet, and guard freshness treated absent optional artifacts as no context instead of stale context when the backlog had a freshness anchor.
- Change made: added `--proof-head-from-packet` proof validation, recorded current local HEAD separately in validator JSON, required proof-branch pushes to use explicit approved-SHA refspecs plus post-push equality proof, made package dry-run validation section-aware, made missing/wrong-kind self-inspection stale with refresh commands, rendered current-truth refresh commands in guard Markdown, added `qa-z doctor --help` to alpha gate CLI smoke, and made preflight/gate `--output` write failures return exit code `2` with a precise stderr message while still printing the evidence payload.
- Post-commit repair: proof-head mode now calculates ahead count from the packet proof SHA, not from moving `HEAD`, so committed proof packets remain valid after local closure commits while still reporting the current local HEAD separately.
- Validation run: `python -m pytest tests/test_alpha_release_truth_validator.py tests/test_worktree_commit_plan.py tests/test_current_truth_worktree_commit_plan.py -q`; `python -m pytest tests/test_self_improvement_selection.py tests/test_guard_cli.py tests/test_current_truth.py -q`; `python -m pytest tests/test_alpha_release_gate.py tests/test_alpha_release_gate_options.py tests/test_alpha_release_gate_render.py tests/test_alpha_release_gate_architecture.py -q`; `python -m pytest tests/test_alpha_release_preflight_cli_render.py tests/test_alpha_release_gate_cli.py -q`; `python scripts\alpha_release_truth_validator.py --proof-head-from-packet --json`; `python scripts\alpha_release_gate.py --quick --allow-dirty --json`.
- Evidence: focused packs passed `46`, `59`, `54`, and `22` tests; truth validator passed `18/18` with `proof_head_mode=packet`; alpha gate passed `28/28`, including `1622` pytest tests, `21` CLI help checks, Ruff format/check, mypy over `534` source files, text hygiene, and worktree-plan evidence.
- Gate delta: local alpha quality evidence is stronger and commit-safe for proof packets, but strict worktree plan still reports `attention_required` because the tracked status report is a patch-add review surface; include-ignored plan remains `ready` with deferred Marketing/X and `.claude/**` still visible.
- User impact: maintainers can validate a committed proof packet without fabricating current-HEAD remote proof, can avoid moving-HEAD proof branch mistakes, can rely on guard output to ask for review when current-truth inputs are missing or stale, and can distinguish release-check failure from evidence-file write failure.
- Remaining blocker: push, tag, GitHub release, package publish, deploy, current-HEAD remote proof, Marketing/X promotion, and Claude mirror promotion all still require explicit human approval and post-action evidence.
- Next safe slice: produce a proof-branch approval packet that uses the explicit approved-SHA refspec and lists the exact post-push CI/public-raw evidence commands, then wait for human approval before any remote mutation.


## 2026-05-13 Release Packet Duplicate-Section Guard
- Repo: JustTyping
- Lane: release truth validator -> release packet parser safety
- User-facing flow: alpha release packet validation and proof-head lifecycle
- Slice type: Contract / Evidence
- Before: the release truth validator selected the first matching alpha decision packet section, so a duplicate section later in the same report could hide stale source-head or ahead-count text behind an otherwise valid first packet.
- Root cause: the validator checked that the current decision packet header existed but did not require it to be unique.
- Change made: added the `release_packet_header_unique` validator check and a regression test that appends a stale duplicate packet section after a valid packet.
- Validation run: `python -m pytest tests\test_alpha_release_truth_validator.py::test_validator_rejects_duplicate_release_decision_packet_sections -q`; `python -m pytest tests\test_alpha_release_truth_validator.py -q`; `python -m ruff check scripts\alpha_release_truth_validator.py tests\test_alpha_release_truth_validator.py`; `python -m ruff format --check scripts\alpha_release_truth_validator.py tests\test_alpha_release_truth_validator.py`; `python scripts\alpha_release_truth_validator.py --proof-head-from-packet --json`.
- Evidence: the new test failed before the implementation because duplicate sections still produced `passed`; after the fix the focused test passed, the full truth-validator file passed `14` tests, Ruff passed, and proof-head mode returned `19/19` checks with `proof_head_mode=packet`.
- Gate delta: release packet validation is stricter against stale shadow sections while preserving committed proof-head packet validation.
- User impact: maintainers get an explicit failure if two current alpha decision packets coexist in the report instead of trusting whichever section happens to appear first.
- Remaining blocker: push, tag, GitHub release, package publish, deploy, current-HEAD remote proof, Marketing/X promotion, and Claude mirror promotion all still require explicit human approval and post-action evidence.
- Next safe slice: mine release command-contract tests for another safe negative case that improves approval-gated packet validation without touching deferred Marketing/X or `.claude/**`.
