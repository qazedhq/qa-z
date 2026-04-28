"""Detail render helpers for benchmark reports."""

from __future__ import annotations

from typing import Any

from qa_z.benchmark_helpers import string_list


def generated_output_policy_lines() -> list[str]:
    return [
        "## Generated Output Policy",
        "",
        "- `benchmarks/results/summary.json` and `benchmarks/results/report.md` are generated benchmark outputs.",
        "- They are local by default; commit them only as intentional frozen evidence with surrounding context.",
        "- Snapshot directories matching `benchmarks/results-*` are generated runtime artifacts unless intentionally frozen with surrounding context.",
        "- `benchmarks/results/work/` is disposable scratch output.",
        "",
        "## Category Rates",
        "",
    ]


def render_category_rate_lines(
    category_rates: dict[str, dict[str, int | float]],
) -> list[str]:
    return [
        f"- {category}: {summary['passed']}/{summary['total']} ({summary['rate']}, {summary['coverage']})"
        for category, summary in category_rates.items()
    ]


def render_deep_warning_lines(deep_actual: dict[str, Any]) -> list[str]:
    warning_count = int(
        deep_actual.get("scan_quality_warning_count")
        or deep_actual.get("scan_warning_count")
        or 0
    )
    if not warning_count:
        return []
    lines = [f"- Deep scan warnings: {warning_count}"]
    for label, primary_key, fallback_key in (
        ("Warning types", "scan_quality_warning_types", "scan_warning_types"),
        ("Warning paths", "scan_quality_warning_paths", "scan_warning_paths"),
        ("Warning checks", "scan_quality_check_ids", None),
    ):
        values = string_list(deep_actual.get(primary_key))
        if not values and fallback_key:
            values = string_list(deep_actual.get(fallback_key))
        if values:
            lines.append(f"- {label}: {', '.join(values)}")
    return lines


def render_artifact_lines(artifacts: dict[str, Any]) -> list[str]:
    return [
        f"- Artifact {key}: {value}"
        for key, value in sorted((str(k), str(v)) for k, v in artifacts.items())
        if key.strip() and value.strip()
    ]


def render_fixture_lines(fixture: dict[str, Any]) -> list[str]:
    lines = [
        f"### {fixture['name']}",
        "",
        f"- Status: {'passed' if fixture['passed'] else 'failed'}",
    ]
    failures = fixture.get("failures") or []
    if failures:
        lines.append("- Failures:")
        lines.extend(f"  - {failure}" for failure in failures)
    else:
        lines.append("- Failures: none")
    actual = fixture.get("actual")
    if isinstance(actual, dict):
        deep_actual = actual.get("deep")
        if isinstance(deep_actual, dict):
            lines.extend(render_deep_warning_lines(deep_actual))
    artifacts = fixture.get("artifacts")
    if isinstance(artifacts, dict):
        lines.extend(render_artifact_lines(artifacts))
    lines.append("")
    return lines
