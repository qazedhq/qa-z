from __future__ import annotations

from pathlib import Path

import qa_z.benchmark_executor_bridge_runtime as bridge_runtime_module
import qa_z.benchmark_executor_dry_run_runtime as dry_run_runtime_module
import qa_z.benchmark_executor_result_runtime as result_runtime_module


def test_benchmark_execution_surface_targets_split_executor_runtime_modules() -> None:
    source = Path("src/qa_z/benchmark_execution.py").read_text(encoding="utf-8")

    assert "__all__" in source
    assert "execute_fast_fixture" in source
    assert "execute_verify_fixture" in source


def test_split_executor_runtime_modules_expose_helpers() -> None:
    assert callable(bridge_runtime_module.execute_executor_bridge_fixture)
    assert callable(result_runtime_module.execute_executor_result_fixture)
    assert callable(dry_run_runtime_module.execute_executor_dry_run_fixture)


def test_executor_runtime_integration_tests_live_in_split_file() -> None:
    split_source = Path("tests/test_benchmark_executor_runtime.py").read_text(
        encoding="utf-8"
    )
    operator_source = Path(
        "tests/test_benchmark_executor_runtime_operator_actions.py"
    ).read_text(encoding="utf-8")
    benchmark_source = Path("tests/test_benchmark.py").read_text(encoding="utf-8")

    for test_name in (
        "test_run_benchmark_executes_executor_result_candidate_run_fixture",
        "test_run_benchmark_executes_executor_result_future_timestamp_rejection_fixture",
        "test_run_benchmark_executes_executor_result_partial_fixture_with_realism_fields",
        "test_run_benchmark_executes_executor_result_validation_conflict_fixture",
        "test_run_benchmark_executes_executor_dry_run_fixture",
    ):
        assert test_name in split_source
        assert test_name not in benchmark_source
    assert (
        "test_run_benchmark_executes_mixed_partial_rejected_executor_dry_run_fixture"
        in operator_source
    )
    assert (
        "test_run_benchmark_executes_mixed_partial_rejected_executor_dry_run_fixture"
        not in benchmark_source
    )


def test_split_executor_runtime_test_file_stays_under_budget() -> None:
    line_count = len(
        Path("tests/test_benchmark_executor_runtime.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 700


def test_executor_runtime_operator_action_test_file_stays_under_budget() -> None:
    line_count = len(
        Path("tests/test_benchmark_executor_runtime_operator_actions.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 220
