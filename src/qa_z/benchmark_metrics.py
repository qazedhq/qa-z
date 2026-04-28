"""Metric helpers for benchmark coverage summaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_z.benchmark import BenchmarkFixtureResult


def category_rate(
    results: list["BenchmarkFixtureResult"], category: str
) -> dict[str, int | float]:
    """Calculate pass rate for one benchmark category."""
    applicable = [
        result.categories.get(category)
        for result in results
        if result.categories.get(category) is not None
    ]
    passed = sum(1 for item in applicable if item is True)
    total = len(applicable)
    return {"passed": passed, "total": total, "rate": rate(passed, total)}


def rate(passed: int, total: int) -> float:
    """Return a stable decimal pass rate."""
    if total == 0:
        return 0.0
    return round(passed / total, 4)


def category_coverage_label(category_summary: dict[str, int | float]) -> str:
    """Return whether a category has selected-fixture coverage."""
    return "covered" if int(category_summary["total"]) > 0 else "not covered"
