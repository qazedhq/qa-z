"""Benchmark runtime orchestration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z import benchmark as benchmark_module
from qa_z import benchmark_runtime_support
from qa_z.benchmark_fixture_runtime import run_fixture as run_fixture_impl


def run_benchmark(
    *,
    fixtures_dir: Path = Path("benchmarks") / "fixtures",
    results_dir: Path = Path("benchmarks") / "results",
    fixture_names: list[str] | None = None,
) -> dict[str, Any]:
    """Run benchmark fixtures, compare outputs, and write summary artifacts."""
    fixtures = benchmark_runtime_support.select_requested_fixtures(
        benchmark_module.discover_fixtures(fixtures_dir), fixture_names
    )
    results_dir.mkdir(parents=True, exist_ok=True)
    with benchmark_module.benchmark_results_lock(results_dir):
        work_dir = benchmark_runtime_support.prepare_work_dir(results_dir)
        results = benchmark_runtime_support.run_fixture_batch(
            fixtures, work_dir=work_dir, results_dir=results_dir
        )
        summary = benchmark_module.build_benchmark_summary(results)
        benchmark_module.write_benchmark_artifacts(summary, results_dir)
        return summary


def run_fixture(*args, **kwargs):
    return run_fixture_impl(*args, **kwargs)
