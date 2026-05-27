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


## 2026-05-13 Init Bootstrap Artifact Path Contract
- Repo: JustTyping
- Lane: init/doctor -> starter configuration -> first local QA-Z run
- User-facing flow: `qa-z init`
- Slice type: Contract / Evidence
- Before: init write failures said bootstrap files could not be written but did not identify the exact starter file path.
- Root cause: the shared `write_text_if_missing()` helper wrote starter files directly and let the raw filesystem error escape to the broad init boundary.
- Change made: made `write_text_if_missing()` preserve the failed path and strengthened the init write-failure regression to require `qa-z.yaml`.
- Validation run: `python -m pytest tests\test_cli.py::test_init_reports_artifact_write_failure -q`; `python -m pytest tests\test_cli.py::test_init_creates_bootstrap_files tests\test_cli.py::test_init_config_matches_public_example tests\test_cli.py::test_init_is_idempotent tests\test_cli.py::test_init_reports_artifact_write_failure -q`; `python -m ruff check src\qa_z\commands\common.py src\qa_z\commands\bootstrap_init.py tests\test_cli.py`; `python -m ruff format --check src\qa_z\commands\common.py src\qa_z\commands\bootstrap_init.py tests\test_cli.py`.
- Evidence: regression failed first because output only contained `disk full`, then passed with the starter file path; focused init pack passed `4` tests; Ruff check passed; Ruff format reported `3 files already formatted`.
- Gate delta: init bootstrap failures now identify the exact starter artifact before operators can run doctor, fast, deep, or repair flows.
- User impact: new QA-Z users can repair a blocked starter config or template path without guessing which init file failed.
- Remaining blocker: init bootstrap remains local setup and does not prove remote release, package publish, deployment, or production readiness.
- Next safe slice: commit init path context, then run latest-HEAD release validation and wall-clock compliance checks.


## 2026-05-13 Repair Handoff Artifact Path Contract
- Repo: JustTyping
- Lane: finding -> repair prompt -> external executor handoff
- User-facing flow: `qa-z repair-prompt --handoff-json` and handoff artifact generation
- Slice type: Contract / Evidence
- Before: normalized repair handoff write failures named the output directory but not the exact `handoff.json` file.
- Root cause: `write_repair_handoff_artifact()` wrapped directory creation and JSON persistence in one broad output-dir boundary.
- Change made: split directory creation from `handoff.json` persistence and strengthened the handoff write regression to require the exact JSON artifact path.
- Validation run: `python -m pytest tests\test_repair_handoff.py::test_write_repair_handoff_artifact_wraps_write_failures -q`; `python -m pytest tests\test_repair_handoff.py::test_write_repair_handoff_artifact_wraps_write_failures tests\test_repair_handoff.py::test_repair_prompt_cli_writes_handoff_and_adapter_artifacts tests\test_repair_handoff.py::test_repair_prompt_cli_can_print_handoff_json tests\test_repair_prompt_error_contracts.py -q`; `python -m ruff check src\qa_z\repair_handoff.py tests\test_repair_handoff.py tests\test_repair_prompt_error_contracts.py`; `python -m ruff format --check src\qa_z\repair_handoff.py tests\test_repair_handoff.py tests\test_repair_prompt_error_contracts.py`.
- Evidence: regression failed first because the message stopped at the repair output directory, then passed with `handoff.json`; focused handoff/repair-prompt pack passed `6` tests; Ruff check passed; Ruff format reported `3 files already formatted`.
- Gate delta: external executor handoff failures now identify the exact normalized handoff JSON artifact before adapters or downstream verification trust the packet.
- User impact: maintainers can distinguish a blocked handoff JSON write from prompt, Codex, Claude, or repair-packet artifact failures.
- Remaining blocker: repair handoff artifacts remain local deterministic handoff evidence and do not execute repairs, mutate target repositories, or prove remote release readiness.
- Next safe slice: commit handoff path context, then run final strict plan, truth validator, alpha gate, and wall-clock checks.


## 2026-05-13 Demo Runtime Config Artifact Path Contract
- Repo: JustTyping
- Lane: init/doctor -> demo -> guard/repair proof
- User-facing flow: `qa-z demo auth-bug`
- Slice type: Contract / Evidence
- Before: demo runtime config write failures said demo artifacts could not be prepared but did not identify `qa-z.demo.yaml`.
- Root cause: `write_demo_runtime_config()` wrote the runtime config directly and let the raw filesystem error escape to the broad demo artifact boundary.
- Change made: made runtime demo config persistence path-aware and strengthened the demo failure regression to require the exact config path.
- Validation run: `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_runtime_config_write_failure -q`; `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_command_writes_repair_and_guard_artifacts tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_runtime_config_write_failure tests\test_demo_guard_action_package.py::test_packaged_auth_bug_demo_matches_public_source_demo -q`; `python -m ruff format src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py`; `python -m ruff format --check src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py`; `python -m ruff check src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py`.
- Evidence: regression failed first because the message stopped at `disk full`, then passed with `qa-z.demo.yaml`; focused demo pack passed `3` tests; Ruff formatted one file, then format check and Ruff check passed.
- Gate delta: demo bootstrap failures now identify the exact runtime config artifact before plan/guard/repair proof is rehearsed.
- User impact: operators can fix demo setup failures without confusing runtime config persistence with packaged resource copy, guard output, or repair artifacts.
- Remaining blocker: the demo remains local deterministic proof and does not push, publish, deploy, or prove production readiness.
- Next safe slice: commit demo path context, then run final latest-HEAD release validation and wall-clock compliance checks.


## 2026-05-13 Demo Resource Copy Artifact Path Contract
- Repo: JustTyping
- Lane: init/doctor -> demo -> guard/repair proof
- User-facing flow: `qa-z demo auth-bug`
- Slice type: Contract / Evidence
- Before: packaged demo resource copy failures surfaced only the broad demo artifact boundary and raw filesystem error.
- Root cause: `copy_resource_tree()` wrote copied files directly with `Path.write_bytes()` and relied on the outer demo handler for error context.
- Change made: added a path-aware demo resource writer and a regression requiring the copied `README.md` target path on write failure.
- Validation run: `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_copied_resource_write_failure -q`; `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_command_writes_repair_and_guard_artifacts tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_runtime_config_write_failure tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_copied_resource_write_failure tests\test_demo_guard_action_package.py::test_packaged_auth_bug_demo_matches_public_source_demo -q`; `python -m ruff check src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py`; `python -m ruff format --check src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py`.
- Evidence: regression failed first because output only contained `disk full`, then passed with the copied resource path; focused demo pack passed `4` tests; Ruff check passed; Ruff format reported `2 files already formatted`.
- Gate delta: demo bootstrap failures now distinguish packaged resource copy failures from runtime config persistence and downstream guard/repair artifacts.
- User impact: operators can repair blocked demo file copies without treating the whole deterministic demo as unreliable.
- Remaining blocker: the demo remains local deterministic proof and does not push, publish, deploy, or prove production readiness.
- Next safe slice: commit demo resource path context, then run final latest-HEAD release validation and wall-clock compliance checks.


## 2026-05-13 Demo Resource Directory Artifact Path Contract
- Repo: JustTyping
- Lane: init/doctor -> demo -> guard/repair proof
- User-facing flow: `qa-z demo auth-bug`
- Slice type: Contract / Evidence
- Before: demo resource directory creation failures surfaced only the broad demo artifact boundary and raw filesystem error.
- Root cause: `copy_resource_tree()` created target directories directly and relied on the outer demo handler for context.
- Change made: wrapped demo resource directory creation with the exact target directory path and added a regression for `.qa-z/demo/auth-bug` creation failure.
- Validation run: `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_resource_directory_create_failure -q`; `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_command_writes_repair_and_guard_artifacts tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_runtime_config_write_failure tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_copied_resource_write_failure tests\test_demo_guard_action_package.py::test_demo_auth_bug_reports_resource_directory_create_failure tests\test_demo_guard_action_package.py::test_packaged_auth_bug_demo_matches_public_source_demo -q`; `python -m ruff format src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py`; `python -m ruff format --check src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py`; `python -m ruff check src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py`.
- Evidence: regression failed first because output only contained `disk full`, then passed with the demo resource directory path; focused demo pack passed `5` tests; Ruff formatted one file, then format check and Ruff check passed.
- Gate delta: demo bootstrap failures now distinguish resource directory creation from copied resource files, runtime config, guard output, and repair artifacts.
- User impact: operators can repair filesystem or permission problems in the demo target directory directly.
- Remaining blocker: the demo remains local deterministic proof and does not push, publish, deploy, or prove production readiness.
- Next safe slice: commit demo resource directory path context, then run final latest-HEAD release validation and wall-clock compliance checks.


## 2026-05-13 Repair Prompt Adapter Handoff Path Contract
- Repo: JustTyping
- Lane: finding -> repair prompt -> external executor handoff
- User-facing flow: `qa-z repair-prompt --json`
- Slice type: Contract / Evidence
- Before: Codex/Claude handoff Markdown write failures named the path but not which adapter handoff failed.
- Root cause: `write_handoff_markdown()` wrapped both adapter outputs with a generic path-only message.
- Change made: threaded the adapter label through handoff Markdown persistence and strengthened the Codex handoff write-failure regression.
- Validation run: `python -m pytest tests\test_repair_prompt_error_contracts.py::test_repair_prompt_json_reports_artifact_write_failure -q`; `python -m pytest tests\test_repair_prompt_error_contracts.py tests\test_repair_handoff.py::test_repair_prompt_cli_writes_handoff_and_adapter_artifacts tests\test_repair_handoff.py::test_repair_prompt_cli_can_print_handoff_json -q`; `python -m ruff check src\qa_z\commands\execution_repair.py tests\test_repair_prompt_error_contracts.py tests\test_repair_handoff.py`; `python -m ruff format --check src\qa_z\commands\execution_repair.py tests\test_repair_prompt_error_contracts.py tests\test_repair_handoff.py`.
- Evidence: regression failed first because the message lacked `repair-prompt codex handoff`, then passed; focused repair-prompt/handoff pack passed `5` tests; Ruff check passed; Ruff format reported `3 files already formatted`.
- Gate delta: repair-prompt adapter artifact failures now distinguish Codex handoff Markdown from Claude handoff Markdown and other repair artifacts.
- User impact: operators can fix the exact adapter handoff artifact before handing work to a specific external executor.
- Remaining blocker: adapter handoffs remain local deterministic prompts and do not execute repairs, mutate target repositories, or prove remote release readiness.
- Next safe slice: run final latest-HEAD release validation and wall-clock compliance checks.


## 2026-05-13 Current-HEAD Release Proof Alignment
- Repo: JustTyping
- Lane: release truth / proof evidence
- User-facing flow: alpha release packet -> truth validator -> proof branch handoff -> rollback plan
- Slice type: Contract / Evidence
- Before: the alpha release decision packet was pinned to an older proof HEAD, so default `alpha_release_truth_validator.py --json` failed against current local HEAD `2644e81afedcfbd28cf06b55df17059381ea1d02`.
- Root cause: the durable release packet, proof-branch command packet, rollback packet, and package handoff were not regenerated after the latest local hardening commits.
- Change made: refreshed the release decision packet for current HEAD, made the truth validator require a unique source proof head plus exact proof-branch/rollback/package current-head commands, exposed the exact proof branch and local-only remote-proof state in validator JSON facts, and kept proof-head-from-packet mode meaningful for commit-safe validation.
- Validation run: `python -m pytest tests\test_alpha_release_truth_validator.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_cli.py tests\test_current_truth_worktree_commit_plan.py tests\test_worktree_commit_plan_validation_commands.py -q`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts\alpha_release_truth_validator.py --json`; `python scripts\alpha_release_truth_validator.py --proof-head-from-packet --json`; `python scripts\alpha_release_gate.py --quick --allow-dirty --json`.
- Evidence: focused release-alignment packs passed `22`, `52`, and `29` tests; strict worktree plan returned `status=ready`; both truth validator modes passed `20/20` with `proof_branch=codex/alpha-rc-2644e81afedc-20260513` and `current_head_remote_proof=local_only_not_remote_visible`; alpha release gate passed `28/28`; full pytest inside the gate reported `1710 passed`.
- Gate delta: default release truth now proves the current local HEAD packet, while proof-head-from-packet mode still proves the packet-internal head and stale-packet negative tests keep mismatched heads failing.
- User impact: maintainers can request a proof-branch push using exact current-head commands without confusing local RC readiness with remote alpha, package publish, or production readiness.
- Remaining blocker: current HEAD remains local-only until an explicitly approved proof-branch push creates remote CI and public raw evidence; tag, GitHub release, package publish, deploy, Marketing/X, and Claude mirror promotion remain blocked.
- Next safe slice: approve and execute the proof-branch push for `2644e81afedcfbd28cf06b55df17059381ea1d02`, then capture remote CI and public raw evidence before any tag or publish decision.


## 2026-05-13 Remote-Visible Release Truth And Support Routing
- Repo: JustTyping
- Lane: release truth / GitHub public launch surface
- User-facing flow: GitHub discovery -> support routing -> release packet -> truth validator -> public raw proof
- Slice type: Contract / Evidence
- Before: the release truth packet still described an older proof-head shape where current HEAD was not remote-visible, and public support routing was split between CONTRIBUTING and SECURITY without a dedicated support file.
- Root cause: remote `main` advanced to `b9a2504ad07d15776eb900f07d6ee83f22ef9076` after the previous proof packet, but the validator and docs only accepted the older exact-commit raw `404` wording.
- Change made: taught `alpha_release_truth_validator.py` to classify both local-only and `remote_visible` current-head proof, refreshed release packet/package/security/roadmap/product docs to current `v0.9.9-alpha` and `b9a2504` reality, added `SUPPORT.md`, and pinned the support/release-truth surfaces with current-truth tests.
- Validation run: `python -m pytest tests\test_alpha_release_truth_validator.py tests\test_current_truth_worktree_commit_plan.py -q`; `python scripts\alpha_release_truth_validator.py --json`; `python scripts\alpha_release_truth_validator.py --proof-head-from-packet --json`; `python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m pytest tests\test_public_docs_current_truth.py tests\test_text_file_hygiene.py tests\test_public_raw_urls.py tests\test_github_workflow.py tests\test_launch_growth_package.py -q`; `python scripts\check_public_raw_urls.py --repo qazedhq/qa-z --ref main --commit b9a2504ad07d15776eb900f07d6ee83f22ef9076`; `python -m qa_z doctor --json`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`.
- Evidence: focused release/current-truth pack passed `30` tests; both release truth validator modes passed `20/20` with `current_head_remote_proof=remote_visible`; public hygiene passed; public docs/workflow/star-ready pack passed `68` tests; public raw URL hygiene passed for branch and exact current SHA; doctor returned `status=passed`; strict worktree plan returned `status=ready` with `cross_cutting_count=0`.
- Gate delta: release truth now distinguishes remote-visible current HEAD proof from local-only proof without weakening approval-gated tag, release, package, deploy, Marketing/X, or Claude mirror boundaries.
- User impact: a GitHub visitor now has clearer support routing, and maintainers have a validator-backed packet that matches the public `main` SHA instead of stale local-only release evidence.
- Remaining blocker: no tag, GitHub release, package publish, deploy, Marketing/X promotion, or Claude mirror promotion was approved or executed in this slice.
- Next safe slice: run a full final quality wave and prepare exact commit-ready packets for the release-truth, support/community, and commit-plan-support batches.


## 2026-05-13 Public Support Docs Commit-Plan Ownership
- Repo: JustTyping
- Lane: current truth / release staging safety
- User-facing flow: public GitHub support docs -> current-truth tests -> worktree commit plan -> release packet staging
- Slice type: Contract / Evidence
- Before: `SUPPORT.md`, `SECURITY.md`, `docs/product/PRODUCT_DIRECTION.md`, and `docs/roadmap.md` were covered by public/current-truth tests but did not appear in a changed commit-plan batch.
- Root cause: the `current_truth_release_surface` batch owned launch docs and tests, but not root support/security docs or product/roadmap truth docs.
- Change made: routed support/security/product/roadmap truth docs into `current_truth_release_surface` and added a regression requiring those paths to stay in that batch with no cross-cutting or unassigned-source attention.
- Validation run: `python -m pytest tests\test_worktree_commit_plan.py::test_commit_plan_routes_public_support_docs_to_current_truth_batch -q`; `python -m pytest tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_cli.py tests\test_current_truth_worktree_commit_plan.py tests\test_public_docs_current_truth.py tests\test_launch_growth_package.py -q`; `python -m ruff check scripts\worktree_commit_plan_support.py tests\test_worktree_commit_plan.py`; `python -m ruff format --check scripts\worktree_commit_plan_support.py tests\test_worktree_commit_plan.py`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`.
- Evidence: the new regression failed first because only `tests/test_public_docs_current_truth.py` was assigned; after the fix it passed, the focused pack passed `77` tests, Ruff check passed, Ruff format reported `2 files already formatted`, and strict worktree plan returned `status=ready` with `current_truth_release_surface` including `SECURITY.md`, `SUPPORT.md`, `docs/product/PRODUCT_DIRECTION.md`, and `docs/roadmap.md`.
- Gate delta: public support and direction docs now have explicit staging ownership instead of relying on tests alone.
- User impact: maintainers can prepare a GitHub launch/support-doc commit packet without silently omitting root support/security or product direction truth.
- Remaining blocker: deferred `.claude/**`, `marketing/x/**`, and `tests/test_x_automation.py` paths still require separate approval and remain out of QA-Z alpha staging.
- Next safe slice: tighten GitHub issue-template/community-profile evidence so repository health proof and local validators agree on the public support route.


## 2026-05-13 Public Text Mojibake Hygiene Guard
- Repo: JustTyping
- Lane: GitHub first impression / public text hygiene
- User-facing flow: public README/docs -> text hygiene gate -> GitHub launch confidence
- Slice type: Contract / Evidence
- Before: console inspection could show a mojibake-looking README heading, but the public text hygiene gate only covered line endings and collapsed text.
- Root cause: `check_text_file_hygiene.py` had no explicit marker check for known public text encoding damage.
- Change made: added a likely-mojibake marker check for public text blobs and a regression that creates a damaged README fixture without embedding the damaged marker directly in tracked source.
- Validation run: `python -m pytest tests\test_text_file_hygiene.py::test_likely_mojibake_in_public_text_fails -q`; `python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m pytest tests\test_text_file_hygiene.py tests\test_public_docs_current_truth.py tests\test_launch_growth_package.py -q`; `python -m ruff check scripts\check_text_file_hygiene.py tests\test_text_file_hygiene.py`; `python -m ruff format --check scripts\check_text_file_hygiene.py tests\test_text_file_hygiene.py`.
- Evidence: the new regression passed, working-tree public hygiene passed, the public docs/text hygiene pack passed `39` tests, Ruff check passed, and Ruff format reported `2 files already formatted`.
- Gate delta: a known mojibake marker in public text now fails the same hygiene script used by release/public-readiness validation.
- User impact: GitHub first-impression files are less likely to ship with visibly broken encoding damage.
- Remaining blocker: this does not prove remote raw hygiene for unpushed local changes; public raw proof still depends on a pushed commit or current remote ref.
- Next safe slice: tighten GitHub issue-template/community-profile evidence so bug, feature, support, and security routes are locally validated.


## 2026-05-13 GitHub Issue Template Support Routing
- Repo: JustTyping
- Lane: GitHub community health / contributor onboarding
- User-facing flow: GitHub visitor -> issue chooser -> support/security/release route -> deterministic evidence issue
- Slice type: Contract / Evidence
- Before: bug and feature issue forms existed, but blank issues were not explicitly disabled and issue chooser contact links did not point users to support, private security reporting, or release/package approval handoffs.
- Root cause: `.github/ISSUE_TEMPLATE/config.yml` was missing, and the commit plan did not assign `.github/ISSUE_TEMPLATE/**` or PR template changes to the current-truth release surface.
- Change made: added GitHub issue-template config with support, private security advisory, and release/package approval contact links; updated bug and feature form intro text; routed GitHub community templates into `current_truth_release_surface`; and added regressions for both route content and commit-plan ownership.
- Validation run: `python -m pytest tests\test_launch_growth_package.py::test_github_issue_templates_route_support_security_and_release_contacts -q`; `python -m pytest tests\test_worktree_commit_plan.py::test_commit_plan_routes_github_community_templates_to_current_truth_batch tests\test_worktree_commit_plan.py::test_commit_plan_routes_public_support_docs_to_current_truth_batch -q`; `python -m pytest tests\test_launch_growth_package.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_cli.py tests\test_public_docs_current_truth.py tests\test_text_file_hygiene.py -q`; `python -m ruff check scripts\worktree_commit_plan_support.py scripts\check_text_file_hygiene.py tests\test_worktree_commit_plan.py tests\test_launch_growth_package.py tests\test_text_file_hygiene.py`; `python -m ruff format --check scripts\worktree_commit_plan_support.py scripts\check_text_file_hygiene.py tests\test_worktree_commit_plan.py tests\test_launch_growth_package.py tests\test_text_file_hygiene.py`; `python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`.
- Evidence: the new route test failed first on missing `config.yml`, then passed; commit-plan ownership failed first with only the test assigned, then passed; the public/community/commit-plan pack passed `86` tests; Ruff check and format passed; public text hygiene passed; strict worktree plan returned `status=ready` with `.github/ISSUE_TEMPLATE/**` assigned to `current_truth_release_surface`.
- Gate delta: GitHub community profile routes now have local file evidence, test coverage, and staging ownership.
- User impact: new contributors get directed away from unsafe public security reports and unapproved release requests, while real deterministic bug/feature issues stay structured.
- Remaining blocker: applying repository settings, branch protection, releases, package publish, deployment, Marketing/X promotion, and Claude mirror promotion still require separate approval.
- Next safe slice: inspect quickstart/demo command snippets against current CLI output and add a narrow docs-command validator where the public first-run flow is weakest.


## 2026-05-13 README Demo Follow-Up Command Contract
- Repo: JustTyping
- Lane: 60-second demo / first-run UX
- User-facing flow: README quick demo -> `qa-z demo auth-bug` -> guard -> repair-prompt
- Slice type: Flow / Contract / Evidence
- Before: running the README demo commands literally from the starting directory made `qa-z demo auth-bug` succeed, then made `qa-z guard --from-run latest` and `qa-z repair-prompt --from-run latest` fail because the latest run lived under `.qa-z/demo/auth-bug`.
- Root cause: the README and terminal proof omitted the required move into the isolated demo root, and the demo command output named the demo root without showing the next commands.
- Change made: added explicit `Next:` commands to `qa-z demo auth-bug`, inserted `cd .qa-z/demo/auth-bug` into the README and checked-in terminal proof, and added a regression that executes the follow-up guard and repair-prompt commands from the demo root.
- Validation run: manual literal README flow before the fix showed `DEMO_EXIT=0`, `GUARD_EXIT=2`, and `REPAIR_EXIT=4`; `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_command_writes_repair_and_guard_artifacts -q`; `python -m pytest tests\test_launch_growth_package.py::test_readme_demo_visual_is_checked_in_and_public_safe -q`; `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_readme_followup_commands_run_from_demo_root -q`; `python -m pytest tests\test_demo_guard_action_package.py tests\test_launch_growth_package.py tests\test_examples.py -q`; `python -m ruff check src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py tests\test_launch_growth_package.py tests\test_examples.py`; `python -m ruff format --check src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py tests\test_launch_growth_package.py tests\test_examples.py`; `python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public`; `git diff --check`.
- Evidence: the two public-flow regressions failed first, then passed; the new runtime follow-up test passed; the demo/launch/examples pack passed `30` tests; Ruff check and format passed; public text hygiene passed; `git diff --check` passed.
- Gate delta: the first-run demo contract now proves that the commands after `qa-z demo auth-bug` run against the generated demo run instead of a missing root `.qa-z/runs` directory.
- User impact: a GitHub visitor can copy the README demo sequence and continue to guard and repair evidence without needing to infer the demo working directory.
- Remaining blocker: strict worktree plan currently reports `README.md` as a cross-cutting patch-add path until the README hunk is isolated in a commit-ready packet.
- Next safe slice: prepare commit-ready staging packets or run the next product-code slice while preserving the README patch-add boundary.


## 2026-05-13 Demo Parent Directory Follow-Up Hint
- Repo: JustTyping
- Lane: 60-second demo / CLI error UX
- User-facing flow: `qa-z demo auth-bug` -> accidental parent-directory guard/repair-prompt retry
- Slice type: Flow / Contract / Evidence
- Before: after `qa-z demo auth-bug`, running `qa-z guard --from-run latest` or `qa-z repair-prompt --from-run latest` from the parent directory failed with only `No run directory found at ...\.qa-z\runs`.
- Root cause: the shared latest-run resolver did not detect that the auth-bug demo had already produced valid run evidence under `.qa-z/demo/auth-bug`.
- Change made: added a targeted auth-bug demo follow-up hint to the shared artifact resolver when `latest` cannot be resolved from the current root but demo evidence exists, and added a regression covering both guard and repair-prompt parent-directory mistakes.
- Validation run: `python -m pytest tests\test_demo_guard_action_package.py::test_demo_auth_bug_parent_directory_followup_reports_demo_root_hint -q`; `python -m pytest tests\test_demo_guard_action_package.py tests\test_guard_cli.py tests\test_repair_prompt.py tests\test_review_packet_runtime.py tests\test_deep_run_resolution.py -q`; `python -m ruff check src\qa_z\artifacts.py src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py`; `python -m ruff format --check src\qa_z\artifacts.py src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py`; `git diff --check`; `python scripts\worktree_commit_plan.py --summary-only --json`.
- Evidence: the new parent-directory regression failed first on missing `cd .qa-z/demo/auth-bug`, then passed; the run-source/guard/repair/review/deep pack passed `51` tests; Ruff check and format passed; `git diff --check` passed; non-strict worktree plan returned `status=ready` with only `README.md` listed as a patch-add cross-cutting path.
- Gate delta: accidental parent-directory follow-up now points directly to the demo root and the two expected next commands instead of leaving users to infer where `latest` lives.
- User impact: the README/demo experience is more forgiving while preserving the isolated demo directory model.
- Remaining blocker: strict worktree plan still requires patch-add or commit handling for the README hunk.
- Next safe slice: update or validate public quickstart command snippets that still mention optional deep checks without clear Semgrep gating.


## 2026-05-13 README Quickstart Demo-First Flow
- Repo: JustTyping
- Lane: first-run quickstart / GitHub first impression
- User-facing flow: README Quickstart -> deterministic demo -> own-repository setup
- Slice type: Flow / Contract / Evidence
- Before: the short README Quickstart told users to run `qa-z init`, then `qa-z guard`, then `qa-z repair-prompt`; a literal empty-directory trial produced a guard error from missing default tools and paths before reaching a clean demo story.
- Root cause: the public Quickstart mixed an own-repository setup flow with a zero-context first-run demo flow.
- Change made: made the short Quickstart demo-first, moved own-repository setup into a separate block with `qa-z init --profile python --with-agent-templates` and `qa-z doctor`, and added a regression pinning that the short Quickstart includes the runnable demo sequence.
- Validation run: manual literal old Quickstart trial returned `INIT=0`, `GUARD=1`, `REPAIR=0` with missing tool/path repair evidence; `python -m pytest tests\test_launch_growth_package.py::test_readme_short_quickstart_uses_runnable_demo_flow -q`; `python -m pytest tests\test_launch_growth_package.py tests\test_demo_guard_action_package.py tests\test_public_docs_current_truth.py tests\test_text_file_hygiene.py -q`; `python -m ruff check src\qa_z\artifacts.py src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py tests\test_launch_growth_package.py tests\test_public_docs_current_truth.py tests\test_text_file_hygiene.py`; `python -m ruff format --check src\qa_z\artifacts.py src\qa_z\commands\demo.py tests\test_demo_guard_action_package.py tests\test_launch_growth_package.py tests\test_public_docs_current_truth.py tests\test_text_file_hygiene.py`; `python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public`.
- Evidence: the new README Quickstart regression failed first on the old `qa-z init` -> `qa-z guard` block, then passed; the public/demo/current-truth/text pack passed `52` tests; Ruff check and format passed; public text hygiene passed.
- Gate delta: the first public Quickstart no longer sends a blank local directory through project-specific checks before showing QA-Z's deterministic value.
- User impact: GitHub visitors get a copy-paste demo before they have to adapt QA-Z to their own repository.
- Remaining blocker: strict worktree plan still treats README as cross-cutting and needs patch-add/commit handling.
- Next safe slice: refresh commit-ready packet evidence or continue into another narrow CLI/docs truth check without touching deferred Marketing/X or Claude mirror paths.


## 2026-05-13 Community Health Link Surface
- Repo: JustTyping
- Lane: contributor onboarding / community health
- User-facing flow: README -> CONTRIBUTING/SUPPORT/SECURITY/CODE_OF_CONDUCT -> issue or PR
- Slice type: Contract / Evidence
- Before: the README Contributing section showed setup commands but did not link the repository community-health files, and CONTRIBUTING did not point contributors to support or private security disclosure routes.
- Root cause: support/security routing had been added as standalone docs without a README/CONTRIBUTING current-truth assertion or commit-plan ownership for `CONTRIBUTING.md`.
- Change made: linked `CONTRIBUTING.md`, `SUPPORT.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md` from README, linked support/security routes from CONTRIBUTING, and routed `CONTRIBUTING.md` plus `CODE_OF_CONDUCT.md` into the current-truth release surface batch.
- Validation run: `python -m pytest tests\test_public_docs_current_truth.py::test_readme_contributing_section_links_community_health_files -q`; `python -m pytest tests\test_worktree_commit_plan.py::test_commit_plan_routes_public_support_docs_to_current_truth_batch -q`; `python -m pytest tests\test_public_docs_current_truth.py tests\test_launch_growth_package.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_cli.py tests\test_text_file_hygiene.py -q`; `python -m ruff check scripts\worktree_commit_plan_support.py scripts\check_text_file_hygiene.py tests\test_public_docs_current_truth.py tests\test_launch_growth_package.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_cli.py tests\test_text_file_hygiene.py`; `python -m ruff format --check scripts\worktree_commit_plan_support.py scripts\check_text_file_hygiene.py tests\test_public_docs_current_truth.py tests\test_launch_growth_package.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_cli.py tests\test_text_file_hygiene.py`; `python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public`.
- Evidence: the new community-health link assertion failed first, then passed; the support-doc commit-plan assertion failed first for `CONTRIBUTING.md`/`CODE_OF_CONDUCT.md`, then passed; the public docs/launch/commit-plan/text pack passed `88` tests; Ruff check and format passed; public text hygiene passed.
- Gate delta: root community-health docs now have README discoverability, CONTRIBUTING routing, current-truth tests, and commit-plan staging ownership.
- User impact: contributors and security reporters can find the right route without guessing from issue templates alone.
- Remaining blocker: branch protection, release execution, package publish, deployment, Marketing/X, and Claude mirror promotion still require separate approval.
- Next safe slice: run a wider validation wave or convert the accumulated public/demo/community changes into explicit commit-ready packets.


## 2026-05-13 Public Surface Gate Recovery Wave
- Repo: JustTyping
- Lane: validation / gate integrity
- User-facing flow: public README/community/demo changes -> full quick alpha gate
- Slice type: Evidence / Cleanup
- Before: `python scripts\alpha_release_gate.py --quick --allow-dirty --json` failed because README exceeded the public landing-page line budget and `tests/test_worktree_commit_plan.py` exceeded its split budget.
- Root cause: the public quickstart/community additions were correct behaviorally but added too many README lines, and new commit-plan public docs tests belonged in a focused split file.
- Change made: compressed README advanced-command and non-goal wording while preserving current-truth anchors, split public docs commit-plan tests into `tests/test_worktree_commit_plan_public_docs.py`, and updated the commit-plan validation command to include the new file.
- Validation run: `python -m pytest tests\test_current_truth.py::test_readme_is_public_landing_page_linking_to_internal_anchors tests\test_worktree_commit_plan_architecture.py::test_worktree_commit_plan_main_test_file_stays_under_split_budget tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_public_docs.py tests\test_worktree_commit_plan_validation_commands.py -q`; `python -m ruff check scripts\worktree_commit_plan_support.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_public_docs.py tests\test_worktree_commit_plan_validation_commands.py tests\test_current_truth.py`; `python -m ruff format --check scripts\worktree_commit_plan_support.py tests\test_worktree_commit_plan.py tests\test_worktree_commit_plan_public_docs.py tests\test_worktree_commit_plan_validation_commands.py tests\test_current_truth.py`; `git diff --check`; `python scripts\alpha_release_gate.py --quick --allow-dirty --json`.
- Evidence: README is now `227` lines, `tests/test_worktree_commit_plan.py` is now `719` lines, focused gate-recovery tests passed `34`, Ruff check and format passed, `git diff --check` passed, and alpha release gate quick passed `28/28` with full pytest `1719 passed`.
- Gate delta: the accumulated public/demo/community work now clears the quick alpha quality gate again.
- User impact: public onboarding improvements did not come at the cost of repository maintainability limits or release-gate confidence.
- Remaining blocker: strict worktree plan still requires patch-add/commit handling for README, and remote mutation remains unapproved.
- Next safe slice: continue improving star-ready surfaces or prepare exact staged commit packets without touching deferred out-of-alpha paths.


## 2026-05-13 Social Preview Copy Console-Safe Contract
- Repo: JustTyping
- Lane: GitHub discoverability / social preview
- User-facing flow: GitHub repository share card -> launch package -> social preview setup
- Slice type: Contract / Evidence
- Before: `docs/launch/social-preview.md` used an emoji-only brand line that rendered as mojibake-looking text in the Windows console, and `docs/launch-package.md` described a different social preview tagline than the checked-in SVG asset.
- Root cause: the social preview setup doc, launch package copy block, and SVG asset copy were not pinned by one shared public-surface regression.
- Change made: made the social preview copy ASCII-safe, aligned the launch package text with the checked-in SVG tagline, and added a regression that checks the social preview docs, launch package, and SVG copy together.
- Validation run: `python -m pytest tests\test_launch_growth_package.py::test_social_preview_copy_matches_asset_and_stays_ascii_safe tests\test_launch_growth_package.py::test_launch_asset_docs_avoid_fabricated_public_claims tests\test_public_docs_current_truth.py::test_public_docs_point_to_latest_github_prerelease_without_package_publish -q`; `python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check docs tests\test_launch_growth_package.py`; `python -m ruff format --check tests\test_launch_growth_package.py`.
- Evidence: focused social-preview/public-release docs tests passed `3`; public text hygiene passed; Ruff check and format passed.
- Gate delta: social preview copy is now tied to asset truth and avoids console-hostile characters in the public setup doc.
- User impact: maintainers applying the GitHub social preview see the same tagline that appears in the generated preview asset, without broken-looking terminal output.
- Remaining blocker: the GitHub UI social preview upload still requires repository settings mutation and remains approval-gated.
- Next safe slice: review OpenSSF Scorecard and GitHub launch trust docs for opt-in permissions, local validation limits, and current remote-proof wording.


## 2026-05-13 OpenSSF Scorecard Trust Boundary
- Repo: JustTyping
- Lane: GitHub trust evidence / scorecard
- User-facing flow: GitHub visitor -> trust evidence -> Scorecard workflow and code-scanning result
- Slice type: Contract / Evidence
- Before: `docs/scorecard.md` named the Scorecard workflow but did not describe its exact triggers, permissions, publish boundary, or local-validation limitation.
- Root cause: the Scorecard workflow was covered by workflow structure tests, but the public-facing trust doc was not tied to the concrete YAML contract.
- Change made: documented the weekly/manual/branch-protection triggers, `contents: read`, `security-events: write`, `publish_results: false`, SARIF upload path, non-mutation boundary, and local validation limits; added a regression that reads the workflow YAML and asserts the docs describe the same trust boundary.
- Validation run: `python -m pytest tests\test_launch_growth_package.py::test_scorecard_docs_describe_permissions_triggers_and_local_limits tests\test_launch_growth_package.py::test_optional_pr_comment_and_scorecard_surfaces_are_opt_in -q`; `python -m pytest tests\test_github_workflow.py -q`; `python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests\test_launch_growth_package.py`; `python -m ruff format --check tests\test_launch_growth_package.py`.
- Evidence: targeted Scorecard docs tests passed `2`; GitHub workflow suite passed `23`; public text hygiene passed; Ruff check and format passed.
- Gate delta: Scorecard is now presented as reproducible trust evidence without implying local validation can fabricate a current OpenSSF score.
- User impact: a skeptical GitHub visitor can see what the repository-owned Scorecard workflow does, what it cannot do, and why the result belongs in GitHub code scanning.
- Remaining blocker: current live Scorecard result still depends on a GitHub Actions run; local validation only proves workflow and docs shape.
- Next safe slice: inspect package publish and install docs for any stale v0.9.8/v0.9.9 or package-registry wording drift after public launch updates.


## 2026-05-13 Detailed Quickstart Packaged Demo Lead-In
- Repo: JustTyping
- Lane: quickstart / install trial
- User-facing flow: docs quickstart -> install -> 60-second packaged demo -> deeper example repository demo
- Slice type: Flow / Contract / Evidence
- Before: the root README offered the `qa-z demo auth-bug` first-run path, but `docs/quickstart.md` still led with the older `examples/agent-auth-bug` source-checkout flow.
- Root cause: the detailed quickstart had not been realigned after the installed packaged demo became the best first trial path.
- Change made: added a `Run The 60-Second Packaged Demo` section with `qa-z demo auth-bug`, `cd .qa-z/demo/auth-bug`, `qa-z guard`, and `qa-z repair-prompt` before the deeper example-repository flow; added a regression proving the packaged demo appears before `cd examples/agent-auth-bug`.
- Validation run: `python -m pytest tests\test_launch_growth_package.py::test_docs_quickstart_leads_with_packaged_demo_before_example_repo_flow tests\test_launch_growth_package.py::test_readme_short_quickstart_uses_runnable_demo_flow tests\test_public_docs_current_truth.py::test_quickstart_states_repair_verification_success_signal -q`; `python -m ruff format tests\test_launch_growth_package.py`; `python -m ruff check tests\test_launch_growth_package.py`; `python -m ruff format --check tests\test_launch_growth_package.py`; `python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public`.
- Evidence: quickstart-focused tests passed `3`; Ruff reformatted the new test once, then check and format passed; public text hygiene passed.
- Gate delta: both README and detailed quickstart now lead with a copy-paste packaged demo before asking users to adapt QA-Z to a source checkout.
- User impact: GitHub visitors have the same low-friction first trial from the docs index as they do from the README.
- Remaining blocker: PyPI/TestPyPI publishing remains unapproved; Git tag install is still the public alpha install path.
- Next safe slice: run a wider public launch regression pack after the latest README/quickstart/scorecard/social-preview changes.


## 2026-05-13 Demo JSON Failure Contract
- Repo: JustTyping
- Lane: demo / CLI UX / automation evidence
- User-facing flow: `qa-z demo auth-bug --json` -> automation reads one stable payload -> operator sees deterministic recovery state.
- Slice type: Evidence / Contract
- Before: JSON success and runtime-config write failures were covered, but copied-resource failures, resource-directory creation failures, and nested demo command failures did not have dedicated JSON-mode regressions.
- Root cause: the demo command had grown into the public first-run path before its setup-failure contract was split into a focused test file.
- Change made: added `tests/test_demo_json_failure_contracts.py` with regressions for copied resource write failure, resource directory creation failure, and nested guard failure JSON payloads.
- Validation run: `python -m pytest tests\test_demo_json_failure_contracts.py tests\test_demo_guard_action_package.py -q`; `python -m ruff check tests\test_demo_json_failure_contracts.py`; `python -m ruff format --check tests\test_demo_json_failure_contracts.py`; `python scripts\alpha_release_truth_validator.py --json`; `python scripts\alpha_release_truth_validator.py --proof-head-from-packet --json`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`.
- Evidence: focused demo tests passed `16`; Ruff check and format passed; after commit `340e3380c8e5`, both release truth validator modes passed `20/20`, and strict worktree plan remained `ready`.
- Gate delta: the first-run demo JSON contract now covers setup and nested-command failures without relying on human stdout parsing.
- User impact: GitHub visitors and CI scripts can automate the packaged demo more confidently because failures stay machine-readable and deterministic.
- Remaining blocker: current HEAD remains local-only until push approval; release packet stays proof-only and mutation-gated.
- Next safe slice: continue a product-code slice from stale-current-truth, repair prompt handoff, or benchmark lock coverage, then rerun the relevant focused validator.


## 2026-05-13 Select-Next Taskless Recovery Guidance
- Repo: JustTyping
- Lane: current truth / self-inspect / select-next
- User-facing flow: `qa-z select-next --refresh --json` -> no selected tasks -> deterministic follow-through instead of an inferred stop.
- Slice type: Flow / Contract / Evidence
- Before: taskless selection artifacts recorded `blocked_no_candidates`, `selection_gap_reason`, and `open_backlog_count`, but JSON and human stdout did not carry copyable next actions or refresh commands.
- Root cause: empty-backlog selection was treated as loop-health residue, while long-running improvement workflows still need explicit local next steps before claiming safe exhaustion.
- Change made: added additive `next_actions` and `next_commands` to taskless `selected_tasks.json`, rendered them in human `select-next` output and saved loop plans, and documented the fields in the artifact schema.
- Validation run: `python -m pytest tests\test_self_improvement_selection.py::test_select_next_records_reason_when_no_backlog_tasks_are_open tests\test_cli.py::test_select_next_refresh_runs_self_inspection_before_selection tests\test_current_truth.py::test_current_truth_docs_cover_dry_run_publish_and_session_residue -q`; `python -m pytest tests\test_self_improvement_selection.py tests\test_self_improvement.py tests\test_cli.py tests\test_current_truth.py::test_current_truth_docs_cover_dry_run_publish_and_session_residue -q`; `python -m ruff check src\qa_z\self_improvement_selection.py src\qa_z\task_selection_render.py src\qa_z\commands\planning_output.py tests\test_self_improvement_selection.py tests\test_cli.py tests\test_current_truth.py`; `python -m ruff format --check src\qa_z\self_improvement_selection.py src\qa_z\task_selection_render.py src\qa_z\commands\planning_output.py tests\test_self_improvement_selection.py tests\test_cli.py tests\test_current_truth.py`; `python -m mypy src\qa_z\self_improvement_selection.py src\qa_z\task_selection_render.py src\qa_z\commands\planning_output.py tests\test_self_improvement_selection.py tests\test_cli.py`; `python scripts\alpha_release_truth_validator.py --json`; `python scripts\alpha_release_truth_validator.py --proof-head-from-packet --json`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`.
- Evidence: the focused red test first failed on missing `next_actions`, then passed; broader self-improvement/CLI/current-truth validation passed `78` tests before commit and `93` tests after packet sync; Ruff, mypy, text hygiene, both truth validator modes, and strict worktree plan passed.
- Gate delta: taskless selection now has deterministic follow-through and does not look like an unexplained early stop during long worktrains.
- User impact: an operator can distinguish true safe exhaustion from "no backlog item selected yet" and immediately rerun backlog/strict worktree evidence or use `docs/agent/next-real-slices.md`.
- Remaining blocker: this is local planning evidence only; it does not approve push, release, package publish, Marketing/X, or Claude mirror promotion.
- Next safe slice: run another backlog expansion pass and choose a product-code or release-proof slice that does not require remote mutation.


## 2026-05-13 GitHub Repository Settings Packet
- Repo: JustTyping
- Lane: GitHub discoverability / launch package
- User-facing flow: launch maintainer -> repository settings -> description/topics/social preview.
- Slice type: Contract / Evidence
- Before: the launch package listed topics and social preview assets, but the GitHub repository description was not pinned by the same local regression, and topic format/count was not tested.
- Root cause: discoverability settings were documented as narrative launch copy instead of a concrete settings packet with mutation boundaries.
- Change made: added a `Repository Settings` section with the recommended GitHub description, explicit settings-mutation boundary, and a regression that validates the description plus 20 lower-case unique topic slugs.
- Validation run: read-only `gh repo view qazedhq/qa-z --json name,owner,description,stargazerCount,forkCount,watchers,repositoryTopics,isPrivate,defaultBranchRef,licenseInfo`; `python -m pytest tests\test_launch_growth_package.py::test_launch_package_pins_github_description_and_topics tests\test_launch_growth_package.py::test_social_preview_copy_matches_asset_and_stays_ascii_safe tests\test_launch_growth_package.py::test_launch_asset_docs_avoid_fabricated_public_claims -q`; `python -m pytest tests\test_launch_growth_package.py -q`; `python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests\test_launch_growth_package.py`; `python -m ruff format --check tests\test_launch_growth_package.py`; `python scripts\alpha_release_truth_validator.py --json`; `python scripts\alpha_release_truth_validator.py --proof-head-from-packet --json`; `python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`.
- Evidence: the new focused test first failed because `## Repository Settings` was absent, then passed; the launch growth package passed `17` tests; read-only GitHub metadata showed public repo `qazedhq/qa-z`, default branch `main`, Apache-2.0 license, and the current remote description; both truth validator modes and strict worktree plan passed after commit `d0d6f5b42a94`.
- Gate delta: repository description/topics/social preview are now a tested launch packet rather than loose copy.
- User impact: maintainers can apply GitHub discoverability settings from one tested doc without implying unapproved package publish, release, tag, or deployment.
- Remaining blocker: applying repository description/topics/social preview still requires approved GitHub settings mutation.
- Next safe slice: inspect release/package proof docs for stale publish wording or run a wider alpha gate validation wave.


## 2026-05-15 Auth Demo Semgrep Owner-Check Evidence
- Repo: JustTyping
- Lane: examples / Semgrep deep evidence
- User-facing flow: auth-bug demo -> Semgrep deep -> repair prompt -> verify.
- Slice type: Flow / Contract / Evidence
- Before: the Python and FastAPI auth-bug examples only pinned the signed-in-user shortcut rule, while PR #38's owner-check work was open, draft, behind current `main`, and not covered by repo-local parity tests.
- Root cause: the public examples and packaged auth-bug template did not have a deterministic test asserting the second owner-check rule across source and template rule files, and the FastAPI/Semgrep docs did not describe the two-finding custom-rule flow.
- Change made: added the missing owner-check Semgrep rule to the public Python auth demo, nested demo repo, FastAPI auth demo, and packaged auth-bug template rule files; added YAML-parsing parity tests; updated example docs, FastAPI walkthrough, and Semgrep custom-rule docs to name the two-finding local flow and generated-artifact boundary.
- Validation run: `python -m pytest tests/test_auth_demo_semgrep_rules.py -q`; `python -m pytest tests/test_demo_guard_action_package.py::test_packaged_auth_bug_demo_matches_public_source_demo tests/test_launch_growth_package.py::test_agent_bug_examples_are_documented_and_configured -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `semgrep --config semgrep-rules/auth-bypass.yml --json --metrics off app` in both auth examples; fixed-file Semgrep scans for `app/auth.fixed.py` and `app/main.fixed.py`; `python -m ruff check tests/test_auth_demo_semgrep_rules.py`; `python -m ruff format --check tests/test_auth_demo_semgrep_rules.py`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `git diff --check`.
- Evidence: the new parity test failed first on the one-rule state, then passed `4`; packaged-demo and launch example checks passed `2`; public docs current-truth passed `15`; Semgrep `1.159.0` reported `2` findings on each vulnerable baseline and `0` findings on both fixed files; Ruff check and format passed; public text hygiene and diff whitespace passed.
- Gate delta: the auth demos now have two deterministic Semgrep signals and repo-local tests to prevent public/template drift.
- User impact: maintainers can merge the refreshed equivalent of PR #38 with concrete local evidence, and users get FastAPI/custom-rule docs that explain what QA-Z deep adds beyond raw Semgrep.
- Remaining blocker: no GitHub issue was closed or commented on, no branch/commit/push/tag/release/package publish/deploy was performed, and package publish remains blocked pending explicit human release-owner approval.
- Next safe slice: close #14 only after the refreshed branch is merged, update or close #22 based on maintainer acceptance of the new Semgrep docs, keep #13 open if a fuller artifact walkthrough is still desired, and keep #5 open until TestPyPI/PyPI approval and evidence exist.


## 2026-05-15 FastAPI Auth-Bug Verification Evidence Walkthrough
- Repo: JustTyping
- Lane: examples / verification evidence
- User-facing flow: FastAPI auth-bug baseline -> fast/deep -> repair prompt -> fixed candidate -> verify -> artifact inspection.
- Slice type: Evidence / Docs Truth
- Before: after the owner-check Semgrep slice, issue #13 remained open because the FastAPI walkthrough listed baseline and candidate commands but did not guide contributors through the concrete fast, deep, repair, and verify artifacts.
- Root cause: the docs named `.qa-z/runs/baseline` and `.qa-z/runs/candidate` as directories, but did not pin the specific `summary.json`, Semgrep, SARIF, repair prompt, compare, and report files that prove the repair outcome.
- Change made: added a FastAPI evidence tour to `docs/walkthroughs/auth-bug.md`, added a compact artifact checklist to `examples/fastapi-agent-bug/README.md`, and added a docs regression that pins the artifact paths, `improved` verdict expectation, `repair_improved` signal, and generated `.qa-z` no-commit policy.
- Validation run: `python -m pytest tests/test_fastapi_auth_walkthrough_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_examples_index_links_visual_proof_and_labels_run_status -q`; `python -m ruff check tests/test_fastapi_auth_walkthrough_docs.py`; `python -m ruff format --check tests/test_fastapi_auth_walkthrough_docs.py`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `git diff --check`.
- Evidence: the new docs guard first failed on missing FastAPI artifact-tour paths and the missing README checklist, then passed `2`; public docs current-truth passed `15`; launch example docs check passed `1`; Ruff check and format passed; public text hygiene and diff whitespace passed.
- Gate delta: contributors can now follow the FastAPI demo from failing baseline through machine-readable verification evidence without treating generated runtime artifacts as source.
- User impact: issue #13 can be closed if maintainers do not require a separate screenshot or capture walkthrough.
- Remaining blocker: optional screenshot/capture evidence remains a separate follow-up if maintainers want a visual tour.
- Next safe slice: close or narrow #13 after review, then decide whether #22's Semgrep docs acceptance is complete or needs a small follow-up.


## 2026-05-15 Semgrep Custom Rule Docs Closeout Guard
- Repo: JustTyping
- Lane: Semgrep docs -> custom rule acceptance -> issue #22 closeout.
- User-facing flow: local custom Semgrep rule -> `qa-z deep` -> SARIF/summary -> review and repair packets.
- Slice type: Contract / Evidence
- Before: PR #41 substantially addressed #22, but the docs were only partially pinned by tests that checked the baseline deep command shape.
- Root cause: the #22 acceptance criteria covered local custom rule config, SARIF output, deterministic/no-live-service boundaries, and QA-Z-deep-vs-raw-Semgrep guidance, but no focused current-truth guard covered that full contract.
- Change made: added `tests/test_semgrep_docs_current_truth.py` to pin the Semgrep docs acceptance text and the FastAPI `sg_scan` config, and added one explicit closeout sentence tying the custom-rule example to local `qa-z.yaml`, SARIF output, and local deterministic execution.
- Validation run: `python -m pytest tests/test_semgrep_docs_current_truth.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python -m ruff check tests/test_semgrep_docs_current_truth.py`; `python -m ruff format --check tests/test_semgrep_docs_current_truth.py`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the missing custom-rule workflow closeout sentence, then passed `2`; public docs current-truth passed `15`; launch growth package docs-link check passed `1`; Ruff check and format passed; public text hygiene and diff whitespace passed.
- Gate delta: #22 can be closed after merge because the custom-rule documentation contract is now test-protected.
- User impact: contributors can trust `docs/use-with-semgrep.md` as executable local guidance for custom Semgrep rules without inferring live services, model APIs, package registries, or hidden network behavior.
- Remaining blocker: runtime Semgrep scans are not required for this docs closeout; local Windows Semgrep startup can remain a separate environment issue.
- Next safe slice: decide whether #5 TestPyPI rehearsal docs are ready for a small publish-boundary checklist slice.


## 2026-05-15 TestPyPI Rehearsal No-Upload Checklist
- Repo: JustTyping
- Lane: package publish / release governance
- User-facing flow: release proof -> package dry-run -> TestPyPI credential boundary -> blocked upload.
- Slice type: Contract / Evidence
- Before: #5 was still open and `docs/package-publish-plan.md` had a local dry-run packet, but it did not pin the full TestPyPI rehearsal checklist with `pipx`, `uvx`, credential separation, and a no-upload evidence field.
- Root cause: package dry-run evidence and registry publish approval were documented close together, making the local rehearsal boundary easier to blur.
- Change made: added a local-only TestPyPI publish rehearsal checklist with build, artifact smoke, `twine check`, `pipx`, and `uvx` commands; documented GitHub prerelease credentials as separate from TestPyPI/PyPI registry credentials; added `registry_upload_executed=false`; kept upload commands only in the blocked packet; added current-truth coverage and a release-handoff pointer.
- Validation run: `python -m pytest tests/test_public_docs_current_truth.py::test_package_publish_plan_documents_no_upload_testpypi_rehearsal -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_current_truth_worktree_commit_plan.py::test_alpha_rc_packet_documents_package_publish_dry_run_and_preflight_contract -q`; `python -m ruff check tests/test_public_docs_current_truth.py`; `python -m ruff format --check tests/test_public_docs_current_truth.py`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `git diff --check`; `python -m build --sdist --wheel`; `python scripts/alpha_release_artifact_smoke.py --json`.
- Evidence: the new current-truth test failed first on the missing checklist, then passed; public docs current-truth passed `16`; package dry-run preflight contract test passed `1`; Ruff check and format passed after formatting the test file once; public text hygiene and diff whitespace passed; local build produced `qa_z-0.9.8a0.tar.gz` and `qa_z-0.9.8a0-py3-none-any.whl`; artifact smoke passed for both wheel and sdist after network-approved dependency resolution.
- Gate delta: package rehearsal is now test-pinned as local-only evidence and cannot be mistaken for a TestPyPI/PyPI publish claim.
- User impact: maintainers can work #5 from a copy-paste checklist that proves local artifact readiness while preserving the release-owner approval boundary.
- Remaining blocker: no PyPI/TestPyPI upload, tag, release, push, or package registry mutation was performed; `python -m twine check dist/*` could not run because `twine` is not installed, and `pipx`/`uvx` smoke commands could not run because those tools are not installed in this environment.
- Next safe slice: install or provision `twine`, `pipx`, and `uv` in a controlled release-rehearsal environment, then rerun the no-upload checklist and keep `registry_upload_executed=false` until explicit release-owner approval exists.


## 2026-05-15 Verify Baseline/Candidate Workflow
- Repo: JustTyping
- Lane: verify workflow -> baseline/candidate evidence
- User-facing flow: baseline run -> repair prompt -> candidate run -> `qa-z verify` -> verification artifacts.
- Slice type: Docs / Contract / Evidence
- Before: verify verdicts existed in repair-session docs and artifact schema docs, but no focused baseline/candidate walkthrough showed the standalone `qa-z verify` loop.
- Root cause: contributors had to piece together commands, artifact paths, and verdict meanings from schema, repair-session, and auth-bug walkthrough docs.
- Change made: added a focused `qa-z verify` guide with baseline/candidate commands, required artifact paths, verdict interpretation, common failure modes, deterministic evidence language, and generated-artifact policy; linked it from the docs index; added focused docs coverage.
- Validation run: `python -m pytest tests/test_verify_workflow_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_verify_workflow_docs.py`; `python -m ruff format --check tests/test_verify_workflow_docs.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the missing walkthrough and docs index link, then passed `5`; public docs current-truth passed `16`; launch docs index check passed `1`; public text hygiene passed; Ruff check passed; Ruff format check passed; diff whitespace check passed.
- Gate delta: verify evidence becomes a standalone contributor workflow for proving repaired candidates against baseline runs.
- User impact: contributors can prove repaired candidates improved baseline evidence without relying on LLM-only claims.
- Remaining blocker: no local blocker; remote CI still depends on the PR run after push.
- Next safe slice: after validation and PR review, use real verify artifacts from a future repair loop to refine any missing troubleshooting cases.


## 2026-05-15 Scorecard Trust Evidence Follow-up
- Repo: JustTyping
- Lane: Scorecard trust surface -> deterministic follow-up tasks
- User-facing flow: Scorecard workflow -> SARIF/code scanning -> deterministic QA-Z follow-up task.
- Slice type: Contract / Evidence
- Before: the Scorecard workflow and basic trust docs existed, but first-run inspection and finding-to-task conversion were not pinned by focused current-truth tests.
- Root cause: Scorecard evidence was documented as a workflow and permission boundary, but maintainers still lacked a deterministic pattern for turning live findings into actionable QA-Z hardening work.
- Change made: documented first Scorecard run inspection, uploaded SARIF and GitHub code scanning evidence, the `openssf-scorecard` category, numeric badge caution, finding-to-task mapping, and a follow-up issue template; added current-truth coverage for the workflow permission and publish boundaries.
- Validation run: `python -m pytest tests/test_scorecard_docs_current_truth.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_optional_pr_comment_and_scorecard_surfaces_are_opt_in tests/test_launch_growth_package.py::test_scorecard_docs_describe_permissions_triggers_and_local_limits -q`; `python -m pytest tests/test_github_workflow.py -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_scorecard_docs_current_truth.py`; `python -m ruff format --check tests/test_scorecard_docs_current_truth.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the missing first-run inspection section, then passed `2`; launch growth Scorecard checks passed `2`; GitHub workflow suite passed `23`; public text hygiene passed; Ruff check and format passed; diff whitespace check passed.
- Gate delta: Scorecard output is now a deterministic trust-evidence input for follow-up tasks instead of a loose score/badge claim.
- User impact: maintainers can inspect the first Scorecard run, verify SARIF/code scanning evidence, and open scoped hardening tasks with source, affected setting, validation, non-goals, and generated-artifact boundaries.
- Remaining blocker: the live Scorecard score and findings still come only from GitHub Actions or uploaded SARIF, not local validation.
- Next safe slice: after the PR merges and issues #19/#28 close, inspect any real `openssf-scorecard` code scanning findings and convert them into separate deterministic follow-up issues.


## 2026-05-15 SARIF Code Scanning Walkthrough
- Repo: JustTyping
- Lane: SARIF evidence -> GitHub code scanning walkthrough
- User-facing flow: `qa-z deep` -> `deep/results.sarif` -> optional GitHub SARIF upload -> code scanning alerts.
- Slice type: Docs / Evidence
- Before: SARIF generation and upload were documented separately, but the walkthrough did not pin the CI SARIF path, `qa-z-semgrep` category, optional permission boundary, or a capture that avoids private data.
- Root cause: issue #17 needed a screenshot-or-capture proof surface, while a real screenshot could expose private repository details or secrets.
- Change made: expanded the SARIF code scanning walkthrough with local and CI SARIF paths, `github/codeql-action/upload-sarif@v4`, `security-events: write`, `qa-z-semgrep`, GitHub code scanning inspection guidance, and no-mutation boundaries; added a sanitized textual capture and a focused docs current-truth test; linked the walkthrough from `docs/github-action.md`.
- Validation run: `python -m pytest tests/test_sarif_code_scanning_docs.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python -m pytest tests/test_github_workflow.py -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_sarif_code_scanning_docs.py`; `python -m ruff format --check tests/test_sarif_code_scanning_docs.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the missing `<run-id>` SARIF path and missing capture file, then passed `2`; launch docs index check passed `1`; GitHub workflow suite passed `23`; public text hygiene passed; Ruff check and format passed; diff whitespace check passed.
- Gate delta: maintainers now have a deterministic capture for where QA-Z SARIF appears in GitHub code scanning without relying on private UI screenshots.
- User impact: contributors can explain the path from `.qa-z/runs/ci/deep/results.sarif` to code scanning alerts while keeping SARIF upload optional and permission-scoped.
- Remaining blocker: actual GitHub code scanning UI details can vary by repository settings and permissions; live `.qa-z/**` runtime artifacts were not generated for this docs slice.
- Next safe slice: if needed, inspect a real public code scanning alert after CI upload and open a separate deterministic follow-up task for any remaining SARIF presentation gap.


## 2026-05-15 PR Comment Dry-Run Capture
- Repo: JustTyping
- Lane: optional PR comment -> dry-run capture -> permission boundary
- User-facing flow: optional PR comment template -> default non-posting dry run -> maintainer permission decision.
- Slice type: Docs / Contract / Evidence
- Before: the optional PR comment workflow defaulted to `QA_Z_POST_PR_COMMENT=false`, but no sanitized capture showed the default non-posting behavior.
- Root cause: issue #26 needed screenshot-or-capture evidence for the dry-run path, and a real PR screenshot could expose private repository data, user emails, or comments.
- Change made: documented the Default Dry Run, linked a sanitized textual capture, clarified that job summaries and artifacts remain the review surface, documented the `pull-requests: write` tradeoff, and added current-truth tests for the docs, capture, default env value, posting guards, and permission boundary.
- Validation run: `python -m pytest tests/test_pr_comment_docs_current_truth.py -q`; `python -m pytest tests/test_github_workflow.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_optional_pr_comment_and_scorecard_surfaces_are_opt_in -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_pr_comment_docs_current_truth.py`; `python -m ruff format --check tests/test_pr_comment_docs_current_truth.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the missing Default Dry Run section and missing capture file, then passed `3`; GitHub workflow suite passed `23`; launch opt-in surface test passed `1`; public text hygiene passed; Ruff check and format passed; diff whitespace check passed.
- Gate delta: optional PR comments are now pinned as disabled-by-default evidence rather than an implied bot-comment behavior.
- User impact: maintainers can review the dry-run contract before granting `pull-requests: write` or enabling PR comments.
- Remaining blocker: actual PR comment posting remains opt-in and requires maintainer approval; `QA_Z_POST_PR_COMMENT=true` was not run.
- Next safe slice: if maintainers later approve comment posting, add a separate explicit opt-in validation packet without changing the default template behavior.


## 2026-05-15 Public Roadmap Proposal Template
- Repo: JustTyping
- Lane: public roadmap proposal -> evidence-backed contributor workflow
- User-facing flow: public roadmap proposal -> evidence, validation, user impact, non-goals -> maintainer prioritization.
- Slice type: Docs / Contract / Evidence
- Before: `docs/public-roadmap.md` listed roadmap bands, but there was no roadmap-specific issue template requiring evidence, validation, user impact, non-goals, or generated-artifact policy.
- Root cause: public roadmap proposals could arrive as vague requests and accidentally imply package publish, live automation, tag/release/deploy, branch mutation, or bot-comment approval.
- Change made: added `.github/ISSUE_TEMPLATE/roadmap_proposal.yml` with required proposal, roadmap area, user impact, evidence, validation plan, non-goals, and boundary checks; linked the template from `docs/public-roadmap.md`; added current-truth tests for the template, docs link, overclaim prevention, and blank-issue policy.
- Validation run: `python -m pytest tests/test_public_roadmap_issue_template.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_public_roadmap_issue_template.py`; `python -m ruff format --check tests/test_public_roadmap_issue_template.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the missing roadmap proposal template and missing public-roadmap docs link, then passed `4`; public docs current-truth passed `16`; launch docs index check passed `1`; public text hygiene passed; Ruff check and format passed; diff whitespace check passed.
- Gate delta: roadmap intake now requires deterministic evidence and validation before a proposal enters maintainer prioritization.
- User impact: contributors can propose roadmap items without implying live model execution, package publish, tag/release/deploy, branch mutation, bot-comment automation, or source commits of generated runtime artifacts.
- Remaining blocker: roadmap proposals still require maintainer prioritization before implementation; no assignment or bot comment was made for the external contributor request on #20.
- Next safe slice: triage remaining public-launch good-first issues by choosing the next evidence-backed docs/test closeout that does not require release approval.


## 2026-05-15 Community Examples Evidence Guide
- Repo: JustTyping
- Lane: community examples -> deterministic evidence intake
- User-facing flow: community example proposal -> deterministic evidence -> artifact policy -> maintainer review.
- Slice type: Docs / Contract / Evidence
- Before: `docs/community-distribution.md` listed launch channels, but did not define how contributors should submit example evidence.
- Root cause: community examples could arrive without reproducible evidence, validation commands, privacy rules, or generated-output boundaries.
- Change made: added community example submission guidance, required evidence, acceptable artifacts, forbidden generated outputs, validation commands, and public roadmap linkage.
- Validation run: `python -m pytest tests/test_community_examples_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_public_roadmap_issue_template.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python -m ruff check tests/test_community_examples_docs.py`; `python -m ruff format --check tests/test_community_examples_docs.py`.
- Evidence: the new focused docs guard first failed on the missing community example sections and missing public-roadmap link, then passed `4`; public docs current-truth passed `16`; public roadmap issue-template checks passed `4`; launch docs index check passed `1`; Ruff check and format passed.
- Gate delta: community example intake now requires deterministic evidence, validation commands, privacy notes, and generated-artifact boundaries before maintainer review.
- User impact: contributors can submit examples without leaking private data or committing generated runtime output.
- Remaining blocker: community examples still require maintainer review before acceptance; no assignment or bot comment was made for the external contributor request on #25.
- Next safe slice: triage the next public-launch docs/test closeout that can be proven without release approval, live automation, or generated runtime artifacts.


## 2026-05-15 TypeScript Agent Bug Evidence Walkthrough
- Repo: JustTyping
- Lane: TypeScript example -> baseline/candidate verification evidence
- User-facing flow: TypeScript authorization bug -> baseline failure -> candidate owner-check fix -> QA-Z verification artifacts.
- Slice type: Docs / Contract / Evidence
- Before: the TypeScript example was runnable and documented basic commands, but lacked a standalone walkthrough and artifact inspection guide.
- Root cause: contributors could run the TypeScript demo but had to infer the same baseline/candidate evidence tour already documented for the Python and FastAPI auth paths.
- Change made: added a TypeScript walkthrough, README evidence checklist, tests for commands/artifacts/source/config consistency, and docs index link.
- Validation run: `python -m pytest tests/test_typescript_agent_bug_walkthrough_docs.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_examples_index_links_visual_proof_and_labels_run_status -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_typescript_agent_bug_walkthrough_docs.py`; `python -m ruff format --check tests/test_typescript_agent_bug_walkthrough_docs.py`; `git diff --check`; `qa-z plan --title "TypeScript agent bug caught by QA-Z" --issue issue.md --spec spec.md --slug typescript-auth-bug --overwrite`; `qa-z fast --path examples/typescript-agent-bug --output-dir .qa-z/runs/qa-z-ts-agent-bug`.
- Evidence: focused walkthrough tests passed `5`, examples index smoke passed `1`, public current-truth tests passed `16`, public text hygiene passed, Ruff check and format passed, diff whitespace passed; optional smoke first required a generated contract, then produced baseline fast evidence with `ts_lint` and `ts_type` passed and expected `ts_test` failure: `non-owner user_2 was allowed to view inv_1`.
- Gate delta: #6 can close after merge because the TypeScript agent bug flow now has a deterministic evidence walkthrough.
- User impact: contributors can replay a TypeScript agent bug without live agents and inspect deterministic QA-Z evidence before merge.
- Remaining blocker: no local blocker; generated contract and `.qa-z/**` smoke output were removed and must stay uncommitted.
- Next safe slice: use real TypeScript verify artifacts from a future repair loop to refine troubleshooting guidance if contributors hit environment-specific Semgrep setup failures.


## 2026-05-15 GitHub Actions Summary Capture
- Repo: JustTyping
- Lane: GitHub Action summary -> reviewer evidence capture
- User-facing flow: QA-Z GitHub Actions guard -> Job Summary -> `qa-z-runs` artifact pointers -> reviewer decision.
- Slice type: Docs / Contract / Evidence
- Before: the GitHub Action docs explained the composite guard action, optional SARIF upload, and artifact preservation, but did not include a sanitized capture of the Job Summary and reviewer artifact pointers.
- Root cause: issue #16 needed screenshot-or-capture evidence for the GitHub Actions summary surface, while a real private repository screenshot could expose repository data, user emails, branch names, PR comments, or secrets.
- Change made: added a Job Summary and artifact pointer section to `docs/github-action.md`, added a sanitized textual capture at `docs/assets/github-actions-summary-capture.md`, and added focused tests pinning `GITHUB_STEP_SUMMARY`, `github-summary.md`, `verdict.md`, `qa-z-runs`, and `.qa-z/runs/latest`.
- Validation run: `python -m pytest tests/test_github_actions_summary_docs.py -q`; `python -m pytest tests/test_github_workflow.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_github_actions_summary_docs.py`; `python -m ruff format --check tests/test_github_actions_summary_docs.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the missing Job Summary docs section and missing capture file, then passed `3`; final validation covered the GitHub workflow suite, launch docs index check, public text hygiene, Ruff check, Ruff format check, and diff whitespace check.
- Gate delta: maintainers now have a deterministic capture for the GitHub Actions Job Summary and uploaded artifact pointers without relying on private UI screenshots.
- User impact: reviewers can start with the QA-Z Job Summary and follow `qa-z-runs` machine-readable evidence without exposing private repository data or secrets.
- Remaining blocker: actual GitHub UI layout can vary by repository permissions and workflow configuration; no live `.qa-z/**` runtime artifacts were generated for this docs slice.
- Next safe slice: after PR merge closes #16, continue with the next public-launch docs/test closeout that can be proven without release approval, live model calls, bot comments, package publish, or generated runtime artifacts.


## 2026-05-15 Enterprise Case Study Template
- Repo: JustTyping
- Lane: case studies -> adoption proof -> evidence boundaries
- User-facing flow: case study draft -> before/after QA-Z evidence -> redaction and claims review -> publishable proof.
- Slice type: Docs / Contract / Evidence
- Before: `docs/case-studies.md` had seed ideas but no template that required before/after evidence, commands, non-goals, redaction, or claims boundaries.
- Root cause: issue #27 needed a case-study template for adoption proof, and the seed page could encourage vague stories, unsupported customer claims, or accidental private-data exposure.
- Change made: added an enterprise case study template, before/after evidence checklist, command template, artifact pointers, validation guidance, redaction guidance, fake-claim boundary, generated-artifact policy, and focused tests pinning those requirements.
- Validation run: `python -m pytest tests/test_case_studies_docs.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_case_studies_docs.py`; `python -m ruff format --check tests/test_case_studies_docs.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the seed-only case-study page, then passed `5`; final validation covered launch docs index, public text hygiene, Ruff check, Ruff format check, and diff whitespace check.
- Gate delta: maintainers now have a deterministic template for publishing case studies without inventing adoption or customer claims.
- User impact: contributors can prepare case studies with explicit before/after evidence, commands, non-goals, redaction, and generated-artifact boundaries.
- Remaining blocker: real customer, adoption, usage, performance, revenue, or security-impact claims still require explicit approval and source evidence.
- Next safe slice: after PR merge closes #27, continue with monthly benchmark report or hosted-demo proof surfaces that reuse the same evidence and claims-boundary pattern.


## 2026-05-15 Hosted Demo Static Replay Plan
- Repo: JustTyping
- Lane: hosted demo -> static replay plan -> local evidence boundary
- User-facing flow: hosted demo page -> static docs assets -> `examples/agent-auth-bug` local replay -> QA-Z artifacts.
- Slice type: Docs / Contract / Evidence
- Before: `docs/hosted-demo.md` stated the static/no-cloud direction but lacked the replay command spine and artifact list needed to recreate the demo.
- Root cause: issue #24 needed a hosted demo plan that stays replayable locally without implying QA-Z Cloud, live-agent execution, or hidden backend state.
- Change made: added a static page boundary, local replay commands, demo artifact list, checked-in asset list, docs-site integration, and focused tests.
- Validation run: `python -m pytest tests/test_hosted_demo_docs.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_launch_growth_package_covers_requested_surfaces -q`; `python -m pytest tests/test_launch_growth_package.py::test_demo_asciinema_asset_is_real_cast_shape -q`; `python -m pytest tests/test_launch_growth_package.py::test_readme_demo_visual_is_checked_in_and_public_safe -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_hosted_demo_docs.py`; `python -m ruff format --check tests/test_hosted_demo_docs.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the missing hosted-demo command spine, artifact list, boundary language, and docs-site source linkage, then passed `4`; final validation covered launch growth asset checks, public text hygiene, Ruff check, Ruff format check, and diff whitespace check.
- Gate delta: maintainers now have a static hosted-demo plan that points to local replay evidence instead of a hosted service.
- User impact: users can understand the hosted demo as a static replay page, not QA-Z Cloud or live-agent execution.
- Remaining blocker: actual public hosted site remains future scope until static-site tooling and domain decisions are made; no generated `.qa-z/**` runtime artifacts were committed.
- Next safe slice: after PR merge closes #24, continue with monthly benchmark report or comparison/positioning docs that reuse the same evidence and no-fake-claims boundary.


## 2026-05-15 Monthly Benchmark Report Evidence Slice
- Repo: JustTyping
- Lane: benchmark reporting -> fixture rows -> QA-Z evidence provenance
- User-facing flow: monthly benchmark report -> fixture contract -> QA-Z run artifacts -> maintainer closeout.
- Slice type: Docs / Contract / Evidence
- Before: `docs/monthly-benchmark-report-template.md` listed high-level metrics but did not require row-level artifact pointers, fixture provenance, validation commands, claims boundaries, or generated-artifact stop rules.
- Root cause: #23 needed a monthly report sample that ties benchmark rows to QA-Z run evidence without fabricating adoption, performance, user, security-impact, package, hosted-automation, or leaderboard claims.
- Change made: added a report boundary, summary fields, fixture row template, artifact evidence list, fixture provenance, validation commands, claims boundary, generated-artifact policy, and benchmark overview linkage.
- Validation run: `python -m pytest tests/test_monthly_benchmark_report_docs.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_monthly_benchmark_report_docs.py`; `python -m ruff format --check tests/test_monthly_benchmark_report_docs.py`; `git diff --check`; optional `python -m pytest tests/test_public_docs_current_truth.py -q`; optional `python -m pytest tests/test_case_studies_docs.py -q`.
- Evidence: the new focused docs guard first failed on the missing monthly report evidence sections and benchmark overview linkage, then passed `5`; launch docs index check passed `1`; public text hygiene passed; Ruff check and format passed; diff whitespace check passed; optional public docs current-truth passed `16`; optional case-study docs passed `5`.
- Gate delta: monthly benchmark reports now require fixture rows to point at `expected.json`, baseline/candidate QA-Z artifacts, verify artifacts, provenance, validation evidence, and generated-results policy.
- User impact: maintainers can publish benchmark reports that point to deterministic QA-Z evidence without fabricating adoption, performance, user-impact, security-impact, package, hosted-automation, or leaderboard claims.
- Remaining blocker: actual monthly reports still require real benchmark runs and explicit freeze decisions before committing generated outputs.
- Next safe slice: after PR merge closes #23, continue with the next public proof surface that can be verified without live model calls, benchmark artifact commits, release approval, deploy, package publish, or bot comments.


## 2026-05-15 Codex Repair Prompt Snippet Card Slice
- Repo: JustTyping
- Lane: Codex handoff -> copyable prompt snippet -> deterministic evidence boundary
- User-facing flow: QA-Z repair prompt -> human-operated Codex handoff -> validation evidence.
- Slice type: Docs / Contract / Evidence
- Before: `docs/use-with-codex.md` described the Codex loop, but the compact copy-this prompt did not pin `.qa-z/runs/latest/repair/codex.md` as the default handoff path.
- Root cause: #21 needed a copyable Codex prompt that preserves QA-Z artifacts as source of truth without implying live Codex API execution or LLM-only judgment.
- Change made: added a copy-this-prompt-to-Codex snippet, clarified latest-run versus reproducible run paths, linked README to the deeper Codex guide, and pinned the evidence boundary with focused tests.
- Validation run: `python -m pytest tests/test_codex_prompt_snippet_docs.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_codex_prompt_snippet_docs.py`; `python -m ruff format --check tests/test_codex_prompt_snippet_docs.py`; `git diff --check`; optional `python -m pytest tests/test_verify_workflow_docs.py -q`.
- Evidence: the new focused docs guard first failed on the missing copy-this prompt, human-operated Codex boundary, and README guide link, then passed `3`; launch docs index check passed `1`; public docs current-truth passed `16`; public text hygiene passed; Ruff check and format passed; diff whitespace check passed; optional verify workflow docs passed `5`.
- Gate delta: Codex handoff guidance now points at latest QA-Z repair evidence while keeping deterministic artifacts as the source of truth.
- User impact: users can hand Codex the right QA-Z repair artifact without turning QA-Z into a live Codex executor or LLM judge.
- Remaining blocker: actual Codex edits and validation remain human-operated and outside QA-Z.
- Next safe slice: after PR merge closes #21, continue with the next small public proof or handoff clarity issue that can be verified without live model calls, release approval, deploy, package publish, or bot comments.


## 2026-05-15 Monorepo Quickstart Evidence Slice
- Repo: JustTyping
- Lane: quickstart -> monorepo profile -> mixed Python/TypeScript local gate
- User-facing flow: repository onboarding -> monorepo init -> deterministic fast/deep/review/repair evidence.
- Slice type: Docs / Contract / Evidence
- Before: `qa-z init` supported the monorepo profile, but `docs/quickstart.md` did not show a mixed Python/TypeScript install and gate path.
- Root cause: #15 needed current-truth docs for the existing monorepo profile without implying live-agent execution or cloud automation.
- Change made: added monorepo quickstart commands, profile semantics, deterministic/local boundary, public roadmap linkage, and focused docs tests.
- Validation run: `python -m pytest tests/test_monorepo_quickstart_docs.py -q`; `python -m pytest tests/test_init_options.py::test_init_with_profile_monorepo_uses_smart_selection -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_monorepo_quickstart_docs.py`; `python -m ruff format --check tests/test_monorepo_quickstart_docs.py`; `git diff --check`.
- Evidence: the focused monorepo docs guard first failed on the missing mixed Python/TypeScript path, then passed after the quickstart and roadmap truth updates.
- Gate delta: the documented onboarding path now matches the existing `monorepo` init profile and its smart fast selection behavior.
- User impact: users can initialize mixed Python/TypeScript repositories without assuming live-agent execution or cloud automation.
- Remaining blocker: real monorepo project adoption still depends on users mapping their concrete check commands into `qa-z.yaml`.
- Next safe slice: continue with #18 positioning or #4 runnable Next.js demo after this PR merges, preserving deterministic/local boundaries and avoiding generated runtime artifacts.


## 2026-05-15 Comparison Positioning Evidence Slice
- Repo: JustTyping
- Lane: comparison / positioning / model-agnostic merge evidence
- User-facing flow: comparison page -> agent-tool fit -> deterministic merge evidence boundary.
- Slice type: Docs / Contract / Evidence
- Before: `docs/comparison.md` compared Codex, Claude Code, Cursor, Semgrep, test tools, and QA-Z, but it did not mention aider, OpenHands, or Goose, and the root README did not link to the deeper comparison surface.
- Root cause: #18 needed the comparison page to frame QA-Z around popular coding agents without making QA-Z look like a coding-agent replacement or unsupported superiority claim.
- Change made: expanded `docs/comparison.md` with role-based positioning for Codex, Claude Code, Cursor, aider, OpenHands, Goose, Semgrep, CI/test tools, human review, and QA-Z; added a concise README comparison link; added focused current-truth tests for agent mentions, model-agnostic merge evidence wording, non-goal boundaries, and README clutter protection.
- Validation run: `python -m pytest tests/test_comparison_positioning_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_docs_index_and_readme_link_full_growth_package -q`; `python -m pytest tests/test_codex_prompt_snippet_docs.py tests/test_monorepo_quickstart_docs.py -q`; `python -m pytest tests/test_current_truth.py::test_readme_is_public_landing_page_linking_to_internal_anchors -q`; `python -m pytest -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_comparison_positioning_docs.py`; `python -m ruff format --check tests/test_comparison_positioning_docs.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on missing aider/OpenHands/Goose, missing model-agnostic evidence and non-goal boundary text, and missing README comparison link, then passed `3`; the first remote CI run exposed the README line-budget guard at `232 <= 230`, so the link was folded into an existing paragraph without weakening the cap; public docs current-truth passed `16`; launch docs link check passed `1`; adjacent Codex/monorepo docs checks passed `7`; README line-budget guard passed `1`; full local pytest passed `1795`; public text hygiene passed; Ruff check and format passed; diff whitespace check passed.
- Gate delta: comparison positioning is now pinned by focused tests instead of relying only on narrative docs.
- User impact: users can understand QA-Z as a model-agnostic QA evidence layer around coding agents, not a competing agent, before they decide whether to use it with their own agent workflow.
- Remaining blocker: detailed feature-by-feature claims about aider, OpenHands, Goose, or model quality still require official-source verification before expansion.
- Next safe slice: after PR merge closes #18, continue with #4 runnable Next.js demo only if it can be built from deterministic local artifacts without live model calls, deploy, package publish, or bot comments.


## 2026-05-15 Next.js Runnable Demo Slice
- Repo: JustTyping
- Lane: Next.js example -> runnable demo -> deterministic fast gate
- User-facing flow: examples index -> Next.js demo -> local npm checks -> QA-Z plan/fast evidence.
- Slice type: Docs / Contract / Evidence / Test
- Before: `examples/nextjs-demo` was placeholder-only and the examples index, docs index, reports, and current-truth tests described it as non-runnable.
- Root cause: #4 needed a small runnable Next.js project that shows QA-Z around a real TypeScript fast gate without implying hosted services, live agents, package publish, deploy, or executor automation.
- Change made: added package files, TypeScript and ESLint config, a minimal Next.js `app/` surface, deterministic invoice-access source, Vitest coverage, QA-Z fast-check config, issue/spec inputs, README commands, examples/docs index updates, and focused current-truth tests.
- Validation run: `npm install`; `npm run lint`; `npm run typecheck`; `npm test`; `python -m qa_z plan --path . --title "Protect Next.js invoice access" --issue issue.md --spec spec.md`; `python -m qa_z fast --path . --selection smart`; `python -m pytest tests/test_nextjs_demo_current_truth.py -q`; `python -m pytest tests/test_launch_growth_package.py::test_launch_growth_package_covers_requested_surfaces -q`; `python -m pytest tests/test_launch_growth_package.py::test_examples_index_links_visual_proof_and_labels_run_status -q`; `python -m pytest tests/test_examples.py::test_nextjs_demo_is_runnable_fast_gate tests/test_current_truth.py::test_readme_repository_map_marks_examples_as_runnable tests/test_current_truth.py::test_reports_record_nextjs_runnable_live_free_boundary_sync -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_nextjs_demo_current_truth.py`; `python -m ruff format --check tests/test_nextjs_demo_current_truth.py`; `git diff --check`.
- Evidence: the new focused current-truth test first failed on missing package/config/source/test/docs surfaces, then passed `4`; local npm lint, typecheck, and Vitest passed with `3` tests; QA-Z plan generated the invoice-access contract and QA-Z fast passed after the Windows npm shim path was made deterministic through the local wrapper script; public docs and launch-growth guards passed after stale placeholder labels were updated.
- Gate delta: the Next.js example now exercises `ts_lint`, `ts_type`, and `ts_test` through local npm scripts instead of remaining a placeholder.
- User impact: users can try QA-Z on a small Next.js/TypeScript project and see deterministic fast evidence without starting a server or using networked services after dependencies are installed.
- Generated cleanup: `node_modules`, `.qa-z/**`, generated `qa/contracts/**`, `.next`, coverage, and the incidental `package-lock.json` are not intended source artifacts and must be removed before staging.
- Remaining blocker: broader Next.js app patterns still require project-specific `qa-z.yaml` mapping; `npm install` reported `2` moderate advisories from the resolved dependency tree, which were not auto-fixed to avoid unreviewed dependency churn.
- Next safe slice: after PR merge closes #4, continue with the next runnable public proof surface that can be validated locally without live model calls, package publish, deploy, release, branch mutation, or bot comments.


## 2026-05-15 v0.10.0-beta Readiness Audit Packet
- Repo: JustTyping
- Lane: release readiness / current-truth proof / package rehearsal boundary
- User-facing flow: closed public issue backlog -> beta readiness decision -> release-owner action packet.
- Slice type: Evidence / Contract / Cleanup
- Before: open GitHub issue and PR backlog was empty after PR #59 merged #4, but there was no single report that mapped `v0.10.0-beta` goals to current release, package metadata, hosted-demo, docs, local validation, unavailable tools, generated cleanup, and approval blockers.
- Root cause: release polish, hosted-demo path, and package-publish readiness were distributed across roadmap, launch docs, package-publish plan, release notes, and tests, so a maintainer could confuse local readiness evidence with actual release execution.
- Change made: added `docs/reports/v0.10.0-beta-readiness.md`, added `tests/test_beta_readiness_docs.py`, and routed the new readiness packet through the worktree commit-plan current-truth batch so strict release staging stays clean.
- Validation run: GitHub API open issue/PR checks; `gh release view v0.9.9-alpha --repo qazedhq/qa-z --json tagName,isPrerelease,isDraft,publishedAt,targetCommitish,url`; `python -m pytest tests/test_public_docs_current_truth.py tests/test_beta_readiness_docs.py -q`; `python -m pytest tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py tests/test_beta_readiness_docs.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python -m pytest -q`; `python -m ruff check .`; `python -m ruff format --check .`; `python -m mypy src tests`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m qa_z --help`; `python -m qa_z doctor --help`; `python -m qa_z demo auth-bug --json`; `python -m qa_z benchmark --results-dir benchmarks/results-ci --json`; `python -m build --sdist --wheel`; `python scripts/alpha_release_artifact_smoke.py --json`; `python scripts/alpha_release_artifact_smoke.py --with-deps --json`; Next.js `npm install`, `npm run lint`, `npm run typecheck`, `npm test`, `python -m qa_z plan --path . --title "Protect Next.js invoice access" --issue issue.md --spec spec.md`, and `python -m qa_z fast --path . --selection smart`.
- Evidence: GitHub API returned `0` open issues and `0` open PRs; issue #4 is closed/completed and PR #59 is merged; GitHub release `v0.9.9-alpha` is a published prerelease; focused docs tests passed `20`; focused commit-plan/readiness tests passed `8`; strict worktree plan passed with `status=ready`, `changed_batch_count=2`, and no generated/cross-cutting/unassigned blockers; full pytest passed `1804`; Ruff check and format passed after formatting the new test; mypy passed for `565` source files; public text hygiene passed; demo JSON returned `status=created`; benchmark passed `54/54`; build produced `qa_z-0.9.8a0.tar.gz` and `qa_z-0.9.8a0-py3-none-any.whl`; artifact smoke passed with and without dependency resolution; Next.js lint/typecheck/Vitest/QA-Z plan/fast passed.
- Gate delta: `v0.10.0-beta` now has a non-executing readiness report that preserves `v0.9.9-alpha` versus planned beta, package metadata `0.9.8a0`, local-only package rehearsal evidence, unavailable package-smoke tools, generated-artifact cleanup, and human approval blockers.
- User impact: a release owner can decide the next beta step without mistaking source/tag install docs, static hosted-demo plans, local wheel smoke, or closed issues for an actual beta release or registry publish.
- Remaining blocker: no PyPI/TestPyPI/npm/GitHub Packages upload, tag, GitHub Release, deploy, push, bot comment, live model call, or GitHub settings mutation was performed; `twine`, `pipx`, and `uvx` were unavailable in this environment; Next.js `npm install` still reports `2` moderate advisories that need a separate dependency decision.
- Next safe slice: clean generated artifacts, rerun strict worktree status, then ask the release owner whether the next packet should be a proof-branch CI/public-raw packet, a non-executing version-policy PR, or a credentialed registry rehearsal with `registry_upload_executed=false`.


## 2026-05-15 v0.10.0-beta Release-owner Decision Packet
- Repo: JustTyping
- Lane: v0.10.0-beta readiness -> release-owner decision
- User-facing flow: readiness report -> release-owner path choice -> release execution remains blocked.
- Slice type: Evidence / Contract / Cleanup
- Before: PR #60 merged the readiness report with release execution `NO-GO`, but the release owner still needed a separate decision packet that translated the report into path choices without executing tag, release, package upload, deploy, bot comment, settings mutation, or live model actions.
- Root cause: readiness evidence, version state, package registry approval, unavailable `twine`/`pipx`/`uvx` smokes, and Next.js advisory risk could be mistaken for a release run unless the owner decision boundary was test-pinned.
- Change made: added `docs/reports/v0.10.0-beta-release-decision.md` and `tests/test_beta_release_decision_docs.py`, preserving `v0.10.0-beta` as unreleased, current public alpha `v0.9.9-alpha`, package metadata `0.9.8a0`, blocked upload/tag/release/deploy commands, required approval fields, path options, rollback/yank policy, and explicit non-actions.
- Validation run: `python -m pytest tests/test_beta_release_decision_docs.py -q`; `python -m pytest tests/test_beta_readiness_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py tests/test_current_truth.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_beta_release_decision_docs.py scripts/worktree_commit_plan_support.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py`; `python -m ruff format --check tests/test_beta_release_decision_docs.py scripts/worktree_commit_plan_support.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py`; `git diff --check`.
- Evidence: focused decision-packet guard passed `5`; beta readiness docs passed `4`; public docs current truth passed `16`; commit-plan routing/current-truth pack passed `75`; strict worktree plan returned `status=ready`, `changed_batch_count=2`, `changed_path_count=6`, and zero generated, cross-cutting, unassigned, or report-path blockers; public text hygiene passed; Ruff check/format passed; diff whitespace passed.
- Gate delta: release execution and release-owner decisioning are now separate tracked surfaces; upload/tag/release/deploy commands are documented only as blocked examples.
- User impact: the release owner can choose no release, GitHub prerelease only, TestPyPI rehearsal only, TestPyPI publish, PyPI publish, or version metadata bump only without confusing readiness with release execution.
- Remaining blocker: release-owner approval, registry credentials, `twine`/`pipx`/`uvx` smoke, Next.js moderate advisories, version policy, exact release SHA remote CI proof, public raw proof, and package registry rollback/yank policy remain blocked.
- Next safe slice: after this decision packet merges, the owner should choose either no release yet, a no-upload package-smoke closeout in a provisioned environment, or a separate version-policy PR before any release execution packet.


## 2026-05-16 Package Smoke Rehearsal Harness
- Repo: JustTyping
- Lane: package smoke rehearsal -> release blocker closeout
- User-facing flow: build artifact -> artifact install smoke -> safe package rehearsal -> release-owner evidence.
- Slice type: Evidence / Contract / Cleanup
- Before: `twine`, `pipx`, and `uvx` package smokes were tracked as manual/not-run blockers, and package docs used a hardcoded `dist/qa_z-0.9.8a0-py3-none-any.whl` command path.
- Root cause: release readiness needed a repeatable local-only harness that discovers the exact built artifact, records missing tools as `NOT RUN`, and keeps package upload/tag/release/deploy commands outside executable validation.
- Change made: added `scripts/package_smoke_rehearsal.py` and support helpers, added fake-runner unit coverage, routed the new release helper through commit-plan validation, updated the package publish plan and v0.10.0-beta decision packet to use the harness, and kept `registry_upload_executed=false`.
- Validation run: `python -m pytest tests/test_package_smoke_rehearsal.py -q`; `python -m pytest tests/test_beta_release_decision_docs.py -q`; `python -m pytest tests/test_beta_readiness_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py -q`; `python -m pytest tests/test_alpha_release_truth_validator.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check` and `python -m ruff format --check` over the changed Python files; `git diff --check`; `python -m build --sdist --wheel`; `python scripts/alpha_release_artifact_smoke.py --with-deps --json`; `python scripts/package_smoke_rehearsal.py --json --allow-missing-tools`.
- Evidence: package rehearsal tests passed `7`; release decision docs passed `5`; beta readiness docs passed `4`; public docs current-truth passed `16`; commit-plan routing tests passed `33`; alpha release truth validator passed `24`; strict worktree plan returned `status=ready`, `changed_path_count=13`, and zero generated, cross-cutting, report-path, shared patch-add, multi-batch, unassigned, or product-decision blockers; text hygiene passed; Ruff check/format passed; diff whitespace passed; build produced `qa_z-0.9.8a0.tar.gz` and `qa_z-0.9.8a0-py3-none-any.whl`; artifact smoke passed for wheel and sdist with dependency resolution; package smoke rehearsal exited `0` with `twine_check`, `pipx_wheel_help`, and `uvx_wheel_help` recorded as `NOT RUN`; `registry_upload_executed=false`.
- Gate delta: package smoke status is now machine-readable as `PASS`, `FAIL`, `NOT RUN`, or `BLOCKED`, and missing tool availability can no longer be mistaken for a pass.
- User impact: release owners get repeatable package readiness evidence without global tool installs, hardcoded wheel drift, registry upload, tag creation, GitHub Release creation, deploy, bot comment, or live model behavior.
- Generated cleanup: removed `build/`, `dist/`, `src/qa_z.egg-info/`, `.pytest_cache/`, and `.ruff_cache/` before staging.
- Remaining blocker: `twine`, `pipx`, and `uvx` remain unavailable in this environment, so those smokes are still `NOT RUN`; release-owner approval, package credentials, version policy, exact release SHA proof, public raw proof, Next.js moderate advisories, and registry rollback/yank policy remain blocked.
- Next safe slice: run the same harness in a provisioned release rehearsal environment where `twine`, `pipx`, and `uvx` are already available, still with `registry_upload_executed=false`, or split a separate version-policy PR if the release owner chooses metadata first.


## 2026-05-16 Next.js Advisory Decision Evidence
- Repo: JustTyping
- Lane: Next.js demo dependency advisory -> release-owner decision
- User-facing flow: Next.js demo install -> npm audit -> v0.10.0-beta blocker classification.
- Slice type: Evidence / Contract / Cleanup
- Before: the beta readiness and release decision packets recorded `2` moderate Next.js advisories, but did not name the exact advisory, resolved dependency versions, or why an automatic dependency fix would not close the blocker.
- Root cause: `examples/nextjs-demo/package.json` has no checked-in lockfile; a current temporary install resolves `next@15.5.18`, and that package still declares `postcss@8.4.31` while `GHSA-qx2v-qp2m-jg93` / `CVE-2026-41305` is patched in PostCSS `8.5.10`.
- Change made: updated the v0.10.0-beta readiness and release-owner decision packets to record the advisory ID, resolved Next.js/PostCSS versions, `postcss@latest`, `next@latest` still declaring `postcss@8.4.31`, and the explicit no-auto-fix/no-downgrade/no-override boundary; added focused docs tests.
- Validation run: `npm install --package-lock-only --ignore-scripts --audit=false --fund=false` in a temporary directory outside the repo; `npm audit --json --omit=dev`; `npm view next@15.5.18 dependencies --json`; `npm view next@latest version dependencies --json`; `npm view postcss@latest version`; `python -m pytest tests/test_beta_readiness_docs.py tests/test_beta_release_decision_docs.py -q`; `git diff --check`.
- Evidence: temporary audit reproduced `2` moderate advisories; requested `next@^15.0.0` resolved to `next@15.5.18`; resolved PostCSS was `8.4.31`; GitHub advisory patched version is `8.5.10`; `postcss@latest` was `8.5.14`; `next@latest` was `16.2.6` and still declared `postcss@8.4.31`; focused docs tests passed.
- Gate delta: the Next.js advisory blocker is now classified as an upstream dependency decision rather than a local package-smoke or blind `npm audit fix` task.
- User impact: release owners can see why release execution remains `NO-GO` without confusing a passing Next.js demo fast gate with dependency advisory closure.
- Remaining blocker: the advisory is not locally closed; closing it requires a reviewed Next.js/PostCSS compatibility decision, an upstream Next.js package update, a release policy exception, or replacing/removing the Next.js dependency from the beta release scope.
- Next safe slice: rerun the advisory audit after Next.js publishes a version that declares `postcss >=8.5.10`, or write a separate dependency decision PR that explicitly chooses defer/exception/remove without touching package publish, tag, release, deploy, or registry state.


## 2026-05-16 v0.10.0-beta Version Policy
- Repo: JustTyping
- Lane: v0.10.0-beta release decision -> version policy
- User-facing flow: release-owner decision packet -> version/tag/package metadata choice -> release execution remains blocked.
- Slice type: Evidence / Contract
- Before: the release decision packet existed and kept release execution `NO-GO`, but the version policy was still unresolved across `v0.9.9-alpha`, package metadata `0.9.8a0`, and planned `v0.10.0-beta`.
- Root cause: release owners could confuse a GitHub prerelease tag, Python package metadata, TestPyPI/PyPI package versions, and future `pipx install qa-z` / `uv tool install qa-z` commands unless the choice matrix was separately documented and test-pinned.
- Change made: added `docs/reports/v0.10.0-beta-version-policy.md`, linked it from the release decision packet and package publish plan, clarified future PyPI install commands, added focused current-truth tests, and routed the new report/test through worktree commit-plan ownership.
- Validation run: `python -m pytest tests/test_beta_version_policy_docs.py -q`; `python -m pytest tests/test_beta_release_decision_docs.py tests/test_beta_readiness_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_beta_version_policy_docs.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py scripts/worktree_commit_plan_support.py`; `python -m ruff format --check tests/test_beta_version_policy_docs.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py scripts/worktree_commit_plan_support.py`; `git diff --check`.
- Evidence: focused version policy tests cover the policy doc, unreleased beta state, current public alpha, current package metadata, `0.10.0b0` as candidate-only metadata, unchanged `pyproject.toml`, release decision linkage, future PyPI install wording, and approval-gated blocked actions.
- Gate delta: version policy is now separated from release execution and from package publish mechanics.
- User impact: release owners can choose no release, GitHub prerelease-only, TestPyPI rehearsal, TestPyPI publish, PyPI publish, or metadata-only PR without mistaking policy documentation for an actual release.
- Remaining blocker: release-owner version choice, tool-equipped `twine`/`pipx`/`uvx` smoke, registry credentials, Next.js advisory decision, exact SHA proof, public raw proof, and rollback/yank policy remain blocked.
- Next safe slice: run tool-equipped package smoke in a provisioned no-upload environment or open a separate approved metadata PR if the release owner chooses `0.10.0b0`.


## 2026-05-16 Next.js/PostCSS Advisory Decision Packet
- Repo: JustTyping
- Lane: Next.js advisory blocker -> release-owner decision
- User-facing flow: release-readiness docs -> advisory option packet -> release execution remains blocked.
- Slice type: Evidence / Contract / Cleanup
- Before: the Next.js/PostCSS advisory was documented as a release blocker, but release owners did not have a separate option packet that distinguished upstream fix, compatibility exception, replacement/removal, reviewed pin/change, explicit defer, and continued `NO-GO`.
- Root cause: the advisory evidence could be confused with a dependency fix or release recommendation unless decision options, required proof, explicit non-actions, and remaining blockers were separately test-pinned.
- Change made: added `docs/reports/v0.10.0-beta-nextjs-advisory-decision.md`, linked readiness/release-decision/version-policy reports, added focused docs tests, and routed the new packet through worktree commit-plan ownership.
- Validation run: `python -m pytest tests/test_nextjs_advisory_decision_docs.py -q`; `python -m pytest tests/test_beta_release_decision_docs.py tests/test_beta_readiness_docs.py tests/test_beta_version_policy_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_nextjs_advisory_decision_docs.py`; `python -m ruff format --check tests/test_nextjs_advisory_decision_docs.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the missing packet and links, then passed after the packet and report links were added.
- Gate delta: the advisory remains unresolved, but the release owner now has proof requirements and release impact for each decision path.
- User impact: maintainers can choose a safe advisory handling path without mistaking documentation for dependency remediation, package publish, version bump, tag, GitHub Release, deploy, bot comment, or live service action.
- Remaining blocker: release-owner selected option, upstream/dependency proof, tool-equipped `twine`/`pipx`/`uvx` smoke, registry credentials, exact SHA proof, public raw proof, rollback/yank policy, and version policy remain blocked.
- Next safe slice: after this packet merges, the release owner should choose explicit defer, compatibility exception, wait-for-upstream, dependency replacement/removal, or a reviewed dependency change PR before any release execution packet.


## 2026-05-16 v0.10.0-beta Exact SHA Proof Packet
- Repo: JustTyping
- Lane: release readiness -> exact SHA proof
- User-facing flow: release-owner decision -> exact candidate SHA -> remote CI/public raw evidence -> release execution remains blocked.
- Slice type: Evidence / Contract
- Before: readiness, release-decision, version-policy, package-smoke, and advisory packets existed, but the pre-packet PR #65 main baseline exact SHA, remote CI proof, public raw proof, and report linkage were not pinned in one packet.
- Root cause: release owners could confuse release readiness docs with release execution unless exact SHA proof, workflow run IDs, raw-file accessibility, explicit non-actions, and remaining blockers were separated and test-pinned.
- Change made: added `docs/reports/v0.10.0-beta-exact-sha-proof.md`, linked readiness/release-decision/version-policy/advisory reports, routed the new packet through commit-plan ownership, and added focused current-truth tests.
- Validation run: `python -m pytest tests/test_beta_exact_sha_proof_docs.py -q`; `python -m pytest tests/test_beta_release_decision_docs.py tests/test_beta_readiness_docs.py tests/test_beta_version_policy_docs.py tests/test_nextjs_advisory_decision_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_beta_exact_sha_proof_docs.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py scripts/worktree_commit_plan_support.py`; `python -m ruff format --check tests/test_beta_exact_sha_proof_docs.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py scripts/worktree_commit_plan_support.py`; `git diff --check`.
- Evidence: the new focused docs/routing guard failed first on the missing proof packet, missing links, and missing commit-plan ownership, then passed after the proof report, links, and routing were added. Remote proof for `865efa12fccc1976d6d9bf2cddec89bca6610f67` recorded `CI` run `25959011641` and `Public Raw Hygiene` run `25959011658` as successful main-push runs. Public raw proof recorded HTTP `200` for README, `pyproject.toml`, beta release reports, package publish plan, and package smoke rehearsal script at the exact SHA.
- Gate delta: exact candidate SHA proof is no longer an unrecorded blocker for the PR #65 main baseline, but it becomes historical after this proof PR merges or if `origin/main` otherwise moves and it does not authorize release execution.
- User impact: release owners can review one exact-SHA proof packet without mistaking it for a tag, GitHub Release, package publish, deploy, version bump, bot comment, settings mutation, or live model action.
- Remaining blocker: release-owner approval, tool-equipped `twine`/`pipx`/`uvx` smoke, registry credentials, Next.js/PostCSS advisory option and proof, post-merge exact SHA refresh, package registry rollback/yank policy, and package metadata/version policy remain blocked.
- Next safe slice: after this proof PR merges, refresh exact SHA proof for the merge commit; otherwise run no-upload package smoke in a provisioned environment with `twine`, `pipx`, and `uvx`, or record a release-owner advisory decision path before any release execution packet.


## 2026-05-17 v0.10.0-beta Post-merge Exact SHA Proof Refresh
- Repo: JustTyping
- Lane: release readiness -> post-merge exact SHA proof
- User-facing flow: PR #66 merge commit -> remote CI/public raw proof -> release execution remains blocked.
- Slice type: Evidence / Contract
- Before: PR #66's proof packet recorded exact-SHA proof for the PR #65 main baseline, which became historical after PR #66 merged.
- Root cause: release owners could mistake historical PR #65 proof for current release-owner execution evidence unless the PR #66 merge SHA, remote workflow runs, public raw checks, non-actions, and remaining blockers were refreshed together.
- Change made: refreshed `docs/reports/v0.10.0-beta-exact-sha-proof.md` to separate historical pre-packet proof from post-merge current proof for `7ec919b8ed255e623c7b684d296d8256d82d16ca`; updated readiness, release-decision, version-policy, and advisory packets to point at the current proof without unlocking release execution; updated focused docs tests.
- Validation run: `python -m pytest tests/test_beta_exact_sha_proof_docs.py -q`; `python -m pytest tests/test_beta_release_decision_docs.py tests/test_beta_readiness_docs.py tests/test_beta_version_policy_docs.py tests/test_nextjs_advisory_decision_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_beta_exact_sha_proof_docs.py`; `python -m ruff format --check tests/test_beta_exact_sha_proof_docs.py`; `git diff --check`.
- Evidence: `origin/main` and remote `refs/heads/main` both pointed to `7ec919b8ed255e623c7b684d296d8256d82d16ca`; GitHub Actions reported `CI` run `25976157325` and `Public Raw Hygiene` run `25976157333` as successful main-push runs; exact-SHA public raw checks returned HTTP `200` for README, `pyproject.toml`, beta release reports, the exact-SHA proof report, and `scripts/package_smoke_rehearsal.py`; exact-SHA docs tests passed `7`; beta release/readiness/version/advisory docs tests passed `19`; public docs current-truth tests passed `16`; strict worktree plan returned `status=ready`, `changed_path_count=8`, and zero generated, cross-cutting, report-path, shared patch-add, multi-batch, unassigned, or product-decision blockers; text hygiene, Ruff, and diff whitespace checks passed.
- Gate delta: post-merge exact SHA refresh moved from blocker to recorded proof for the current `origin/main` SHA, while release execution remains `NO-GO`.
- User impact: release owners can distinguish historical PR #65 proof from current PR #66 merge proof without mistaking it for tag creation, GitHub Release creation, package publish, deploy, version bump, bot comment, settings mutation, or live model action.
- Remaining blocker: release-owner approval, tool-equipped `twine`/`pipx`/`uvx` smoke, registry credentials, Next.js/PostCSS advisory option and proof, package registry rollback/yank policy, and package metadata/version policy remain blocked.
- Next safe slice: run no-upload package smoke in a provisioned environment with `twine`, `pipx`, and `uvx`, or record a release-owner advisory decision path before any release execution packet.


## 2026-05-17 v0.10.0-beta Final SHA Proof Protocol
- Repo: JustTyping
- Lane: release readiness -> final SHA proof protocol
- User-facing flow: historical exact-SHA proof reports -> release-candidate SHA freeze -> final execution proof outside the PR-merge loop.
- Slice type: Evidence / Contract / Cleanup
- Before: exact SHA proof PRs recorded useful remote CI and public raw evidence, but each proof became historical after its PR merged and moved `main`.
- Root cause: committing exact SHA proof to `main` changes the SHA being proven, so repeated proof-refresh PRs cannot produce final release-execution proof.
- Change made: added `docs/reports/v0.10.0-beta-final-sha-proof-protocol.md`, updated the exact SHA proof report to mark PR-committed proof as historical, linked the protocol from beta release reports, added focused protocol tests, and routed the new protocol report/test through commit-plan ownership.
- Validation run: `python -m pytest tests/test_beta_final_sha_proof_protocol_docs.py -q`; `python -m pytest tests/test_beta_exact_sha_proof_docs.py -q`; `python -m pytest tests/test_beta_release_decision_docs.py tests/test_beta_readiness_docs.py tests/test_beta_version_policy_docs.py tests/test_nextjs_advisory_decision_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_beta_final_sha_proof_protocol_docs.py`; `python -m ruff format --check tests/test_beta_final_sha_proof_protocol_docs.py`; `git diff --check`.
- Evidence: focused protocol docs tests require the PR proof loop explanation, release-candidate SHA freeze timing, final proof fields, allowed storage locations, disallowed release actions, preserved blockers, and links from release reports. Existing exact SHA proof docs tests now require historical proof wording and the final protocol link.
- Gate delta: repeated PR-based SHA refresh is no longer the recommended next action; final release proof stays blocked until release-candidate SHA freeze and release-owner execution review.
- User impact: release owners can use historical proof reports without mistaking them for final proof, and operators have a protocol for where final SHA proof belongs.
- Remaining blocker: release-owner approval, final release-execution-time SHA proof, tool-equipped `twine`/`pipx`/`uvx` smoke, Next.js/PostCSS advisory option and proof, registry credentials, package metadata/version execution decision, and package registry rollback/yank policy remain blocked.
- Next safe slice: run no-upload package smoke in a provisioned environment with `twine`, `pipx`, and `uvx`, or record the release-owner advisory decision before any release execution packet.


## 2026-05-17 v0.10.0-beta Release Execution Checklist
- Repo: JustTyping
- Lane: release readiness -> execution checklist
- User-facing flow: distributed release-readiness packets -> single release-owner pre-execution checklist -> release execution remains blocked.
- Slice type: Evidence / Contract / Cleanup
- Before: readiness, release-decision, version-policy, advisory, exact-SHA, final-SHA protocol, and package-publish documents existed, but the execution gates and approval fields were distributed across reports.
- Root cause: release owners could confuse historical proof, advisory decisions, version policy, package smoke, credentials, and rollback/yank policy without one checklist that fixes order, status vocabulary, and explicit non-actions.
- Change made: added `docs/reports/v0.10.0-beta-release-execution-checklist.md`, linked it from existing beta release reports, added focused docs tests, and routed the new report/test through worktree commit-plan ownership.
- Validation run: `python -m pytest tests/test_beta_release_execution_checklist_docs.py -q`; `python -m pytest tests/test_beta_final_sha_proof_protocol_docs.py tests/test_beta_exact_sha_proof_docs.py -q`; `python -m pytest tests/test_beta_release_decision_docs.py tests/test_beta_readiness_docs.py tests/test_beta_version_policy_docs.py tests/test_nextjs_advisory_decision_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py tests/test_current_truth.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_beta_release_execution_checklist_docs.py`; `python -m ruff format --check tests/test_beta_release_execution_checklist_docs.py`; `python -m ruff check scripts/worktree_commit_plan_support.py tests/test_beta_release_execution_checklist_docs.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py`; `python -m ruff format --check scripts/worktree_commit_plan_support.py tests/test_beta_release_execution_checklist_docs.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py`; `git diff --check`.
- Evidence: the new focused checklist test first failed on the missing checklist and report links, then passed after the checklist and links were added; focused checklist tests passed `6`; beta final-SHA/exact-SHA tests passed `14`; beta release/readiness/version/advisory tests passed `19`; public docs current-truth tests passed `16`; commit-plan routing/current-truth tests passed `75`; strict worktree plan returned `status=ready`, `changed_path_count=11`, zero generated artifacts, zero cross-cutting paths, zero report-path blockers, and zero unassigned source paths; text hygiene passed; Ruff check/format passed; diff whitespace passed.
- Gate delta: release execution now has one non-executing checklist with `PASS`, `FAIL`, `BLOCKED`, `NOT RUN`, `NO-GO`, `APPROVED`, and `NOT APPROVED` definitions plus current blocker statuses.
- User impact: the release owner can review approval fields, proof links, final SHA freeze requirements, package publish boundaries, advisory/version/smoke/credential/rollback blockers, and explicit no-release actions from one document.
- Remaining blocker: release-owner approval, final execution-time proof, tool-equipped twine/pipx/uvx smoke, Next.js/PostCSS advisory option/proof, registry credentials, version execution decision, and rollback/yank policy remain blocked.
- Next safe slice: run no-upload package smoke in a provisioned environment with `twine`, `pipx`, and `uvx`, or record the release-owner advisory decision before any release execution packet.


## 2026-05-17 v0.10.0-beta Rollback/Yank Policy
- Repo: JustTyping
- Lane: release readiness -> rollback/yank policy
- User-facing flow: release execution checklist -> release-path rollback/yank policy packet -> release execution remains blocked.
- Slice type: Evidence / Contract / Cleanup
- Before: rollback/yank policy was a release blocker in the checklist and package publish plan, but it was not a separate policy packet with registry/release-path-specific decision fields.
- Root cause: release owners could confuse local git rollback or local artifact deletion with registry-owned package yank/delete/deprecate, GitHub Release/tag deletion, or deploy rollback behavior.
- Change made: added `docs/reports/v0.10.0-beta-rollback-yank-policy.md`, linked it from the release execution checklist, release decision, version policy, and package publish plan, added focused docs tests, and routed the new report/test through worktree commit-plan ownership.
- Validation run: `python -m pytest tests/test_beta_rollback_yank_policy_docs.py -q`; `python -m pytest tests/test_beta_release_execution_checklist_docs.py -q`; `python -m pytest tests/test_beta_release_decision_docs.py tests/test_beta_readiness_docs.py tests/test_beta_version_policy_docs.py tests/test_nextjs_advisory_decision_docs.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py tests/test_current_truth.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_beta_rollback_yank_policy_docs.py`; `python -m ruff format --check tests/test_beta_rollback_yank_policy_docs.py`; `python -m ruff check scripts/worktree_commit_plan_support.py tests/test_beta_rollback_yank_policy_docs.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py`; `python -m ruff format --check scripts/worktree_commit_plan_support.py tests/test_beta_rollback_yank_policy_docs.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py`; `git diff --check`.
- Evidence: the new focused docs guard first failed on the missing policy packet and links, then passed after the policy report and links were added. The policy packet records official source pointers for PyPI/TestPyPI yanking, npm unpublish/deprecate, GitHub Release deletion, Git tag reference deletion, GitHub Packages delete/restore, and deploy-platform policy checks while keeping every registry action blocked.
- Gate delta: rollback/yank policy is now documented as a separate policy-only packet, but it remains `BLOCKED` until release-owner approval, selected registry/release path, official policy verification, and execution-time proof.
- User impact: release owners can compare GitHub prerelease/tag, TestPyPI, PyPI, npm, GitHub Packages, hosted deploy, no-release, and metadata-only paths without mistaking the packet for a release, package publish, yank, delete, deploy, or version bump.
- Remaining blocker: release-owner selected registry/release path, official policy verification at execution time, actual rollback/yank proof, tool-equipped `twine`/`pipx`/`uvx` smoke, registry credentials, version execution decision, advisory option/proof, and final release-execution-time SHA proof remain blocked.
- Next safe slice: run no-upload package smoke in a provisioned environment with `twine`, `pipx`, and `uvx`, or record the release-owner advisory decision before any release execution packet.


## 2026-05-17 v0.10.0-beta No-release Decision Packet
- Repo: JustTyping
- Lane: release readiness -> no-release decision
- User-facing flow: release execution checklist -> release-owner no-release decision -> deferred blockers remain visible.
- Slice type: Evidence / Contract / Cleanup
- Before: a stale dirty local `main` checkout contained an untrusted draft no-release packet, while `origin/main` already included PR #70 rollback/yank policy at `62224680e7433604f6a150f0c157833ad9ea3173`.
- Root cause: copying or committing from the stale dirty checkout risked overwriting newer release docs and treating local draft artifacts as PR evidence.
- Change made: created the no-release decision packet from a clean `origin/main` worktree, linked it from the latest release execution checklist and release decision report, added focused docs tests, and routed the new packet through worktree commit-plan ownership.
- Validation run: `python -m pytest tests/test_beta_no_release_decision_docs.py -q`; `python -m pytest tests/test_beta_no_release_decision_docs.py tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_beta_release_execution_checklist_docs.py tests/test_beta_release_decision_docs.py -q`; `python -m pytest tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py tests/test_current_truth.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_beta_no_release_decision_docs.py`; `python -m ruff format --check tests/test_beta_no_release_decision_docs.py`; `python -m ruff check tests/test_beta_no_release_decision_docs.py scripts/worktree_commit_plan_support.py`; `python -m ruff format --check tests/test_beta_no_release_decision_docs.py scripts/worktree_commit_plan_support.py`; `python -m qa_z --help`; `git diff --check`.
- Evidence: the focused no-release docs guard first failed on the missing packet and missing links, then passed after the packet and links were added. Focused no-release tests passed `4`; no-release plus public current-truth tests passed `20`; release checklist and release decision docs tests passed `11`; commit-plan routing/current-truth tests passed `75`; strict worktree plan returned `status=ready`, `changed_path_count=6`, zero generated, cross-cutting, report-path, shared patch-add, multi-batch, unassigned, product-decision, attention, or deferred-alpha blockers, and one approved-alpha support path for this ledger append; text hygiene passed; Ruff check/format passed; QA-Z help rendered; diff whitespace passed.
- Gate delta: `v0.10.0-beta` now has an explicit `No release yet` decision packet, but release execution remains `NO-GO` and blockers are deferred rather than resolved.
- User impact: release owners can distinguish a deliberate no-release decision from release approval, package publish, tag creation, GitHub Release creation, deploy, version bump, bot comment, settings mutation, or live model action.
- Remaining blocker: release-owner selected registry/release path, official policy verification at execution time, actual rollback/yank proof, tool-equipped `twine`/`pipx`/`uvx` smoke, registry credentials, version execution decision, advisory option/proof, and final release-execution-time SHA proof remain blocked.
- Next safe slice: run no-upload package smoke in a provisioned environment with `twine`, `pipx`, and `uvx`, or record the release-owner advisory decision before any release execution packet.


## 2026-05-17 v0.10.0-beta Tool-smoke Preflight Packet
- Repo: JustTyping
- Lane: release readiness -> tool-equipped package-smoke preflight
- User-facing flow: no-release decision -> clean origin/main worktree -> tool/credential preflight -> release smoke remains honestly blocked.
- Slice type: Evidence / Contract
- Before: the no-release decision correctly kept tool-equipped `twine`/`pipx`/`uvx` smoke as `NOT RUN`, but there was no fresh clean-worktree packet showing whether the current environment could run no-upload package smoke.
- Root cause: release owners could not distinguish a ready no-upload smoke environment from a missing-tool environment without a preflight packet that also checked credential contamination and preserved release non-actions.
- Change made: created `docs/reports/v0.10.0-beta-tool-smoke-preflight.md`, linked it from the no-release decision, execution checklist, and release decision packet, added focused docs tests, and routed the new report/test through worktree commit-plan ownership.
- Validation run: `python -m pytest tests/test_beta_tool_smoke_preflight_docs.py -q`; `python -m pytest tests/test_beta_no_release_decision_docs.py tests/test_beta_release_execution_checklist_docs.py tests/test_beta_release_decision_docs.py -q`; `python -m pytest tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py -q`; `python -m pytest tests/test_public_docs_current_truth.py -q`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_beta_tool_smoke_preflight_docs.py scripts/worktree_commit_plan_support.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py`; `python -m ruff format --check tests/test_beta_tool_smoke_preflight_docs.py scripts/worktree_commit_plan_support.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py`; `git diff --check`.
- Evidence: clean worktree `F:\JustTyping\.worktrees\v010-beta-tool-smoke-preflight` on branch `codex/v010-beta-tool-smoke-preflight` at `origin/main` SHA `bc1cef8b2a38a1099f92bad52a6db11bf34640f2`; `python -m twine --version` failed with no `twine` module; `pipx --version` and `uvx --version` were not recognized; package-publish credential env indicators returned `NO_PACKAGE_PUBLISH_CREDENTIAL_ENV_FOUND`; `.pypirc` returned `PYPIRC_ABSENT`; focused preflight docs tests passed `7`; linked beta docs tests passed `15`; commit-plan routing tests passed `5`; public docs current-truth tests passed `16`; strict worktree plan returned `status=ready`, `changed_path_count=8`, zero generated, cross-cutting, report-path, shared patch-add, multi-batch, unassigned, product-decision, or attention blockers; text hygiene, Ruff, and diff whitespace checks passed; `.pytest_cache` and `.ruff_cache` were removed.
- Gate delta: current environment is now explicitly `BLOCKED_TOOL_MISSING`; no-upload package smoke remains `NOT RUN`, and `registry_upload_executed=false` remains true.
- User impact: release owners can see that this clean environment is not eligible for tool-equipped no-upload package smoke until `twine`, `pipx`, and `uvx` are already provisioned, without confusing missing tools with a passing smoke.
- Remaining blocker: tool-equipped `twine`/`pipx`/`uvx` smoke, release-owner approval, registry credentials, advisory option/proof, version execution decision, final release-execution-time SHA proof, and rollback/yank proof remain blocked.
- Next safe slice: re-run the same preflight in a clean environment where `twine`, `pipx`, and `uvx` are already available, or record the release-owner advisory decision before any release execution packet.


## 2026-05-17 v0.10.0-beta Tool-smoke Execution
- Repo: JustTyping
- Lane: release readiness -> no-upload package smoke
- User-facing flow: package build -> package-smoke rehearsal -> release-owner blocker matrix.
- Slice type: Evidence
- Before: PR #72 correctly recorded this workstation's clean base environment as `BLOCKED_TOOL_MISSING`, so `twine`, `pipx`, and `uvx` package smokes remained `NOT RUN`.
- Root cause: the base environment lacked release smoke tools; actual blocker reduction needed a tool-equipped no-upload environment while preserving the no-upload and no-release boundaries.
- Change made: created `docs/reports/v0.10.0-beta-tool-smoke-execution.md`, updated release decision/checklist/readiness/version/exact-SHA/advisory/rollback truth surfaces, and kept the earlier preflight packet as historical missing-tool evidence.
- Validation run: `python -m build --sdist --wheel --outdir <temp-dist>`; `python scripts/package_smoke_rehearsal.py --wheel <temp-wheel> --sdist <temp-sdist> --json`; focused release-truth docs tests.
- Evidence: temporary artifacts were `qa_z-0.9.8a0-py3-none-any.whl` and `qa_z-0.9.8a0.tar.gz`; `scripts/package_smoke_rehearsal.py` returned `package smoke rehearsal passed`, `exit_code=0`, `twine_check=PASS`, `pipx_wheel_help=PASS`, `uvx_wheel_help=PASS`, and `registry_upload_executed=false`.
- Gate delta: tool-equipped no-upload package smoke is now `PASS` local evidence. Release execution remains `NO-GO`; no tag, GitHub Release, package upload, deploy, version bump, registry credential use, or bot comment was performed.
- User impact: release owners can stop treating tool-smoke availability as unresolved and focus on approval, advisory, credentials, version, final SHA proof, and rollback/yank decisions.
- Remaining blocker: release-owner approval and selected release path, Next.js/PostCSS advisory option/proof, registry credentials, version execution decision, final release-execution-time SHA proof, and rollback/yank proof remain blocked.
- Next safe slice: record the release-owner advisory decision path, or generate final proof only after a release-candidate SHA freeze.


## 2026-05-18 v0.10.0-beta Package Publish Path Decision

- Repo: JustTyping
- Lane: package publish readiness -> release-owner path decision
- User-facing flow: no-release decision -> no-upload smoke proof -> package publish path decision.
- Slice type: Evidence
- Before: no-release decision exists, tool-equipped no-upload smoke is `PASS`, and package publish path selection remained undecided.
- Root cause: release owners could confuse local no-upload smoke with TestPyPI/PyPI publish proof, live `pipx install qa-z` availability, version execution, or approval to upload packages.
- Change made: added `docs/reports/v0.10.0-beta-package-publish-path-decision.md`, linked package publish plan/no-release/checklist/version truth surfaces, added focused docs tests, and routed the packet through worktree commit-plan ownership.
- Validation run: `python -m pytest tests/test_beta_package_publish_path_decision_docs.py -q`; linked beta docs, public docs truth, worktree plan, hygiene, Ruff, and diff whitespace checks.
- Evidence: the focused docs guard failed first on the missing packet and links, then passed after the packet and links were added. The packet records `No release yet`, `v0.10.0-beta` not released, current package metadata `0.9.8a0`, `registry_upload_executed=false`, future-only `pipx install qa-z` / `uv tool install qa-z`, blocked `twine upload`, and explicit non-actions.
- Gate delta: release-owner path options are now separated from release execution. No TestPyPI/PyPI upload, tag, GitHub Release, deploy, version bump, credential load, bot comment, or README growth slice change was performed.
- User impact: release owners can choose `No release yet`, `TestPyPI rehearsal only`, `TestPyPI publish`, `PyPI beta publish`, `metadata-only version PR`, or `GitHub prerelease only` without mistaking the decision packet for publish approval.
- Remaining blockers: selected path, release-owner approval, registry credentials, version execution decision, final release-execution-time SHA proof, advisory option/proof, and rollback/yank execution proof remain blocked.
- Next safe slice: release owner chooses `TestPyPI rehearsal only`, `PyPI beta publish`, or another explicit path in a separate approved packet; README first-screen growth remains a separate PR.


## 2026-05-17 Historical Alpha Proof Packet Validator Stabilization
- Repo: JustTyping
- Lane: release truth -> historical proof validation
- User-facing flow: proof packet -> `alpha_release_truth_validator --proof-head-from-packet` -> strict worktree plan.
- Slice type: Contract
- Before: `--proof-head-from-packet` read the packet proof SHA but still defaulted branch, `origin/main`, and ahead-count facts from the current worktree, so a later merge or branch-specific worktree could make a truthful historical packet fail validation.
- Root cause: packet mode was only partially historical; it treated proof head as packet-owned but treated the rest of the proof facts as live git state unless every value was manually overridden.
- Change made: added packet fact extraction for source HEAD, branch, remote `main`, and ahead count; packet mode now uses those historical values by default while preserving explicit CLI overrides and still reporting the current local HEAD separately.
- Validation run: `python -m pytest tests/test_alpha_release_truth_validator.py -q`; `python scripts/alpha_release_truth_validator.py --proof-head-from-packet --json --output .qa-z/tmp/alpha-release-truth-validator-tool-smoke.json`; `python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting`; `python scripts/alpha_release_gate.py --allow-dirty --json`; `python -m ruff check scripts/alpha_release_truth_validator.py tests/test_alpha_release_truth_validator.py`; `python -m ruff format --check scripts/alpha_release_truth_validator.py tests/test_alpha_release_truth_validator.py`.
- Evidence: the focused validator pack passed `26`; the live historical packet validator passed `20/20` and reported packet facts `head=1ede65172f770c66159b2cc5e9e7d4f2063bf634`, `branch=main`, `origin_main=b9a2504ad07d15776eb900f07d6ee83f22ef9076`, `ahead_count=1`, and current local HEAD `b63d1f43f6a194e2c9302238a7557760e5cc492b`; strict worktree plan returned `status=ready`, `changed_path_count=27`, and zero generated, cross-cutting, report-path, shared patch-add, multi-batch, unassigned, product-decision, or attention blockers; full alpha release gate passed `33/33`, including `1869` pytest tests, Ruff, mypy, QA-Z fast/deep/benchmark, build, and artifact smoke.
- Gate delta: historical alpha packet validation is stable across current branch/origin drift again. This does not approve release execution, package upload, tag creation, GitHub Release creation, deploy, version bump, bot comment, or credential use.
- User impact: operators can run the commit-safe validator after later worktree or main movement without rewriting historical proof packets just to match live git state.
- Remaining blocker: release-owner approval and selected release path, Next.js/PostCSS advisory option/proof, registry credentials, version execution decision, final release-execution-time SHA proof, and rollback/yank proof remain blocked.
- Next safe slice: record the release-owner advisory decision path, or generate final proof only after a release-candidate SHA freeze.


## 2026-05-18 GitHub Action Adoption Docs
- Repo: JustTyping
- Lane: growth -> GitHub Action adoption
- User-facing flow: README demo -> copy-paste PR gate -> Job Summary/artifacts -> optional SARIF.
- Slice type: Flow / Evidence
- Before: README showed a minimal workflow and the action doc described the contract, but the adoption path was not organized around a fast three-step PR-gate setup.
- Root cause: visitors could understand the demo proof without immediately seeing the smallest safe GitHub Actions path for their own pull requests.
- Change made: tightened the README GitHub Action section, reorganized `docs/github-action.md` into minimal PR gate, PR summary/artifacts, and SARIF opt-in steps, and added tests for minimal permissions, bot-comment opt-in, SARIF opt-in, and no PyPI live install claim.
- Validation run: `python -m pytest tests/test_github_workflow.py -q`; `python -m pytest tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_current_truth.py tests/test_github_actions_summary_docs.py -q`; `python -m pytest -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_github_workflow.py tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py`; `python -m ruff format --check tests/test_github_workflow.py tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py`; `git diff --check`; `python -m qa_z --help`.
- Evidence: GitHub workflow docs tests passed `23`; launch-growth and public current-truth tests passed `34`; current-truth and GitHub Actions summary docs tests passed `45`; full pytest passed `1877`; text hygiene, Ruff check, Ruff format check, diff whitespace, and QA-Z help all passed. Generated `.pytest_cache` and `.ruff_cache` were removed.
- Gate delta: adoption docs now tell visitors to start with `contents: read` and `actions: read`, add `security-events: write` only for SARIF upload, and keep PR/bot comments opt-in. No PyPI availability, live `pipx install qa-z`, package publish, tag, GitHub Release, deploy, version bump, or generated `.qa-z/**` source artifact was added.
- User impact: visitors can move from the README demo to a minimal QA-Z PR gate in about five minutes without broad default permissions.
- Remaining blocker: official PyPI/TestPyPI install path still requires release-owner approval and separate release execution.
- Next safe slice: TestPyPI rehearsal path selection, or a small GitHub Actions troubleshooting FAQ once adoption docs receive review feedback.


## 2026-05-20 GitHub Action Troubleshooting FAQ
- Repo: JustTyping
- Lane: growth -> GitHub Action adoption troubleshooting
- User-facing flow: README demo -> minimal PR gate -> failed workflow diagnosis -> Job Summary/artifacts.
- Slice type: Flow / Evidence
- Before: the GitHub Action docs explained the 5-minute setup, minimal permissions, Job Summary/artifacts, and SARIF opt-in, but did not give a focused FAQ for first-run failures.
- Root cause: new adopters could respond to ordinary setup failures by adding broad permissions, expecting bot comments, or looking for PyPI install commands that are not live yet.
- Change made: added a troubleshooting FAQ covering minimal workflow permissions, SARIF permission failures, opt-in PR comments, verdict/repair/artifact locations, Semgrep/deep CI drift, profile/adapter mismatches, and the GitHub-source install boundary; linked it from the README and pinned the wording with public-doc tests.
- Validation run: `python -m pytest tests/test_github_workflow.py -q`; `python -m pytest tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_github_workflow.py tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py`; `python -m ruff format --check tests/test_github_workflow.py tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py`; `git diff --check`; `python -m qa_z --help`.
- Evidence: GitHub workflow docs tests passed `24`; launch-growth and public current-truth tests passed `34`; text hygiene passed; Ruff check passed; Ruff format check passed after formatting touched tests; diff whitespace check passed; QA-Z help rendered.
- Gate delta: GitHub Action troubleshooting is now documented and regression-tested without changing the minimal workflow permissions, enabling bot comments by default, claiming PyPI availability, or running release actions.
- User impact: users can debug a failed minimal QA-Z PR gate without broad default permissions, bot comments by default, or PyPI live install claims.
- Remaining blocker: TestPyPI/PyPI release-owner path selection remains blocked until separately approved.
- Next safe slice: TestPyPI rehearsal path selection after this FAQ PR is reviewed and merged.


## 2026-05-20 v0.10.0-beta TestPyPI Rehearsal Approval
- Repo: JustTyping
- Lane: package publish readiness -> TestPyPI rehearsal approval
- User-facing flow: no-release decision -> no-upload smoke proof -> selected TestPyPI rehearsal path.
- Slice type: Evidence / Contract
- Before: package publish paths were documented, no-upload tool smoke had passed, and the package publish path matrix listed TestPyPI rehearsal as an option, but there was no selected next path after GitHub Action onboarding closed.
- Root cause: release owners could confuse choosing a next review path with approval to upload unless the decision packet separated rehearsal selection from execution approval.
- Change made: selected TestPyPI rehearsal as the next review path in `docs/reports/v0.10.0-beta-testpypi-rehearsal-approval.md`, linked the packet from package publish, no-release, and release checklist docs, and kept actual upload blocked.
- Validation run: `python -m pytest tests/test_beta_testpypi_rehearsal_approval_docs.py -q`; linked package-publish/no-release/release-checklist docs tests; public current-truth docs tests; worktree commit-plan routing tests; strict worktree plan; text hygiene; Ruff check/format; diff whitespace check.
- Evidence: the focused approval docs guard passed `5`; linked beta release docs passed `16`; public current-truth docs passed `16`; worktree commit-plan routing tests passed `75`; strict worktree plan returned `status=ready`, `generated_artifact_count=0`, `cross_cutting_count=0`, `report_path_count=0`, and `unassigned_source_path_count=0`; text hygiene, Ruff, and diff whitespace checks passed.
- Gate delta: no upload executed; release execution remains `NO-GO`; package metadata remains `0.9.8a0`; `registry_upload_executed=false` remains the boundary.
- User impact: release owners now have one clear next path without mistaking it for TestPyPI/PyPI publish approval.
- Remaining blocker: execution approval, registry credentials, version execution decision, final SHA proof, rollback/yank policy, advisory option/proof, and final execution packet remain blocked.
- Next safe slice: prepare actual TestPyPI execution packet only after approval/credentials/final proof exist, or continue README/launch content improvements while upload remains blocked.


## 2026-05-21 v0.10.0-beta TestPyPI Rehearsal Execution Packet
- Repo: JustTyping
- Lane: package publish readiness -> TestPyPI rehearsal execution packet
- User-facing flow: selected TestPyPI rehearsal path -> upload stop rule -> final approval blockers.
- Slice type: Evidence / Contract
- Before: PR #81 selected TestPyPI rehearsal as the next review path, but the pre-upload execution packet and stop rule were not yet recorded.
- Root cause: release owners need one packet that separates local proof preparation from actual registry upload before any TestPyPI credentials or `twine upload` command can be considered.
- Change made: added `docs/reports/v0.10.0-beta-testpypi-rehearsal-execution-packet.md`, linked it from approval/path/checklist/package-publish docs, and pinned the no-upload contract with focused tests.
- Validation run: focused execution-packet docs test; linked approval/path docs tests; public current-truth docs test; strict worktree commit-plan; public text hygiene; Ruff check/format; diff whitespace check.
- Evidence: current `origin/main` was `0c4288d98f8826e891ab8cd46fd5157000cadff0`; main CI and Public Raw Hygiene were success; package metadata stayed `0.9.8a0`; PyPI/TestPyPI JSON endpoints returned HTTP 404; no `v0.10.0-beta*` tag or release existed.
- Gate delta: no upload executed; `registry_upload_executed=false`; `twine upload` remains blocked; release execution remains `NO-GO`; package publish proof still does not exist.
- User impact: release owners now have an upload stop-rule packet before TestPyPI rehearsal can move to execution approval.
- Remaining blocker: release-owner execution approval, `PACKAGE_PUBLISH_ALLOWED=true`, TestPyPI credentials, final SHA proof, rollback/yank execution-time check, advisory proof, generated-artifact cleanup proof, and a final execution packet.
- Next safe slice: only after approval fields and credential boundary are present, regenerate final SHA proof and rerun no-upload package smoke for the frozen candidate SHA.


## 2026-05-22 Launch Kit Growth Slice
- Repo: JustTyping
- Lane: launch growth / repo-local launch kit
- User-facing flow: GitHub visitor or maintainer -> launch kit -> source install, auth-bug demo, 5-minute PR gate, draft outreach copy.
- Slice type: Cleanup / Evidence
- Before: launch post, social preview, action docs, demo plan, and package publish docs existed separately, but there was no single draft-only launch kit that tied the current demo story to the no-PyPI/no-release boundary.
- Root cause: launch-growth copy had been improved incrementally while TestPyPI rehearsal stayed blocked, leaving maintainers without one safe shareable packet for repo-local launch preparation.
- Change made: added `docs/launch/launch-kit.md`, linked it from README and the docs index, and pinned the launch-kit boundary with public current-truth tests.
- Validation run: `python -m pytest tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py -q`; `python -m pytest tests/test_current_truth.py -q`; `python -m pytest tests/test_github_workflow.py -q`; `python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public`; `python -m ruff check tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py tests/test_current_truth.py`; `python -m ruff format --check tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py tests/test_current_truth.py`; `git diff --check`; `python -m qa_z --help`.
- Evidence: launch/public current-truth tests passed `35`; current-truth tests passed `42`; GitHub workflow tests passed `24`; public text hygiene passed; Ruff check passed; Ruff format reported `3 files already formatted`; diff whitespace check passed; QA-Z help rendered.
- Gate delta: no release action; no PyPI/TestPyPI publish; no tag; no GitHub Release; no deploy; no `pyproject.toml` bump; no registry credentials; no external posts; no bot comments; no generated `.qa-z/**` source artifacts.
- User impact: maintainers get one draft-only launch kit with product description, target users, auth-bug demo story, GitHub source install, minimal GitHub Action path, social drafts, launch order, FAQ, and explicit no-PyPI live claim.
- Remaining blocker: release-owner approval, TestPyPI/PyPI credentials, final execution proof, and external posting remain blocked.
- Next safe slice: turn repeated launch feedback into README/FAQ edits, or continue only with repo-local adoption docs while release execution stays `NO-GO`.


## 2026-05-26 v0.10.0-beta Installed-Package Runtime Smoke
- Repo: JustTyping
- Lane: package publish readiness -> installed-package runtime reliability
- User-facing flow: install artifact -> demo auth-bug -> guard -> repair-prompt -> verify.
- Slice type: Evidence / Contract
- Before: metadata-only `0.10.0b0` readiness documented local build and twine metadata checks, but did not prove the built wheel and sdist worked after installation into fresh virtual environments.
- Root cause: PyPI readiness needs installed-package runtime evidence, not only source-tree or editable-checkout behavior.
- Change made: added `scripts/installed_package_smoke.py`, covered it with `tests/test_installed_package_smoke.py`, recorded local PASS evidence in `docs/reports/v0.10.0-beta-installed-package-smoke.md`, and linked the proof from PyPI readiness and package publish docs.
- Validation run: `python scripts/installed_package_smoke.py --json`; focused installed-package smoke tests; PyPI readiness docs tests; text hygiene, Ruff, format, and diff checks.
- Evidence: local installed-package smoke passed for both `qa_z-0.10.0b0-py3-none-any.whl` and `qa_z-0.10.0b0.tar.gz`; both fresh venvs passed CLI help, module help, auth-bug demo resource loading, doctor, guard, repair-prompt, and deterministic verify comparison.
- Gate delta: no PyPI/TestPyPI upload, `twine upload`, tag, GitHub Release, deploy, version bump, live PyPI install claim, registry credential use, or generated source artifact commit occurred.
- User impact: release owners can now distinguish package metadata readiness from installed-package runtime readiness before any production PyPI publish decision.
- Remaining blocker: production PyPI publish remains blocked until separate owner approval, selected registry method, frozen SHA proof, remote CI/public raw proof, and release execution packet exist.
- Next safe slice: improve `qa-z doctor` installed-environment diagnostics so failed installs explain location, package version, config, Semgrep, demo-resource, and writable-runtime-directory state.


## 2026-05-27 v0.13 Evidence Summary UX
- Repo: JustTyping
- Lane: local run evidence -> first-read evidence navigator
- User-facing flow: run QA-Z -> read verdict, top risks, artifact paths, repair prompt path, verify path, and next command.
- Slice type: Flow / Evidence
- Before: users had to know whether to open `review/review.md`, `guard/verdict.json`, `github-summary.md`, `repair/prompt.md`, or `verify/report.md` first after a run.
- Root cause: QA-Z already wrote many deterministic artifacts, but there was no local first-read command that summarized verdict, risks, paths, and missing-evidence guidance.
- Change made: added `qa-z summary --from-run latest` with human, JSON, Markdown, and optional output modes; added stale/missing run handling; documented the evidence summary workflow and schema.
- Validation run: targeted evidence summary tests, adjacent review/GitHub summary/verification tests, public docs current-truth tests, text hygiene, Ruff, format, diff whitespace, and CLI help.
- Evidence: `tests/test_evidence_summary.py` covers full evidence, no run, missing deep evidence, repair prompt guidance, verify guidance, stale latest manifest fallback, human output, and GitHub summary consistency.
- Gate delta: local evidence readability improved without changing artifact producers, publishing packages, bumping versions, deploying, tagging, creating releases, or claiming live PyPI install.
- User impact: maintainers get one local command for the first post-run read and can jump directly to the next deterministic command.
- Remaining blocker: GitHub Actions job summary UX still depends on the separate `github-summary` command and workflow wiring.
- Next safe slice: surface the same local evidence navigator in GitHub Actions job summaries/artifacts while keeping comments and SARIF upload opt-in.


## 2026-05-27 v0.14 Repair Verify Workflow Productization
- Repo: JustTyping
- Lane: local repair evidence -> deterministic post-repair verification.
- User-facing flow: guard verdict -> repair prompt -> external repair -> `qa-z verify --from-run latest` -> improved/unchanged/worse evidence.
- Slice type: Flow / Evidence
- Before: verify supported explicit baseline/candidate comparison and rerun mode, but the common local repair loop still required users to know candidate-run mechanics.
- Root cause: the repair prompt and verify command were individually useful, but the product path between them was not encoded as the shortest safe command sequence.
- Change made: added `--from-run` as the first-class verify baseline alias, defaulted it to rerun candidate evidence when used alone, improved verify stdout/JSON with deltas and next actions, added forbidden shortcuts plus verify follow-up to Codex handoffs, aligned the auth-bug demo and installed-package smoke with a deterministic fixed-file verify path, and documented the loop.
- Validation run: focused repair/verify workflow tests, repair prompt and verification suites, demo guard action package tests, public docs current-truth tests, text hygiene, Ruff, format, diff whitespace, CLI help, and an auth-bug demo repair/verify smoke.
- Evidence: `tests/test_repair_verify_workflow.py` covers `verify --from-run latest`, worse/regressed human output, Codex handoff guidance, and the deterministic auth-bug fixed-file verify path.
- Gate delta: repair verification is easier to run locally without changing QA-Z's boundary; QA-Z still does not apply target-repository repairs, call live model APIs, publish packages, deploy, create tags, or post externally.
- User impact: users can go from a blocked guard verdict to a repair prompt and then to a clear verify result with one follow-up command after applying the fix.
- Remaining blocker: GitHub Action workflows still need separate wiring to expose the same repair/verify loop as job-summary guidance.
- Next safe slice: productize GitHub Actions repair/verify summary artifacts while keeping SARIF upload, PR comments, and external posting opt-in.


## 2026-05-27 v0.15 GitHub Action Runtime Hardening
- Repo: JustTyping
- Lane: GitHub Actions gate -> runtime diagnostics and safe configuration.
- User-facing flow: pull request workflow -> input validation -> guard evidence -> Job Summary/artifacts -> repair/verify next commands.
- Slice type: Flow / Evidence / Contract
- Before: action input validation was thin, the older full fast/deep action always attempted SARIF upload, and missing summary artifacts produced sparse fallback text.
- Root cause: CI users needed actionable failure messages and permission guidance directly in logs and Job Summary output, not only in docs.
- Change made: added action input validation with supported values and docs links; kept SARIF upload opt-in in the reusable action; validated the optional PR comment flag; expanded GitHub summary rendering with verdict, top blocked reason, artifact existence, SARIF permission guidance, and repair/verify next commands; documented the runtime boundary.
- Validation run: focused GitHub workflow and summary tests, public current-truth docs, public text hygiene, Ruff, format, diff whitespace, and QA-Z help.
- Evidence: `tests/test_github_workflow.py` and `tests/test_github_summary*.py` cover invalid action inputs, SARIF opt-in, comment opt-in validation, missing-run guidance, and Job Summary next commands.
- Gate delta: GitHub Action failures are easier to diagnose without adding broad permissions, enabling bot comments by default, publishing packages, bumping versions, creating tags/releases, or deploying.
- User impact: maintainers can fix bad `profile`, `deep`, `adapter`, `run-dir`, SARIF, and comment settings from the job log or summary without guessing which artifact to open first.
- Remaining blocker: live hosted action release and production PyPI install remain separate release-owner decisions.
- Next safe slice: add a deterministic action-summary fixture or dry-run harness that exercises the fallback summary text without requiring live GitHub Actions.


## 2026-05-27 v0.16 Scorecard Productization
- Repo: JustTyping
- Lane: local readiness evidence -> user-facing scorecard.
- User-facing flow: repository maintainer -> `qa-z scorecard` -> readiness dimensions, evidence pointers, warnings, and next commands.
- Slice type: Evidence / Contract
- Before: config validation, benchmark corpus state, Semgrep availability, installed-package smoke evidence, GitHub Action wiring, and latest run evidence were inspectable only through separate docs, commands, and files.
- Root cause: QA-Z had useful readiness signals, but no read-only local command that assembled them into a single coarse readiness view without running expensive workflows.
- Change made: added `qa-z scorecard` with human, JSON, Markdown, and optional output modes; added stable dimension schema; documented the local scorecard separately from the OpenSSF Scorecard workflow.
- Validation run: targeted scorecard tests and runtime command seam tests are passing; full slice validation is recorded in the PR closeout.
- Evidence: `tests/test_scorecard.py` covers healthy, missing-config, missing-Semgrep, stable JSON schema, human next actions, and no generated `.qa-z` artifact creation.
- Gate delta: no release, PyPI/TestPyPI upload, `twine upload`, version bump, tag, deploy, live PyPI install claim, benchmark result artifact, or generated runtime artifact was added.
- User impact: maintainers can see which QA-Z coverage surfaces are ready, warning, blocked, not configured, or unknown from one local command.
- Remaining blocker: production PyPI publish and hosted release surfaces remain separate owner-approved release decisions.
- Next safe slice: add a deterministic action-summary dry-run harness that exercises GitHub Action fallback summary text without live GitHub Actions.


## 2026-05-27 v0.17 Multi-Agent Adapter Quality Pack
- Repo: JustTyping
- Lane: repair handoff -> multi-agent executor prompts.
- User-facing flow: failed QA-Z run -> `qa-z repair-prompt --adapter <tool>` -> evidence-backed external repair -> `qa-z verify`.
- Slice type: Flow / Evidence
- Before: normalized repair handoff data existed, but only Codex and Claude Markdown were first-class adapter artifacts and the common merge-safety sections were not enforced across other tools.
- Root cause: QA-Z's core boundary is model-agnostic, but adapter presentation had not caught up with the broader Codex, Claude Code, Cursor, aider, OpenHands, and human-review workflows.
- Change made: added a shared adapter renderer registry, expanded `repair-prompt`, guard, and repair-session artifacts to write `codex.md`, `claude.md`, `cursor.md`, `aider.md`, `openhands.md`, and `generic.md`, and documented the shared adapter contract.
- Validation run: focused repair-handoff and repair-prompt tests are passing; full slice validation is recorded in the PR closeout.
- Evidence: `tests/test_repair_handoff.py` covers supported adapter outputs, required merge-safety sections, unknown adapter failure, selected adapter stdout, and artifact writes.
- Gate delta: no external agent API call, live model call, release, deploy, package upload, version bump, live PyPI install claim, or generated runtime artifact was added.
- User impact: operators can hand QA-Z repair evidence to the coding tool they actually use while keeping QA-Z as the deterministic merge-safety judge.
- Remaining blocker: live executor orchestration remains out of scope; adapter files are local handoff prompts only.
- Next safe slice: add a deterministic action-summary dry-run harness that exercises GitHub Action fallback summary text without live GitHub Actions.


## 2026-05-27 v0.18 Production PyPI GO-NO-GO Packet
- Repo: JustTyping
- Lane: package publish readiness -> production PyPI release gate.
- User-facing flow: release owner -> approval flags and credential boundary -> build/twine/install smoke -> README install transition only after proof.
- Slice type: Evidence / Contract
- Before: production PyPI install conversion had local readiness docs and installed-package smoke, but no v0.18 packet tying the required approval flags, credential boundary, current PyPI absence, exact artifact proof, and README transition status together.
- Root cause: production PyPI publish is an external release execution gate; missing approval must still leave useful repo-local proof instead of stopping at a blocker sentence.
- Change made: added `docs/reports/v0.18-production-pypi-go-no-go.md`, linked it from package publish/readiness/release-note truth surfaces, recorded `NO_GO_MISSING_APPROVAL` with `NO_GO_MISSING_CREDENTIALS` as secondary, and pinned the no-upload contract with docs tests.
- Validation run: production PyPI state checks, `python -m build --sdist --wheel`, `python -m twine check` on exact artifacts, `python scripts/installed_package_smoke.py --json`, focused release docs tests, public current-truth docs tests, launch package docs tests, text hygiene, Ruff, format, diff whitespace, and CLI help.
- Evidence: production PyPI simple index returned 404 and `python -m pip index versions qa-z` found no distribution; local build produced `qa_z-0.10.0b0-py3-none-any.whl` and `qa_z-0.10.0b0.tar.gz`; `twine check` passed after updating the local checker dependency; installed-package smoke passed for wheel and sdist with `registry_upload_executed=false`.
- Gate delta: no production PyPI upload, TestPyPI upload, `twine upload`, tag, GitHub Release, deploy, version bump, credential print/commit, README live PyPI install claim, or generated artifact commit occurred.
- User impact: release owners now have a concrete no-go packet that says exactly which external gate remains while preserving local package readiness evidence.
- Remaining blocker: production PyPI release-owner approval flags, PyPI credential or Trusted Publishing proof, final frozen release SHA, upload execution, post-upload install smoke, and README install transition remain blocked.
- Next safe slice: prepare a trusted-publishing CI proof packet or rerun v0.18 as an upload execution only after all required approval flags and credential proof are present.


## 2026-05-27 v0.19 Production PyPI Trusted Publishing & Release Governance
- Repo: JustTyping
- Lane: production PyPI governance -> approval and credential boundary.
- User-facing flow: release owner -> method decision -> protected publish workflow design -> rollback/yank playbook -> production publish remains blocked.
- Slice type: Contract / Evidence
- Before: v0.18 recorded production PyPI as blocked on approval and credential/trusted-publishing proof, but the future production path still needed one governance packet covering method choice, protected workflow shape, approval flags, and rollback/yank execution stance.
- Root cause: release execution should not start from an upload command; it needs a reviewed governance packet that separates approval, trust configuration, workflow permissions, install transition, and incident response.
- Change made: added v0.19 governance, Trusted Publishing design, non-active workflow draft, rollback/yank playbook, current-truth links, and docs tests while preserving the no-upload boundary.
- Validation run: focused v0.19 governance docs test first failed on missing files, then passed after adding the packet. Full requested validation is recorded in the PR closeout.
- Evidence: v0.19 docs record production PyPI status as not published, package metadata `0.10.0b0`, GitHub source tag `v0.9.9-alpha` as the current public install, required approval flags, required proof, Trusted Publishing as the recommended default, manual token fallback only, and explicit no-upload non-actions.
- Gate delta: no PyPI/TestPyPI upload, `twine upload`, tag, GitHub Release, deploy, credential print/commit, README live PyPI install claim, or generated artifact commit occurred.
- User impact: release owners can review the future production PyPI path without exposing credentials or accidentally turning readiness proof into release execution.
- Remaining blocker: production PyPI remains blocked until required approval flags, Trusted Publishing or credential proof, final SHA proof, refreshed build/hash/`twine check`, upload proof, install smoke, README transition proof, and rollback/yank stance are present in a separate execution packet.
- Next safe slice: v0.20 production PyPI publish-execution gate, only after the release owner explicitly supplies the required approval flags and trust/credential proof.
