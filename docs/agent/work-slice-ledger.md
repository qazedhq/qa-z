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
