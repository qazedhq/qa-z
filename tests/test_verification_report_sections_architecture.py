from __future__ import annotations

from pathlib import Path


def test_verification_report_surface_targets_section_module() -> None:
    source = Path("src/qa_z/verification_report.py").read_text(encoding="utf-8")

    assert "verification_report_sections" in source


def test_verification_report_sections_layout_budget_stays_small() -> None:
    line_count = len(
        Path("src/qa_z/verification_report_sections.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 90, (
        f"verification_report_sections.py exceeded budget: {line_count}"
    )
