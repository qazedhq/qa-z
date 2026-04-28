"""Benchmark report rendering and artifact-writing helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z import benchmark as benchmark_module
from qa_z import benchmark_report_details


def render_benchmark_report(summary: dict[str, Any]) -> str:
    """Render a human-readable benchmark report."""
    category_rates = {
        category: {
            **category_summary,
            "coverage": benchmark_module.category_coverage_label(category_summary),
        }
        for category, category_summary in summary["category_rates"].items()
    }
    lines = [
        "# QA-Z Benchmark Report",
        "",
        f"- Snapshot: {summary['snapshot']}",
        f"- Fixtures run: {summary['fixtures_total']}",
        f"- Fixtures passed: {summary['fixtures_passed']}",
        f"- Fixtures failed: {summary['fixtures_failed']}",
        f"- Overall pass rate: {summary['overall_rate']}",
        "",
        *benchmark_report_details.generated_output_policy_lines(),
        *benchmark_report_details.render_category_rate_lines(category_rates),
        "",
        "## Fixture Results",
        "",
    ]
    for fixture in summary["fixtures"]:
        lines.extend(benchmark_report_details.render_fixture_lines(fixture))
    return "\n".join(lines).strip() + "\n"


def write_benchmark_artifacts(summary: dict[str, Any], results_dir: Path) -> None:
    """Write benchmark summary JSON and Markdown report artifacts."""
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (results_dir / "report.md").write_text(
        render_benchmark_report(summary), encoding="utf-8"
    )
