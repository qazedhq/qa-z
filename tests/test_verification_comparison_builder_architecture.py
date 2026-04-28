from __future__ import annotations

from pathlib import Path


def test_verification_compare_surface_targets_builder_module() -> None:
    source = Path("src/qa_z/verification_compare.py").read_text(encoding="utf-8")

    assert "verification_comparison_builder" in source


def test_verification_comparison_builder_layout_budget_stays_small() -> None:
    line_count = len(
        Path("src/qa_z/verification_comparison_builder.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 70, (
        f"verification_comparison_builder.py exceeded budget: {line_count}"
    )
