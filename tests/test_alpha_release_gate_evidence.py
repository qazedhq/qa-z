"""Release evidence tests for the alpha release local gate runner."""

from __future__ import annotations

import json

from tests.alpha_release_gate_test_support import (
    RecordingRunner,
    load_gate_module,
    load_worktree_plan_module,
)


def test_alpha_release_gate_extracts_real_worktree_commit_plan_payload() -> None:
    gate = load_gate_module()
    plan = load_worktree_plan_module()
    payload = plan.analyze_status_lines(
        [
            " M src/qa_z/benchmark.py",
            " M README.md",
            "?? dist/alpha-release-gate.json",
        ]
    )
    payload["output_path"] = "dist/alpha-release-gate.worktree-plan.json"
    payload["repository"] = {"branch": "main", "head": "abc1234"}

    evidence = gate.release_evidence_for_command(
        "worktree_commit_plan",
        json.dumps(payload),
    )

    assert evidence == {
        "kind": "qa_z.worktree_commit_plan",
        "schema_version": 1,
        "output_path": "dist/alpha-release-gate.worktree-plan.json",
        "status": "ready",
        "branch": "main",
        "head": "abc1234",
        "batch_count": 11,
        "changed_path_count": 3,
        "changed_batch_count": 1,
        "unchanged_batch_count": 10,
        "generated_artifact_count": 1,
        "generated_artifact_file_count": 0,
        "generated_artifact_dir_count": 1,
        "generated_local_only_count": 1,
        "generated_local_by_default_count": 0,
        "report_path_count": 0,
        "cross_cutting_count": 1,
        "cross_cutting_group_count": 1,
        "shared_patch_add_count": 1,
        "unassigned_source_path_count": 0,
        "multi_batch_path_count": 0,
        "next_action_count": 2,
        "strict_mode": {
            "fail_on_generated": False,
            "fail_on_cross_cutting": False,
        },
    }


def test_alpha_release_gate_evidence_preserves_cross_cutting_group_count() -> None:
    gate = load_gate_module()
    payload = {
        "kind": "qa_z.worktree_commit_plan",
        "schema_version": 1,
        "status": "attention_required",
        "summary": {
            "changed_batch_count": 0,
            "generated_artifact_count": 0,
            "report_path_count": 1,
            "cross_cutting_count": 0,
            "cross_cutting_group_count": 1,
            "shared_patch_add_count": 1,
            "unassigned_source_path_count": 0,
            "multi_batch_path_count": 0,
        },
        "next_actions": [
            "Patch-add cross-cutting docs, report files, or current-truth tests."
        ],
    }

    evidence = gate.release_evidence_for_command(
        "worktree_commit_plan",
        json.dumps(payload),
    )
    lines = gate.render_release_evidence_lines({"worktree_commit_plan": evidence})

    assert evidence["cross_cutting_group_count"] == 1
    assert any("patch_add_groups=1" in line for line in lines)


def test_alpha_release_gate_preserves_preflight_raw_urls_when_targets_unavailable():
    gate = load_gate_module()

    evidence = gate.release_evidence_for_command(
        "local_preflight",
        json.dumps(
            {
                "summary": "release preflight failed",
                "check_count": 9,
                "passed_count": 4,
                "failed_count": 2,
                "skipped_count": 3,
                "failed_checks": ["github_repository", "origin_matches_expected"],
                "repository_url": "https://gitlab.com/qazedhq/qa-z.git",
                "expected_origin_url": "ssh://git@example.com/qazedhq/qa-z.git",
                "remote_blocker": "repository_target_mismatch",
                "skip_remote": False,
                "allow_existing_refs": False,
                "allow_dirty": True,
            }
        ),
    )

    assert evidence == {
        "summary": "release preflight failed",
        "check_count": 9,
        "passed_count": 4,
        "failed_count": 2,
        "skipped_count": 3,
        "failed_checks": ["github_repository", "origin_matches_expected"],
        "repository_url": "https://gitlab.com/qazedhq/qa-z.git",
        "expected_origin_url": "ssh://git@example.com/qazedhq/qa-z.git",
        "remote_blocker": "repository_target_mismatch",
        "skip_remote": False,
        "allow_existing_refs": False,
        "allow_dirty": True,
    }


def test_alpha_release_gate_preserves_preflight_next_counts_in_evidence():
    gate = load_gate_module()

    evidence = gate.release_evidence_for_command(
        "local_preflight",
        json.dumps(
            {
                "summary": "release preflight passed",
                "check_count": 9,
                "passed_count": 6,
                "failed_count": 0,
                "skipped_count": 3,
                "failed_checks": [],
                "repository_target": "qazedhq/qa-z",
                "expected_origin_target": "qazedhq/qa-z",
                "actual_origin_url": "git@github.com:qazedhq/qa-z.git",
                "origin_state": "configured",
                "remote_path": "skipped",
                "release_path_state": "local_only_remote_preflight",
                "remote_readiness": "ready_for_remote_checks",
                "publish_strategy": "remote_preflight",
                "next_actions": [
                    (
                        "Run remote preflight against qazedhq/qa-z before public "
                        "publish; skip-remote only covers local readiness."
                    )
                ],
                "next_commands": [
                    (
                        "python scripts/alpha_release_preflight.py --repository-url "
                        "https://github.com/qazedhq/qa-z.git --expected-origin-url "
                        "https://github.com/qazedhq/qa-z.git --allow-dirty --json"
                    )
                ],
                "skip_remote": True,
                "allow_existing_refs": False,
                "allow_dirty": True,
            }
        ),
    )

    assert evidence == {
        "summary": "release preflight passed",
        "check_count": 9,
        "passed_count": 6,
        "failed_count": 0,
        "skipped_count": 3,
        "failed_checks": [],
        "repository_target": "qazedhq/qa-z",
        "repository_probe_state": "skipped",
        "expected_origin_target": "qazedhq/qa-z",
        "actual_origin_url": "git@github.com:qazedhq/qa-z.git",
        "origin_state": "configured",
        "remote_path": "skipped",
        "release_path_state": "local_only_remote_preflight",
        "remote_readiness": "ready_for_remote_checks",
        "publish_strategy": "remote_preflight",
        "next_action_count": 1,
        "next_command_count": 1,
        "skip_remote": True,
        "allow_existing_refs": False,
        "allow_dirty": True,
    }


def test_alpha_release_gate_preserves_preflight_generated_policy_split_counts():
    gate = load_gate_module()

    evidence = gate.release_evidence_for_command(
        "local_preflight",
        json.dumps(
            {
                "summary": "release preflight failed",
                "check_count": 9,
                "passed_count": 7,
                "failed_count": 1,
                "skipped_count": 1,
                "failed_checks": ["generated_artifacts_untracked"],
                "tracked_generated_artifact_count": 4,
                "generated_local_only_tracked_count": 2,
                "generated_local_by_default_tracked_count": 2,
                "repository_target": "qazedhq/qa-z",
                "remote_path": "skipped",
                "release_path_state": "local_only_remote_preflight",
                "publish_strategy": "remote_preflight",
                "skip_remote": True,
                "allow_existing_refs": False,
                "allow_dirty": True,
                "next_actions": [
                    "Remove or untrack tracked local-only generated artifacts before publish: dist/, .qa-z/.",
                    "Decide whether tracked benchmark result evidence stays local or is intentionally frozen with surrounding context before publish: benchmarks/results-l31/, benchmarks/results/.",
                ],
            }
        ),
    )

    assert evidence == {
        "summary": "release preflight failed",
        "check_count": 9,
        "passed_count": 7,
        "failed_count": 1,
        "skipped_count": 1,
        "failed_checks": ["generated_artifacts_untracked"],
        "tracked_generated_artifact_count": 4,
        "generated_local_only_tracked_count": 2,
        "generated_local_by_default_tracked_count": 2,
        "repository_target": "qazedhq/qa-z",
        "repository_probe_state": "skipped",
        "remote_path": "skipped",
        "release_path_state": "local_only_remote_preflight",
        "publish_strategy": "remote_preflight",
        "next_action_count": 2,
        "skip_remote": True,
        "allow_existing_refs": False,
        "allow_dirty": True,
    }


def test_alpha_release_gate_preserves_repository_metadata_in_evidence():
    gate = load_gate_module()

    evidence = gate.release_evidence_for_command(
        "local_preflight",
        json.dumps(
            {
                "summary": "release preflight passed",
                "check_count": 9,
                "passed_count": 9,
                "failed_count": 0,
                "skipped_count": 0,
                "failed_checks": [],
                "repository_target": "qazedhq/qa-z",
                "repository_http_status": 200,
                "repository_probe_state": "probed",
                "repository_probe_generated_at": "2026-04-21T05:02:00Z",
                "repository_visibility": "public",
                "repository_archived": False,
                "repository_default_branch": "release",
                "remote_path": "direct_publish",
                "release_path_state": "remote_direct_publish",
                "publish_strategy": "push_default_branch",
                "skip_remote": False,
                "allow_existing_refs": False,
                "allow_dirty": False,
            }
        ),
    )

    assert evidence == {
        "summary": "release preflight passed",
        "check_count": 9,
        "passed_count": 9,
        "failed_count": 0,
        "skipped_count": 0,
        "failed_checks": [],
        "repository_target": "qazedhq/qa-z",
        "repository_http_status": 200,
        "repository_probe_state": "probed",
        "repository_probe_generated_at": "2026-04-21T05:02:00Z",
        "repository_visibility": "public",
        "repository_archived": False,
        "repository_default_branch": "release",
        "remote_path": "direct_publish",
        "release_path_state": "remote_direct_publish",
        "publish_strategy": "push_default_branch",
        "skip_remote": False,
        "allow_existing_refs": False,
        "allow_dirty": False,
    }


def test_alpha_release_gate_preserves_last_known_probe_basis_in_evidence():
    gate = load_gate_module()

    evidence = gate.release_evidence_for_command(
        "local_preflight",
        json.dumps(
            {
                "summary": "release preflight passed",
                "check_count": 9,
                "passed_count": 6,
                "failed_count": 0,
                "skipped_count": 3,
                "failed_checks": [],
                "repository_target": "qazedhq/qa-z",
                "repository_probe_state": "skipped",
                "repository_probe_basis": "last_known",
                "repository_probe_generated_at": "2026-04-21T05:20:00Z",
                "repository_probe_freshness": "carried_forward",
                "repository_probe_age_hours": 1,
                "repository_http_status": 200,
                "repository_visibility": "public",
                "repository_archived": False,
                "repository_default_branch": "release",
                "remote_path": "skipped",
                "release_path_state": "local_only_remote_preflight",
                "publish_strategy": "remote_preflight",
                "skip_remote": True,
                "allow_existing_refs": False,
                "allow_dirty": True,
            }
        ),
    )

    assert evidence == {
        "summary": "release preflight passed",
        "check_count": 9,
        "passed_count": 6,
        "failed_count": 0,
        "skipped_count": 3,
        "failed_checks": [],
        "repository_target": "qazedhq/qa-z",
        "repository_probe_state": "skipped",
        "repository_probe_basis": "last_known",
        "repository_probe_generated_at": "2026-04-21T05:20:00Z",
        "repository_probe_freshness": "carried_forward",
        "repository_probe_age_hours": 1,
        "repository_http_status": 200,
        "repository_visibility": "public",
        "repository_archived": False,
        "repository_default_branch": "release",
        "remote_path": "skipped",
        "release_path_state": "local_only_remote_preflight",
        "publish_strategy": "remote_preflight",
        "skip_remote": True,
        "allow_existing_refs": False,
        "allow_dirty": True,
    }


def test_alpha_release_gate_preserves_bootstrap_publish_strategy_in_evidence():
    gate = load_gate_module()

    evidence = gate.release_evidence_for_command(
        "local_preflight",
        json.dumps(
            {
                "summary": "release preflight passed",
                "check_count": 9,
                "passed_count": 6,
                "failed_count": 0,
                "skipped_count": 3,
                "failed_checks": [],
                "repository_target": "qazedhq/qa-z",
                "origin_state": "missing",
                "remote_path": "skipped",
                "release_path_state": "local_only_bootstrap_origin",
                "remote_readiness": "needs_origin_bootstrap",
                "publish_strategy": "bootstrap_origin",
                "publish_checklist": [
                    "Add the intended origin with `git remote add origin https://github.com/qazedhq/qa-z.git`.",
                    (
                        "Rerun remote preflight with `python scripts/alpha_release_preflight.py "
                        "--repository-url https://github.com/qazedhq/qa-z.git "
                        "--expected-origin-url https://github.com/qazedhq/qa-z.git "
                        "--allow-dirty --json`."
                    ),
                ],
                "next_actions": [
                    (
                        "Configure origin and rerun remote preflight before public "
                        "publish; skip-remote only defers the remote bootstrap step."
                    )
                ],
                "next_commands": [
                    "git remote add origin https://github.com/qazedhq/qa-z.git",
                    (
                        "python scripts/alpha_release_preflight.py --repository-url "
                        "https://github.com/qazedhq/qa-z.git --expected-origin-url "
                        "https://github.com/qazedhq/qa-z.git --allow-dirty --json"
                    ),
                ],
                "skip_remote": True,
                "allow_existing_refs": False,
                "allow_dirty": True,
            }
        ),
    )

    assert evidence == {
        "summary": "release preflight passed",
        "check_count": 9,
        "passed_count": 6,
        "failed_count": 0,
        "skipped_count": 3,
        "failed_checks": [],
        "repository_target": "qazedhq/qa-z",
        "repository_probe_state": "skipped",
        "origin_state": "missing",
        "remote_path": "skipped",
        "release_path_state": "local_only_bootstrap_origin",
        "remote_readiness": "needs_origin_bootstrap",
        "publish_strategy": "bootstrap_origin",
        "publish_checklist_count": 2,
        "next_action_count": 1,
        "next_command_count": 2,
        "skip_remote": True,
        "allow_existing_refs": False,
        "allow_dirty": True,
    }


def test_alpha_release_gate_preserves_publish_checklist_count_in_evidence():
    gate = load_gate_module()

    evidence = gate.release_evidence_for_command(
        "local_preflight",
        json.dumps(
            {
                "summary": "release preflight passed",
                "check_count": 9,
                "passed_count": 9,
                "failed_count": 0,
                "skipped_count": 0,
                "failed_checks": [],
                "repository_target": "qazedhq/qa-z",
                "expected_origin_target": "qazedhq/qa-z",
                "origin_state": "configured",
                "remote_path": "direct_publish",
                "release_path_state": "remote_direct_publish",
                "publish_strategy": "push_default_branch",
                "publish_checklist": [
                    "Push the validated release baseline to main with `git push -u origin HEAD:main`.",
                    "Wait for remote CI before tagging.",
                    "Tag the validated default branch.",
                ],
                "skip_remote": False,
                "allow_existing_refs": False,
                "allow_dirty": False,
            }
        ),
    )

    assert evidence == {
        "summary": "release preflight passed",
        "check_count": 9,
        "passed_count": 9,
        "failed_count": 0,
        "skipped_count": 0,
        "failed_checks": [],
        "repository_target": "qazedhq/qa-z",
        "expected_origin_target": "qazedhq/qa-z",
        "origin_state": "configured",
        "remote_path": "direct_publish",
        "release_path_state": "remote_direct_publish",
        "publish_strategy": "push_default_branch",
        "publish_checklist_count": 3,
        "skip_remote": False,
        "allow_existing_refs": False,
        "allow_dirty": False,
    }


def test_alpha_release_gate_preserves_actual_origin_target_in_evidence():
    gate = load_gate_module()

    evidence = gate.release_evidence_for_command(
        "local_preflight",
        json.dumps(
            {
                "summary": "release preflight failed",
                "check_count": 9,
                "passed_count": 4,
                "failed_count": 1,
                "skipped_count": 3,
                "failed_checks": ["origin_matches_expected"],
                "repository_target": "qazedhq/qa-z",
                "expected_origin_target": "qazedhq/qa-z",
                "actual_origin_target": "other/qa-z",
                "actual_origin_url": "git@github.com:other/qa-z.git",
                "origin_state": "configured",
                "remote_path": "blocked",
                "remote_blocker": "origin_mismatch",
                "skip_remote": True,
                "allow_existing_refs": False,
                "allow_dirty": False,
            }
        ),
    )

    assert evidence == {
        "summary": "release preflight failed",
        "check_count": 9,
        "passed_count": 4,
        "failed_count": 1,
        "skipped_count": 3,
        "failed_checks": ["origin_matches_expected"],
        "repository_target": "qazedhq/qa-z",
        "expected_origin_target": "qazedhq/qa-z",
        "actual_origin_target": "other/qa-z",
        "actual_origin_url": "git@github.com:other/qa-z.git",
        "origin_state": "configured",
        "remote_path": "blocked",
        "release_path_state": "blocked_origin_alignment",
        "remote_blocker": "origin_mismatch",
        "skip_remote": True,
        "allow_existing_refs": False,
        "allow_dirty": False,
    }


def test_alpha_release_gate_preserves_remote_ref_diagnostics_in_evidence():
    gate = load_gate_module()

    evidence = gate.release_evidence_for_command(
        "local_preflight",
        json.dumps(
            {
                "summary": "release preflight failed",
                "check_count": 9,
                "passed_count": 5,
                "failed_count": 1,
                "skipped_count": 0,
                "failed_checks": ["remote_empty"],
                "repository_target": "qazedhq/qa-z",
                "remote_path": "blocked",
                "remote_blocker": "existing_refs_present",
                "remote_ref_count": 2,
                "remote_ref_head_count": 2,
                "remote_ref_tag_count": 0,
                "remote_ref_kinds": ["heads"],
                "remote_ref_sample": [
                    "refs/heads/main",
                    "refs/heads/release/v0.9.8-alpha",
                ],
                "skip_remote": False,
                "allow_existing_refs": False,
                "allow_dirty": False,
            }
        ),
    )

    assert evidence == {
        "summary": "release preflight failed",
        "check_count": 9,
        "passed_count": 5,
        "failed_count": 1,
        "skipped_count": 0,
        "failed_checks": ["remote_empty"],
        "repository_target": "qazedhq/qa-z",
        "remote_path": "blocked",
        "release_path_state": "blocked_existing_refs",
        "remote_blocker": "existing_refs_present",
        "remote_ref_count": 2,
        "remote_ref_head_count": 2,
        "remote_ref_tag_count": 0,
        "remote_ref_kinds": ["heads"],
        "remote_ref_sample": [
            "refs/heads/main",
            "refs/heads/release/v0.9.8-alpha",
        ],
        "skip_remote": False,
        "allow_existing_refs": False,
        "allow_dirty": False,
    }


def test_alpha_release_gate_fails_on_inconsistent_benchmark_evidence(tmp_path):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    benchmark_payload = {
        "fixtures_passed": 51,
        "fixtures_failed": 0,
        "fixtures_total": 51,
        "overall_rate": 1.0,
        "snapshot": "52/52 fixtures, overall_rate 1.0",
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["qa_z_benchmark"]): (
                0,
                json.dumps(benchmark_payload),
                "",
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert result.summary == "alpha release gate failed"
    assert "release_evidence_consistency" in result.payload["failed_checks"]
    assert result.payload["evidence_consistency_errors"] == [
        (
            "benchmark snapshot mismatch: snapshot is "
            "'52/52 fixtures, overall_rate 1.0' but counters imply "
            "'51/51 fixtures, overall_rate 1.0'"
        )
    ]
    assert result.payload["next_actions"] == [
        (
            "Rerun the alpha release gate and inspect `python -m qa_z benchmark "
            "--json`; publish only after benchmark counters and snapshot agree."
        )
    ]
    consistency_check = result.payload["checks"][-1]
    assert consistency_check["name"] == "release_evidence_consistency"
    assert consistency_check["status"] == "failed"
    assert "benchmark snapshot mismatch" in consistency_check["stdout_tail"]


def test_alpha_release_gate_fails_on_inconsistent_worktree_generated_split(tmp_path):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    worktree_plan_payload = {
        "status": "ready",
        "summary": {
            "batch_count": 11,
            "changed_batch_count": 1,
            "changed_path_count": 5,
            "generated_artifact_count": 4,
            "generated_artifact_file_count": 2,
            "generated_artifact_dir_count": 1,
            "cross_cutting_count": 0,
            "shared_patch_add_count": 0,
            "unassigned_source_path_count": 0,
            "multi_batch_path_count": 0,
        },
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["worktree_commit_plan"]): (
                0,
                json.dumps(worktree_plan_payload),
                "",
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert "release_evidence_consistency" in result.payload["failed_checks"]
    assert result.payload["evidence_consistency_errors"] == [
        (
            "worktree generated artifact split mismatch: "
            "generated_artifact_count is 4 but file plus directory counts imply 3"
        )
    ]
    assert result.payload["next_actions"] == [
        (
            "Rerun `python scripts/worktree_commit_plan.py --include-ignored "
            "--json` and the alpha release gate; publish only after generated "
            "artifact totals and split counts agree."
        )
    ]


def test_alpha_release_gate_fails_on_inconsistent_worktree_generated_policy_split(
    tmp_path,
):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    worktree_plan_payload = {
        "status": "ready",
        "summary": {
            "batch_count": 11,
            "changed_batch_count": 1,
            "changed_path_count": 5,
            "generated_artifact_count": 4,
            "generated_artifact_file_count": 2,
            "generated_artifact_dir_count": 2,
            "generated_local_only_count": 2,
            "generated_local_by_default_count": 1,
            "cross_cutting_count": 0,
            "shared_patch_add_count": 0,
            "unassigned_source_path_count": 0,
            "multi_batch_path_count": 0,
        },
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["worktree_commit_plan"]): (
                0,
                json.dumps(worktree_plan_payload),
                "",
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert "release_evidence_consistency" in result.payload["failed_checks"]
    assert result.payload["evidence_consistency_errors"] == [
        (
            "worktree generated artifact policy split mismatch: "
            "generated_artifact_count is 4 but local-only plus local-by-default "
            "counts imply 3"
        )
    ]
    assert result.payload["next_actions"] == [
        (
            "Rerun `python scripts/worktree_commit_plan.py --include-ignored "
            "--json` and the alpha release gate; publish only after generated "
            "artifact totals and policy-bucket counts agree."
        )
    ]


def test_alpha_release_gate_fails_on_inconsistent_worktree_patch_add_groups(
    tmp_path,
):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    worktree_plan_payload = {
        "status": "ready",
        "summary": {
            "batch_count": 11,
            "changed_batch_count": 1,
            "changed_path_count": 5,
            "generated_artifact_count": 0,
            "generated_artifact_file_count": 0,
            "generated_artifact_dir_count": 0,
            "cross_cutting_count": 0,
            "cross_cutting_group_count": 2,
            "shared_patch_add_count": 1,
            "unassigned_source_path_count": 0,
            "multi_batch_path_count": 0,
        },
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["worktree_commit_plan"]): (
                0,
                json.dumps(worktree_plan_payload),
                "",
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert "release_evidence_consistency" in result.payload["failed_checks"]
    assert result.payload["evidence_consistency_errors"] == [
        (
            "worktree patch-add group mismatch: "
            "cross_cutting_group_count is 2 but shared_patch_add_count is 1"
        )
    ]
    assert result.payload["next_actions"] == [
        (
            "Rerun `python scripts/worktree_commit_plan.py --summary-only "
            "--json` and the alpha release gate; publish only after shared "
            "patch-add group counts agree."
        )
    ]


def test_alpha_release_gate_fails_on_missing_carried_probe_freshness(tmp_path):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    preflight_payload = {
        "summary": "release preflight passed",
        "exit_code": 0,
        "check_count": 9,
        "passed_count": 6,
        "failed_count": 0,
        "skipped_count": 3,
        "failed_checks": [],
        "repository_target": "qazedhq/qa-z",
        "repository_probe_state": "skipped",
        "repository_probe_basis": "last_known",
        "repository_probe_generated_at": "2026-04-21T05:20:00Z",
        "remote_path": "skipped",
        "release_path_state": "local_only_remote_preflight",
        "skip_remote": True,
        "allow_existing_refs": False,
        "allow_dirty": True,
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["local_preflight"]): (
                0,
                json.dumps(preflight_payload),
                "",
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert "release_evidence_consistency" in result.payload["failed_checks"]
    assert result.payload["evidence_consistency_errors"] == [
        (
            "preflight carried probe freshness missing: "
            "repository_probe_basis=last_known requires "
            "repository_probe_generated_at, repository_probe_freshness, and "
            "repository_probe_age_hours"
        )
    ]
    assert result.payload["next_actions"] == [
        (
            "Rerun `python scripts/alpha_release_preflight.py --skip-remote "
            "--output <path> --json` or the alpha release gate so carried "
            "probe basis, freshness, and age fields come from one consistent "
            "preflight artifact."
        )
    ]


def test_alpha_release_gate_fails_on_inconsistent_current_probe_freshness(tmp_path):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    preflight_payload = {
        "summary": "release preflight passed",
        "exit_code": 0,
        "check_count": 9,
        "passed_count": 9,
        "failed_count": 0,
        "skipped_count": 0,
        "failed_checks": [],
        "repository_target": "qazedhq/qa-z",
        "repository_probe_state": "probed",
        "repository_probe_generated_at": "2026-04-21T05:20:00Z",
        "repository_probe_freshness": "stale",
        "repository_probe_age_hours": 5,
        "remote_path": "direct_publish",
        "release_path_state": "remote_direct_publish",
        "skip_remote": False,
        "allow_existing_refs": False,
        "allow_dirty": False,
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["local_preflight"]): (
                0,
                json.dumps(preflight_payload),
                "",
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert result.payload["evidence_consistency_errors"] == [
        (
            "preflight current probe freshness mismatch: "
            "repository_probe_state=probed requires "
            "repository_probe_freshness=current and "
            "repository_probe_age_hours=0"
        )
    ]


def test_alpha_release_gate_fails_on_wrong_target_probe_evidence(tmp_path):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    preflight_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
        "check_count": 9,
        "passed_count": 4,
        "failed_count": 2,
        "skipped_count": 3,
        "failed_checks": ["github_repository", "origin_matches_expected"],
        "repository_url": "https://gitlab.com/qazedhq/qa-z.git",
        "repository_probe_state": "probed",
        "repository_probe_generated_at": "2026-04-21T05:20:00Z",
        "repository_http_status": 404,
        "remote_path": "blocked",
        "remote_blocker": "repository_target_mismatch",
        "skip_remote": False,
        "allow_existing_refs": False,
        "allow_dirty": True,
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["local_preflight"]): (
                1,
                json.dumps(preflight_payload),
                "",
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert result.payload["evidence_consistency_errors"] == [
        (
            "preflight wrong-target probe evidence mismatch: "
            "repository_target_mismatch must not report "
            "repository_probe_state or repository_http_status"
        )
    ]


def test_alpha_release_gate_synthesizes_legacy_benchmark_snapshot(tmp_path):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    benchmark_payload = {
        "fixtures_passed": 52,
        "fixtures_failed": 0,
        "fixtures_total": 52,
        "overall_rate": 1.0,
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["qa_z_benchmark"]): (
                0,
                json.dumps(benchmark_payload),
                "",
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 0
    assert result.payload["evidence"]["benchmark"]["snapshot"] == (
        "52/52 fixtures, overall_rate 1.0"
    )
    assert "evidence_consistency_errors" not in result.payload


def test_alpha_release_gate_promotes_preflight_next_actions(tmp_path):
    module = load_gate_module()
    preflight_command = module.default_gate_commands()[0].command
    preflight_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
        "failed_checks": ["github_repository", "remote_reachable"],
        "next_actions": [
            (
                "Create or expose the public GitHub repository qazedhq/qa-z, "
                "then rerun remote preflight for https://github.com/qazedhq/qa-z.git."
            )
        ],
        "next_commands": [
            (
                "python scripts/alpha_release_preflight.py --repository-url "
                "https://github.com/qazedhq/qa-z.git --json"
            )
        ],
    }
    runner = RecordingRunner(
        {tuple(preflight_command): (1, json.dumps(preflight_payload), "")}
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert result.payload["failed_checks"] == ["local_preflight"]
    assert result.payload["preflight_failed_checks"] == [
        "github_repository",
        "remote_reachable",
    ]
    assert result.payload["next_actions"] == preflight_payload["next_actions"]
    assert result.payload["next_commands"] == preflight_payload["next_commands"]


def test_alpha_release_gate_preserves_empty_preflight_next_actions(tmp_path):
    module = load_gate_module()
    preflight_command = module.default_gate_commands()[0].command
    preflight_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
        "failed_checks": ["current_branch"],
        "next_actions": [],
    }
    runner = RecordingRunner(
        {tuple(preflight_command): (1, json.dumps(preflight_payload), "")}
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert result.payload["preflight_failed_checks"] == ["current_branch"]
    assert result.payload["next_actions"] == []


def test_alpha_release_gate_promotes_preflight_remote_check_guidance_on_success(
    tmp_path,
):
    module = load_gate_module()
    preflight_command = module.default_gate_commands()[0].command
    preflight_payload = {
        "summary": "release preflight passed",
        "exit_code": 0,
        "failed_checks": [],
        "remote_path": "skipped",
        "remote_readiness": "ready_for_remote_checks",
        "next_actions": [
            (
                "Run remote preflight against qazedhq/qa-z before public publish; "
                "skip-remote only covers local readiness."
            )
        ],
        "next_commands": [
            (
                "python scripts/alpha_release_preflight.py --repository-url "
                "https://github.com/qazedhq/qa-z.git --expected-origin-url "
                "https://github.com/qazedhq/qa-z.git --json"
            )
        ],
    }
    runner = RecordingRunner(
        {tuple(preflight_command): (0, json.dumps(preflight_payload), "")}
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 0
    assert result.payload["next_actions"] == preflight_payload["next_actions"]
    assert result.payload["next_commands"] == preflight_payload["next_commands"]


def test_alpha_release_gate_promotes_direct_publish_guidance_on_success(tmp_path):
    module = load_gate_module()
    preflight_command = module.default_gate_commands(include_remote=True)[0].command
    preflight_payload = {
        "summary": "release preflight passed",
        "exit_code": 0,
        "failed_checks": [],
        "remote_path": "direct_publish",
        "publish_strategy": "push_default_branch",
        "next_actions": [
            (
                "Remote is empty and ready for direct publish; push the release "
                "baseline to main, wait for remote CI, and tag only after the "
                "validated default branch is green."
            )
        ],
        "next_commands": ["git push -u origin HEAD:main"],
    }
    runner = RecordingRunner(
        {tuple(preflight_command): (0, json.dumps(preflight_payload), "")}
    )

    result = module.run_alpha_release_gate(
        tmp_path,
        include_remote=True,
        runner=runner,
    )

    assert result.exit_code == 0
    assert result.payload["next_actions"] == preflight_payload["next_actions"]
    assert result.payload["next_commands"] == preflight_payload["next_commands"]


def test_alpha_release_gate_deduplicates_promoted_preflight_guidance(tmp_path):
    module = load_gate_module()
    preflight_command = module.default_gate_commands()[0].command
    repeated_action = "Set origin to the intended repository URL."
    preflight_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
        "failed_checks": ["origin_matches_expected"],
        "next_actions": [
            repeated_action,
            repeated_action,
            "Rerun remote preflight.",
        ],
    }
    runner = RecordingRunner(
        {tuple(preflight_command): (1, json.dumps(preflight_payload), "")}
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)
    output = module.render_alpha_release_gate_human(result.payload)

    assert result.exit_code == 1
    assert result.payload["next_actions"] == [
        repeated_action,
        "Rerun remote preflight.",
    ]
    assert output.count(f"- {repeated_action}") == 1
    assert output.count("- Rerun remote preflight.") == 1


def test_alpha_release_gate_synthesizes_dirty_preflight_next_action(tmp_path):
    module = load_gate_module()
    preflight_command = module.default_gate_commands()[0].command
    preflight_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
        "failed_checks": ["worktree_clean"],
    }
    runner = RecordingRunner(
        {tuple(preflight_command): (1, json.dumps(preflight_payload), "")}
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert result.payload["preflight_failed_checks"] == ["worktree_clean"]
    assert result.payload["next_actions"] == [
        (
            "Commit, stash, or intentionally rerun with --allow-dirty before "
            "publishing; the worktree_clean check must be clean for release."
        )
    ]


def test_alpha_release_gate_synthesizes_dirty_action_for_malformed_next_actions(
    tmp_path,
):
    module = load_gate_module()
    preflight_command = module.default_gate_commands()[0].command

    for malformed_next_actions in (None, "commit first", {"action": "commit"}):
        preflight_payload = {
            "summary": "release preflight failed",
            "exit_code": 1,
            "failed_checks": ["worktree_clean"],
            "next_actions": malformed_next_actions,
        }
        runner = RecordingRunner(
            {tuple(preflight_command): (1, json.dumps(preflight_payload), "")}
        )

        result = module.run_alpha_release_gate(tmp_path, runner=runner)

        assert result.exit_code == 1
        assert result.payload["next_actions"] == [
            (
                "Commit, stash, or intentionally rerun with --allow-dirty before "
                "publishing; the worktree_clean check must be clean for release."
            )
        ]


def test_alpha_release_gate_reads_preflight_repair_fields_from_output_file(tmp_path):
    module = load_gate_module()
    preflight_output = tmp_path / "evidence" / "preflight.json"
    preflight_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
        "failed_checks": ["github_repository", "remote_reachable"],
        "next_actions": [
            (
                "Create or expose the public GitHub repository qazedhq/qa-z, "
                "then rerun remote preflight."
            )
        ],
    }

    class FileWritingRunner(RecordingRunner):
        def __call__(self, command, cwd):
            self.commands.append(tuple(command))
            if any(
                str(argument).endswith("alpha_release_preflight.py")
                for argument in command
            ):
                preflight_output.parent.mkdir(parents=True, exist_ok=True)
                preflight_output.write_text(
                    json.dumps(preflight_payload), encoding="utf-8"
                )
                return 1, "release preflight failed\n", ""
            return 0, "ok\n", ""

    result = module.run_alpha_release_gate(
        tmp_path, preflight_output=preflight_output, runner=FileWritingRunner()
    )

    assert result.exit_code == 1
    assert result.payload["preflight_failed_checks"] == [
        "github_repository",
        "remote_reachable",
    ]
    assert result.payload["next_actions"] == preflight_payload["next_actions"]


def test_alpha_release_gate_supplements_partial_stdout_with_output_file(tmp_path):
    module = load_gate_module()
    preflight_output = tmp_path / "evidence" / "preflight.json"
    stdout_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
    }
    file_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
        "failed_checks": ["origin_matches_expected", "github_repository"],
        "next_actions": [
            "Set origin to the intended repository URL, then rerun preflight.",
        ],
    }

    class PartialStdoutRunner(RecordingRunner):
        def __call__(self, command, cwd):
            self.commands.append(tuple(command))
            if any(
                str(argument).endswith("alpha_release_preflight.py")
                for argument in command
            ):
                preflight_output.parent.mkdir(parents=True, exist_ok=True)
                preflight_output.write_text(json.dumps(file_payload), encoding="utf-8")
                return 1, json.dumps(stdout_payload), ""
            return 0, "ok\n", ""

    result = module.run_alpha_release_gate(
        tmp_path, preflight_output=preflight_output, runner=PartialStdoutRunner()
    )

    assert result.exit_code == 1
    assert result.payload["preflight_failed_checks"] == [
        "origin_matches_expected",
        "github_repository",
    ]
    assert result.payload["next_actions"] == file_payload["next_actions"]
