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
