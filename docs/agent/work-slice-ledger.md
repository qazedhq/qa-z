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


## 2026-05-13 Repair Prompt Selection Context Visibility
- Repo: JustTyping
- Lane: repair prompt -> external executor handoff quality
- User-facing flow: `qa-z repair-prompt --from-run ... --json`
- Slice type: Flow / Evidence
- Before: repair-prompt JSON preserved selection context, but the Markdown `agent_prompt` omitted changed files and high-risk reasons, making executor-facing repair instructions less self-contained.
- Root cause: the renderer only printed selection mode, input source, and check buckets.
- Change made: rendered selected changed files and high-risk reasons in the repair prompt's check-selection section, with a helper that converts structured changed-file entries into inline-code paths.
- Validation run: `python -m pytest tests\test_repair_prompt.py::test_repair_prompt_json_includes_selection_context -q`; `python -m pytest tests\test_repair_prompt.py tests\test_repair_handoff.py -q`; `python -m ruff check src\qa_z\reporters\repair_prompt.py src\qa_z\reporters\repair_prompt_sections.py tests\test_repair_prompt.py tests\test_repair_handoff.py`; `python -m ruff format --check src\qa_z\reporters\repair_prompt.py src\qa_z\reporters\repair_prompt_sections.py tests\test_repair_prompt.py tests\test_repair_handoff.py`.
- Evidence: the focused test failed before implementation because `agent_prompt` omitted the high-risk line; after the fix the focused test passed, the repair prompt/handoff pack passed `16` tests, Ruff check exited `0` with a cache-write warning, and Ruff format reported `4` files already formatted.
- Gate delta: core handoff guidance is more actionable without adding live executor, queue, branch, commit, push, or API behavior.
- User impact: external repair executors now see the selection risk reason and changed file directly in the prompt, not only in machine JSON.
- Remaining blocker: this does not run or approve any external repair executor; QA-Z remains a local deterministic handoff generator.
- Next safe slice: run the second backlog expansion and choose a release command or benchmark fixture negative test that is safe to land locally.


## 2026-05-13 Direct Publish Approved-SHA Contract
- Repo: JustTyping
- Lane: alpha release preflight -> release command contracts -> current-truth handoff
- User-facing flow: `scripts/alpha_release_preflight.py --json`, alpha gate preflight promotion, and `docs/releases/v0.9.8-alpha-publish-handoff.md`
- Slice type: Contract / Evidence
- Before: the direct-publish path for an empty remote emitted `git push -u origin HEAD:<branch>`, while the release truth packet required approved-SHA refspecs and explicitly rejected moving `HEAD:main` pushes.
- Root cause: preflight direct-publish guidance predated the approved-SHA proof branch contract and still treated the local working `HEAD` as the push source.
- Change made: direct-publish checklists now require `test "$(git rev-parse HEAD)" = "<approved-sha>"` and `git push origin <approved-sha>:<repository_default_branch>`; preflight `next_commands` emit the same approved-SHA contract, and current-truth release handoff docs were updated to match.
- Validation run: `python -m pytest tests\test_alpha_release_preflight_remote.py::test_preflight_passes_when_local_clean_and_empty_remote_reachable tests\test_alpha_release_preflight_remote.py::test_preflight_direct_publish_guidance_uses_repository_default_branch tests\test_alpha_release_preflight_cli_render.py::test_render_preflight_human_prints_publish_checklist tests\test_alpha_release_gate_evidence.py::test_alpha_release_gate_promotes_direct_publish_guidance_on_success tests\test_current_truth_release_handoff.py::test_alpha_publish_handoff_pins_remote_blocker_and_next_commands -q`; `python -m pytest tests\test_alpha_release_preflight_remote.py tests\test_alpha_release_preflight_cli_render.py tests\test_alpha_release_gate_evidence.py tests\test_current_truth_release_handoff.py -q`; `python -m ruff check scripts\alpha_release_preflight_evidence.py tests\test_alpha_release_preflight_remote.py tests\test_alpha_release_preflight_cli_render.py tests\test_alpha_release_gate_evidence.py tests\test_current_truth_release_handoff.py`; `python -m ruff format --check scripts\alpha_release_preflight_evidence.py tests\test_alpha_release_preflight_remote.py tests\test_alpha_release_preflight_cli_render.py tests\test_alpha_release_gate_evidence.py tests\test_current_truth_release_handoff.py`; `python scripts\check_text_file_hygiene.py --source working-tree`.
- Evidence: the focused RED run failed while preflight still emitted `git push -u origin HEAD:main`; after implementation the focused pack passed `5` tests, the broader affected pack passed `73` tests, Ruff check/format passed, text hygiene passed, and a targeted search found no remaining positive direct-publish `HEAD:<branch>` guidance under `docs`, `scripts`, or `tests`.
- Gate delta: direct-publish release commands now align with proof-head safety and avoid moving-HEAD refspecs; no push, tag, release, package publish, deploy, credential, queue, or API mutation was performed.
- User impact: maintainers get a machine-checkable, immutable-SHA publish command instead of a moving local ref when a new empty repository is approved for direct publish.
- Remaining blocker: actual push/tag/GitHub release/package/deploy execution still requires explicit human approval and fresh remote proof.
- Next safe slice: mine preflight/worktree/alpha-gate consistency gaps for another local-only negative test that prevents release-readiness overclaims.


## 2026-05-13 Release PR Expected-Branch Command Contract
- Repo: JustTyping
- Lane: alpha release preflight -> release command contracts
- User-facing flow: `scripts/alpha_release_preflight.py --allow-existing-refs --json`
- Slice type: Contract / Evidence
- Before: the release-PR path checklist used the caller-provided `expected_branch`, but `next_actions` and `next_commands` still hardcoded the historical `codex/qa-z-bootstrap` branch.
- Root cause: branch-aware release PR guidance was only applied to the checklist renderer, not to the machine-readable command/action helpers.
- Change made: `next_actions_for_result` now accepts `expected_branch`, and release-PR `next_commands` push that same expected branch.
- Validation run: `python -m pytest tests\test_alpha_release_preflight_remote_refs.py::test_preflight_release_pr_guidance_uses_expected_branch -q`; `python -m pytest tests\test_alpha_release_preflight_remote_refs.py tests\test_alpha_release_preflight_remote.py -q`; `python -m ruff check scripts\alpha_release_preflight_evidence.py tests\test_alpha_release_preflight_remote_refs.py`; `python -m ruff format --check scripts\alpha_release_preflight_evidence.py tests\test_alpha_release_preflight_remote_refs.py`.
- Evidence: the focused RED run failed because the action still said `push codex/qa-z-bootstrap`; after the fix the focused test passed, the remote/ref preflight pack passed `30` tests, and Ruff check/format passed.
- Gate delta: release PR command packets are now branch-consistent for non-default release branch names without changing approval boundaries or executing a remote mutation.
- User impact: operators using an explicit release branch no longer receive mismatched human checklist and machine `next_commands` guidance.
- Remaining blocker: actually pushing the release branch still requires explicit approval and remote proof.
- Next safe slice: check CLI JSON/status contracts for planner, verify, or doctor output where a failure path may still be under-specified.


## 2026-05-13 Verify JSON Failure Contract
- Repo: JustTyping
- Lane: core verify CLI -> deterministic operator output
- User-facing flow: `qa-z verify --json`
- Slice type: Flow / Contract
- Before: successful `qa-z verify --json` emitted machine-readable comparison JSON, but missing-source and other failure paths still printed plain text, making automation parse failures differently from successes.
- Root cause: `handle_verify` handled exceptions with direct text `print` calls regardless of `--json`.
- Change made: added a `qa_z.verify_error` JSON payload for `--json` failure paths while preserving the existing non-JSON text output.
- Validation run: `python -m pytest tests\test_cli.py::test_verify_cli_json_reports_source_not_found_as_machine_payload tests\test_cli.py::test_verify_cli_returns_source_not_found_for_missing_run -q`; `python -m pytest tests\test_cli.py::test_verify_cli_compares_existing_runs_and_writes_artifacts tests\test_cli.py::test_verify_cli_rerun_creates_candidate_before_comparing tests\test_cli.py::test_verify_cli_returns_source_not_found_for_missing_run tests\test_cli.py::test_verify_cli_json_reports_source_not_found_as_machine_payload tests\test_session_commands.py -q`; `python -m ruff check src\qa_z\commands\session_verify.py tests\test_cli.py`; `python -m ruff format --check src\qa_z\commands\session_verify.py tests\test_cli.py`.
- Evidence: the focused RED failed with `JSONDecodeError` because output started with `qa-z verify: source not found`; after the fix the focused pair passed, the broader verify/session command pack passed `9` tests, and Ruff check/format passed.
- Gate delta: verify failure output is now machine-readable in JSON mode without changing verify exit codes or running external executors.
- User impact: scripts can branch on `kind=qa_z.verify_error`, `error`, and `exit_code` instead of brittle text parsing when verify cannot load a run.
- Remaining blocker: this does not prove repair quality by itself; callers still need comparable baseline and candidate run artifacts.
- Next safe slice: extend the same JSON failure contract to one adjacent command only after confirming its current tests and operator expectations.


## 2026-05-13 Repair Prompt JSON Failure Contract
- Repo: JustTyping
- Lane: repair prompt -> external executor handoff quality -> deterministic CLI output
- User-facing flow: `qa-z repair-prompt --json` and `qa-z repair-prompt --handoff-json`
- Slice type: Flow / Contract
- Before: successful repair-prompt JSON modes emitted machine-readable packets, but missing-source and artifact-error failures printed plain text.
- Root cause: `handle_repair_prompt` exception handlers did not branch on JSON output modes.
- Change made: added a `qa_z.repair_prompt_error` JSON payload for `--json` and `--handoff-json` failure paths while preserving existing plain-text output for legacy/default use.
- Validation run: `python -m pytest tests\test_repair_prompt.py::test_repair_prompt_json_failure_reports_machine_payload tests\test_repair_prompt.py::test_repair_prompt_cli_failures_report_expected_codes -q`; `python -m pytest tests\test_repair_prompt.py tests\test_repair_handoff.py tests\test_repair_prompt_contracts.py -q`; `python -m ruff check src\qa_z\commands\execution_repair.py tests\test_repair_prompt.py`; `python -m ruff format --check src\qa_z\commands\execution_repair.py tests\test_repair_prompt.py`.
- Evidence: the focused RED failed with `JSONDecodeError` because output started with `qa-z repair-prompt: source not found`; after the fix the focused pair passed, the repair prompt/handoff/contract pack passed `21` tests, Ruff check exited `0` with the known cache-write warning, and Ruff format passed.
- Gate delta: external executor handoff failures are parseable in JSON modes without running an executor, mutating a queue, or changing repair prompt success semantics.
- User impact: automation can treat repair-prompt missing-run and broken-artifact failures as structured error payloads instead of scraping text.
- Remaining blocker: this still only generates local deterministic repair guidance; it does not execute or approve external repairs.
- Next safe slice: run a validation wave across the changed release and core CLI packs before selecting another workstream.


## 2026-05-13 Executor Bridge JSON Failure Contract
- Repo: JustTyping
- Lane: external executor bridge -> deterministic CLI output
- User-facing flow: `qa-z executor-bridge --json`
- Slice type: Flow / Contract
- Before: successful executor-bridge JSON emitted a structured manifest, but missing-session and configuration failures still printed plain text even with `--json`.
- Root cause: `handle_executor_bridge` rendered exception paths directly instead of sharing JSON-mode error handling.
- Change made: added a `qa_z.executor_bridge_error` JSON payload for `--json` failure paths while preserving existing text output for non-JSON mode.
- Validation run: `python -m pytest tests\test_executor_bridge.py::test_executor_bridge_cli_json_missing_session_reports_machine_payload tests\test_executor_bridge.py::test_executor_bridge_cli_from_loop_and_missing_session -q`; `python -m pytest tests\test_executor_bridge.py tests\test_executor_bridge_helper_architecture.py -q`; `python -m ruff check src\qa_z\commands\runtime_bridge.py tests\test_executor_bridge.py`; `python -m ruff format --check src\qa_z\commands\runtime_bridge.py tests\test_executor_bridge.py`.
- Evidence: the focused RED failed with `JSONDecodeError` because output started with `qa-z executor-bridge: source not found`; after the fix the focused pair passed, the executor bridge pack passed `19` tests, and Ruff check/format passed.
- Gate delta: executor-bridge failures are now parseable in JSON mode without changing manifest success behavior or invoking a live executor.
- User impact: external executor orchestration wrappers can distinguish `source_not_found`, `artifact_error`, and `configuration_error` without brittle stdout parsing.
- Remaining blocker: executor bridge still only packages local handoff material; it does not run external agents or mutate target repositories.
- Next safe slice: broaden final validation across all changed CLI failure-contract packs, then pick a non-CLI release gate or benchmark fixture if continuing.


## 2026-05-13 Executor Result JSON Failure Contract
- Repo: JustTyping
- Lane: external executor return path -> deterministic CLI output
- User-facing flow: `qa-z executor-result dry-run --json` and `qa-z executor-result ingest --json`
- Slice type: Flow / Contract
- Before: executor-result dry-run and ingest success paths were structured, but exception paths printed plain text even in JSON mode.
- Root cause: the runtime executor-result command handlers had direct exception `print` calls instead of a JSON-aware error renderer.
- Change made: added a `qa_z.executor_result_error` payload with `command`, `error`, `exit_code`, and `message` for JSON failure paths while preserving text output otherwise.
- Validation run: `python -m pytest tests\test_executor_result_dry_run.py::test_executor_result_dry_run_json_missing_session_reports_machine_payload -q`; `python -m pytest tests\test_executor_result.py tests\test_executor_result_dry_run.py tests\test_executor_result_parsing.py tests\test_runtime_executor_result_architecture.py -q`; `python -m ruff check src\qa_z\commands\runtime_executor_result.py tests\test_executor_result_dry_run.py`; `python -m ruff format --check src\qa_z\commands\runtime_executor_result.py tests\test_executor_result_dry_run.py`.
- Evidence: the focused RED failed with `JSONDecodeError` because dry-run output started with `qa-z executor-result dry-run: artifact error`; after the fix the focused test passed, the executor-result pack passed `33` tests, and Ruff check/format passed.
- Gate delta: executor result return-path failures are now parseable in JSON mode without weakening ingest rejection handling or executing external repair work.
- User impact: callers can distinguish dry-run versus ingest failures and branch on stable error ids instead of scraping command-prefixed text.
- Remaining blocker: executor-result artifacts still must come from an approved external process; QA-Z only ingests and evaluates the local evidence.
- Next safe slice: run final validation across release command contracts plus core JSON failure contracts.


## 2026-05-13 Guard JSON Failure Contract
- Repo: JustTyping
- Lane: guard CLI -> deterministic operator output
- User-facing flow: `qa-z guard --json`
- Slice type: Flow / Contract
- Before: successful guard JSON emitted a structured verdict, but configuration and guard setup failures printed plain text even in JSON mode.
- Root cause: `handle_guard` reused a text-only config loader and printed exception paths directly.
- Change made: added a `qa_z.guard_error` payload for `--json` failure paths while preserving existing non-JSON text output and exit code `2`.
- Validation run: `python -m pytest tests\test_guard_cli.py::test_guard_json_config_error_reports_machine_payload tests\test_guard_cli.py::test_guard_happy_path_writes_merge_ok_verdict -q`; `python -m pytest tests\test_guard_cli.py -q`; `python -m ruff check src\qa_z\commands\guard.py tests\test_guard_cli.py`; `python -m ruff format --check src\qa_z\commands\guard.py tests\test_guard_cli.py`.
- Evidence: the focused RED run failed with `JSONDecodeError` because output started with `qa-z guard: configuration error`; after the fix the focused pair passed, the full guard CLI file passed `11` tests, and Ruff check/format passed.
- Gate delta: guard failures are now parseable in JSON mode without changing merge verdict semantics or adding remote/model behavior.
- User impact: automation can branch on `kind=qa_z.guard_error` and `error=configuration_error` instead of scraping human text when guard cannot load config.
- Remaining blocker: this does not prove a target repository is merge-safe; callers still need fresh guard verdict artifacts from valid config and current input evidence.
- Next safe slice: extend the same JSON failure contract to benchmark runtime failures, then run a broader validation wave.


## 2026-05-13 Benchmark JSON Failure Contract
- Repo: JustTyping
- Lane: benchmark CLI -> deterministic operator output
- User-facing flow: `qa-z benchmark --json`
- Slice type: Flow / Contract
- Before: successful benchmark JSON emitted a structured summary, but locked-results and other benchmark runtime errors printed plain text even in JSON mode.
- Root cause: `handle_benchmark` handled `BenchmarkError` with a direct text `print` regardless of `--json`.
- Change made: added a `qa_z.benchmark_error` JSON payload for benchmark failures in JSON mode while preserving existing text output otherwise.
- Validation run: `python -m pytest tests\test_benchmark_runtime.py::test_benchmark_cli_reports_locked_results_dir tests\test_benchmark_runtime.py::test_run_benchmark_rejects_locked_results_dir -q`; `python -m pytest tests\test_benchmark_runtime.py -q`; `python -m ruff check src\qa_z\commands\runtime_benchmark.py tests\test_benchmark_runtime.py`; `python -m ruff format --check src\qa_z\commands\runtime_benchmark.py tests\test_benchmark_runtime.py`.
- Evidence: the focused RED run failed with `JSONDecodeError` because locked-results output started with `qa-z benchmark: benchmark error`; after the fix the focused pair passed, the benchmark runtime pack passed, and Ruff check/format passed.
- Gate delta: benchmark runtime failures are now parseable in JSON mode without weakening lock handling or deleting generated results.
- User impact: operators and automation can distinguish benchmark infrastructure failure from fixture failure using stable JSON fields.
- Remaining blocker: this does not make benchmark results release proof by itself; operators still need a fresh successful benchmark run and committed/frozen evidence only when intentionally promoted.
- Next safe slice: run final validation across core CLI failure contracts, benchmark runtime, worktree plan, alpha gate, and truth-validator proof-head mode.


## 2026-05-13 Release Truth Validator Recovery Guidance
- Repo: JustTyping
- Lane: release truth validator -> proof-head lifecycle -> operator recovery guidance
- User-facing flow: `python scripts\alpha_release_truth_validator.py --json`
- Slice type: Contract / Evidence
- Before: default current-HEAD validation correctly failed when the tracked release packet was pinned to an older proof head, but the JSON payload only listed failed checks and did not provide the safe historical-proof rerun command.
- Root cause: release truth failure payloads had no deterministic next-action synthesis for stale packet/current-head mismatch checks.
- Change made: failed truth-validator payloads now include additive `next_actions` and `next_commands`, including the commit-safe `--proof-head-from-packet` validator rerun when stale packet/current-head checks fail; passed proof-head mode emits empty guidance arrays.
- Validation run: `python -m pytest tests\test_alpha_release_truth_validator.py::test_validator_rejects_stale_local_head_in_release_packet -q`; `python -m pytest tests\test_alpha_release_truth_validator.py -q`; `python scripts\alpha_release_truth_validator.py --json`; `python scripts\alpha_release_truth_validator.py --proof-head-from-packet --json`; `python -m ruff check scripts\alpha_release_truth_validator.py tests\test_alpha_release_truth_validator.py`; `python -m ruff format --check scripts\alpha_release_truth_validator.py tests\test_alpha_release_truth_validator.py`.
- Evidence: the focused RED failed with `KeyError: 'next_actions'`; after implementation the focused test passed, the truth-validator pack passed `14` tests, default validator still failed honestly on current-head packet staleness while showing recovery guidance, proof-head-from-packet mode passed `19/19`, and Ruff check/format passed.
- Gate delta: release truth remains fail-closed for moved HEADs while machine callers now receive the safe packet-proof validation command instead of scraping human context.
- User impact: operators can distinguish "regenerate for current HEAD" from "review historical proof packet" directly from JSON output.
- Remaining blocker: current local HEAD is still not remote-proven, and unapproved push/tag/GitHub release/package/deploy actions remain blocked.
- Next safe slice: run a broader validation wave across changed release truth and CLI failure-contract surfaces before choosing another release or core workflow hardening cycle.


## 2026-05-13 Release Truth Validator Human Recovery Output
- Repo: JustTyping
- Lane: release truth validator -> operator UX failure clarity
- User-facing flow: `python scripts\alpha_release_truth_validator.py`
- Slice type: Flow / Contract
- Before: the JSON truth-validator payload exposed stale-packet recovery guidance, but default human output still printed only failed check names.
- Root cause: `render_human()` did not render additive `next_actions` or `next_commands` from the same payload.
- Change made: human output now prints `next actions:` and `next commands:` sections when the truth-validator payload carries recovery guidance; passing proof-head mode remains terse.
- Validation run: `python -m pytest tests\test_alpha_release_truth_validator.py::test_validator_human_output_renders_recovery_guidance -q`; `python -m pytest tests\test_alpha_release_truth_validator.py -q`; `python -m ruff check scripts\alpha_release_truth_validator.py tests\test_alpha_release_truth_validator.py`; `python -m ruff format --check scripts\alpha_release_truth_validator.py tests\test_alpha_release_truth_validator.py`; `python scripts\alpha_release_truth_validator.py`; `python scripts\alpha_release_truth_validator.py --proof-head-from-packet`.
- Evidence: the focused RED failed because `next actions:` was absent; after implementation the focused test passed, the full truth-validator pack passed `15` tests, non-JSON default output still failed honestly while printing recovery sections, proof-head human output passed `19/19`, and Ruff check/format passed.
- Gate delta: operators using human output receive the same safe proof-head rerun guidance as JSON callers without weakening fail-closed current-HEAD validation.
- User impact: a terminal-only release operator can recover from stale packet/current-head mismatch without opening JSON.
- Remaining blocker: actual current-HEAD remote proof and release execution still require explicit approval and external/remote evidence.
- Next safe slice: run another backlog expansion pass and choose a different workstream instead of repeatedly polishing the same validator surface.


## 2026-05-13 Fast/Deep JSON Failure Contracts
- Repo: JustTyping
- Lane: fast/deep execution -> deterministic CLI output
- User-facing flow: `qa-z fast --json` and `qa-z deep --json`
- Slice type: Flow / Contract
- Before: successful fast/deep runs emitted structured JSON summaries, but missing-contract, argument, and missing-source failures printed human text even when JSON mode was requested.
- Root cause: the execution command handlers used direct exception `print` calls instead of a JSON-aware error renderer.
- Change made: added `qa_z.fast_error` and `qa_z.deep_error` payloads with stable `error`, `exit_code`, and `message` fields for JSON failure paths while preserving existing non-JSON output.
- Validation run: `python -m pytest tests\test_cli.py -q -k "fast_cli_json_reports_config_error or deep_cli_json_reports_argument_error or deep_cli_json_reports_source_not_found"`; `python -m pytest tests\test_cli.py -q`; `python -m ruff check src\qa_z\commands\execution_runs.py tests\test_cli.py`; `python -m ruff format --check src\qa_z\commands\execution_runs.py tests\test_cli.py`.
- Evidence: the focused RED failed with `JSONDecodeError` for all three covered failure paths; after implementation the focused tests passed, the CLI pack passed `47` tests, and Ruff check/format passed.
- Gate delta: core fast/deep workflow failures are now machine-parseable in JSON mode without weakening run summaries, artifact loading, or exit-code semantics.
- User impact: local automation can branch on stable error ids when the primary analysis commands cannot start, instead of scraping terminal prose.
- Remaining blocker: this does not prove target repositories are safe; operators still need fresh fast/deep artifacts from valid inputs before repair, guard, or release decisions.
- Next safe slice: extend JSON failure-contract coverage to review/github-summary or repair-session, then run a broader validation wave.


## 2026-05-13 Review JSON Failure Contract
- Repo: JustTyping
- Lane: review packet -> deterministic CLI output
- User-facing flow: `qa-z review --json`
- Slice type: Flow / Contract
- Before: successful review JSON emitted structured packets, but missing run and missing contract failures printed human text even when JSON mode was requested.
- Root cause: `handle_review` had text-only exception handling for artifact and source failures.
- Change made: added a `qa_z.review_error` payload with stable `error`, `exit_code`, and `message` fields for JSON failure paths while preserving existing human output.
- Validation run: `python -m pytest tests\test_review_packet_runtime.py -q -k "review_json_reports_missing"`; `python -m pytest tests\test_review_packet_runtime.py tests\test_review_packet_architecture.py -q`; `python -m ruff check src\qa_z\commands\review_packet.py tests\test_review_packet_runtime.py`; `python -m ruff format --check src\qa_z\commands\review_packet.py tests\test_review_packet_runtime.py`; `python -m qa_z review --path . --from-run .qa-z/runs/missing --json`.
- Evidence: the focused RED failed with `JSONDecodeError` for both missing run and missing contract paths; after implementation the focused tests passed, the review packet pack passed `17` tests, Ruff check/format passed, and the live missing-run command emitted `kind=qa_z.review_error`.
- Gate delta: the fast/deep -> review chain now keeps JSON mode parseable even when source artifacts are missing.
- User impact: external executor and CI wrappers can detect review source failures without scraping Markdown or terminal text.
- Remaining blocker: review packets still require fresh fast/deep input evidence; missing sources remain hard failures.
- Next safe slice: harden repair-session JSON failure contracts for the repair/verify loop.


## 2026-05-13 Repair Session JSON Failure Contracts
- Repo: JustTyping
- Lane: repair-session -> external executor handoff -> verify
- User-facing flow: `qa-z repair-session status --json` and `qa-z repair-session verify --json`
- Slice type: Flow / Contract
- Before: repair-session success paths emitted structured JSON, but missing session artifacts and verify argument errors printed human text even in JSON mode.
- Root cause: repair-session handlers used direct text `print` calls for artifact, source, and configuration failures.
- Change made: added `qa_z.repair_session_error` payloads with `command`, `error`, `exit_code`, and `message` fields for JSON failure paths while preserving existing start/status/verify human output and exit-code semantics.
- Validation run: `python -m pytest tests\test_repair_session.py -q -k "repair_session_status_json_reports_missing_session or repair_session_verify_json_reports_argument_error or repair_session_verify_json_reports_missing_session"`; `python -m pytest tests\test_repair_session.py -q`; `python -m ruff check src\qa_z\commands\session_repair.py tests\test_repair_session.py`; `python -m ruff format --check src\qa_z\commands\session_repair.py tests\test_repair_session.py`; `python -m qa_z repair-session status --path . --session .qa-z/sessions/missing --json`; `python -m qa_z repair-session verify --path . --session .qa-z/sessions/missing --json`.
- Evidence: the focused RED failed with `JSONDecodeError` for all three covered JSON failure paths; after implementation the focused tests passed, the repair-session pack passed `14` tests, Ruff check/format passed, and live missing-session/argument-error commands emitted `kind=qa_z.repair_session_error`.
- Gate delta: the repair-session loop now stays machine-parseable when handoff state is missing or verify invocation is invalid.
- User impact: external executor coordinators can distinguish `status` artifact failures from `verify` argument failures using stable fields.
- Remaining blocker: repair-session evidence still depends on a real failed baseline, external repair attempt, and candidate verification artifacts.
- Next safe slice: run a wider validation wave across CLI failure-contract surfaces and release truth proof-head mode before mining another workstream.


## 2026-05-13 Config Loader JSON Error Contract
- Repo: JustTyping
- Lane: CLI configuration loading -> deterministic JSON failure contracts
- User-facing flow: `qa-z fast --json`, `qa-z deep --json`, `qa-z review --json`, `qa-z verify --json`, and `qa-z repair-session verify --json`
- Slice type: Contract / Cleanup
- Before: command handlers emitted JSON for many runtime failures, but malformed config stopped inside the shared config loader and printed human text before command-specific JSON error helpers could run.
- Root cause: `load_cli_config()` had only a text output path and no way for JSON-capable callers to provide their error payload kind.
- Change made: added optional `json_error_kind` and `json_error_command` parameters to the shared config loader, then wired the fast, deep, review, verify, and repair-session verify handlers to their existing JSON error schemas.
- Validation run: `python -m pytest tests\test_cli.py -q -k "fast_cli_json_reports_broken_config or verify_cli_json_reports_broken_config"`; `python -m pytest tests\test_cli.py tests\test_review_packet_runtime.py tests\test_repair_session.py -q -k "broken_config"`; `python -m pytest tests\test_cli.py tests\test_review_packet_runtime.py tests\test_repair_session.py -q`; `python -m ruff check src\qa_z\commands\common.py src\qa_z\commands\execution_runs.py src\qa_z\commands\review_packet.py src\qa_z\commands\session_verify.py src\qa_z\commands\session_repair.py tests\test_cli.py tests\test_review_packet_runtime.py tests\test_repair_session.py`; `python -m ruff format --check src\qa_z\commands\common.py src\qa_z\commands\execution_runs.py src\qa_z\commands\review_packet.py src\qa_z\commands\session_verify.py src\qa_z\commands\session_repair.py tests\test_cli.py tests\test_review_packet_runtime.py tests\test_repair_session.py`.
- Evidence: the initial RED failed with `JSONDecodeError` for malformed fast and verify configs; after implementation five broken-config JSON tests passed, the related CLI/review/repair-session suite passed `76` tests, and Ruff check/format passed.
- Gate delta: malformed local config is now a machine-parseable failure for the primary analysis, review, verify, and repair-session verify surfaces.
- User impact: local orchestrators can fail closed on configuration errors using stable JSON fields instead of terminal prose.
- Remaining blocker: commands without JSON modes still intentionally render human text, and release execution remains approval-blocked.
- Next safe slice: run a broader validation wave, then mine non-JSON CLI surfaces or release-preflight truth gaps.


## 2026-05-13 Review Packet Error Contract Test Split
- Repo: JustTyping
- Lane: review packet tests -> architecture budget gate
- User-facing flow: `qa-z review --json`
- Slice type: Cleanup / Evidence
- Before: the mid-run alpha gate caught that `tests/test_review_packet_runtime.py` exceeded its architecture budget after JSON failure-contract tests were added.
- Root cause: review runtime behavior tests and review JSON error-contract tests were sharing one file despite an explicit regression-pack line budget.
- Change made: moved review JSON failure-contract coverage into `tests/test_review_packet_error_contracts.py`, leaving `tests/test_review_packet_runtime.py` at the enforced budget boundary.
- Validation run: `python -m pytest tests\test_review_packet_error_contracts.py tests\test_review_packet_runtime.py tests\test_repair_prompt_architecture.py::test_repair_prompt_regression_pack_stays_split -q`; `python -m ruff check tests\test_review_packet_error_contracts.py tests\test_review_packet_runtime.py`; `python -m ruff format --check tests\test_review_packet_error_contracts.py tests\test_review_packet_runtime.py`.
- Evidence: the architecture budget check now passes, `test_review_packet_runtime.py` is `220` lines, the new error-contract file is `74` lines, and the focused split validation passed `12` tests.
- Gate delta: full pytest no longer fails on review packet test-pack size while preserving all review JSON error-contract coverage.
- User impact: future review packet behavior changes can add runtime tests without immediately colliding with JSON error-contract coverage.
- Remaining blocker: the alpha gate still needs to be rerun after this split to confirm the full release-quality wave returns green.
- Next safe slice: rerun alpha gate and then continue backlog mining.


## 2026-05-13 Remaining JSON Config Loader Hookups
- Repo: JustTyping
- Lane: CLI configuration loading -> repair/executor/autonomy JSON contracts
- User-facing flow: `qa-z repair-prompt --json`, `qa-z repair-prompt --handoff-json`, `qa-z executor-result ingest --json`, and `qa-z autonomy --json`
- Slice type: Contract / Cleanup
- Before: the shared config loader supported JSON-capable callers, but repair-prompt, executor-result ingest, and autonomy had not yet wired their config-load failures to command-specific JSON payloads.
- Root cause: repair-prompt needed a JSON condition that includes `--handoff-json`, while executor-result and autonomy still used the default text-only loader call.
- Change made: added an explicit `json_error_when` option to `load_cli_config()`, then wired repair-prompt, executor-result ingest, and autonomy to their stable JSON error kinds.
- Validation run: `python -m pytest tests\test_cli_config_error_contracts.py -q`; `python -m pytest tests\test_cli_config_error_contracts.py tests\test_repair_prompt.py tests\test_repair_prompt_error_contracts.py tests\test_executor_result.py tests\test_executor_result_dry_run.py tests\test_autonomy.py -q`; `python -m ruff check src\qa_z\commands\common.py src\qa_z\commands\execution_repair.py src\qa_z\commands\runtime_executor_result.py src\qa_z\commands\runtime_autonomy.py tests\test_cli_config_error_contracts.py`; `python -m ruff format --check src\qa_z\commands\common.py src\qa_z\commands\execution_repair.py src\qa_z\commands\runtime_executor_result.py src\qa_z\commands\runtime_autonomy.py tests\test_cli_config_error_contracts.py`.
- Evidence: the focused RED failed with `JSONDecodeError` for all four newly covered malformed-config paths; after implementation the focused config-loader contract tests passed, the broader repair/executor/autonomy pack passed `88` tests, and Ruff check/format passed.
- Gate delta: malformed config is now machine-parseable across the primary JSON command family used in repair handoff, executor return, and autonomy planning.
- User impact: unattended wrappers can distinguish local configuration failure from artifact/source failure across more of the core QA-Z loop.
- Remaining blocker: commands without JSON output remain human-output-only, and remote release execution is still approval-blocked.
- Next safe slice: mine non-config JSON/stderr gaps or release-preflight truth gaps.


## 2026-05-13 Release Truth Validator Output Contract
- Repo: JustTyping
- Lane: alpha release truth validator -> machine evidence persistence
- User-facing flow: `python scripts\alpha_release_truth_validator.py --json --output <path>`
- Slice type: Contract / Evidence
- Before: the truth validator could emit JSON to stdout, but unlike the release gate and preflight scripts it had no `--output` evidence file path and no deterministic write-failure exit contract.
- Root cause: `alpha_release_truth_validator.py` had not adopted the common release-script output writer pattern.
- Change made: added `--output` support, newline-terminated JSON file writing, parent directory creation, and a deterministic stderr message plus exit code `2` when evidence writing fails.
- Validation run: `python -m pytest tests\test_alpha_release_truth_validator.py -q -k "truth_validator_cli"`; `python -m pytest tests\test_alpha_release_truth_validator.py -q`; `python -m ruff check scripts\alpha_release_truth_validator.py tests\test_alpha_release_truth_validator.py`; `python -m ruff format --check scripts\alpha_release_truth_validator.py tests\test_alpha_release_truth_validator.py`.
- Evidence: the focused RED failed because `--output` was an unrecognized argument; after implementation the focused CLI tests passed, the full truth-validator pack passed `17` tests, and Ruff check/format passed.
- Gate delta: release-truth evidence can now be saved as a first-class JSON artifact without depending on terminal capture.
- User impact: alpha release rehearsals and automation wrappers can archive truth-validator payloads beside gate/preflight evidence and detect output-write failures consistently.
- Remaining blocker: default validator output still correctly fails when the release packet proof head is stale against the current local HEAD; release execution remains approval-blocked.
- Next safe slice: validate strict plan and continue backlog mining for another release/preflight or core CLI contract gap.


## 2026-05-13 Release Truth Output Command Propagation
- Repo: JustTyping
- Lane: worktree commit plan -> alpha release validation commands
- User-facing flow: changed alpha release batches in `python scripts\worktree_commit_plan.py --json`
- Slice type: Evidence / Contract
- Before: the truth validator supported `--output`, but the alpha release closure batch still recommended stdout-only truth validation.
- Root cause: the commit-plan support rule had not been updated after adding persistent truth-validator evidence.
- Change made: updated the alpha release closure validation command to include `--output .qa-z/tmp/alpha-release-truth-validator.json`.
- Validation run: `python -m pytest tests\test_worktree_commit_plan.py::test_commit_plan_batches_include_targeted_validation_commands -q`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python -m ruff check scripts\worktree_commit_plan_support.py tests\test_worktree_commit_plan.py`; `python -m ruff format --check scripts\worktree_commit_plan_support.py tests\test_worktree_commit_plan.py`.
- Evidence: the focused RED showed the batch still emitted the stdout-only command; after implementation the targeted commit-plan test passed, strict worktree plan stayed `ready`, and Ruff check/format passed.
- Gate delta: release-closure batches now carry a persistent truth-validator evidence command beside gate/preflight output artifacts.
- User impact: maintainers following commit-plan validation no longer need to remember an extra output path by hand.
- Remaining blocker: remote release execution remains approval-blocked; output files under `.qa-z/tmp` remain local evidence and are not staged.
- Next safe slice: run a wider commit-plan validation wave or mine the next release/preflight truth gap.


## 2026-05-13 GitHub Summary Output Failure Contract
- Repo: JustTyping
- Lane: review/github-summary -> CI summary artifact writing
- User-facing flow: `qa-z github-summary --output <path>`
- Slice type: Flow / Contract
- Before: GitHub summary wrote successful `--output` files, but filesystem write failures could escape as raw Python exceptions instead of a deterministic command failure.
- Root cause: `handle_github_summary()` wrote directly to the output path without an OSError boundary, and the repair/session publish commit-plan validation omitted GitHub summary tests.
- Change made: added a small `write_github_summary_output()` helper that returns a stable write-failure message, keeps the rendered Markdown on stdout, reports the write failure on stderr, and exits `2`; updated the repair/session publish validation command to include GitHub summary tests.
- Validation run: `python -m pytest tests\test_github_summary_render.py::test_github_summary_cli_reports_output_write_failure -q`; `python -m pytest tests\test_github_summary_render.py tests\test_github_summary_session.py tests\test_review_commands.py -q`; `python -m pytest tests\test_github_summary_render.py tests\test_github_summary_session.py tests\test_review_commands.py tests\test_worktree_commit_plan.py::test_commit_plan_batches_include_targeted_validation_commands -q`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python -m ruff check src\qa_z\commands\review_github.py scripts\worktree_commit_plan_support.py tests\test_github_summary_render.py tests\test_worktree_commit_plan.py`; `python -m ruff format --check src\qa_z\commands\review_github.py scripts\worktree_commit_plan_support.py tests\test_github_summary_render.py tests\test_worktree_commit_plan.py`.
- Evidence: the focused RED raised `OSError: disk full`; after implementation the focused test passed, the GitHub summary/review pack passed `14` tests, the combined GitHub summary plus commit-plan validation passed `15` tests, strict worktree plan stayed `ready`, and Ruff check/format passed.
- Gate delta: CI/job-summary wrappers now get deterministic failure semantics when Markdown cannot be persisted.
- User impact: operators can distinguish a summary write failure from missing input artifacts without raw tracebacks or silent success.
- Remaining blocker: missing source artifacts remain hard failures, and remote release execution remains approval-blocked.
- Next safe slice: commit this pair, rerun strict plan, then mine another CLI/write-failure or guard-current-truth gap.


## 2026-05-13 Worktree Commit Plan Validation Test Split
- Repo: JustTyping
- Lane: worktree commit plan tests -> architecture budget gate
- User-facing flow: `python scripts\alpha_release_gate.py --quick --allow-dirty --json`
- Slice type: Cleanup / Evidence
- Before: the mid-run alpha gate caught `tests/test_worktree_commit_plan.py` at `732` lines, above the enforced `720` line split budget.
- Root cause: validation-command coverage had grown inside the main commit-plan behavior test file instead of a focused split file.
- Change made: moved validation-command assertions into `tests/test_worktree_commit_plan_validation_commands.py`, updated the architecture support-import check, and updated the commit-plan support validation command to include the new split file.
- Validation run: `python -m pytest tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_validation_commands.py tests\test_worktree_commit_plan_architecture.py::test_worktree_commit_plan_main_test_file_stays_under_split_budget -q`; `python -m pytest tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_validation_commands.py tests\test_worktree_commit_plan_architecture.py -q`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python -m ruff check scripts\worktree_commit_plan_support.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_validation_commands.py tests\test_worktree_commit_plan_architecture.py`; `python -m ruff format --check scripts\worktree_commit_plan_support.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_validation_commands.py tests\test_worktree_commit_plan_architecture.py`.
- Evidence: the split-focused pack passed `29` tests, the full commit-plan/architecture split pack passed `34` tests, `tests/test_worktree_commit_plan.py` is now `678` lines, strict worktree plan stayed `ready`, and Ruff check/format passed; Ruff format still reported non-fatal cache write warnings from `.ruff_cache`.
- Gate delta: the full alpha gate failure was traced to a real test-architecture budget breach and repaired without weakening the budget.
- User impact: future worktree plan behavior tests have room to grow in focused files instead of bloating the main regression pack.
- Remaining blocker: alpha gate must be rerun after this split before claiming the release-quality wave is green again.
- Next safe slice: rerun alpha gate, then continue backlog mining.


## 2026-05-13 Deep SARIF Output Failure Contract
- Repo: JustTyping
- Lane: deep analysis -> SARIF artifact writing
- User-facing flow: `qa-z deep --sarif-output <path> --json`
- Slice type: Flow / Contract
- Before: a SARIF copy write failure could escape as raw `OSError` after the deep run completed, even in JSON mode.
- Root cause: `handle_deep()` wrote SARIF artifacts outside its normalized command-error boundary, and `write_sarif_artifact()` did not attach the target path to OSError details.
- Change made: wrapped deep summary/SARIF artifact writes in the existing `qa_z.deep_error` path with `artifact_write_error`, made SARIF writer errors include the output path, and routed SARIF output-contract changes to the deep runner commit-plan batch.
- Validation run: `python -m pytest tests\test_sarif_cli.py::test_deep_json_reports_sarif_output_write_failure -q`; `python -m pytest tests\test_sarif_cli.py tests\test_deep_run_resolution.py tests\test_cli.py -q -k "sarif or deep"`; `python -m pytest tests\test_worktree_commit_plan.py::test_commit_plan_routes_sarif_output_contract_to_deep_batch tests\test_sarif_cli.py tests\test_deep_run_resolution.py -q`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python -m ruff check src\qa_z\commands\execution_runs.py src\qa_z\reporters\sarif.py scripts\worktree_commit_plan_support.py tests\test_sarif_cli.py tests\test_worktree_commit_plan.py`; `python -m ruff format --check src\qa_z\commands\execution_runs.py src\qa_z\reporters\sarif.py scripts\worktree_commit_plan_support.py tests\test_sarif_cli.py tests\test_worktree_commit_plan.py`.
- Evidence: the focused RED raised `OSError: disk full`; after implementation the focused SARIF error test passed, the SARIF/deep filtered pack passed `13` tests, the routing/SARIF/deep pack passed `11` tests, strict worktree plan stayed `ready`, and Ruff check/format passed.
- Gate delta: deep JSON mode now remains machine-parseable when SARIF evidence cannot be written.
- User impact: CI wrappers and local operators can distinguish deep analysis results from artifact persistence failures without raw tracebacks.
- Remaining blocker: release execution remains approval-blocked; a full alpha gate rerun is still needed after this slice before claiming the wave remains green.
- Next safe slice: commit SARIF/deep changes, rerun alpha gate or a focused deep validation wave, then continue mining.


## 2026-05-13 Repair Prompt Artifact Write Failure Contract
- Repo: JustTyping
- Lane: repair-prompt -> external executor handoff artifact writing
- User-facing flow: `qa-z repair-prompt --json`
- Slice type: Flow / Contract
- Before: a failed write of generated handoff markdown could escape as raw `OSError` after the repair packet had been built.
- Root cause: `handle_repair_prompt()` wrote Codex/Claude handoff markdown directly and only normalized source/artifact-load failures; the repair/session publish validation command also omitted the repair-prompt error-contract file.
- Change made: added a path-aware handoff markdown writer, normalized OSError to `qa_z.repair_prompt_error` with `artifact_write_error`, and updated the repair/session publish validation command to include `tests/test_repair_prompt_error_contracts.py`.
- Validation run: `python -m pytest tests\test_repair_prompt_error_contracts.py::test_repair_prompt_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_repair_prompt.py tests\test_repair_prompt_error_contracts.py tests\test_cli_config_error_contracts.py -q`; `python -m pytest tests\test_worktree_commit_plan_validation_commands.py::test_commit_plan_batches_include_targeted_validation_commands tests\test_repair_prompt_error_contracts.py tests\test_repair_prompt.py -q`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python -m ruff check src\qa_z\commands\execution_repair.py scripts\worktree_commit_plan_support.py tests\test_repair_prompt_error_contracts.py tests\test_worktree_commit_plan_validation_commands.py`; `python -m ruff format --check src\qa_z\commands\execution_repair.py scripts\worktree_commit_plan_support.py tests\test_repair_prompt_error_contracts.py tests\test_worktree_commit_plan_validation_commands.py`.
- Evidence: the focused RED raised `OSError: disk full`; after implementation the focused write-failure test passed, the repair-prompt/config pack passed `16` tests, the validation-command plus repair-prompt pack passed `13` tests, strict worktree plan stayed `ready`, and Ruff check/format passed.
- Gate delta: repair-prompt JSON mode now remains machine-parseable when local handoff artifacts cannot be written.
- User impact: external executor handoff automation can fail closed on artifact persistence failures instead of receiving a traceback.
- Remaining blocker: release execution remains approval-blocked; broader alpha gate should be rerun after this slice.
- Next safe slice: commit repair-prompt and validation-command updates, rerun a release-quality wave, then continue backlog mining.


## 2026-05-13 Review Packet Artifact Write Failure Contract
- Repo: JustTyping
- Lane: review packet -> review artifact writing
- User-facing flow: `qa-z review --json --output-dir <path>`
- Slice type: Flow / Contract
- Before: a failed `review.md` or `review.json` write could escape as raw `OSError` after the review packet was rendered.
- Root cause: `handle_review()` called the review artifact writer outside a command-owned OSError boundary, and the writer did not attach review-specific context to filesystem failures.
- Change made: added a review artifact write boundary that returns `qa_z.review_error` with `artifact_write_error`, and made the review artifact writer include the target output directory in write-failure details.
- Validation run: `python -m pytest tests\test_review_packet_error_contracts.py::test_review_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_review_packet_error_contracts.py tests\test_review_packet_runtime.py tests\test_review_packet_architecture.py tests\test_cli_config_error_contracts.py -q`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts\check_text_file_hygiene.py --source working-tree`; `python -m ruff check src\qa_z\commands\review_packet.py src\qa_z\reporters\review_packet.py tests\test_review_packet_error_contracts.py`; `python -m ruff format --check src\qa_z\commands\review_packet.py src\qa_z\reporters\review_packet.py tests\test_review_packet_error_contracts.py`; `git diff --check`.
- Evidence: the focused RED raised `OSError: disk full`; after implementation the focused write-failure test passed, the review/config pack passed `23` tests, strict worktree plan stayed `ready`, text-file hygiene passed, and Ruff check/format plus `git diff --check` passed.
- Gate delta: review JSON mode now remains machine-parseable when local review artifacts cannot be written.
- User impact: downstream review packet automation can tell artifact persistence failure apart from missing run/contract inputs without raw tracebacks.
- Remaining blocker: release execution remains approval-blocked; a broader alpha gate should be rerun after this slice.
- Next safe slice: commit review packet changes, then mine another output-failure surface such as verify or executor bridge.


## 2026-05-13 Verify Artifact Write Failure Contract
- Repo: JustTyping
- Lane: verify -> comparison artifact writing
- User-facing flow: `qa-z verify --json --output-dir <path>` and default candidate-run `verify` artifacts
- Slice type: Flow / Contract
- Before: a failed `summary.json`, `compare.json`, or `report.md` write could escape as raw `OSError` after the verification comparison was built.
- Root cause: `handle_verify()` wrote verification artifacts outside a command-owned OSError boundary, and the writer did not include output-directory context on persistence failures.
- Change made: added a verify artifact write boundary that returns `qa_z.verify_error` with `artifact_write_error`, made verification artifact writer failures path-aware, and updated the repair/session publish commit-plan ownership and validation command to include the new verify error-contract test.
- Validation run: `python -m pytest tests\test_verify_cli_error_contracts.py::test_verify_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_verify_cli_error_contracts.py tests\test_verification_artifact_io.py tests\test_verification_artifact_io_architecture.py tests\test_session_commands.py tests\test_worktree_commit_plan_validation_commands.py -q`; `python -m pytest tests\test_cli.py -q -k verify`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts\check_text_file_hygiene.py --source working-tree`; `python -m ruff check src\qa_z\commands\session_verify.py src\qa_z\verification_artifact_writing.py scripts\worktree_commit_plan_support.py tests\test_verify_cli_error_contracts.py tests\test_worktree_commit_plan_validation_commands.py`; `python -m ruff format --check src\qa_z\commands\session_verify.py src\qa_z\verification_artifact_writing.py scripts\worktree_commit_plan_support.py tests\test_verify_cli_error_contracts.py tests\test_worktree_commit_plan_validation_commands.py`; `git diff --check`.
- Evidence: the focused RED raised `OSError: disk full`; after implementation the focused write-failure test passed, the verify/artifact/session/commit-plan pack passed `11` tests, the verify-filtered CLI pack passed `5` tests, strict worktree plan returned `ready`, and hygiene/Ruff/diff checks passed.
- Gate delta: verify JSON mode now remains machine-parseable when local verification artifacts cannot be written.
- User impact: repair verification automation can fail closed on artifact persistence issues without losing the comparison error shape.
- Remaining blocker: release execution remains approval-blocked; alpha gate should be rerun after committing this slice.
- Next safe slice: commit verify behavior and commit-plan routing, then continue mining executor bridge or benchmark artifact write failures.


## 2026-05-13 Executor Bridge Artifact Write Failure Contract
- Repo: JustTyping
- Lane: executor bridge -> external executor handoff package writing
- User-facing flow: `qa-z executor-bridge --json`
- Slice type: Flow / Contract
- Before: a failed `bridge.json` or guide/template write could escape as raw `OSError` while creating an executor handoff package.
- Root cause: `create_executor_bridge()` cleaned up incomplete package directories but re-raised filesystem write failures without a CLI JSON boundary; the first implementation also had to preserve `ArtifactSourceNotFound` because it subclasses `FileNotFoundError`.
- Change made: added path-aware executor-bridge package write failure context, mapped true OSError persistence failures to `qa_z.executor_bridge_error` with `artifact_write_error`, and preserved source-not-found classification for missing packaged inputs.
- Validation run: `python -m pytest tests\test_executor_bridge.py::test_executor_bridge_cli_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_executor_bridge.py tests\test_session_commands.py -q`; `python -m mypy src tests`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts\check_text_file_hygiene.py --source working-tree`; `python -m ruff check src\qa_z\commands\runtime_bridge.py src\qa_z\executor_bridge_package.py tests\test_executor_bridge.py`; `python -m ruff format --check src\qa_z\commands\runtime_bridge.py src\qa_z\executor_bridge_package.py tests\test_executor_bridge.py`; `git diff --check`.
- Evidence: the focused RED raised `OSError: disk full`; after implementation the focused test passed, the executor bridge/session pack passed `21` tests, mypy reported no issues, strict worktree plan stayed `ready`, and hygiene/Ruff/diff checks passed.
- Gate delta: executor-bridge JSON mode now fails closed on package persistence failures while keeping missing source evidence distinct.
- User impact: external handoff automation receives machine-readable failure context and does not leave partial bridge packages behind.
- Remaining blocker: release execution remains approval-blocked; a broader alpha gate should be rerun after committing this slice.
- Next safe slice: commit executor bridge changes, then mine benchmark/report artifact write failures or guard workflow persistence failures.


## 2026-05-13 Benchmark Artifact Write Failure Contract
- Repo: JustTyping
- Lane: benchmark runtime -> benchmark summary/report artifacts
- User-facing flow: `qa-z benchmark --json`
- Slice type: Evidence / Contract
- Before: a failed `benchmarks/results/summary.json` or `report.md` write could escape as raw `OSError` after benchmark fixtures finished.
- Root cause: benchmark artifact writing had no path-aware OSError boundary, and the CLI only normalized `BenchmarkError` fixture/lock failures.
- Change made: added path-aware benchmark artifact write failures and mapped true persistence errors to `qa_z.benchmark_error` with `artifact_write_error`, while keeping fixture and lock failures as `benchmark_error`.
- Validation run: `python -m pytest tests\test_benchmark_runtime.py::test_benchmark_cli_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_benchmark_runtime.py tests\test_benchmark_reporting.py tests\test_benchmark_architecture.py tests\test_worktree_commit_plan_validation_commands.py -q`; `python -m pytest tests\test_benchmark.py -q`; `python -m mypy src tests`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts\check_text_file_hygiene.py --source working-tree`; `python -m ruff check src\qa_z\commands\runtime_benchmark.py src\qa_z\benchmark_reporting.py tests\test_benchmark_runtime.py`; `python -m ruff format --check src\qa_z\commands\runtime_benchmark.py src\qa_z\benchmark_reporting.py tests\test_benchmark_runtime.py`; `git diff --check`.
- Evidence: the focused RED raised `OSError: disk full`; after implementation the focused test passed, the benchmark runtime/reporting/architecture pack passed `20` tests, `tests\test_benchmark.py` passed `15` tests, mypy reported no issues, strict worktree plan stayed `ready`, and hygiene/Ruff/diff checks passed.
- Gate delta: benchmark JSON mode now fails closed when result artifacts cannot be persisted and does not conflate write failure with fixture expectation failure.
- User impact: maintainers can distinguish benchmark corpus failures from local disk/output-path failures in automation.
- Remaining blocker: release execution remains approval-blocked; a broader alpha gate should be rerun after committing this slice.
- Next safe slice: commit benchmark write failure handling, then mine guard workflow or run-summary artifact write failures.


## 2026-05-13 Guard Verdict Artifact Write Failure Contract
- Repo: JustTyping
- Lane: guard verdict -> deterministic operator output
- User-facing flow: `qa-z guard --json`
- Slice type: Flow / Contract
- Before: a failed `guard/verdict.json` or `guard/verdict.md` write could escape as raw `OSError` after the guard verdict was computed.
- Root cause: `write_verdict_artifacts()` wrote guard artifacts without path-aware error context, and `handle_guard()` only normalized configuration and guard input failures.
- Change made: added guard verdict artifact write context, mapped true persistence errors to `qa_z.guard_error` with `artifact_write_error`, and updated planning/runtime commit-plan validation to include the direct guard CLI test file.
- Validation run: `python -m pytest tests\test_guard_cli.py::test_guard_json_reports_verdict_artifact_write_failure -q`; `python -m pytest tests\test_guard_cli.py -q`; `python -m pytest tests\test_worktree_commit_plan_validation_commands.py::test_commit_plan_batches_include_targeted_validation_commands -q`; `python -m ruff check src\qa_z\commands\guard.py src\qa_z\guard\verdict.py tests\test_guard_cli.py`; `python -m ruff format --check src\qa_z\commands\guard.py src\qa_z\guard\verdict.py tests\test_guard_cli.py`; `python -m mypy src\qa_z\commands\guard.py src\qa_z\guard\verdict.py tests\test_guard_cli.py`.
- Evidence: the focused RED raised `OSError: disk full`; after implementation the focused test passed, the guard CLI file passed `12` tests, the commit-plan validation command canary passed, Ruff check/format passed, and focused mypy reported no issues.
- Gate delta: guard JSON mode now fails closed when verdict artifacts cannot be persisted instead of leaking a traceback after checks have run.
- User impact: merge-guard automation can distinguish local persistence failure from merge risk, stale current-truth, or bad config.
- Remaining blocker: this does not prove remote release readiness; push/tag/release/package/deploy remain approval-blocked.
- Next safe slice: commit guard behavior and validation routing, then mine the remaining guard repair or run-summary persistence surfaces.


## 2026-05-13 Run Summary Artifact Write Failure Contract
- Repo: JustTyping
- Lane: fast/deep execution -> run summary artifact writing
- User-facing flow: `qa-z fast --json` and `qa-z deep --json`
- Slice type: Flow / Contract
- Before: a failed `summary.json`, `summary.md`, or per-check JSON write from the shared run-summary reporter could escape as raw `OSError` on `qa-z fast`, while `qa-z deep` kept JSON mode but lost the artifact path context.
- Root cause: `write_run_summary_artifacts()` did not attach run-summary-specific context to filesystem failures, and `handle_fast()` wrote summary/latest-run artifacts outside a command-owned OSError boundary.
- Change made: made the shared run-summary artifact writer path-aware, mapped fast persistence failures to `qa_z.fast_error` with `artifact_write_error`, and updated planning/runtime commit-plan validation to include direct fast/deep error-contract tests.
- Validation run: `python -m pytest tests\test_execution_runs_error_contracts.py -q`; `python -m pytest tests\test_execution_runs_error_contracts.py tests\test_sarif_cli.py tests\test_deep_run_resolution.py -q`; `python -m pytest tests\test_cli.py -q -k "fast or deep"`; `python -m pytest tests\test_worktree_commit_plan_validation_commands.py::test_commit_plan_batches_include_targeted_validation_commands -q`; `python -m ruff check src\qa_z\commands\execution_runs.py src\qa_z\reporters\run_summary.py tests\test_execution_runs_error_contracts.py scripts\worktree_commit_plan_support.py tests\test_worktree_commit_plan_validation_commands.py`; `python -m ruff format --check src\qa_z\commands\execution_runs.py src\qa_z\reporters\run_summary.py tests\test_execution_runs_error_contracts.py scripts\worktree_commit_plan_support.py tests\test_worktree_commit_plan_validation_commands.py`; `python -m mypy src\qa_z\commands\execution_runs.py src\qa_z\reporters\run_summary.py tests\test_execution_runs_error_contracts.py`.
- Evidence: the focused RED failed with raw `OSError` for fast and missing path context for deep; after implementation the focused error-contract file passed, the SARIF/deep run-resolution pack passed `12` tests, the fast/deep CLI filter passed `16` tests, the commit-plan validation canary passed, Ruff check/format passed, and focused mypy reported no issues.
- Gate delta: fast/deep execution JSON mode now keeps local artifact persistence failures machine-readable and path-aware.
- User impact: automation can tell runner/check failures from disk or output-path failures without scraping tracebacks.
- Remaining blocker: release execution remains approval-blocked and current local HEAD is still not remote-proven.
- Next safe slice: commit run-summary behavior and validation routing, then mine repair-session or executor-ingest persistence surfaces.


## 2026-05-13 Executor Result Ingest Artifact Write Failure Contract
- Repo: JustTyping
- Lane: executor result -> ingest summary/report persistence
- User-facing flow: `qa-z executor-result ingest --json`
- Slice type: Flow / Contract
- Before: a failed `ingest.json` or `ingest_report.md` write could escape as raw `OSError` from the executor-result ingest path.
- Root cause: `finalized_ingest_outcome()` wrote ingest artifacts without path-aware context, and `handle_executor_result_ingest()` normalized source/config/artifact-load errors but not local persistence failures.
- Change made: added executor-result ingest artifact write context, mapped ingest persistence failures to `qa_z.executor_result_error` with `artifact_write_error`, and updated executor-return commit-plan validation to include the ingest outcome test file.
- Validation run: `python -m pytest tests\test_executor_ingest_outcome.py::test_finalized_ingest_outcome_reports_artifact_write_failure -q`; `python -m pytest tests\test_executor_result.py::test_executor_result_ingest_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_executor_result.py tests\test_executor_ingest_outcome.py tests\test_executor_result_dry_run.py -q`; `python -m pytest tests\test_benchmark_executor_runtime.py -q`; `python -m pytest tests\test_worktree_commit_plan_validation_commands.py::test_commit_plan_batches_include_targeted_validation_commands -q`; `python -m ruff check src\qa_z\commands\runtime_executor_result.py src\qa_z\executor_ingest_outcome.py tests\test_executor_ingest_outcome.py tests\test_executor_result.py`; `python -m ruff format --check src\qa_z\commands\runtime_executor_result.py src\qa_z\executor_ingest_outcome.py tests\test_executor_ingest_outcome.py tests\test_executor_result.py`; `python -m mypy src\qa_z\commands\runtime_executor_result.py src\qa_z\executor_ingest_outcome.py tests\test_executor_ingest_outcome.py tests\test_executor_result.py`.
- Evidence: the focused RED showed the writer preserving only `disk full` and the CLI leaking raw `OSError`; after implementation both focused tests passed, the executor-result/ingest/dry-run pack passed `35` tests, the benchmark executor runtime pack passed `5` tests, the commit-plan validation canary passed, Ruff check/format passed, and focused mypy reported no issues.
- Gate delta: executor-result ingest now fails closed with machine-readable local persistence failures while preserving existing source/config rejection behavior.
- User impact: maintainers can distinguish a bad external result from a local artifact persistence failure before trusting ingest/verify state.
- Remaining blocker: executor-result ingest still consumes local handoff artifacts only; no external executor or target repository mutation was added.
- Next safe slice: commit executor-result ingest behavior and validation routing, then mine repair-session lifecycle artifact persistence or run a release-quality validation wave.


## 2026-05-13 Repair Session Verification Artifact Write Failure Contract
- Repo: JustTyping
- Lane: repair-session verify -> outcome persistence
- User-facing flow: `qa-z repair-session verify --json`
- Slice type: Flow / Contract
- Before: a failed session `summary.json`, `outcome.md`, or manifest update during verification could escape as raw `OSError`.
- Root cause: `complete_session_verification()` wrote verification outcome artifacts without a path-aware boundary, and the repair-session CLI did not classify local persistence failures.
- Change made: added repair-session verification artifact write context, mapped start/verify persistence failures to `qa_z.repair_session_error` with `artifact_write_error`, and preserved the existing source/config/artifact-load failure contracts.
- Validation run: `python -m pytest tests\test_repair_session.py::test_repair_session_verify_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_repair_session.py tests\test_session_commands.py tests\test_verify_cli_error_contracts.py -q`; `python -m ruff check src\qa_z\commands\session_repair.py src\qa_z\repair_session_lifecycle.py tests\test_repair_session.py`; `python -m ruff format --check src\qa_z\commands\session_repair.py src\qa_z\repair_session_lifecycle.py tests\test_repair_session.py`; `python -m mypy src\qa_z\commands\session_repair.py src\qa_z\repair_session_lifecycle.py tests\test_repair_session.py`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the focused test passed, the repair-session/session/verify pack passed `22` tests, Ruff check/format passed, and focused mypy reported no issues.
- Gate delta: repair-session verify JSON mode now distinguishes local persistence failure from verification verdicts and source/config errors.
- User impact: external repair workflows do not mistake a disk/output failure for an actual verification result.
- Remaining blocker: repair-session still waits for external human/agent repair work; QA-Z does not edit target repositories.
- Next safe slice: commit repair-session verify behavior, then mine remaining start-session handoff or executor dry-run persistence paths.


## 2026-05-13 Repair Session Start JSON and Artifact Write Contract
- Repo: JustTyping
- Lane: repair-session start -> external handoff package persistence
- User-facing flow: `qa-z repair-session start --json`
- Slice type: Flow / Contract
- Before: repair-session start had only human stdout, and a failed handoff/session artifact write could lose path context or stay text-only.
- Root cause: the start parser lacked `--json`, while `create_repair_session()` wrote packet, handoff, guide, safety, and manifest artifacts without a single start-owned OSError boundary.
- Change made: added start JSON output for the session manifest, wrapped start artifact persistence with a path-aware error, and reused `qa_z.repair_session_error` with `artifact_write_error` for JSON-mode start failures.
- Validation run: `python -m pytest tests\test_repair_session.py::test_repair_session_start_json_writes_session_payload tests\test_repair_session.py::test_repair_session_start_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_repair_session.py tests\test_session_commands.py -q`; `python -m ruff check src\qa_z\commands\session_repair.py src\qa_z\repair_session_lifecycle.py tests\test_repair_session.py`; `python -m ruff format --check src\qa_z\commands\session_repair.py src\qa_z\repair_session_lifecycle.py tests\test_repair_session.py`; `python -m mypy src\qa_z\commands\session_repair.py src\qa_z\repair_session_lifecycle.py tests\test_repair_session.py`.
- Evidence: the focused RED failed because `--json` was unrecognized; after implementation both start JSON tests passed, the repair-session/session pack passed `23` tests, Ruff check/format passed, and focused mypy reported no issues.
- Gate delta: repair-session start can now be consumed by automation without scraping human stdout and fails closed on local persistence problems.
- User impact: external repair handoff setup is easier to script while staying local-only and deterministic.
- Remaining blocker: start only packages local handoff artifacts; it does not execute external repair work or mutate target repositories.
- Next safe slice: commit repair-session start behavior, then mine executor dry-run/report or autonomy artifact persistence surfaces.


## 2026-05-13 Executor Result Dry-Run Artifact Write Failure Contract
- Repo: JustTyping
- Lane: executor result -> dry-run safety report persistence
- User-facing flow: `qa-z executor-result dry-run --json`
- Slice type: Evidence / Contract
- Before: a failed `dry_run_summary.json` or `dry_run_report.md` write could escape as raw `OSError` from the executor-result dry-run command.
- Root cause: `run_executor_result_dry_run()` wrote materialized dry-run artifacts without a path-aware boundary, and the dry-run CLI normalized load/source/config failures but not persistence failures.
- Change made: added executor-result dry-run artifact write context, mapped dry-run persistence failures to `qa_z.executor_result_error` with `artifact_write_error`, and updated executor-return commit-plan validation to include the dry-run test file.
- Validation run: `python -m pytest tests\test_executor_result_dry_run.py::test_executor_result_dry_run_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_executor_result_dry_run.py tests\test_executor_result.py tests\test_executor_ingest_outcome.py -q`; `python -m pytest tests\test_worktree_commit_plan_validation_commands.py::test_commit_plan_batches_include_targeted_validation_commands -q`; `python -m ruff check src\qa_z\commands\runtime_executor_result.py src\qa_z\executor_dry_run.py tests\test_executor_result_dry_run.py`; `python -m ruff format --check src\qa_z\commands\runtime_executor_result.py src\qa_z\executor_dry_run.py tests\test_executor_result_dry_run.py`; `python -m mypy src\qa_z\commands\runtime_executor_result.py src\qa_z\executor_dry_run.py tests\test_executor_result_dry_run.py`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the focused test passed, the executor-result dry-run/result/ingest pack passed `36` tests, the commit-plan validation canary passed, Ruff check/format passed, and focused mypy reported no issues.
- Gate delta: dry-run safety evidence now remains machine-parseable when the local artifact store fails.
- User impact: maintainers can distinguish unsafe executor history from a failed dry-run evidence write.
- Remaining blocker: dry-run remains live-free and cannot prove actual target-repo repair quality without subsequent verification.
- Next safe slice: commit dry-run behavior and validation routing, then mine autonomy/self-inspection artifact persistence or run another release-quality validation wave.


## 2026-05-13 Autonomy Artifact Write Failure Contract
- Repo: JustTyping
- Lane: autonomy loop -> runtime summary artifact persistence
- User-facing flow: `qa-z autonomy --json`
- Slice type: Flow / Contract
- Before: a failed autonomy runtime artifact write could escape as raw `OSError` during a local autonomy loop, even in JSON mode.
- Root cause: `handle_autonomy()` loaded config through a normalized JSON error path but called `run_autonomy()` outside a command-owned OSError boundary.
- Change made: mapped autonomy runtime persistence failures to `qa_z.autonomy_error` with `artifact_write_error`, preserved the existing configuration JSON contract, and added a focused regression that fails the latest autonomy summary write.
- Validation run: `python -m pytest tests\test_autonomy.py::test_autonomy_cli_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_autonomy.py::test_autonomy_cli_json_reports_artifact_write_failure tests\test_autonomy.py::test_autonomy_cli_run_and_status -q`; `python -m pytest tests\test_cli_config_error_contracts.py::test_autonomy_json_reports_broken_config_as_machine_payload -q`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the new artifact write regression and the existing runtime/status and broken-config contracts passed.
- Gate delta: autonomy JSON mode now distinguishes local artifact persistence failure from runtime budget or task selection results.
- User impact: long-running local autonomy operators get a machine-readable failure reason instead of a traceback if the artifact store fails.
- Remaining blocker: release execution remains approval-blocked and autonomy still prepares local planning/handoff artifacts only; it does not mutate target repositories.
- Next safe slice: commit autonomy behavior, then mine self-inspection/select-next artifact persistence or run another release-quality validation wave.


## 2026-05-13 Self-Improvement Planner Artifact Write Failure Contract
- Repo: JustTyping
- Lane: self-inspect/select-next -> backlog and selected-task artifact persistence
- User-facing flow: `qa-z self-inspect --json` and `qa-z select-next --json`
- Slice type: Flow / Contract
- Before: failed self-inspection or selected-task artifact writes could escape as raw `OSError` from the planner CLI commands.
- Root cause: `handle_self_inspect()` and `handle_select_next()` delegated to artifact-writing helpers and then read their outputs without command-owned OSError boundaries.
- Change made: mapped planner persistence failures to `qa_z.self_inspect_error` or `qa_z.select_next_error` with `artifact_write_error`, and added focused regressions for failed `self_inspect.json` and `selected_tasks.json` writes.
- Validation run: `python -m pytest tests\test_self_improvement.py::test_self_inspect_json_reports_artifact_write_failure tests\test_self_improvement.py::test_select_next_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_self_improvement.py::test_self_improvement_cli_commands_write_expected_paths -q`.
- Evidence: both focused RED tests raised raw `OSError: disk full`; after implementation both artifact write contracts passed and the existing CLI path regression still passed.
- Gate delta: the self-improvement planning loop now keeps local persistence failures machine-readable before autonomy, repair, or guard workflows consume stale planner state.
- User impact: maintainers can distinguish a planner output-store failure from a true empty backlog or task-selection outcome.
- Remaining blocker: planner commands remain local-only; they do not create commits, mutate target repositories, or prove release execution readiness.
- Next safe slice: commit planner behavior, then rerun strict plan and a broader self-improvement validation wave.


## 2026-05-13 Init Bootstrap Artifact Write Failure Contract
- Repo: JustTyping
- Lane: init/doctor onboarding -> starter file persistence
- User-facing flow: `qa-z init`
- Slice type: Flow / Contract
- Before: a failed starter `qa-z.yaml`, contracts README, agent template, or workflow write could escape as raw `OSError`.
- Root cause: `handle_init()` called starter file writers directly and only reported created/skipped paths after all writes succeeded.
- Change made: wrapped bootstrap artifact writes in a command-owned OSError boundary that returns exit code `2` and prints a deterministic `qa-z init: artifact write error` message.
- Validation run: `python -m pytest tests\test_cli.py::test_init_reports_artifact_write_failure -q`; `python -m pytest tests\test_cli.py::test_init_reports_artifact_write_failure tests\test_cli.py::test_init_creates_bootstrap_files tests\test_cli.py::test_init_is_idempotent -q`; `python -m pytest tests\test_init_options.py -q`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the focused init failure contract passed, the core init create/idempotent tests passed, and the optional init profile/template/workflow pack passed `14` tests.
- Gate delta: onboarding failure output is deterministic before doctor or fast/deep workflows run.
- User impact: new QA-Z adopters get a clear local filesystem failure instead of a traceback during repository bootstrap.
- Remaining blocker: init remains local-only and does not prove any remote, package, or production readiness.
- Next safe slice: commit init behavior, then run an init/doctor/CLI validation wave before mining the next command-contract gap.


## 2026-05-13 Plan Contract Artifact Write Failure Contract
- Repo: JustTyping
- Lane: plan -> QA contract draft persistence
- User-facing flow: `qa-z plan`
- Slice type: Flow / Contract
- Before: a failed contract draft write could escape as raw `OSError` from `qa-z plan`.
- Root cause: `handle_plan()` loaded config through a normalized boundary but delegated contract rendering and persistence without catching local filesystem failures.
- Change made: wrapped contract draft generation in a command-owned OSError boundary that returns exit code `2` and prints a deterministic `qa-z plan: artifact write error` message.
- Validation run: `python -m pytest tests\test_cli.py::test_plan_reports_artifact_write_failure -q`; `python -m pytest tests\test_cli.py::test_plan_reports_artifact_write_failure tests\test_cli.py::test_plan_creates_a_contract_draft_from_sources tests\test_cli.py::test_plan_uses_custom_contract_output_directory -q`; `python -m pytest tests\test_bootstrap_commands.py -q`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the plan artifact failure regression, existing plan creation/custom-output tests, and bootstrap seam tests passed.
- Gate delta: contract-generation failures are now separate from config errors, source inputs, and existing-contract no-op results.
- User impact: maintainers can tell a local output-store failure from a real generated contract status before review or repair-prompt workflows consume the draft.
- Remaining blocker: plan remains a local contract draft generator and does not execute checks, mutate repositories, or prove release readiness.
- Next safe slice: commit plan behavior, then run the bootstrap/planner validation pack before mining another command-contract gap.


## 2026-05-13 Backlog Refresh Artifact Write Failure Contract
- Repo: JustTyping
- Lane: backlog refresh -> self-inspection/current-truth artifact persistence
- User-facing flow: `qa-z backlog --refresh --json`
- Slice type: Flow / Contract
- Before: a failed self-inspection artifact write during backlog refresh could escape as raw `OSError`.
- Root cause: `handle_backlog()` called the shared refresh helper and then loaded backlog state without a command-owned OSError boundary.
- Change made: mapped refresh-time persistence failures to `qa_z.backlog_error` with `artifact_write_error`, preserving existing successful plain-text and JSON backlog behavior.
- Validation run: `python -m pytest tests\test_cli.py::test_backlog_refresh_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_cli.py::test_backlog_refresh_json_reports_artifact_write_failure tests\test_cli.py::test_backlog_refresh_runs_self_inspection_before_printing tests\test_cli.py::test_backlog_plain_output_focuses_on_open_items -q`; `python -m pytest tests\test_planning_commands.py -q`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the refresh failure regression, existing backlog refresh/plain output tests, and planning seam tests passed.
- Gate delta: current-truth refresh output now distinguishes local artifact persistence failure from an empty or closed backlog.
- User impact: operators can rerun or repair the local artifact store instead of acting on a misleading backlog state when refresh writes fail.
- Remaining blocker: backlog refresh remains a local evidence refresh and does not prove remote release execution readiness.
- Next safe slice: commit backlog behavior, then run the self-improvement/backlog validation pack before mining another CLI contract gap.


## 2026-05-13 Skill Install Artifact Write Failure Contract
- Repo: JustTyping
- Lane: skill install -> local agent instruction persistence
- User-facing flow: `qa-z skill install codex`
- Slice type: Flow / Contract
- Before: a failed instruction file write could escape as raw `OSError` from `qa-z skill install`.
- Root cause: `handle_skill_install()` iterated install targets without a command-owned filesystem error boundary.
- Change made: mapped install-time persistence failures to a deterministic `qa-z skill install: artifact write error` message with exit code `2`.
- Validation run: `python -m pytest tests\test_skill_install_cli.py::test_skill_install_reports_artifact_write_failure -q`; `python -m pytest tests\test_skill_install_cli.py::test_skill_install_reports_artifact_write_failure tests\test_skill_install_cli.py::test_skill_install_codex_writes_agents_file tests\test_skill_install_cli.py::test_skill_install_all_targets_create_expected_files -q`; `python -m pytest tests\test_demo_guard_action_package.py::test_agent_skill_pack_and_templates_exist tests\test_demo_guard_action_package.py::test_packaged_skill_pack_matches_public_source_pack -q`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the focused failure contract, codex/all-target install paths, and packaged skill/template parity checks passed.
- Gate delta: local agent-instruction setup now fails with deterministic operator output when the filesystem rejects writes.
- User impact: maintainers setting up Codex/Claude/Cursor/Copilot instruction files can distinguish an overwrite refusal from a local artifact write failure.
- Remaining blocker: skill install remains a local instruction writer and does not approve or mutate release execution.
- Next safe slice: commit skill install behavior, then run the guard/skill/demo validation pack before mining the next safe local CLI contract.


## 2026-05-13 Demo Auth-Bug Artifact Write Failure Contract
- Repo: JustTyping
- Lane: demo auth-bug -> local demo artifact preparation
- User-facing flow: `qa-z demo auth-bug`
- Slice type: Flow / Contract
- Before: a failed demo copy or runtime config write could escape as raw `OSError`.
- Root cause: `handle_demo_auth_bug()` prepared the isolated demo directory and config before any command-owned filesystem error boundary.
- Change made: wrapped demo artifact preparation in a deterministic `qa-z demo auth-bug: artifact write error` path with exit code `2`.
- Validation run: `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_runtime_config_write_failure -q`; `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_runtime_config_write_failure tests\test_demo_guard_action_package.py::test_demo_auth_bug_command_writes_repair_and_guard_artifacts -q`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the focused failure contract and the existing end-to-end auth-bug demo artifact test passed.
- Gate delta: the public demo smoke path now separates local filesystem setup failure from guard/plan failure.
- User impact: prospective operators running the built-in demo get a clear local artifact failure instead of a traceback before trusting the demo result.
- Remaining blocker: demo remains local-only proof and does not add remote, publish, or production readiness.
- Next safe slice: commit demo behavior, then run the demo/artifact-smoke validation pack before mining another command-contract gap.


## 2026-05-13 Executor Safety Artifact Write Failure Contract
- Repo: JustTyping
- Lane: repair-session/executor-bridge -> pre-live executor safety package persistence
- User-facing flow: `qa-z repair-session start --json` and `qa-z executor-bridge --json`
- Slice type: Contract / Evidence
- Before: the shared executor safety package writer could raise a raw `OSError` without naming the executor safety artifact directory when `executor_safety.json` or `executor_safety.md` failed to persist.
- Root cause: `write_executor_safety_artifacts()` created and wrote both artifacts without a path-aware filesystem boundary, while the consuming CLI commands had to add higher-level context later.
- Change made: wrapped the shared writer with a deterministic `could not write executor safety artifacts to ...` message and added a focused regression that simulates a failed `executor_safety.json` write.
- Validation run: `python -m pytest tests\test_artifact_schema.py::test_write_executor_safety_artifacts_wraps_write_failures -q`; `python -m pytest tests\test_artifact_schema.py::test_write_executor_safety_artifacts_wraps_write_failures tests\test_artifact_schema.py::test_executor_safety_package_schema_v1_required_fields_are_stable tests\test_repair_session.py::test_repair_session_start_json_reports_artifact_write_failure tests\test_executor_bridge.py::test_executor_bridge_cli_json_reports_artifact_write_failure -q`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the new writer regression, safety schema canary, repair-session artifact failure contract, and executor-bridge artifact failure contract passed.
- Gate delta: both repair-session and executor-bridge now inherit path-aware safety package persistence failures before any live executor or target-repo mutation can be implied.
- User impact: operators can distinguish a failed local safety package write from a repair handoff, bridge manifest, or executor-result failure.
- Remaining blocker: the safety package remains pre-live/local-only and does not authorize external executor dispatch or remote release execution.
- Next safe slice: commit executor safety behavior, then mine the repair handoff writer or run a broader repair/executor validation wave.


## 2026-05-13 Repair Handoff Artifact Write Failure Contract
- Repo: JustTyping
- Lane: finding -> repair prompt -> normalized external handoff persistence
- User-facing flow: `qa-z repair-prompt --json` and guard/benchmark handoff generation
- Slice type: Flow / Contract
- Before: the shared normalized repair handoff writer could raise a raw `OSError` without naming the handoff artifact directory when `handoff.json` failed to persist.
- Root cause: `write_repair_handoff_artifact()` created the output directory and wrote `handoff.json` without a path-aware filesystem boundary, leaving each caller to add broader context after the original path was lost.
- Change made: wrapped the shared handoff writer with a deterministic `could not write repair handoff artifact to ...` message and added a focused regression for a failed `handoff.json` write.
- Validation run: `python -m pytest tests\test_repair_handoff.py::test_write_repair_handoff_artifact_wraps_write_failures tests\test_repair_handoff.py::test_repair_prompt_cli_writes_handoff_and_adapter_artifacts tests\test_repair_prompt_error_contracts.py::test_repair_prompt_json_reports_artifact_write_failure -q`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the new writer regression, repair-prompt handoff write path, and JSON artifact failure contract passed.
- Gate delta: repair prompt, guard workflow, benchmark handoff generation, and repair-session start now share a path-aware handoff persistence boundary.
- User impact: operators can tell a handoff JSON persistence failure apart from adapter markdown rendering, repair packet generation, or artifact source loading.
- Remaining blocker: repair handoff remains an external-executor instruction artifact; QA-Z still does not directly edit target repositories.
- Next safe slice: commit repair handoff behavior, then run a broader repair/guard/benchmark validation wave before mining the next writer gap.


## 2026-05-13 Guard GitHub Summary Artifact Write Failure Contract
- Repo: JustTyping
- Lane: guard -> GitHub summary artifact persistence
- User-facing flow: `qa-z guard --github-summary --json`
- Slice type: Flow / Contract
- Before: a failed optional guard GitHub summary write returned `qa-z guard: artifact error: disk full` without naming the summary artifact path.
- Root cause: `run_guard()` created the guard directory and wrote `github-summary.md` inline, so the command-level OSError boundary could not add artifact-specific context.
- Change made: added a path-aware `write_guard_github_summary_artifact()` helper and a focused JSON regression for failed `github-summary.md` persistence.
- Validation run: `python -m pytest tests\test_guard_cli.py::test_guard_github_summary_json_reports_artifact_write_failure tests\test_guard_cli.py::test_guard_github_summary_option_writes_summary tests\test_guard_cli.py::test_guard_json_reports_verdict_artifact_write_failure -q`.
- Evidence: the focused RED produced only `qa-z guard: artifact error: disk full`; after implementation the failure payload includes `could not write guard GitHub summary artifact to ...`, and existing summary/verdict artifact tests still pass.
- Gate delta: guard JSON output now distinguishes optional GitHub-summary persistence failures from verdict artifact failures and source/config errors.
- User impact: maintainers using guard in CI can identify the exact failing summary path before trusting or rerunning the guard result.
- Remaining blocker: GitHub summary rendering remains local artifact generation only; no GitHub comment, release, push, or deployment behavior was added.
- Next safe slice: commit guard summary behavior, then run the guard/GitHub-summary validation pack before mining another writer gap.


## 2026-05-13 Guard Repair Artifact Write Failure Contract
- Repo: JustTyping
- Lane: guard -> blocking verdict repair handoff persistence
- User-facing flow: `qa-z guard --json` when fast/deep checks block merge
- Slice type: Flow / Contract
- Before: a failed guard repair companion write, such as `repair/codex.md`, returned `qa-z guard: artifact error: disk full` without naming the failed repair artifact path.
- Root cause: `write_guard_repair()` wrote `repair.json`, `codex.md`, and `claude.md` inline after the shared repair packet/handoff writers succeeded.
- Change made: added a path-aware guard repair text artifact writer and a focused JSON regression for failed `repair/codex.md` persistence.
- Validation run: `python -m pytest tests\test_guard_cli.py::test_guard_repair_json_reports_adapter_write_failure tests\test_guard_cli.py::test_guard_failed_fast_check_returns_do_not_merge tests\test_guard_cli.py::test_guard_github_summary_json_reports_artifact_write_failure -q`.
- Evidence: the focused RED produced only `qa-z guard: artifact error: disk full`; after implementation the failure payload includes `could not write guard repair codex artifact to ...`, and existing blocking-verdict repair generation still passes.
- Gate delta: guard can now separate repair companion persistence failure from verdict, GitHub summary, repair packet, and handoff write failures.
- User impact: operators see exactly which local repair artifact failed before handing work to an external executor.
- Remaining blocker: repair artifacts remain local handoff instructions; QA-Z still does not fix target repositories or dispatch live executors.
- Next safe slice: commit guard repair behavior, then run the guard/repair validation pack and select the next current-truth or artifact writer gap.


## 2026-05-13 Latest Run Manifest Write Failure Contract
- Repo: JustTyping
- Lane: fast/guard/benchmark/executor ingest -> latest run discovery manifest persistence
- User-facing flow: `qa-z fast --json` and any workflow that resolves the latest run
- Slice type: Contract / Evidence
- Before: a failed `.qa-z/runs/latest-run.json` write returned `qa-z fast: artifact write error: disk full` without naming the latest-run manifest path.
- Root cause: `write_latest_run_manifest()` created and wrote the manifest without a path-aware filesystem boundary.
- Change made: wrapped the shared latest-run manifest writer with a deterministic `could not write latest run manifest ...` message and added a focused fast JSON regression.
- Validation run: `python -m pytest tests\test_execution_runs_error_contracts.py::test_fast_json_reports_latest_run_manifest_write_failure tests\test_execution_runs_error_contracts.py::test_fast_json_reports_run_summary_artifact_write_failure tests\test_cli.py::test_fast_writes_latest_run_manifest -q`.
- Evidence: the focused RED produced only `qa-z fast: artifact write error: disk full`; after implementation the failure payload includes the exact `latest-run.json` path, while normal latest-run manifest creation still passes.
- Gate delta: latest-run discovery failures are now distinguishable from run summary write failures before guard, repair-prompt, verify, or executor ingest consumes stale run state.
- User impact: operators can repair the local latest-run manifest path directly instead of misreading the failure as a check failure or missing run artifact.
- Remaining blocker: latest-run manifests remain local deterministic state; this does not add remote proof or release execution approval.
- Next safe slice: commit latest-run manifest behavior, then run fast/executor-ingest validation and mine another shared artifact writer.


## 2026-05-13 Autonomy History Write Failure Contract
- Repo: JustTyping
- Lane: autonomy loop/executor-result ingest -> loop history JSONL persistence
- User-facing flow: `qa-z autonomy --json` and executor-result history updates
- Slice type: Contract / Evidence
- Before: failed autonomy `history.jsonl` rewrites in loop update or executor-result merge paths raised raw `OSError` without naming the history file.
- Root cause: `update_history_entry()` and `record_executor_result()` both rewrote JSONL history inline after mutating entries.
- Change made: added a shared path-aware autonomy history writer and focused regressions for both loop outcome history updates and executor-result history updates.
- Validation run: `python -m pytest tests\test_autonomy.py::test_record_executor_result_wraps_history_write_failure tests\test_autonomy.py::test_update_history_entry_wraps_history_write_failure tests\test_autonomy.py::test_record_executor_result_updates_matching_history_entry -q`.
- Evidence: both focused RED tests raised raw `OSError: disk full`; after implementation both failures include `could not write autonomy history ...`, and the existing executor-result history merge test still passes.
- Gate delta: autonomy current-truth/history failures now preserve the exact JSONL path before planner, backlog, or executor-result status reads stale state.
- User impact: long-running operators can distinguish history persistence failure from no-op, blocked, or completed autonomy loop outcomes.
- Remaining blocker: autonomy remains local planning/handoff only and does not mutate target repositories or dispatch live executors.
- Next safe slice: commit autonomy history behavior, then run the autonomy/executor-result validation pack and mine the next runtime artifact writer.


## 2026-05-13 Autonomy Outcome JSON Write Failure Contract
- Repo: JustTyping
- Lane: autonomy loop -> per-loop and latest outcome artifact persistence
- User-facing flow: `qa-z autonomy --json`
- Slice type: Contract / Evidence
- Before: a failed autonomy `outcome.json` rewrite raised raw `OSError` without naming the outcome artifact path.
- Root cause: the shared autonomy `write_json()` helper created parent directories and wrote JSON artifacts without a filesystem boundary.
- Change made: wrapped autonomy JSON artifact writes with `could not write autonomy JSON artifact ...` and added a focused regression for failed per-loop outcome persistence.
- Validation run: `python -m pytest tests\test_autonomy.py::test_write_outcome_artifact_wraps_json_write_failure tests\test_autonomy.py::test_record_executor_result_wraps_history_write_failure tests\test_autonomy.py::test_autonomy_one_loop_writes_per_loop_latest_outcome_and_history -q`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the failure includes the exact outcome path, and the one-loop latest outcome/history regression still passes.
- Gate delta: autonomy outcome persistence failures now remain distinct from history updates, planner selection, and executor-result ingestion failures.
- User impact: long-running operators can identify exactly which loop outcome artifact failed before relying on latest-loop status.
- Remaining blocker: autonomy outcome artifacts remain local deterministic evidence and do not execute repairs or release actions.
- Next safe slice: commit autonomy outcome behavior, then run the autonomy validation pack and mine copy/summary writer gaps.


## 2026-05-13 Autonomy Latest Outcome Copy Failure Contract
- Repo: JustTyping
- Lane: autonomy loop -> latest outcome pointer persistence
- User-facing flow: `qa-z autonomy --json` and `qa-z autonomy status --json`
- Slice type: Contract / Evidence
- Before: a failed copy from the per-loop outcome to `.qa-z/loops/latest/outcome.json` raised raw `OSError` without naming the latest target path.
- Root cause: `copy_artifact()` called `shutil.copyfile()` directly after creating the parent directory.
- Change made: wrapped autonomy artifact copies with `could not copy autonomy artifact ... to ...` and added a focused regression for failed latest outcome copy.
- Validation run: `python -m pytest tests\test_autonomy.py::test_write_outcome_artifact_wraps_latest_copy_failure tests\test_autonomy.py::test_write_outcome_artifact_wraps_json_write_failure tests\test_autonomy.py::test_autonomy_one_loop_writes_per_loop_latest_outcome_and_history -q`.
- Evidence: the focused RED raised raw `OSError: copy failed`; after implementation the failure includes both source and latest outcome target paths, and the one-loop latest outcome/history regression still passes.
- Gate delta: autonomy status/current-truth consumers now get precise evidence when the latest outcome pointer cannot be updated.
- User impact: operators can repair or rerun the local latest-outcome copy path without confusing it for planner or executor-result failure.
- Remaining blocker: latest outcome copies remain local evidence only; no target repo, remote, package, or release mutation was added.
- Next safe slice: commit latest outcome copy behavior, then run the autonomy validation pack and select the next runtime summary writer gap.


## 2026-05-13 Autonomy Loop Plan Write Failure Contract
- Repo: JustTyping
- Lane: autonomy loop -> per-loop and latest loop-plan markdown persistence
- User-facing flow: `qa-z autonomy --json`
- Slice type: Contract / Evidence
- Before: a failed `loop_plan.md` write raised raw `OSError` without naming the per-loop or latest loop-plan path.
- Root cause: `run_autonomy_loop()` wrote both loop-plan markdown files inline after rendering the loop plan.
- Change made: added a path-aware autonomy loop-plan writer and a focused regression for failed per-loop `loop_plan.md` persistence.
- Validation run: `python -m pytest tests\test_autonomy.py::test_run_autonomy_wraps_loop_plan_write_failure tests\test_autonomy.py::test_autonomy_one_loop_writes_per_loop_latest_outcome_and_history -q`.
- Evidence: the focused RED raised raw `OSError: disk full`; after implementation the failure includes `could not write autonomy loop plan artifact ...`, and the one-loop latest outcome/history regression still passes.
- Gate delta: loop-plan persistence failures now remain separate from self-inspection, selected-task, outcome, and history persistence failures.
- User impact: operators can identify exactly which loop plan file failed before handing a plan to a human or external executor.
- Remaining blocker: loop plans remain local planning artifacts and do not perform autonomous repairs or release mutation.
- Next safe slice: commit loop-plan behavior, then run the autonomy validation pack and mine another runtime writer.


## 2026-05-13 Select-Next Loop Plan Write Failure Contract
- Repo: JustTyping
- Lane: self-improvement selection -> latest loop-plan markdown persistence
- User-facing flow: `qa-z select-next --json`
- Slice type: Contract / Evidence
- Before: a failed select-next `loop_plan.md` write returned only `could not write selection artifacts: disk full` without naming the loop-plan path.
- Root cause: `select_next_tasks()` wrote the rendered latest loop plan inline after writing `selected_tasks.json`.
- Change made: added a path-aware select-next loop-plan writer and a focused JSON regression for failed `.qa-z/loops/latest/loop_plan.md` persistence.
- Validation run: `python -m pytest tests\test_self_improvement.py::test_select_next_json_reports_loop_plan_write_failure tests\test_self_improvement.py::test_select_next_json_reports_artifact_write_failure tests\test_self_improvement.py::test_select_next_writes_selected_tasks_plan_and_history -q`.
- Evidence: the focused RED produced only the generic selection artifact error; after implementation the failure includes `could not write selection loop plan artifact ...`, while selected-tasks and history output still pass.
- Gate delta: select-next can now distinguish selected-task JSON persistence from loop-plan markdown persistence before autonomy consumes the selection context.
- User impact: operators can repair or rerun the exact loop-plan path without mistaking the failure for an empty backlog or stale selection.
- Remaining blocker: select-next remains local task-selection evidence and does not mutate target repositories.
- Next safe slice: commit select-next loop-plan behavior, then run self-improvement selection validation and mine self-improvement JSON writer gaps.


## 2026-05-13 Self-Improvement JSON Write Failure Contract
- Repo: JustTyping
- Lane: self-inspection/select-next -> JSON artifact persistence
- User-facing flow: `qa-z self-inspect --json` and `qa-z select-next --json`
- Slice type: Contract / Evidence
- Before: a failed selected-task JSON write returned the generic selection artifact failure without naming `selected_tasks.json`.
- Root cause: the shared `write_json()` helper in `self_improvement_runtime.py` created parent directories and wrote JSON without a path-aware boundary.
- Change made: wrapped self-improvement JSON writes with `could not write self-improvement JSON artifact ...` and tightened the selected-task write failure regression to require the exact path.
- Validation run: `python -m pytest tests\test_self_improvement.py::test_select_next_json_reports_artifact_write_failure tests\test_self_improvement.py::test_self_inspect_json_reports_artifact_write_failure tests\test_self_improvement.py::test_select_next_json_reports_loop_plan_write_failure -q`.
- Evidence: the focused RED lacked the JSON writer detail; after implementation selected-task JSON, self-inspect JSON, and loop-plan write failure contracts passed.
- Gate delta: self-improvement commands now distinguish JSON artifact persistence from loop-plan markdown persistence and stale-selection logic.
- User impact: operators can repair the exact selected-task or self-inspection JSON path before autonomy consumes stale planning state.
- Remaining blocker: self-improvement JSON artifacts remain local planning evidence and do not mutate target repositories.
- Next safe slice: commit self-improvement JSON behavior, then run selection/backlog validation and mine history writer gaps.


## 2026-05-13 Self-Improvement History Append Failure Contract
- Repo: JustTyping
- Lane: self-improvement selection -> loop history JSONL persistence
- User-facing flow: `qa-z select-next --json`
- Slice type: Contract / Evidence
- Before: a failed `.qa-z/loops/history.jsonl` append could surface as a raw `OSError` without the select-next history path.
- Root cause: `append_history()` created the parent directory and opened the JSONL history file inline with no path-aware persistence boundary.
- Change made: wrapped the history parent creation and append in `could not append self-improvement history ...` and added a focused regression for append-mode write failure.
- Validation run: `python -m pytest tests\test_self_improvement_selection.py tests\test_self_improvement_selection_history.py tests\test_self_improvement.py -q`; `python -m ruff check src\qa_z\improvement_state.py tests\test_self_improvement_selection.py`; `python -m ruff format --check src\qa_z\improvement_state.py tests\test_self_improvement_selection.py`.
- Evidence: selection/history/self-inspection pack passed `34` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: select-next now distinguishes selected-task JSON, loop-plan markdown, and loop-history append persistence failures before autonomy or current-truth checks consume incomplete selection state.
- User impact: operators can identify whether the selected task, loop plan, or loop history file failed instead of treating the selection as stale or taskless.
- Remaining blocker: loop history remains local planning evidence and does not prove remote release or production readiness.
- Next safe slice: commit history append behavior, then mine executor-history and verification publication writers for the next path-aware contract gap.


## 2026-05-13 Executor History JSON Write Failure Contract
- Repo: JustTyping
- Lane: external executor handoff -> executor-result history persistence
- User-facing flow: `qa-z executor-result ingest --json`
- Slice type: Contract / Evidence
- Before: failed executor-result attempt/history JSON writes could raise raw filesystem errors from the shared executor-history support helper.
- Root cause: `executor_history_support.write_json()` created parent directories and wrote deterministic JSON without wrapping `OSError` with the affected artifact path.
- Change made: added `could not write executor history JSON artifact ...` around executor-history JSON persistence and a focused support regression for failed writes.
- Validation run: `python -m pytest tests\test_executor_history_support.py tests\test_executor_history_architecture.py tests\test_executor_history_dry_run_layout_architecture.py tests\test_executor_result.py::test_executor_result_ingest_warns_when_bridge_timestamp_is_missing tests\test_executor_result.py::test_executor_result_ingest_accepts_no_op_with_warning_when_explanation_is_missing -q`; `python -m ruff check src\qa_z\executor_history_support.py tests\test_executor_history_support.py`; `python -m ruff format --check src\qa_z\executor_history_support.py tests\test_executor_history_support.py`.
- Evidence: executor-history support, architecture, dry-run layout, and ingest smoke pack passed `17` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: executor-result ingest can now distinguish history JSON persistence failure from result validation, stale bridge evidence, and no-op warning policy.
- User impact: maintainers can identify the exact executor history artifact that failed before trusting verify-resume or dry-run history signals.
- Remaining blocker: executor history remains local evidence and does not authorize remote release or external executor mutation.
- Next safe slice: commit executor-history helper behavior, then inspect verification publication or repair-session guide writers.


## 2026-05-13 Repair Session Executor Guide Write Failure Contract
- Repo: JustTyping
- Lane: repair prompt -> external executor handoff -> repair-session start
- User-facing flow: `qa-z repair-session start --json`
- Slice type: Contract / Evidence
- Before: a failed `executor_guide.md` write was only covered by the broad session-start artifact boundary.
- Root cause: `write_executor_guide()` resolved and wrote the external executor guide path inline without its own path-aware persistence boundary.
- Change made: wrapped executor-guide parent creation and Markdown write with `could not write repair-session executor guide ...`, plus a focused regression for the guide writer.
- Validation run: `python -m pytest tests\test_repair_session.py::test_write_executor_guide_wraps_write_failure tests\test_repair_session.py::test_repair_session_start_json_reports_artifact_write_failure tests\test_repair_session.py::test_repair_session_start_creates_manifest_handoff_and_executor_guide -q`; `python -m pytest tests\test_repair_session.py -q`; `python -m ruff check src\qa_z\repair_session_guides.py tests\test_repair_session.py`; `python -m ruff format --check src\qa_z\repair_session_guides.py tests\test_repair_session.py`.
- Evidence: focused guide/start pack passed `3` tests; full repair-session pack passed `19` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: repair-session start failures now carry both the broad session-start artifact context and the exact executor-guide path when that Markdown handoff fails.
- User impact: operators can distinguish missing handoff JSON from a failed executor guide before sending instructions to a human or external executor.
- Remaining blocker: repair-session guide creation remains local handoff packaging and does not execute repairs or mutate target repositories.
- Next safe slice: commit executor-guide behavior, then continue with verification artifact or publish-summary path clarity.


## 2026-05-13 Repair Prompt Packet Artifact Write Failure Contract
- Repo: JustTyping
- Lane: finding -> repair prompt -> external executor handoff
- User-facing flow: `qa-z repair-prompt --json`
- Slice type: Contract / Evidence
- Before: failed repair-prompt `packet.json` or `prompt.md` writes could surface only through the broad command artifact-write boundary, while adapter handoff files already had per-file context.
- Root cause: `_write_repair_artifacts_impl()` created the output directory and wrote packet/prompt files inline with no per-artifact persistence helper.
- Change made: added a path-aware repair-prompt artifact writer, preserved explicit directory-creation failure context, and added a JSON-mode regression for failed `prompt.md` persistence.
- Validation run: `python -m pytest tests\test_repair_prompt_error_contracts.py tests\test_repair_prompt.py -q`; `python -m pytest tests\test_repair_prompt_architecture.py -q`; `python -m ruff check src\qa_z\reporters\repair_prompt.py tests\test_repair_prompt_error_contracts.py`; `python -m ruff format --check src\qa_z\reporters\repair_prompt.py tests\test_repair_prompt_error_contracts.py`.
- Evidence: repair-prompt behavior pack passed `13` tests; repair-prompt architecture pack passed `6` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: repair-prompt now distinguishes packet/prompt persistence failures from Codex/Claude handoff Markdown failures and source artifact loading failures.
- User impact: operators get the exact failed repair-prompt artifact path before handing a packet to an external repair executor.
- Remaining blocker: repair prompts remain deterministic local handoff artifacts and do not perform repairs or target-repo mutation.
- Next safe slice: commit repair-prompt packet behavior, then mine verification artifact output or skill-install append/overwrite writers.


## 2026-05-13 Verification Artifact Write Failure Contract
- Repo: JustTyping
- Lane: repair-session verify -> verification artifact persistence
- User-facing flow: `qa-z verify --json` and `qa-z repair-session verify --json`
- Slice type: Contract / Evidence
- Before: verification artifact write failures named the output directory but not whether `summary.json`, `compare.json`, or `report.md` failed.
- Root cause: `write_verification_artifacts()` wrote all three artifacts inside one broad `try` block with a directory-level failure message.
- Change made: separated directory creation from per-artifact writes and added `could not write verification artifact ...` for the individual verification files.
- Validation run: `python -m pytest tests\test_verification_artifact_io.py tests\test_verification.py tests\test_verification_artifact_architecture.py tests\test_verification_artifact_io_architecture.py -q`; `python -m ruff check src\qa_z\verification_artifact_writing.py tests\test_verification_artifact_io.py`; `python -m ruff format --check src\qa_z\verification_artifact_writing.py tests\test_verification_artifact_io.py`.
- Evidence: verification artifact IO, behavior, and architecture packs passed `9` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: verification failures can now distinguish summary, compare, and report persistence issues from comparison logic and source artifact loading.
- User impact: maintainers can repair the exact failed verification output before trusting a repair-session completion or publish summary.
- Remaining blocker: verification artifacts remain local evidence and do not prove remote release, package publication, or production readiness.
- Next safe slice: commit verification artifact behavior, then run a broader validation wave before selecting the next writer or CLI contract gap.


## 2026-05-13 Verify CLI Error Contract Sync
- Repo: JustTyping
- Lane: verify CLI -> JSON artifact-write failure contract
- User-facing flow: `qa-z verify --json`
- Slice type: Contract / Evidence
- Before: the full alpha gate caught `tests/test_verify_cli_error_contracts.py` still expecting the old directory-level verification artifact failure phrase after verification writes became per-file.
- Root cause: the verification writer contract moved from `could not write verification artifacts ...` to `could not write verification artifact <path> ...`, but the CLI JSON regression had not been updated with the exact artifact path expectation.
- Change made: tightened the verify CLI JSON failure test to require the per-file phrase and failed `summary.json` path.
- Validation run: `python -m pytest tests\test_verify_cli_error_contracts.py tests\test_verification_artifact_io.py tests\test_verification.py -q`; `python -m ruff check tests\test_verify_cli_error_contracts.py`; `python -m ruff format --check tests\test_verify_cli_error_contracts.py`.
- Evidence: alpha gate failed on this stale assertion with `1690 passed, 1 failed`; after the test contract sync, the focused verify pack passed `6` tests, Ruff check passed, and Ruff format reported `1 file already formatted`.
- Gate delta: verify CLI JSON tests now enforce the same exact-path artifact-write contract as the verification artifact writer.
- User impact: maintainers get regression coverage for the precise failed verification file in CLI JSON mode.
- Remaining blocker: this only repairs local test-contract drift; remote proof and release execution remain approval-blocked.
- Next safe slice: commit the verify CLI contract sync, then rerun the alpha gate quick.


## 2026-05-13 Skill Install Path-Aware Write Failure Contract
- Repo: JustTyping
- Lane: local operating-model setup -> agent instruction install
- User-facing flow: `qa-z skill install codex`
- Slice type: Contract / Evidence
- Before: skill-install write failures named the instruction target but not the exact output file.
- Root cause: `install_target()` wrote or appended instruction files inline, and the command wrapper only added target-level context.
- Change made: added path-aware directory, read, and write boundaries for skill-install artifacts and tightened the existing write-failure regression to require the output path.
- Validation run: `python -m pytest tests\test_skill_install_cli.py -q`; `python -m ruff check src\qa_z\commands\skill_install.py tests\test_skill_install_cli.py`; `python -m ruff format --check src\qa_z\commands\skill_install.py tests\test_skill_install_cli.py`.
- Evidence: skill-install CLI pack passed `8` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: operating-model instruction install failures now identify the exact file before maintainers retry with `--append`, `--force`, or `--output`.
- User impact: maintainers can distinguish a target refusal from a filesystem failure on `AGENTS.md`, `CLAUDE.md`, Cursor rules, or Copilot instructions.
- Remaining blocker: skill install only writes local instruction files and does not prove release readiness or remote publication.
- Next safe slice: commit skill-install path context, then continue mining CLI output/error surfaces.


## 2026-05-13 Executor Bridge JSON Artifact Path Contract
- Repo: JustTyping
- Lane: repair-session -> external executor handoff package
- User-facing flow: `qa-z executor-bridge --json`
- Slice type: Contract / Evidence
- Before: executor-bridge package write failures named the bridge directory but not the exact JSON artifact when `bridge.json` or `result_template.json` failed.
- Root cause: `executor_bridge_support.write_json()` wrote deterministic bridge JSON artifacts without an inner path-aware boundary; only the outer package cleanup boundary wrapped the error.
- Change made: wrapped executor-bridge JSON writes with `could not write executor bridge JSON artifact ...` and tightened the CLI write-failure regression to require `bridge.json`.
- Validation run: `python -m pytest tests\test_executor_bridge.py::test_executor_bridge_cli_json_reports_artifact_write_failure tests\test_executor_bridge.py::test_executor_bridge_from_loop_packages_manifest_guides_and_inputs tests\test_executor_bridge.py::test_executor_bridge_cli_json_missing_session_reports_machine_payload -q`; `python -m pytest tests\test_executor_bridge.py -q`; `python -m ruff check src\qa_z\executor_bridge_support.py tests\test_executor_bridge.py`; `python -m ruff format --check src\qa_z\executor_bridge_support.py tests\test_executor_bridge.py`.
- Evidence: focused bridge pack passed `3` tests; full executor-bridge pack passed `16` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: executor bridge package failures now preserve both cleanup-safe package context and the exact JSON artifact path that failed.
- User impact: operators can distinguish a manifest/template persistence failure from source-copy, guide, or missing-session failures before handing work to an external executor.
- Remaining blocker: executor bridge remains a local package for external handoff and does not execute repairs or remote release actions.
- Next safe slice: commit bridge JSON path context, then inspect remaining Markdown writer paths.


## 2026-05-13 Executor Bridge Markdown Artifact Path Contract
- Repo: JustTyping
- Lane: repair-session -> external executor handoff package
- User-facing flow: `qa-z executor-bridge --json`
- Slice type: Contract / Evidence
- Before: executor-bridge package write failures named the bridge directory but not the exact Markdown handoff guide when `executor_guide.md`, `codex.md`, or `claude.md` failed.
- Root cause: `create_executor_bridge()` wrote Markdown guides inline after the JSON artifacts, leaving the outer package wrapper as the only error context.
- Change made: added a path-aware executor-bridge Markdown writer and a JSON-mode regression that fails `codex.md` persistence.
- Validation run: `python -m pytest tests\test_executor_bridge.py::test_executor_bridge_cli_json_reports_markdown_artifact_write_failure tests\test_executor_bridge.py::test_executor_bridge_cli_json_reports_artifact_write_failure tests\test_executor_bridge.py::test_executor_bridge_from_loop_packages_manifest_guides_and_inputs -q`; `python -m pytest tests\test_executor_bridge.py -q`; `python -m ruff check src\qa_z\executor_bridge_package.py tests\test_executor_bridge.py`; `python -m ruff format --check src\qa_z\executor_bridge_package.py tests\test_executor_bridge.py`.
- Evidence: focused bridge Markdown/JSON/package pack passed `3` tests; full executor-bridge pack passed `17` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: executor bridge package failures now preserve both cleanup-safe package context and the exact failed Markdown guide path.
- User impact: operators can distinguish JSON manifest/template failures from guide-generation persistence failures before giving a bridge package to Codex, Claude, or another external executor.
- Remaining blocker: executor bridge remains a local package for external handoff and does not execute repairs or remote release actions.
- Next safe slice: commit bridge Markdown path context, then continue mining executor-result ingest and dry-run report writer paths.


## 2026-05-13 Executor Result Dry-Run Report Path Contract
- Repo: JustTyping
- Lane: external executor handoff -> executor-result dry-run safety check
- User-facing flow: `qa-z executor-result dry-run --json`
- Slice type: Contract / Evidence
- Before: failed dry-run Markdown report writes named the executor-results directory but not the exact `dry_run_report.md` path.
- Root cause: `run_executor_result_dry_run()` wrote the Markdown report inline inside the same broad artifact boundary as the JSON summary.
- Change made: added a path-aware dry-run report writer and a JSON-mode regression that fails `dry_run_report.md` persistence.
- Validation run: `python -m pytest tests\test_executor_result_dry_run.py::test_executor_result_dry_run_json_reports_report_write_failure tests\test_executor_result_dry_run.py::test_executor_result_dry_run_json_reports_artifact_write_failure tests\test_executor_result_dry_run.py::test_executor_result_dry_run_reports_clear_for_verified_completed_history -q`; `python -m pytest tests\test_executor_result_dry_run.py -q`; `python -m ruff check src\qa_z\executor_dry_run.py tests\test_executor_result_dry_run.py`; `python -m ruff format --check src\qa_z\executor_dry_run.py tests\test_executor_result_dry_run.py`.
- Evidence: focused dry-run write/clear pack passed `3` tests; full dry-run module passed `7` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: executor-result dry-run failures now distinguish JSON summary persistence from Markdown report persistence before an operator trusts safety rehearsal output.
- User impact: maintainers get the exact failed dry-run report path when local executor safety rehearsal cannot persist its operator-facing evidence.
- Remaining blocker: executor-result dry-run remains local pre-live evidence and does not authorize remote release, package publishing, deployment, or executor mutation.
- Next safe slice: commit dry-run report path context, then inspect executor-result ingest report writer path clarity.


## 2026-05-13 Executor Result Ingest Report Path Contract
- Repo: JustTyping
- Lane: external executor handoff -> executor-result ingest
- User-facing flow: `qa-z executor-result ingest --json`
- Slice type: Contract / Evidence
- Before: failed ingest Markdown report writes named the ingest result directory but not the exact `ingest_report.md` path.
- Root cause: `finalized_ingest_outcome()` wrote the Markdown report inline inside the same broad artifact boundary as `ingest.json`.
- Change made: added a path-aware ingest report writer and tightened the existing failure regression to require the failed report path.
- Validation run: `python -m pytest tests\test_executor_ingest_outcome.py -q`; `python -m pytest tests\test_executor_result.py::test_executor_result_ingest_json_reports_artifact_write_failure tests\test_executor_result.py::test_executor_result_ingest_accepts_no_op_with_warning_when_explanation_is_missing tests\test_executor_result.py::test_executor_result_ingest_warns_when_bridge_timestamp_is_missing -q`; `python -m ruff check src\qa_z\executor_ingest_outcome.py tests\test_executor_ingest_outcome.py`; `python -m ruff format --check src\qa_z\executor_ingest_outcome.py tests\test_executor_ingest_outcome.py`.
- Evidence: executor ingest outcome pack passed `4` tests; focused CLI ingest pack passed `3` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: executor-result ingest failures now distinguish machine-summary persistence from Markdown report persistence before history, dry-run, or verify-resume signals are trusted.
- User impact: maintainers can identify the exact failed ingest report artifact when external executor output cannot be materialized cleanly.
- Remaining blocker: executor-result ingest remains local evidence intake and does not execute repairs, push branches, publish packages, or prove production readiness.
- Next safe slice: commit ingest report path context, then continue with remaining command output/error surfaces or a validation wave.


## 2026-05-13 Benchmark Summary and Report Path Contract
- Repo: JustTyping
- Lane: benchmark fixture -> regression proof -> report/summary
- User-facing flow: `qa-z benchmark --json`
- Slice type: Contract / Evidence
- Before: benchmark artifact write failures named the results directory but not whether `summary.json` or `report.md` failed.
- Root cause: `write_benchmark_artifacts()` wrote summary and report files inline inside one broad results-directory boundary.
- Change made: added path-aware benchmark summary/report writers and CLI JSON regressions for both failed output files.
- Validation run: `python -m pytest tests\test_benchmark_runtime.py::test_benchmark_cli_json_reports_artifact_write_failure tests\test_benchmark_runtime.py::test_benchmark_cli_json_reports_report_artifact_write_failure tests\test_benchmark_runtime.py::test_run_benchmark_removes_results_lock_after_success -q`; `python -m pytest tests\test_benchmark_runtime.py -q`; `python -m ruff check src\qa_z\benchmark_reporting.py tests\test_benchmark_runtime.py`; `python -m ruff format --check src\qa_z\benchmark_reporting.py tests\test_benchmark_runtime.py`.
- Evidence: focused benchmark write/lock pack passed `3` tests; full benchmark runtime module passed `8` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: benchmark failures now distinguish summary persistence from report persistence before alpha-gate or release-truth evidence consumes benchmark output.
- User impact: maintainers can repair the exact failed benchmark artifact instead of treating all benchmark output failures as a locked or corrupt results directory.
- Remaining blocker: benchmark output remains local deterministic evidence and does not prove remote release or production readiness.
- Next safe slice: commit benchmark path context, then run a validation wave before mining the next writer surface.


## 2026-05-13 Artifact Writer Seam Budget Repair
- Repo: JustTyping
- Lane: benchmark/doctor reliability and executor-result dry-run safety
- User-facing flow: `qa-z benchmark --json` and `qa-z executor-result dry-run --json`
- Slice type: Cleanup / Evidence
- Before: alpha gate failed because the new path-aware writer helpers pushed `benchmark_reporting.py` and `executor_dry_run.py` over their architecture line-count budgets.
- Root cause: low-level artifact write helpers were added inside orchestration modules that have explicit small-seam layout guards.
- Change made: moved benchmark and dry-run writer helpers into dedicated artifact-writing modules while preserving the exact-path failure behavior.
- Validation run: `python -m pytest tests\test_benchmark_reporting_architecture.py tests\test_executor_history_dry_run_layout_architecture.py tests\test_benchmark_runtime.py tests\test_executor_result_dry_run.py -q`; `python -m ruff check src\qa_z\benchmark_reporting.py src\qa_z\benchmark_artifact_writing.py src\qa_z\executor_dry_run.py src\qa_z\executor_dry_run_artifacts.py tests\test_benchmark_runtime.py tests\test_executor_result_dry_run.py`; `python -m ruff format --check src\qa_z\benchmark_reporting.py src\qa_z\benchmark_artifact_writing.py src\qa_z\executor_dry_run.py src\qa_z\executor_dry_run_artifacts.py tests\test_benchmark_runtime.py tests\test_executor_result_dry_run.py`.
- Evidence: alpha gate exposed `benchmark_reporting.py exceeded budget: 76` and `executor_dry_run.py exceeded budget: 90>80`; after the seam refactor, focused architecture/behavior pack passed `20` tests, Ruff check passed, Ruff format reported `6 files already formatted`, and line counts returned to `60` and `80`.
- Gate delta: path-aware artifact errors now stay compatible with the small-module architecture budget enforced by the alpha gate.
- User impact: maintainers keep sharper write-failure diagnostics without allowing benchmark or dry-run orchestration files to grow past their intended review size.
- Remaining blocker: this repairs local gate integrity only; remote proof, push, package publish, deployment, and production readiness remain approval-blocked.
- Next safe slice: commit the seam-budget repair, rerun the alpha gate quick, then continue only if the gate is green or a new product failure appears.


## 2026-05-13 Guard Verdict Artifact Path Contract
- Repo: JustTyping
- Lane: guard/current-truth correctness -> guard verdict persistence
- User-facing flow: `qa-z guard --json`
- Slice type: Contract / Evidence
- Before: guard verdict artifact write failures named the guard output directory but not whether `verdict.json` or `verdict.md` failed.
- Root cause: `write_verdict_artifacts()` wrote both files inline inside one broad guard-verdict boundary.
- Change made: added a path-aware guard verdict artifact writer and JSON-mode regressions for both verdict JSON and Markdown write failures.
- Validation run: `python -m pytest tests\test_guard_cli.py::test_guard_json_reports_verdict_artifact_write_failure tests\test_guard_cli.py::test_guard_json_reports_verdict_markdown_artifact_write_failure tests\test_guard_cli.py::test_guard_happy_path_writes_merge_ok_verdict -q`; `python -m pytest tests\test_guard_cli.py -q`; `python -m ruff check src\qa_z\guard\verdict.py tests\test_guard_cli.py`; `python -m ruff format --check src\qa_z\guard\verdict.py tests\test_guard_cli.py`.
- Evidence: focused guard verdict pack passed `3` tests; full guard CLI module passed `15` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: guard verdict failures now distinguish machine-verdict persistence from Markdown-verdict persistence before operators trust merge-safety output.
- User impact: maintainers can identify the exact failed guard artifact while keeping current-truth, repair, and GitHub-summary guard paths separate.
- Remaining blocker: guard verdicts remain local merge-safety evidence and do not prove remote release, package publish, deployment, or production readiness.
- Next safe slice: commit guard verdict path context, then mine remaining guard workflow or review packet output surfaces.


## 2026-05-13 Review Packet Artifact Path Contract
- Repo: JustTyping
- Lane: diff/input -> fast/deep analysis -> review packet
- User-facing flow: `qa-z review --json`
- Slice type: Contract / Evidence
- Before: review packet artifact failures named the output directory but not whether `review.md` or `review.json` failed.
- Root cause: `_write_review_artifacts_impl()` wrote Markdown and optional JSON inline inside one broad review-artifact boundary.
- Change made: added a path-aware review artifact writer and JSON-mode regressions for both Markdown and JSON write failures.
- Validation run: `python -m pytest tests\test_review_packet_error_contracts.py tests\test_review_packet_runtime.py tests\test_review_packet_architecture.py -q`; `python -m ruff check src\qa_z\reporters\review_packet.py tests\test_review_packet_error_contracts.py`; `python -m ruff format --check src\qa_z\reporters\review_packet.py tests\test_review_packet_error_contracts.py`.
- Evidence: review packet failure/runtime/architecture pack passed `20` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: review packet failures now distinguish Markdown persistence from JSON persistence before downstream GitHub summary or repair prompt flows consume review evidence.
- User impact: operators get the exact failed review artifact path when a local review packet cannot be written.
- Remaining blocker: review packets remain local deterministic evidence and do not publish GitHub comments, push code, or prove production readiness.
- Next safe slice: commit review packet path context, then continue with SARIF or run-summary output surfaces.


## 2026-05-13 Run Summary Artifact Path Contract
- Repo: JustTyping
- Lane: diff/input -> fast/deep analysis -> summary evidence
- User-facing flow: `qa-z fast --json` and `qa-z deep --json`
- Slice type: Contract / Evidence
- Before: run summary write failures named the artifact directory but not whether `summary.json`, `summary.md`, or a per-check JSON file failed.
- Root cause: `_write_run_summary_artifacts_impl()` wrote all run summary artifacts inline inside one broad artifact-directory boundary.
- Change made: added a path-aware run summary artifact writer and CLI JSON regressions for summary JSON, summary Markdown, per-check JSON, and deep summary JSON failures.
- Validation run: `python -m pytest tests\test_execution_runs_error_contracts.py tests\test_run_summary_architecture.py -q`; `python -m pytest tests\test_artifact_schema.py tests\test_review_packet_runtime.py tests\test_execution_runs_error_contracts.py -q`; `python -m ruff check src\qa_z\reporters\run_summary.py tests\test_execution_runs_error_contracts.py`; `python -m ruff format --check src\qa_z\reporters\run_summary.py tests\test_execution_runs_error_contracts.py`.
- Evidence: focused run-summary error/architecture pack passed `9` tests; artifact schema and review runtime consumer pack passed `33` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: fast/deep evidence failures now distinguish machine summary, Markdown summary, and individual check artifact persistence before review, guard, repair, or verify flows consume the run.
- User impact: operators can repair the exact failed run evidence artifact instead of rerunning blindly after a broad summary-write error.
- Remaining blocker: run summaries remain local evidence and do not prove remote release, package publish, deployment, or production readiness.
- Next safe slice: commit run-summary path context, then run another narrow validation wave before selecting the next output surface.


## 2026-05-13 Executor Safety Artifact Path Contract
- Repo: JustTyping
- Lane: finding -> repair prompt -> external executor handoff -> safety package
- User-facing flow: `qa-z repair-session start` and `qa-z executor-bridge`
- Slice type: Contract / Evidence
- Before: executor safety package write failures named the safety output directory but not whether `executor_safety.json` or `executor_safety.md` failed.
- Root cause: `write_executor_safety_artifacts()` wrote JSON and Markdown safety files inline inside one broad output-directory boundary.
- Change made: added a path-aware executor safety artifact writer and regressions for both JSON and Markdown write failures.
- Validation run: `python -m pytest tests\test_artifact_schema.py::test_executor_safety_package_schema_v1_required_fields_are_stable tests\test_artifact_schema.py::test_write_executor_safety_artifacts_wraps_write_failures tests\test_artifact_schema.py::test_write_executor_safety_artifacts_wraps_markdown_write_failures tests\test_repair_session.py::test_repair_session_start_creates_manifest_handoff_and_executor_guide tests\test_executor_bridge.py::test_executor_bridge_from_loop_packages_manifest_guides_and_inputs -q`; `python -m pytest tests\test_artifact_schema.py -q`; `python -m ruff check src\qa_z\executor_safety.py tests\test_artifact_schema.py`; `python -m ruff format --check src\qa_z\executor_safety.py tests\test_artifact_schema.py`.
- Evidence: focused safety/repair/bridge pack passed `5` tests; full artifact schema module passed `21` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: executor safety failures now distinguish machine policy persistence from Markdown policy persistence before bridge or repair-session handoff packages trust the safety rail.
- User impact: maintainers can repair the exact failed safety artifact before giving work to an external executor.
- Remaining blocker: executor safety artifacts remain local pre-live policy and do not authorize live executor calls, remote mutation, or production release.
- Next safe slice: commit executor safety path context, then run a status/strict-plan check before selecting another safe surface.


## 2026-05-13 Repair Session Lifecycle Artifact Path Contract
- Repo: JustTyping
- Lane: finding -> repair prompt -> external executor handoff -> verify
- User-facing flow: `qa-z repair-session start --json` and `qa-z repair-session verify --json`
- Slice type: Contract / Evidence
- Before: repair-session start and verification failures named the session directory but not the exact handoff, summary, or outcome file that failed.
- Root cause: lifecycle helpers wrote Codex/Claude handoffs plus verification summary/outcome files inline inside broad start/verify artifact boundaries.
- Change made: added a path-aware repair-session lifecycle artifact writer and regressions for Codex handoff, Claude handoff, verification summary, and verification outcome write failures.
- Validation run: `python -m pytest tests\test_repair_session.py::test_repair_session_start_json_reports_artifact_write_failure tests\test_repair_session.py::test_repair_session_start_json_reports_claude_handoff_write_failure tests\test_repair_session.py::test_repair_session_verify_json_reports_artifact_write_failure tests\test_repair_session.py::test_repair_session_verify_json_reports_outcome_write_failure tests\test_repair_session.py::test_repair_session_verify_existing_candidate_writes_outcome -q`; `python -m pytest tests\test_repair_session.py tests\test_repair_session_architecture.py -q`; `python -m ruff check src\qa_z\repair_session_lifecycle.py tests\test_repair_session.py`; `python -m ruff format --check src\qa_z\repair_session_lifecycle.py tests\test_repair_session.py`.
- Evidence: focused lifecycle write/outcome pack passed `5` tests; full repair-session and architecture pack passed `26` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: repair-session lifecycle failures now distinguish handoff, summary, and outcome persistence before external handoff or verification evidence is trusted.
- User impact: operators can identify the exact failed session artifact during start or verify instead of treating the whole session directory as corrupt.
- Remaining blocker: repair-session remains local handoff and verification orchestration; it does not execute repairs, mutate target repositories, or prove remote release readiness.
- Next safe slice: commit repair-session lifecycle path context, then run a mid-stack validation wave.


## 2026-05-13 Repair Session Manifest Artifact Path Contract
- Repo: JustTyping
- Lane: finding -> repair prompt -> external executor handoff -> verify
- User-facing flow: `qa-z repair-session start`, session reload/backfill, and repair-session manifest persistence
- Slice type: Contract / Evidence
- Before: repair-session manifest write failures surfaced the raw filesystem error without naming `session.json`.
- Root cause: `write_session_manifest()` wrote the manifest inline without a path-aware persistence boundary.
- Change made: wrapped manifest persistence with an exact `session.json` failure message and added a regression for manifest write errors.
- Validation run: `python -m pytest tests\test_repair_session_support.py::test_write_session_manifest_reports_manifest_path_on_write_failure -q`; `python -m pytest tests\test_repair_session_support.py tests\test_repair_session.py::test_repair_session_start_json_reports_artifact_write_failure tests\test_repair_session.py::test_repair_session_verify_json_reports_artifact_write_failure -q`; `python -m ruff check src\qa_z\repair_session_support.py tests\test_repair_session_support.py`; `python -m ruff format --check src\qa_z\repair_session_support.py tests\test_repair_session_support.py`.
- Evidence: regression failed first with raw `disk full`, then passed; focused repair-session support/start/verify pack passed `4` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: session manifest failures now identify the exact failed manifest artifact before operators trust handoff, safety, or verification state.
- User impact: maintainers can fix manifest persistence failures without confusing them with handoff, summary, safety, or outcome artifact failures.
- Remaining blocker: repair-session manifests remain local evidence and do not execute repairs, mutate target repositories, or prove remote release readiness.
- Next safe slice: commit manifest path context, then run latest-HEAD strict plan and alpha/truth validation.


## 2026-05-13 Plan Contract Draft Artifact Path Contract
- Repo: JustTyping
- Lane: diff/input -> plan -> contract draft
- User-facing flow: `qa-z plan`
- Slice type: Contract / Evidence
- Before: `qa-z plan` write failures said a contract draft could not be written but did not identify the failed draft path.
- Root cause: `plan_contract()` wrote the draft directly and the CLI wrapped the raw filesystem error with a broad command-level message.
- Change made: made contract draft directory/write failures path-aware and strengthened the CLI regression to require the exact draft path.
- Validation run: `python -m pytest tests\test_cli.py::test_plan_reports_artifact_write_failure -q`; `python -m pytest tests\test_cli.py::test_plan_creates_a_contract_draft_from_sources tests\test_cli.py::test_plan_reports_artifact_write_failure tests\test_cli.py::test_plan_uses_custom_contract_output_directory tests\test_cli.py::test_plan_resolves_relative_context_paths_from_repo_root tests\test_cli.py::test_plan_reads_top_level_fast_check_ids -q`; `python -m ruff check src\qa_z\planner\contracts.py src\qa_z\commands\bootstrap_plan.py tests\test_cli.py`; `python -m ruff format --check src\qa_z\planner\contracts.py src\qa_z\commands\bootstrap_plan.py tests\test_cli.py`.
- Evidence: regression failed first because the output only contained `disk full`, then passed with the draft path; focused plan command pack passed `5` tests; Ruff check passed; Ruff format reported `3 files already formatted`.
- Gate delta: plan artifact failures now point to the exact contract draft before downstream fast/deep/review flows depend on the generated contract.
- User impact: operators can fix a bad contract output directory or blocked draft file without guessing which path failed.
- Remaining blocker: plan contracts remain local deterministic input scaffolding and do not prove remote release, package publish, deployment, or production readiness.
- Next safe slice: commit plan draft path context, then run final latest-HEAD release validation wave.
