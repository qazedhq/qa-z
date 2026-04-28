"""Result assembly helpers for benchmark fixture runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z import benchmark as benchmark_module


def collect_artifact_actual(
    *,
    expectation: Any,
    workspace: Path,
    actual: dict[str, Any],
) -> None:
    if not expectation.expect_artifacts:
        return
    actual["artifact"] = benchmark_module.summarize_artifact_actual(workspace)


def record_execution_error(failures: list[str], exc: Exception) -> None:
    failures.append(f"execution error: {exc}")


def build_fixture_result(
    *,
    fixture: benchmark_module.BenchmarkFixture,
    actual: dict[str, Any],
    artifacts: dict[str, str],
    failures: list[str],
) -> benchmark_module.BenchmarkFixtureResult:
    failures.extend(benchmark_module.compare_expected(actual, fixture.expectation))
    categories = benchmark_module.categorize_result(failures, fixture.expectation)
    return benchmark_module.BenchmarkFixtureResult(
        name=fixture.name,
        passed=not failures,
        failures=failures,
        categories=categories,
        actual=actual,
        artifacts=artifacts,
    )
