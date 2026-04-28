from __future__ import annotations

from pathlib import Path


def test_benchmark_fixture_runtime_surface_targets_result_module() -> None:
    runtime_source = Path("src/qa_z/benchmark_fixture_runtime.py").read_text(
        encoding="utf-8"
    )

    assert "benchmark_fixture_results" in runtime_source
    assert "summarize_artifact_actual(" not in runtime_source
    assert "compare_expected(" not in runtime_source
    assert "categorize_result(" not in runtime_source
    assert "BenchmarkFixtureResult(" not in runtime_source


def test_benchmark_fixture_results_layout_budget_stays_small() -> None:
    line_count = len(
        Path("src/qa_z/benchmark_fixture_results.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 160, (
        f"benchmark_fixture_results.py exceeded budget: {line_count}"
    )
