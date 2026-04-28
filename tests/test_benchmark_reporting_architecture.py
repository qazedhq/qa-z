from __future__ import annotations

from pathlib import Path


def test_benchmark_reporting_surface_targets_report_detail_module() -> None:
    source = Path("src/qa_z/benchmark_reporting.py").read_text(encoding="utf-8")

    assert "benchmark_report_details" in source
    assert "string_list(" not in source


def test_benchmark_reporting_layout_budget_stays_small() -> None:
    line_count = len(
        Path("src/qa_z/benchmark_reporting.py").read_text(encoding="utf-8").splitlines()
    )

    assert line_count <= 65, f"benchmark_reporting.py exceeded budget: {line_count}"
