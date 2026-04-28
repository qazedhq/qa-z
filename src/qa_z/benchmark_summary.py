"""Summary helpers for benchmark fixture results."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qa_z.benchmark_expectation_keys import has_policy_expectation
from qa_z.benchmark_metrics import category_rate, rate

if TYPE_CHECKING:
    from qa_z.benchmark import BenchmarkExpectation, BenchmarkFixtureResult


BENCHMARK_SUMMARY_KIND = "qa_z.benchmark_summary"
BENCHMARK_SCHEMA_VERSION = 1
CATEGORY_NAMES = (
    "detection",
    "handoff",
    "verify",
    "artifact",
    "policy",
    "executor_result",
)


def categorize_result(
    failures: list[str], expectation: "BenchmarkExpectation"
) -> dict[str, bool | None]:
    """Summarize pass/fail by benchmark concern."""
    return {
        "detection": category_status(
            failures,
            prefixes=("fast.", "deep."),
            applies=bool(expectation.expect_fast or expectation.expect_deep),
        ),
        "handoff": category_status(
            failures,
            prefixes=("handoff.",),
            applies=bool(expectation.expect_handoff),
        ),
        "verify": category_status(
            failures,
            prefixes=("verify.",),
            applies=bool(expectation.expect_verify),
        ),
        "artifact": category_status(
            failures,
            prefixes=("artifact.", "executor_bridge."),
            applies=bool(
                expectation.expect_artifacts or expectation.expect_executor_bridge
            ),
        ),
        "policy": category_status(
            failures,
            prefixes=("deep.", "executor_dry_run."),
            applies=bool(expectation.expect_executor_dry_run)
            or has_policy_expectation(expectation.expect_deep),
        ),
        "executor_result": category_status(
            failures,
            prefixes=("executor_result.",),
            applies=bool(expectation.expect_executor_result),
        ),
    }


def category_status(
    failures: list[str], *, prefixes: tuple[str, ...], applies: bool
) -> bool | None:
    """Return category status, or None when no expectation covered it."""
    if not applies:
        return None
    return not any(failure.startswith(prefixes) for failure in failures)


def build_benchmark_summary(
    results: list["BenchmarkFixtureResult"],
) -> dict[str, Any]:
    """Build aggregate benchmark summary data."""
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    overall_rate = rate(passed, len(results))
    return {
        "kind": BENCHMARK_SUMMARY_KIND,
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "fixtures_total": len(results),
        "fixtures_passed": passed,
        "fixtures_failed": failed,
        "overall_rate": overall_rate,
        "snapshot": benchmark_snapshot(passed, len(results), overall_rate),
        "category_rates": {
            category: category_rate(results, category) for category in CATEGORY_NAMES
        },
        "failed_fixtures": [result.name for result in results if not result.passed],
        "fixtures": [result.to_dict() for result in results],
    }


def benchmark_snapshot(
    fixtures_passed: int, fixtures_total: int, overall_rate: float
) -> str:
    """Return the compact benchmark snapshot used by reports and docs."""
    return f"{fixtures_passed}/{fixtures_total} fixtures, overall_rate {overall_rate}"
