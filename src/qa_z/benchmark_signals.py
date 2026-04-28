"""Benchmark-summary observation helpers for self-improvement planning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.benchmark_signal_artifacts import (
    benchmark_summaries,
    benchmark_summary_snapshot,
)

__all__ = [
    "benchmark_summaries",
    "benchmark_summary_snapshot",
    "discover_benchmark_candidate_inputs",
]


def discover_benchmark_candidate_inputs(root: Path) -> list[dict[str, Any]]:
    """Return failed benchmark fixture packets for backlog candidate creation."""
    candidates: list[dict[str, Any]] = []
    for path, summary in benchmark_summaries(root):
        failed_count = int_value(summary.get("fixtures_failed"))
        if failed_count <= 0:
            continue
        candidate_count_before = len(candidates)
        snapshot = benchmark_summary_snapshot(summary)
        fixtures = summary.get("fixtures")
        failed_names = [
            str(name)
            for name in summary.get("failed_fixtures", [])
            if str(name).strip()
        ]
        if isinstance(fixtures, list):
            for fixture in fixtures:
                if not isinstance(fixture, dict) or fixture.get("passed") is not False:
                    continue
                name = str(fixture.get("name") or "unknown").strip()
                failures = [
                    str(item)
                    for item in fixture.get("failures", [])
                    if str(item).strip()
                ]
                candidates.append(
                    {
                        "path": path,
                        "fixture_name": name,
                        "failures": failures,
                        "snapshot": snapshot,
                    }
                )
        else:
            for name in failed_names:
                candidates.append(
                    {
                        "path": path,
                        "fixture_name": name,
                        "failures": [],
                        "snapshot": snapshot,
                    }
                )
        if len(candidates) == candidate_count_before:
            fixture_word = "fixture" if failed_count == 1 else "fixtures"
            candidates.append(
                {
                    "path": path,
                    "fixture_name": "summary",
                    "failures": [
                        (
                            f"benchmark summary reports {failed_count} failed "
                            f"{fixture_word} without fixture details"
                        )
                    ],
                    "snapshot": snapshot,
                }
            )
    return candidates


def int_value(value: object) -> int:
    """Return an integer value, or zero when absent or invalid."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
