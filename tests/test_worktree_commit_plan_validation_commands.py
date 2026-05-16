"""Validation command tests for the worktree commit plan helper."""

from __future__ import annotations

from tests.worktree_commit_plan_test_support import load_plan_module


def test_commit_plan_batches_include_targeted_validation_commands() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M scripts/alpha_release_gate.py",
            "?? scripts/worktree_commit_plan.py",
            " M src/qa_z/benchmark.py",
            " M src/qa_z/autonomy_actions.py",
            " M src/qa_z/guard/verdict.py",
            " M src/qa_z/task_selection_render.py",
            " M src/qa_z/executor_ingest_outcome.py",
            " M src/qa_z/executor_dry_run.py",
            "?? tests/test_execution_runs_error_contracts.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["alpha_release_closure"]["validation_commands"] == [
        "python -m pytest tests/test_alpha_release_gate.py tests/test_alpha_release_gate_environment.py tests/test_alpha_release_preflight.py tests/test_alpha_release_artifact_smoke.py tests/test_package_smoke_rehearsal.py tests/test_alpha_release_bundle_manifest.py tests/test_alpha_release_truth_validator.py tests/test_release_script_environment.py tests/test_github_workflow.py tests/test_text_file_hygiene.py tests/test_public_raw_urls.py -q",
        "python scripts/alpha_release_gate.py --quick --allow-dirty --json",
        "python scripts/alpha_release_truth_validator.py --proof-head-from-packet --json --output .qa-z/tmp/alpha-release-truth-validator.json",
        "python scripts/alpha_release_gate.py --allow-dirty --json",
    ]
    assert batches["commit_plan_support"]["validation_commands"] == [
        "python -m pytest tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py tests/test_current_truth.py -q",
        "python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json",
        "python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting --output .qa-z/tmp/worktree-commit-plan.json",
    ]
    assert (
        "python -m qa_z benchmark --json"
        in batches["benchmark_coverage"]["validation_commands"]
    )
    assert batches["autonomy_loop_planner"]["validation_commands"] == [
        "python -m pytest tests/test_autonomy.py tests/test_autonomy_action_cleanup.py tests/test_autonomy_action_context.py tests/test_cli.py -q",
        "python -m qa_z autonomy status --json",
    ]
    assert (
        "tests/test_beta_readiness_docs.py"
        in batches["current_truth_release_surface"]["validation_commands"][0]
    )
    assert (
        "tests/test_beta_release_decision_docs.py"
        in batches["current_truth_release_surface"]["validation_commands"][0]
    )
    assert (
        "tests/test_beta_version_policy_docs.py"
        in batches["current_truth_release_surface"]["validation_commands"][0]
    )
    assert (
        "tests/test_github_summary_render.py"
        in batches["repair_session_publish"]["validation_commands"][0]
    )
    assert (
        "tests/test_repair_prompt_error_contracts.py"
        in batches["repair_session_publish"]["validation_commands"][0]
    )
    assert (
        "tests/test_verify_cli_error_contracts.py"
        in batches["repair_session_publish"]["validation_commands"][0]
    )
    assert (
        "tests/test_self_improvement_selection_output.py"
        in batches["self_inspection_backlog"]["validation_commands"][0]
    )
    assert (
        "tests/test_guard_cli.py"
        in batches["planning_runtime_foundation"]["validation_commands"][1]
    )
    assert (
        "tests/test_execution_runs_error_contracts.py"
        in batches["planning_runtime_foundation"]["validation_commands"][1]
    )
    assert (
        "tests/test_executor_ingest_outcome.py"
        in batches["executor_return_path"]["validation_commands"][0]
    )
    assert (
        "tests/test_executor_result_dry_run.py"
        in batches["executor_return_path"]["validation_commands"][0]
    )
    assert batches["benchmark_coverage"]["staging_plan"] == {
        "include_paths": ["src/qa_z/benchmark.py"],
        "candidate_patch_add_paths": [],
        "exclude_path_count": 0,
        "git_add_command": ["git", "add", "--", "src/qa_z/benchmark.py"],
        "git_add_patch_command": [],
        "validation_commands": [
            "python -m pytest tests/test_benchmark.py -q",
            "python -m qa_z benchmark --json",
        ],
    }


def test_commit_plan_assigns_alpha_release_support_surfaces_to_closure_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M scripts/alpha_release_artifact_smoke.py",
            " M scripts/alpha_release_bundle_manifest.py",
            "?? scripts/alpha_release_truth_validator.py",
            "?? scripts/package_smoke_rehearsal.py",
            "?? scripts/package_smoke_rehearsal_support.py",
            " M tests/test_alpha_release_artifact_smoke_architecture.py",
            " M tests/test_alpha_release_bundle_manifest.py",
            "?? tests/test_alpha_release_truth_validator.py",
            "?? tests/test_package_smoke_rehearsal.py",
            " M tests/alpha_release_artifact_smoke_test_support.py",
            " M tests/alpha_release_bundle_manifest_test_support.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["alpha_release_closure"]["changed_paths"] == [
        "scripts/alpha_release_artifact_smoke.py",
        "scripts/alpha_release_bundle_manifest.py",
        "scripts/alpha_release_truth_validator.py",
        "scripts/package_smoke_rehearsal.py",
        "scripts/package_smoke_rehearsal_support.py",
        "tests/test_alpha_release_artifact_smoke_architecture.py",
        "tests/test_alpha_release_bundle_manifest.py",
        "tests/test_alpha_release_truth_validator.py",
        "tests/test_package_smoke_rehearsal.py",
        "tests/alpha_release_artifact_smoke_test_support.py",
        "tests/alpha_release_bundle_manifest_test_support.py",
    ]
    assert result["unassigned_source_paths"] == []
