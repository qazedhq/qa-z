from __future__ import annotations

from pathlib import Path


def test_verification_status_surface_targets_summary_counts_module() -> None:
    source = Path("src/qa_z/verification_status.py").read_text(encoding="utf-8")

    assert "verification_summary_counts" in source


def test_verification_summary_counts_layout_budget_stays_small() -> None:
    line_count = len(
        Path("src/qa_z/verification_summary_counts.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 80, (
        f"verification_summary_counts.py exceeded budget: {line_count}"
    )
