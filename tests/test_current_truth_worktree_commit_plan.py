from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_current_truth_anchors() -> str:
    return (ROOT / "docs" / "current-truth-maintenance-anchors.md").read_text(
        encoding="utf-8"
    )


def test_docs_document_worktree_commit_plan_helper() -> None:
    readme = read_current_truth_anchors()
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")
    commit_plan = (ROOT / "docs" / "reports" / "worktree-commit-plan.md").read_text(
        encoding="utf-8"
    )
    release_handoff = (
        ROOT / "docs" / "releases" / "v0.9.8-alpha-publish-handoff.md"
    ).read_text(encoding="utf-8")
    release_notes = (ROOT / "docs" / "releases" / "v0.9.8-alpha.md").read_text(
        encoding="utf-8"
    )

    for text in (readme, commit_plan):
        assert (
            "python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting --output .qa-z/tmp/worktree-commit-plan.json"
            in text
        )
        assert "unassigned_source_paths" in text
        assert "generated_artifact_paths" in text
        assert "generated_local_only_paths" in text
        assert "generated_local_by_default_paths" in text
        assert "cross_cutting_paths" in text
        assert "--summary-only --json" in text
        assert "changed_batches" in text
        assert "shared_patch_add_paths" in text
        assert "cross_cutting_groups" in text
        assert "product_decision_paths" in text
        assert "product_decision_groups" in text
        assert "repository" in text
    assert "--untracked-files=all" in commit_plan
    assert "shared_patch_add_paths" in commit_plan
    assert "src/qa_z/commands/command_registration.py" in commit_plan
    assert "src/qa_z/commands/runtime.py" in commit_plan
    assert "src/qa_z/operator_commands.py" in commit_plan
    assert "tests/test_operator_commands.py" in commit_plan
    assert "tests/test_runtime_commands.py" in commit_plan
    assert (
        "python -m pytest tests/test_self_improvement.py "
        "tests/test_self_improvement_inspection.py "
        "tests/test_self_improvement_selection_output.py "
        "tests/test_repair_signal_inputs.py "
        "tests/test_artifact_consistency_discovery.py tests/test_cli.py -q"
        in commit_plan
    )
    assert (
        "python -m pytest tests/test_autonomy.py "
        "tests/test_autonomy_action_cleanup.py "
        "tests/test_autonomy_action_context.py tests/test_cli.py -q" in commit_plan
    )
    for text in (readme, release_handoff, release_notes):
        assert "worktree commit-plan" in text
        assert "evidence.worktree_commit_plan" in text
        assert "--strict-worktree-plan" in text
        assert "--fail-on-generated --fail-on-cross-cutting" in text
    for text in (readme, release_handoff, schema):
        assert "--fail-on-generated" in text
        assert "--fail-on-cross-cutting" in text
        assert "strict_mode" in text
        assert "worktree generated artifact split mismatch" in text
        assert "worktree patch-add group mismatch" in text
        assert "batch_count" in text
        assert "generated_local_only_count" in text
        assert "generated_local_by_default_count" in text
        assert "product_decision_path_count" in text
        assert "product_decision_group_count" in text

        assert "generated_exclude_count" in text
        assert "Global attention reasons:" in text
        assert "attention_reason_count" in text
        assert "global_attention_reason_count" in text
        assert "selected_batch_empty" in text
        assert "Attention reasons:" in text
        assert "Attention reasons are de-duplicated" in text
        assert "Next actions are de-duplicated" in text
        assert "Next commands are de-duplicated" in text
        assert "attention_reasons" in text
        assert "strict_worktree_plan" in text
    for text in (readme, schema, commit_plan):
        assert "cross_cutting_group_count" in text
        assert "public_docs_contract" in text
        assert "command_router_spine" in text
        assert "current_truth_guards" in text
        assert "command_surface_tests" in text
        assert "status_reports" in text
        assert "paths_truncated_count" in text
    assert "patch_add_groups=" in readme
    assert "patch_add_groups=" in release_handoff
    for text in (readme, schema):
        assert "git_add_command" in text
        assert "git_add_command_text" in text
        assert "git_add_patch_command" in text
        assert "git_add_patch_command_text" in text
        assert "patch_command_text" in text
        assert "batch filters preserve generated_artifacts_present" in text
        assert "cross_cutting_paths_present" in text
        assert "product_decision_paths_present" in text
        assert "output write failures return exit code `2`" in text


def test_docs_warn_planner_artifact_writers_are_serial() -> None:
    readme = read_current_truth_anchors()
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")

    assert "Run local planner artifact writers serially" in readme
    assert "local planner artifact writers serially" in schema


def test_alpha_rc_packet_keeps_deferred_scope_and_remote_proof_explicit() -> None:
    commit_plan = (ROOT / "docs" / "reports" / "worktree-commit-plan.md").read_text(
        encoding="utf-8"
    )

    assert "## Alpha Release-Candidate Decision Packet - 2026-05-12" in commit_plan
    assert "`status=ready` with `changed_batch_count=2`" in commit_plan
    assert "`report_path_count=0`" in commit_plan
    assert "`shared_patch_add_count=0`" in commit_plan
    assert "`product_decision_path_count=0`" in commit_plan
    assert "`cross_cutting_count=0`" in commit_plan
    assert "`cross_cutting_group_count=0`" in commit_plan
    assert "`release_scope_decision_path_count=25`" in commit_plan
    assert "`approved_alpha_support_path_count=0`" in commit_plan
    assert "`deferred_alpha_scope_path_count=25`" in commit_plan
    assert "owned by the alpha release closure batch" in commit_plan
    assert "`alpha release gate passed`, `28/28`" in commit_plan
    assert (
        "python scripts\\alpha_release_truth_validator.py --proof-head-from-packet --json"
        in commit_plan
    )
    assert "proof_branch=codex/alpha-rc-1ede65172f77-20260513" in commit_plan
    assert "current_head_remote_proof=local_only_not_remote_visible" in commit_plan
    assert "`release_path_state=local_only_remote_preflight`" in commit_plan
    assert "Deferred Marketing/X packet:" in commit_plan
    assert "Deferred paths are `marketing/x/**` and `tests/test_x_automation.py`" in (
        commit_plan
    )
    assert "Do not stage Marketing/X source" in commit_plan
    assert "Deferred Claude compatibility mirror packet:" in commit_plan
    assert "Do not stage, delete, or promote `.claude/**`" in commit_plan
    assert "Remote and publishing proof packet:" in commit_plan
    assert "remote checks stayed skipped" in commit_plan
    assert "Production readiness is not claimed." in commit_plan


def test_alpha_rc_packet_pins_remote_proof_freshness_without_prod_claims() -> None:
    commit_plan = (ROOT / "docs" / "reports" / "worktree-commit-plan.md").read_text(
        encoding="utf-8"
    )

    assert "Proof timestamp: `2026-05-13T14:39Z`" in commit_plan
    assert "Source HEAD at proof time: `1ede65172f770c66159b2cc5e9e7d4f2063bf634`" in (
        commit_plan
    )
    assert "`RELEASE_EXECUTION_APPROVED`, `PUSH_ALLOWED`, `TAG_ALLOWED`" in commit_plan
    assert (
        "`python scripts\\alpha_release_preflight.py --skip-remote --json` returned"
        in (commit_plan)
    )
    assert "not a product regression" in commit_plan
    assert "`1723 passed`" in commit_plan
    assert "Read-only remote proof:" in commit_plan
    assert "`repository_http_status=200`" in commit_plan
    assert "`repository_visibility=public`" in commit_plan
    assert "`remote_ref_count=26`" in commit_plan
    assert "`remote_ref_tag_count=2`" in commit_plan
    assert "Remote `main` is" in commit_plan
    assert "`b9a2504ad07d15776eb900f07d6ee83f22ef9076`; tags include" in commit_plan
    assert "GitHub API proof returned repository `qazedhq/qa-z`" in commit_plan
    assert "Latest read-only workflow proof for remote `main`" in commit_plan
    assert "public raw checks captured" in commit_plan
    assert "failed exact-commit raw URLs with HTTP `404`" in commit_plan
    assert "Local proof HEAD is 1 commit ahead of remote `main`" in commit_plan
    assert "`release_path_state=blocked_remote_publish`" in commit_plan
    assert (
        "Skip-remote local preflight remains separate from read-only remote proof"
        in (commit_plan)
    )
    assert "Push/tag/release/package publish: not executed in PROOF_ONLY mode." in (
        commit_plan
    )
    assert "Production readiness: `No`" in commit_plan
    assert "Approval matrix:" in commit_plan
    assert "Publish execution packet:" in commit_plan
    assert (
        'test "$(git rev-parse HEAD)" = "1ede65172f770c66159b2cc5e9e7d4f2063bf634"'
        in commit_plan
    )
    assert (
        "git push -u origin 1ede65172f770c66159b2cc5e9e7d4f2063bf634:refs/heads/codex/alpha-rc-1ede65172f77-20260513"
        in commit_plan
    )
    assert "Expected proof branch output must resolve" in commit_plan
    assert "refs/heads/codex/alpha-rc-1ede65172f77-20260513" in commit_plan
    assert "Direct `main` update needs separate explicit approval" in commit_plan
    assert "git push origin 1ede65172f770c66159b2cc5e9e7d4f2063bf634:main" in (
        commit_plan
    )
    assert "git push origin HEAD:main" not in commit_plan
    assert "Rollback and incident packet:" in commit_plan
    assert (
        "git push origin --delete codex/alpha-rc-1ede65172f77-20260513" in commit_plan
    )
    assert "Production readiness is not claimed." in commit_plan


def test_alpha_rc_packet_documents_package_publish_dry_run_and_preflight_contract() -> (
    None
):
    commit_plan = (ROOT / "docs" / "reports" / "worktree-commit-plan.md").read_text(
        encoding="utf-8"
    )
    package_plan = (ROOT / "docs" / "package-publish-plan.md").read_text(
        encoding="utf-8"
    )
    release_handoff = (
        ROOT / "docs" / "releases" / "v0.9.8-alpha-publish-handoff.md"
    ).read_text(encoding="utf-8")

    assert "Package publish dry-run packet:" in commit_plan
    assert "Package metadata version is `0.9.8a0`" in commit_plan
    assert "`PACKAGE_PUBLISH_ALLOWED` unset" in commit_plan
    assert "python -m build --sdist --wheel" in commit_plan
    assert "python -m twine check dist/*" in commit_plan
    assert "Registry publish remains blocked" in commit_plan

    assert "## Alpha RC package dry-run packet - 2026-05-12" in package_plan
    assert "Package metadata version: `0.9.8a0`" in package_plan
    assert (
        "Current release proof HEAD: `1ede65172f770c66159b2cc5e9e7d4f2063bf634`"
        in package_plan
    )
    assert (
        "No PyPI, TestPyPI, npm, GitHub Packages, or other package registry publish is approved."
        in (package_plan)
    )

    assert "Current quality-mode no-remote rehearsal:" in release_handoff
    assert (
        "python scripts/alpha_release_preflight.py --skip-remote --expected-origin-url https://github.com/qazedhq/qa-z.git --expected-branch main --allow-dirty --skip-release-tag-check --json"
        in release_handoff
    )
    assert "Current-head proof alignment addendum:" in release_handoff
    assert "codex/alpha-rc-1ede65172f77-20260513" in release_handoff
    assert "RELEASE_EXECUTION_APPROVED=true" in release_handoff
    assert "PUSH_ALLOWED=true" in release_handoff
    assert "The bare historical command is retained only as a legacy blocker check" in (
        release_handoff
    )


def test_artifact_schema_documents_runtime_artifact_cleanup_contract() -> None:
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")
    readme = read_current_truth_anchors()

    assert "## Runtime Artifact Cleanup Evidence" in schema
    assert "`kind`: `qa_z.runtime_artifact_cleanup`" in schema
    assert "`mode`: `dry-run` or `apply`" in schema
    assert "`candidates[].policy_bucket`: `local_only` or `local_by_default`" in schema
    assert (
        "`candidates[].status`: `planned`, `deleted`, `skipped_tracked`, or" in schema
    )
    assert "`candidates[].reason`" in schema
    assert "`counts`: status rollup" in schema
    assert "reason" in readme


def test_generated_scratch_verify_summaries_are_excluded_from_live_truth() -> None:
    policy = (ROOT / "docs" / "generated-vs-frozen-evidence-policy.md").read_text(
        encoding="utf-8"
    )
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")
    readme = read_current_truth_anchors()

    assert (
        "Self-inspection only promotes verification summaries from "
        "`.qa-z/runs/*/verify/summary.json` and "
        "`.qa-z/sessions/*/verify/summary.json`" in policy
    )
    assert (
        "ignores nested QA-Z repositories copied under generated scratch roots"
        in policy
    )
    assert (
        "self-inspection verification discovery ignores nested generated scratch repos"
        in readme
    )
    assert (
        "Only root live run/session verification summaries are eligible for "
        "verification backlog candidates" in schema
    )
