"""Benchmark summary loading helpers for self-improvement planning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.self_improvement_runtime import read_json_object

__all__ = [
    "benchmark_summaries",
    "benchmark_summary_snapshot",
]


def benchmark_summary_snapshot(summary: dict[str, Any]) -> str:
    """Return compact benchmark snapshot text when available."""
    snapshot = str(summary.get("snapshot") or "").strip()
    if snapshot:
        return snapshot
    passed = summary.get("fixtures_passed")
    total = summary.get("fixtures_total")
    overall_rate = summary.get("overall_rate")
    if passed is None or total is None or overall_rate is None:
        return ""
    overall_rate_text = str(overall_rate).strip()
    if not overall_rate_text:
        return ""
    return (
        f"{int_value(passed)}/{int_value(total)} fixtures, "
        f"overall_rate {overall_rate_text}"
    )


def benchmark_summaries(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Return known benchmark summary artifacts."""
    candidates = [root / "benchmarks" / "results" / "summary.json"]
    results: list[tuple[Path, dict[str, Any]]] = []
    for path in candidates:
        if not path.is_file():
            continue
        summary = read_json_object(path)
        if summary.get("kind") == "qa_z.benchmark_summary":
            results.append((path, summary))
    return results


def int_value(value: object) -> int:
    """Return an integer value, or zero when absent or invalid."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
