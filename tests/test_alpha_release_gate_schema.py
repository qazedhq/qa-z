from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_alpha_release_gate_evidence_is_documented_in_artifact_schema() -> None:
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")

    assert "## Alpha Release Gate Evidence" in schema
    assert "`generated_at`" in schema
    assert "`quick`" in schema
    assert "`with_deps_requested`" in schema
    assert "`evidence.pytest.passed`" in schema
    assert "`evidence.pytest.skipped`" in schema
    assert "`evidence.deep.scan_quality_status`" in schema
    assert "`evidence.deep.scan_quality_warning_count`" in schema
    assert "`evidence.deep.scan_quality_warning_paths`" in schema
    assert "`evidence.deep.scan_quality_check_ids`" in schema
    assert "`evidence.benchmark.snapshot`" in schema
    assert "`evidence.worktree_commit_plan.kind`" in schema
    assert "`evidence.worktree_commit_plan.schema_version`" in schema
    assert "`evidence.worktree_commit_plan.output_path`" in schema
    assert "`evidence.worktree_commit_plan.branch`" in schema
    assert "`evidence.worktree_commit_plan.head`" in schema
    assert "`evidence.worktree_commit_plan.unchanged_batch_count`" in schema
    assert "`evidence.worktree_commit_plan.attention_reasons`" in schema
    assert "`evidence.worktree_commit_plan.attention_reason_count`" in schema
    assert "`evidence.worktree_commit_plan.strict_mode`" in schema
    assert "`local_release_tag_exists`" in schema
    assert "`evidence.gate_failures.<check>.tag`" in schema
    assert "`evidence.local_preflight.repository_target`" in schema
    assert "`evidence.local_preflight.expected_origin_target`" in schema
    assert "`evidence.local_preflight.repository_url`" in schema
    assert "`evidence.local_preflight.expected_origin_url`" in schema
    assert "`evidence.local_preflight.remote_path`" in schema
    assert "`evidence.local_preflight.remote_blocker`" in schema
    assert "`evidence.local_preflight.skip_remote`" in schema
    assert "`worktree_plan_output`" in schema
    assert "`worktree_plan_attention_reasons`" in schema
    assert "`repository_target`" in schema
    assert "`expected_origin_target`" in schema
    assert "`target=`" in schema
    assert "`path=`" in schema
    assert "`blocker=`" in schema
    assert "`target_url=`" in schema
    assert "`origin_url=`" in schema
    assert "`mode=`" in schema
    assert "`remote_path`" in schema
    assert "`remote_blocker`" in schema
    assert "`Target:`" in schema
    assert "`Origin:`" in schema
    assert "`Mode:`" in schema
    assert "`Decision:`" in schema
    assert "`origin_state`" in schema
    assert "`actual_origin_target`" in schema
    assert "`actual_origin_url`" in schema
    assert "`repository_http_status`" in schema
    assert "`repository_probe_state`" in schema
    assert "`repository_probe_generated_at`" in schema
    assert "`repository_visibility`" in schema
    assert "`repository_archived`" in schema
    assert "`repository_default_branch`" in schema
    assert "`remote_ref_count`" in schema
    assert "`remote_ref_head_count`" in schema
    assert "`remote_ref_tag_count`" in schema
    assert "`remote_ref_kinds`" in schema
    assert "`remote_ref_sample`" in schema
    assert "`publish_strategy`" in schema
    assert "`publish_checklist`" in schema
    assert "`publish_checklist_count`" in schema
    assert "`release_path_state`" in schema
    assert "`push_default_branch`" in schema
    assert "`push_release_branch`" in schema
    assert "`remote_preflight`" in schema
    assert "`bootstrap_origin`" in schema
    assert "`origin_current_target=`" in schema
    assert "`origin_current=`" in schema
    assert "`refs=`" in schema
    assert "`head_refs=`" in schema
    assert "`tag_refs=`" in schema
    assert "`ref_kinds=`" in schema
    assert "`ref_sample=`" in schema
    assert "`ready_for_remote_checks`" in schema
    assert "`origin_present`" in schema
    assert "worktree commit-plan `next_actions`" in schema
    assert "top-level `next_commands`" in schema
    assert "older benchmark artifact has only counters" in schema
    assert "`evidence_consistency_errors`" in schema
    assert "`release_evidence_consistency`" in schema
