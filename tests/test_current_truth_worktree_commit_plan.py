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
            "python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json"
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
        assert "repository" in text
    assert "--untracked-files=all" in commit_plan
    assert "shared_patch_add_paths" in commit_plan
    assert "src/qa_z/commands/command_registration.py" in commit_plan
    assert "src/qa_z/commands/runtime.py" in commit_plan
    assert "tests/test_runtime_commands.py" in commit_plan
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

        assert "generated_exclude_count" in text
        assert "Global attention reasons:" in text
        assert "attention_reason_count" in text
        assert "global_attention_reason_count" in text
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
        assert "git_add_patch_command" in text
        assert "batch filters preserve generated_artifacts_present" in text
        assert "cross_cutting_paths_present" in text
        assert "output write failures return exit code `2`" in text


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
