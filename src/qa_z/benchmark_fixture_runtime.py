"""Fixture-level benchmark runtime orchestration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound
from qa_z import benchmark as benchmark_module
from qa_z import benchmark_fixture_executor_phases
from qa_z import benchmark_fixture_phases
from qa_z import benchmark_fixture_results
from qa_z.config import load_config


def run_fixture(
    fixture: benchmark_module.BenchmarkFixture,
    *,
    work_dir: Path,
    results_dir: Path,
) -> benchmark_module.BenchmarkFixtureResult:
    """Execute one benchmark fixture and compare it to its expectation."""
    actual: dict[str, Any] = {}
    artifacts: dict[str, str] = {}
    failures: list[str] = []
    workspace = benchmark_module.prepare_workspace(fixture, work_dir)
    config = load_config(workspace)
    run_dir = workspace / ".qa-z" / "runs" / "benchmark"
    artifacts["workspace"] = benchmark_module.format_path(workspace, results_dir)

    try:
        with benchmark_module.fixture_path_environment(workspace):
            benchmark_fixture_phases.run_fast_phase(
                expectation=fixture.expectation,
                workspace=workspace,
                config=config,
                run_dir=run_dir,
                results_dir=results_dir,
                actual=actual,
                artifacts=artifacts,
            )
            benchmark_fixture_phases.run_deep_phase(
                expectation=fixture.expectation,
                workspace=workspace,
                config=config,
                run_dir=run_dir,
                results_dir=results_dir,
                actual=actual,
                artifacts=artifacts,
            )
            benchmark_fixture_phases.run_handoff_phase(
                expectation=fixture.expectation,
                workspace=workspace,
                config=config,
                run_dir=run_dir,
                results_dir=results_dir,
                actual=actual,
                artifacts=artifacts,
            )
            benchmark_fixture_phases.run_verify_phase(
                expectation=fixture.expectation,
                workspace=workspace,
                config=config,
                results_dir=results_dir,
                actual=actual,
                artifacts=artifacts,
            )

            benchmark_fixture_executor_phases.run_executor_bridge_phase(
                expectation=fixture.expectation,
                workspace=workspace,
                config=config,
                results_dir=results_dir,
                actual=actual,
                artifacts=artifacts,
            )
            benchmark_fixture_executor_phases.run_executor_result_phase(
                expectation=fixture.expectation,
                workspace=workspace,
                config=config,
                results_dir=results_dir,
                actual=actual,
                artifacts=artifacts,
            )
            benchmark_fixture_executor_phases.run_executor_dry_run_phase(
                expectation=fixture.expectation,
                workspace=workspace,
                actual=actual,
                artifacts=artifacts,
            )

            benchmark_fixture_results.collect_artifact_actual(
                expectation=fixture.expectation,
                workspace=workspace,
                actual=actual,
            )
    except (
        ArtifactLoadError,
        ArtifactSourceNotFound,
        benchmark_module.BenchmarkError,
        FileNotFoundError,
        ValueError,
    ) as exc:
        benchmark_fixture_results.record_execution_error(failures, exc)

    return benchmark_fixture_results.build_fixture_result(
        fixture=fixture,
        actual=actual,
        artifacts=artifacts,
        failures=failures,
    )
