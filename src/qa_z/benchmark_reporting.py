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
    try:
        results_dir.mkdir(parents=True, exist_ok=True)
        write_benchmark_summary(
            results_dir / "summary.json",
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
        )
        write_benchmark_report(
            results_dir / "report.md", render_benchmark_report(summary)
        )
    except OSError as exc:
        raise OSError(
            f"could not write benchmark artifacts to {results_dir}: {exc}"
        ) from exc


def write_benchmark_summary(path: Path, text: str) -> None:
    """Write the benchmark summary JSON with path-aware failures."""
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise OSError(
            f"could not write benchmark summary artifact {path}: {exc}"
        ) from exc


def write_benchmark_report(path: Path, text: str) -> None:
    """Write the benchmark Markdown report with path-aware failures."""
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise OSError(
            f"could not write benchmark report artifact {path}: {exc}"
        ) from exc
