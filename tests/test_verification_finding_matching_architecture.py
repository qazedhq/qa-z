from __future__ import annotations

from pathlib import Path


def test_verification_findings_surface_targets_matching_module() -> None:
    source = Path("src/qa_z/verification_findings.py").read_text(encoding="utf-8")

    assert "verification_finding_matching" in source


def test_verification_finding_matching_layout_budget_stays_small() -> None:
    line_count = len(
        Path("src/qa_z/verification_finding_matching.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 120, (
        f"verification_finding_matching.py exceeded budget: {line_count}"
    )
