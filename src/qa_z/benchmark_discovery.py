"""Benchmark fixture discovery helpers."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z import benchmark as benchmark_module


def discover_fixtures(fixtures_dir: Path) -> list[benchmark_module.BenchmarkFixture]:
    """Discover benchmark fixtures containing an expected.json contract."""
    if not fixtures_dir.exists():
        return []
    fixtures: list[benchmark_module.BenchmarkFixture] = []
    for expected_path in sorted(fixtures_dir.glob("*/expected.json")):
        expectation = load_fixture_expectation(expected_path)
        fixture_dir = expected_path.parent
        fixtures.append(
            benchmark_module.BenchmarkFixture(
                name=expectation.name,
                path=fixture_dir,
                repo_path=fixture_dir / "repo",
                expectation=expectation,
            )
        )
    return sorted(fixtures, key=lambda fixture: fixture.name)


def load_fixture_expectation(
    expected_path: Path,
) -> benchmark_module.BenchmarkExpectation:
    """Load one expected.json contract."""
    try:
        data = json.loads(expected_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise benchmark_module.BenchmarkError(
            f"Could not read {expected_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise benchmark_module.BenchmarkError(
            f"{expected_path} is not valid JSON"
        ) from exc
    if not isinstance(data, dict):
        raise benchmark_module.BenchmarkError(
            f"{expected_path} must contain a JSON object."
        )
    try:
        return benchmark_module.BenchmarkExpectation.from_dict(data)
    except ValueError as exc:
        raise benchmark_module.BenchmarkError(f"{expected_path}: {exc}") from exc
