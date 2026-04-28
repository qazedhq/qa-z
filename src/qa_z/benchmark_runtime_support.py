"""Support helpers for benchmark runtime orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from qa_z import benchmark as benchmark_module


def select_requested_fixtures(
    fixtures: Sequence[benchmark_module.BenchmarkFixture],
    fixture_names: list[str] | None,
) -> list[benchmark_module.BenchmarkFixture]:
    selected = list(fixtures)
    if not fixture_names:
        return selected
    requested = set(fixture_names)
    available = {fixture.name for fixture in selected}
    missing = sorted(requested - available)
    if missing:
        raise benchmark_module.BenchmarkError(
            "unknown benchmark fixtures requested: " + ", ".join(missing)
        )
    return [fixture for fixture in selected if fixture.name in requested]


def prepare_work_dir(results_dir: Path) -> Path:
    work_dir = results_dir / "work"
    benchmark_module.reset_directory(work_dir)
    return work_dir


def run_fixture_batch(
    fixtures: Sequence[benchmark_module.BenchmarkFixture],
    *,
    work_dir: Path,
    results_dir: Path,
) -> list[benchmark_module.BenchmarkFixtureResult]:
    return [
        benchmark_module.run_fixture(
            fixture, work_dir=work_dir, results_dir=results_dir
        )
        for fixture in fixtures
    ]
