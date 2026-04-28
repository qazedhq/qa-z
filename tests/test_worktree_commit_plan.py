"""Tests for the worktree commit plan helper."""

from __future__ import annotations

from tests.worktree_commit_plan_test_support import load_plan_module


def test_commit_plan_groups_changed_paths_by_release_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M scripts/alpha_release_gate.py",
            " M tests/test_alpha_release_gate.py",
            " M src/qa_z/benchmark.py",
            "?? benchmarks/fixtures/deep_scan_warning_diagnostics/",
            " M src/qa_z/self_improvement.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["alpha_release_closure"]["changed_paths"] == [
        "scripts/alpha_release_gate.py",
        "tests/test_alpha_release_gate.py",
    ]
    assert batches["benchmark_coverage"]["changed_paths"] == [
        "src/qa_z/benchmark.py",
        "benchmarks/fixtures/deep_scan_warning_diagnostics/",
    ]
    assert batches["self_inspection_backlog"]["changed_paths"] == [
        "src/qa_z/self_improvement.py"
    ]
    assert result["unassigned_source_paths"] == []
    assert str(result["generated_at"]).endswith("Z")


def test_commit_plan_keeps_generated_artifacts_out_of_batches() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? dist/alpha-release-gate.l20.json",
            "?? .qa-z/runs/latest-run.json",
            "?? .mypy_cache_safe/3.10/cache.db",
            "?? .ruff_cache_safe/0.15.10/cache.db",
            "?? benchmarks/results-p12-summary/summary.json",
            " M README.md",
        ]
    )

    assert result["generated_artifact_paths"] == [
        "dist/",
        ".qa-z/",
        ".mypy_cache_safe/",
        ".ruff_cache_safe/",
        "benchmarks/results-p12-summary/",
    ]
    assert result["cross_cutting_paths"] == ["README.md"]
    assert all(
        "dist/alpha-release-gate.l20.json" not in batch["changed_paths"]
        for batch in result["batches"]
    )


def test_commit_plan_treats_literal_percent_temp_benchmark_output_as_local_only() -> (
    None
):
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? %TEMP%/qa-z-l27-full-benchmark/report.md",
            "?? %TEMP%/qa-z-l27-full-benchmark/summary.json",
            "?? %TEMP%/qa-z-l27-full-benchmark/work/deep_config_error_surface/repo/.qa-z-benchmark-bin/semgrep",
            " M src/qa_z/self_improvement.py",
        ]
    )

    assert result["generated_artifact_paths"] == ["%TEMP%/"]
    assert result["generated_local_only_paths"] == ["%TEMP%/"]
    assert result["generated_local_by_default_paths"] == []
    assert result["unassigned_source_paths"] == []
    assert all(
        "%TEMP%/qa-z-l27-full-benchmark/report.md" not in batch["changed_paths"]
        for batch in result["batches"]
    )


def test_commit_plan_treats_root_tmp_scratch_as_local_only() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? tmp_mypy_smoke.py",
            "?? tmp_mypy_cache/3.10/cache.db",
            "?? tmp_rmtree_probe/x.txt",
        ]
    )

    assert result["generated_artifact_paths"] == [
        "tmp_mypy_smoke.py",
        "tmp_mypy_cache/",
        "tmp_rmtree_probe/",
    ]
    assert result["generated_local_only_paths"] == [
        "tmp_mypy_smoke.py",
        "tmp_mypy_cache/",
        "tmp_rmtree_probe/",
    ]
    assert result["generated_local_by_default_paths"] == []
    assert result["unassigned_source_paths"] == []
    assert all(
        "tmp_mypy_smoke.py" not in batch["changed_paths"] for batch in result["batches"]
    )


def test_commit_plan_treats_benchmark_minlock_probe_as_local_only() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? benchmarks/minlock-plain.txt",
            "?? benchmarks/minlock-repro/.benchmark.lock",
            "?? benchmarks/minlock-x.txt",
        ]
    )

    assert result["generated_artifact_paths"] == [
        "benchmarks/minlock-plain.txt",
        "benchmarks/minlock-repro/",
        "benchmarks/minlock-x.txt",
    ]
    assert result["generated_local_only_paths"] == [
        "benchmarks/minlock-plain.txt",
        "benchmarks/minlock-repro/",
        "benchmarks/minlock-x.txt",
    ]
    assert result["generated_local_by_default_paths"] == []
    assert result["unassigned_source_paths"] == []


def test_commit_plan_reports_unassigned_source_paths() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M src/qa_z/new_surface.py",
            " M tests/test_new_surface.py",
            " M docs/reports/worktree-commit-plan.md",
        ]
    )

    assert result["unassigned_source_paths"] == [
        "src/qa_z/new_surface.py",
        "tests/test_new_surface.py",
    ]
    assert result["report_paths"] == ["docs/reports/worktree-commit-plan.md"]
    assert result["status"] == "attention_required"


def test_commit_plan_next_actions_explain_generated_and_unassigned_work() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? dist/alpha-release-gate.l20.json",
            " M src/qa_z/new_surface.py",
            " M README.md",
        ]
    )

    assert result["next_actions"] == [
        (
            "Keep local-only generated runtime artifacts out of staging and "
            "cleanup review unless a fixture/doc task explicitly freezes them."
        ),
        (
            "Add unassigned source paths to an existing commit batch rule or "
            "split a new explicit batch before release staging."
        ),
        (
            "Patch-add cross-cutting docs, report files, or current-truth tests "
            "with the feature batch they describe instead of staging them wholesale."
        ),
    ]


def test_commit_plan_parses_renames_by_new_path() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "R  src/qa_z/old_self_improvement.py -> src/qa_z/self_improvement.py",
            '?? "benchmarks/fixtures/deep scan warning/expected.json"',
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["self_inspection_backlog"]["changed_paths"] == [
        "src/qa_z/self_improvement.py"
    ]
    assert batches["benchmark_coverage"]["changed_paths"] == [
        "benchmarks/fixtures/deep scan warning/expected.json"
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_classifies_helper_and_schema_guard_tests() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? scripts/worktree_commit_plan.py",
            "?? tests/test_worktree_commit_plan.py",
            " M tests/test_artifact_schema.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["commit_plan_support"]["changed_paths"] == [
        "scripts/worktree_commit_plan.py",
        "tests/test_worktree_commit_plan.py",
    ]
    assert result["cross_cutting_paths"] == ["tests/test_artifact_schema.py"]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_owner_overrides_executor_fixture_overlap_paths() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M benchmarks/fixtures/executor_unowned_overlap/expected.json",
            " M src/qa_z/executor_bridge.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert result["multi_batch_paths"] == []
    assert result["unassigned_source_paths"] == []
    assert batches["executor_return_path"]["changed_paths"] == [
        "benchmarks/fixtures/executor_unowned_overlap/expected.json",
        "src/qa_z/executor_bridge.py",
    ]
    assert result["status"] == "ready"


def test_commit_plan_owner_overrides_known_executor_fixture_paths() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M benchmarks/fixtures/executor_result_partial_mixed_verify_candidate/expected.json",
            " M benchmarks/fixtures/executor_result_partial_mixed_verify_candidate/repo/external-result.json",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert result["multi_batch_paths"] == []
    assert batches["executor_return_path"]["changed_paths"] == [
        "benchmarks/fixtures/executor_result_partial_mixed_verify_candidate/expected.json",
        "benchmarks/fixtures/executor_result_partial_mixed_verify_candidate/repo/external-result.json",
    ]
    assert batches["benchmark_coverage"]["changed_paths"] == []
    assert result["status"] == "ready"


def test_commit_plan_batches_include_targeted_validation_commands() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M scripts/alpha_release_gate.py",
            "?? scripts/worktree_commit_plan.py",
            " M src/qa_z/benchmark.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["alpha_release_closure"]["validation_commands"] == [
        "python -m pytest tests/test_alpha_release_gate.py tests/test_alpha_release_gate_environment.py tests/test_alpha_release_preflight.py tests/test_alpha_release_artifact_smoke.py tests/test_alpha_release_bundle_manifest.py tests/test_release_script_environment.py -q",
        "python scripts/alpha_release_gate.py --allow-dirty --json",
    ]
    assert batches["commit_plan_support"]["validation_commands"] == [
        "python -m pytest tests/test_worktree_commit_plan.py tests/test_current_truth.py -q",
        "python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json",
    ]
    assert (
        "python -m qa_z benchmark --json"
        in batches["benchmark_coverage"]["validation_commands"]
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


def test_commit_plan_payload_includes_compact_summary_counts() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M src/qa_z/benchmark.py",
            " M README.md",
            " M docs/reports/worktree-commit-plan.md",
            "?? dist/alpha-release-gate.json",
        ]
    )

    assert result["summary"] == {
        "batch_count": 11,
        "changed_batch_count": 1,
        "unchanged_batch_count": 10,
        "changed_path_count": 4,
        "generated_artifact_count": 1,
        "generated_artifact_file_count": 0,
        "generated_artifact_dir_count": 1,
        "generated_local_only_count": 1,
        "generated_local_by_default_count": 0,
        "cross_cutting_count": 1,
        "cross_cutting_group_count": 2,
        "report_path_count": 1,
        "shared_patch_add_count": 2,
        "multi_batch_path_count": 0,
        "unassigned_source_path_count": 0,
        "attention_reason_count": 0,
    }


def test_commit_plan_groups_cross_cutting_patch_add_paths() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M README.md",
            " M src/qa_z/cli.py",
            " M src/qa_z/commands/runtime.py",
            " M tests/test_current_truth.py",
            " M docs/reports/current-state-analysis.md",
        ]
    )
    groups = {group["id"]: group for group in result["cross_cutting_groups"]}

    assert result["summary"]["cross_cutting_group_count"] == 4
    assert groups["public_docs_contract"]["paths"] == ["README.md"]
    assert groups["command_router_spine"]["paths"] == [
        "src/qa_z/cli.py",
        "src/qa_z/commands/runtime.py",
    ]
    assert groups["current_truth_guards"]["paths"] == ["tests/test_current_truth.py"]
    assert groups["status_reports"]["paths"] == [
        "docs/reports/current-state-analysis.md"
    ]
    assert groups["command_router_spine"]["patch_command"] == [
        "git",
        "add",
        "--patch",
        "--",
        "src/qa_z/cli.py",
        "src/qa_z/commands/runtime.py",
    ]


def test_commit_plan_assigns_deep_runner_foundation_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M src/qa_z/runners/deep.py",
            " M src/qa_z/runners/deep_policy.py",
            " M src/qa_z/runners/deep_runtime.py",
            " M src/qa_z/runners/semgrep.py",
            " M tests/test_deep_run_resolution.py",
            " M tests/test_semgrep_normalization.py",
            " M tests/test_deep_context_architecture.py",
            " M tests/test_deep_context_helper_architecture.py",
            " M tests/test_deep_runner_architecture.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["deep_runner_foundation"]["changed_paths"] == [
        "src/qa_z/runners/deep.py",
        "src/qa_z/runners/deep_policy.py",
        "src/qa_z/runners/deep_runtime.py",
        "src/qa_z/runners/semgrep.py",
        "tests/test_deep_run_resolution.py",
        "tests/test_semgrep_normalization.py",
        "tests/test_deep_context_architecture.py",
        "tests/test_deep_context_helper_architecture.py",
        "tests/test_deep_runner_architecture.py",
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_assigns_runner_contract_spine_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M src/qa_z/runners/models.py",
            "?? tests/test_runner_models_contract.py",
            "?? tests/test_runner_models_architecture.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["runner_contract_spine"]["changed_paths"] == [
        "src/qa_z/runners/models.py",
        "tests/test_runner_models_contract.py",
        "tests/test_runner_models_architecture.py",
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_routes_shared_support_paths_to_owned_batches() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M tests/conftest.py",
            " M tests/__init__.py",
            " M tests/ast_test_support.py",
            " M tests/benchmark_test_support.py",
            " M tests/executor_result_test_support.py",
            " M tests/test_runtime_executor_result_architecture.py",
            " M tests/test_repair_signal_inputs.py",
            " M tests/test_worktree_discovery_architecture.py",
            " M tests/test_worktree_discovery_candidates.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["planning_runtime_foundation"]["changed_paths"] == [
        "tests/conftest.py",
        "tests/__init__.py",
        "tests/ast_test_support.py",
    ]
    assert batches["benchmark_coverage"]["changed_paths"] == [
        "tests/benchmark_test_support.py"
    ]
    assert batches["executor_return_path"]["changed_paths"] == [
        "tests/executor_result_test_support.py",
        "tests/test_runtime_executor_result_architecture.py",
    ]
    assert batches["self_inspection_backlog"]["changed_paths"] == [
        "tests/test_repair_signal_inputs.py",
        "tests/test_worktree_discovery_architecture.py",
        "tests/test_worktree_discovery_candidates.py",
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_routes_fast_gate_environment_into_planning_runtime_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines([" M tests/test_fast_gate_environment.py"])
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["planning_runtime_foundation"]["changed_paths"] == [
        "tests/test_fast_gate_environment.py"
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_routes_mypy_ini_into_planning_runtime_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(["?? mypy.ini"])
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["planning_runtime_foundation"]["changed_paths"] == ["mypy.ini"]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_assigns_alpha_release_support_surfaces_to_closure_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M scripts/alpha_release_artifact_smoke.py",
            " M scripts/alpha_release_bundle_manifest.py",
            " M tests/test_alpha_release_artifact_smoke_architecture.py",
            " M tests/test_alpha_release_bundle_manifest.py",
            " M tests/alpha_release_artifact_smoke_test_support.py",
            " M tests/alpha_release_bundle_manifest_test_support.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["alpha_release_closure"]["changed_paths"] == [
        "scripts/alpha_release_artifact_smoke.py",
        "scripts/alpha_release_bundle_manifest.py",
        "tests/test_alpha_release_artifact_smoke_architecture.py",
        "tests/test_alpha_release_bundle_manifest.py",
        "tests/alpha_release_artifact_smoke_test_support.py",
        "tests/alpha_release_bundle_manifest_test_support.py",
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_assigns_runtime_cleanup_script_to_self_inspection_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? scripts/runtime_artifact_cleanup.py",
            "?? scripts/runtime_artifact_cleanup_support.py",
            "?? tests/test_runtime_artifact_cleanup.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["self_inspection_backlog"]["changed_paths"] == [
        "scripts/runtime_artifact_cleanup.py",
        "scripts/runtime_artifact_cleanup_support.py",
        "tests/test_runtime_artifact_cleanup.py",
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_assigns_verification_and_reporter_surfaces_to_publish_batch() -> (
    None
):
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M src/qa_z/verification_compare.py",
            " M src/qa_z/reporters/review_packet_render.py",
            " M src/qa_z/commands/review_github_context.py",
            " M tests/test_verification_report.py",
            " M tests/test_repair_prompt.py",
            " M tests/verification_test_support.py",
            " M tests/repair_prompt_test_support.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["repair_session_publish"]["changed_paths"] == [
        "src/qa_z/verification_compare.py",
        "src/qa_z/reporters/review_packet_render.py",
        "src/qa_z/commands/review_github_context.py",
        "tests/test_verification_report.py",
        "tests/test_repair_prompt.py",
        "tests/verification_test_support.py",
        "tests/repair_prompt_test_support.py",
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_assigns_release_workflow_gate_and_operator_action_helper() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M src/qa_z/operator_action_render.py",
            " M tests/test_github_workflow.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["repair_session_publish"]["changed_paths"] == [
        "src/qa_z/operator_action_render.py",
    ]
    assert batches["alpha_release_closure"]["changed_paths"] == [
        "tests/test_github_workflow.py",
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_owner_overrides_known_overlap_paths() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M benchmarks/fixtures/executor_dry_run_completed_verify_blocked/expected.json",
            " M src/qa_z/autonomy_selection.py",
            " M src/qa_z/benchmark_signals.py",
            " M src/qa_z/execution_discovery.py",
            " M src/qa_z/executor_signals.py",
            " M src/qa_z/report_signals.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert result["multi_batch_paths"] == []
    assert batches["executor_return_path"]["changed_paths"] == [
        "benchmarks/fixtures/executor_dry_run_completed_verify_blocked/expected.json"
    ]
    assert batches["autonomy_loop_planner"]["changed_paths"] == [
        "src/qa_z/autonomy_selection.py"
    ]
    assert batches["self_inspection_backlog"]["changed_paths"] == [
        "src/qa_z/benchmark_signals.py",
        "src/qa_z/execution_discovery.py",
        "src/qa_z/executor_signals.py",
        "src/qa_z/report_signals.py",
    ]
