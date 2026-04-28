"""Batch-filtering tests for the worktree commit plan helper."""

from __future__ import annotations

import json

from tests.worktree_commit_plan_test_support import FakeRunner, load_plan_module


def test_commit_plan_can_filter_payload_to_one_batch() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            " M src/qa_z/benchmark.py",
            " M src/qa_z/self_improvement.py",
            " M README.md",
            " M docs/reports/current-state-analysis.md",
        ]
    )

    filtered = module.filter_payload_for_batch(result, "benchmark_coverage")

    assert filtered["selected_batch"] == "benchmark_coverage"
    assert [batch["id"] for batch in filtered["batches"]] == ["benchmark_coverage"]
    assert filtered["batches"][0]["changed_paths"] == ["src/qa_z/benchmark.py"]
    assert filtered["cross_cutting_paths"] == ["README.md"]
    assert filtered["report_paths"] == ["docs/reports/current-state-analysis.md"]
    assert filtered["selected_batch_summary"] == {
        "id": "benchmark_coverage",
        "changed_count": 1,
        "include_path_count": 1,
        "patch_add_candidate_count": 2,
        "generated_exclude_count": 0,
        "validation_command_count": 2,
        "status": "ready",
        "attention_reason_count": 0,
    }


def test_commit_plan_batch_filter_keeps_global_attention_separate() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            "?? dist/alpha-release-gate.json",
            " M src/qa_z/benchmark.py",
        ],
        fail_on_generated=True,
    )

    filtered = module.filter_payload_for_batch(result, "benchmark_coverage")

    assert filtered["global_status"] == "attention_required"
    assert filtered["global_attention_reasons"] == ["generated_artifacts_present"]
    assert filtered["global_attention_reason_count"] == 1
    assert filtered["status"] == "attention_required"
    assert filtered["attention_reasons"] == ["generated_artifacts_present"]
    assert filtered["selected_batch_summary"]["status"] == "ready"
    assert filtered["selected_batch_summary"]["attention_reason_count"] == 1


def test_commit_plan_cli_batch_preserves_strict_generated_exit(
    monkeypatch, capsys
) -> None:
    module = load_plan_module()

    monkeypatch.setattr(
        module,
        "git_status_lines",
        lambda *_args, **_kwargs: [
            "?? dist/alpha-release-gate.json",
            " M src/qa_z/benchmark.py",
        ],
    )
    monkeypatch.setattr(
        module,
        "repository_context",
        lambda *_args, **_kwargs: {"branch": "codex/qa-z-bootstrap", "head": "abc123"},
    )

    exit_code = module.main(
        ["--batch", "benchmark_coverage", "--fail-on-generated", "--json"]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 1
    assert payload["status"] == "attention_required"
    assert payload["attention_reasons"] == ["generated_artifacts_present"]
    assert payload["selected_batch_summary"]["status"] == "ready"


def test_commit_plan_rejects_unknown_batch_filter() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines([" M src/qa_z/benchmark.py"])

    try:
        module.filter_payload_for_batch(result, "missing_batch")
    except ValueError as exc:
        assert "unknown batch missing_batch" in str(exc)
    else:
        raise AssertionError("expected unknown batch filter to fail")


def test_commit_plan_can_include_ignored_generated_artifacts(tmp_path) -> None:
    module = load_plan_module()
    runner = FakeRunner(
        {
            ("git", "status", "--short", "--untracked-files=all", "--ignored"): (
                0,
                "!! dist/alpha-release-gate.l20.json\n"
                "!! .qa-z/runs/latest-run.json\n"
                "!! tests/__pycache__/\n"
                " M src/qa_z/benchmark.py\n",
                "",
            )
        }
    )

    lines = module.git_status_lines(tmp_path, runner=runner, include_ignored=True)
    result = module.analyze_status_lines(lines)

    assert runner.commands == [
        ("git", "status", "--short", "--untracked-files=all", "--ignored")
    ]
    assert result["generated_artifact_paths"] == [
        "dist/",
        ".qa-z/",
        "tests/__pycache__/",
    ]


def test_commit_plan_requests_all_untracked_paths_from_git_status(tmp_path) -> None:
    module = load_plan_module()
    runner = FakeRunner(
        {
            ("git", "status", "--short", "--untracked-files=all"): (
                0,
                "?? src/qa_z/commands/runtime.py\n",
                "",
            )
        }
    )

    lines = module.git_status_lines(tmp_path, runner=runner)

    assert lines == ["?? src/qa_z/commands/runtime.py"]
    assert runner.commands == [("git", "status", "--short", "--untracked-files=all")]


def test_commit_plan_routes_shared_subprocess_env_surfaces_without_unassigned_paths():
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M pyproject.toml",
            " M src/qa_z/runners/subprocess.py",
            "?? src/qa_z/subprocess_env.py",
            "?? tests/test_release_script_environment.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["planning_runtime_foundation"]["changed_paths"] == [
        "pyproject.toml",
        "src/qa_z/subprocess_env.py",
    ]
    assert batches["runner_contract_spine"]["changed_paths"] == [
        "src/qa_z/runners/subprocess.py"
    ]
    assert batches["alpha_release_closure"]["changed_paths"] == [
        "tests/test_release_script_environment.py",
    ]
    assert (
        "tests/test_release_script_environment.py"
        in batches["alpha_release_closure"]["validation_commands"][0]
    )
    assert (
        "tests/test_fast_gate_environment.py"
        in batches["planning_runtime_foundation"]["validation_commands"][0]
    )
    assert result["unassigned_source_paths"] == []


def test_commit_plan_assigns_planning_runtime_surface_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M src/qa_z/cli.py",
            "?? src/qa_z/commands/command_registry.py",
            "?? src/qa_z/commands/planning.py",
            "?? src/qa_z/commands/runtime.py",
            " M src/qa_z/execution_followup_candidates.py",
            " M src/qa_z/live_repository.py",
            " M src/qa_z/report_freshness.py",
            " M tests/test_planning_commands.py",
            " M tests/test_command_registry_architecture.py",
            " M tests/test_runtime_commands.py",
            " M tests/test_live_repository_architecture.py",
            " M tests/test_report_freshness.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["planning_runtime_foundation"]["changed_paths"] == [
        "src/qa_z/execution_followup_candidates.py",
        "src/qa_z/live_repository.py",
        "src/qa_z/report_freshness.py",
        "tests/test_live_repository_architecture.py",
        "tests/test_report_freshness.py",
    ]
    assert batches["self_inspection_backlog"]["changed_paths"] == [
        "src/qa_z/commands/planning.py",
        "tests/test_planning_commands.py",
    ]
    assert result["cross_cutting_paths"] == [
        "src/qa_z/cli.py",
        "src/qa_z/commands/command_registry.py",
        "src/qa_z/commands/runtime.py",
        "tests/test_command_registry_architecture.py",
        "tests/test_runtime_commands.py",
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_routes_modular_command_wrappers_to_feature_batches() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? src/qa_z/commands/planning_backlog.py",
            "?? src/qa_z/commands/review_github.py",
            "?? src/qa_z/commands/review_packet.py",
            "?? src/qa_z/commands/reviewing.py",
            "?? src/qa_z/commands/runtime_autonomy.py",
            "?? src/qa_z/commands/runtime_benchmark.py",
            "?? src/qa_z/commands/runtime_bridge.py",
            "?? src/qa_z/commands/runtime_executor_result.py",
            "?? src/qa_z/commands/runtime_executor_result_stdout.py",
            "?? src/qa_z/commands/session_repair.py",
            "?? src/qa_z/commands/session_verify.py",
            "?? src/qa_z/commands/sessioning.py",
            " M tests/test_session_commands.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["self_inspection_backlog"]["changed_paths"] == [
        "src/qa_z/commands/planning_backlog.py",
    ]
    assert batches["repair_session_publish"]["changed_paths"] == [
        "src/qa_z/commands/review_github.py",
        "src/qa_z/commands/review_packet.py",
        "src/qa_z/commands/reviewing.py",
        "src/qa_z/commands/session_repair.py",
        "src/qa_z/commands/session_verify.py",
        "src/qa_z/commands/sessioning.py",
        "tests/test_session_commands.py",
    ]
    assert batches["autonomy_loop_planner"]["changed_paths"] == [
        "src/qa_z/commands/runtime_autonomy.py",
    ]
    assert batches["benchmark_coverage"]["changed_paths"] == [
        "src/qa_z/commands/runtime_benchmark.py",
    ]
    assert batches["executor_return_path"]["changed_paths"] == [
        "src/qa_z/commands/runtime_bridge.py",
        "src/qa_z/commands/runtime_executor_result.py",
        "src/qa_z/commands/runtime_executor_result_stdout.py",
    ]
    assert result["cross_cutting_paths"] == []
    assert result["unassigned_source_paths"] == []


def test_commit_plan_reads_repository_context(tmp_path) -> None:
    module = load_plan_module()
    runner = FakeRunner(
        {
            ("git", "branch", "--show-current"): (0, "codex/qa-z-bootstrap\n", ""),
            ("git", "rev-parse", "HEAD"): (
                0,
                "4f63cf190b44f67e44559cf8dd8815ee2230f073\n",
                "",
            ),
        }
    )

    context = module.repository_context(tmp_path, runner=runner)

    assert context == {
        "branch": "codex/qa-z-bootstrap",
        "head": "4f63cf190b44f67e44559cf8dd8815ee2230f073",
    }
