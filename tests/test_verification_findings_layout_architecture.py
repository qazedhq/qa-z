"""Layout guards for verification finding seams."""

from __future__ import annotations

from pathlib import Path

import qa_z.verification_findings as verification_findings_module


def test_verification_finding_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/verification_findings.py": 120,
        "src/qa_z/verification_finding_support.py": 150,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )


def test_verification_findings_surface_targets_support_module() -> None:
    source = Path("src/qa_z/verification_findings.py").read_text(encoding="utf-8")

    assert "verification_finding_support" in source
    assert "verification_finding_matching" in source
    assert "verification_finding_compare_support" in source
    assert "importlib" not in source
    assert "def find_matching_candidate" not in source
    assert "def extract_deep_findings" not in source
    assert "def normalize_active_finding" not in source


def test_verification_findings_surface_keeps_explicit_public_contract() -> None:
    assert verification_findings_module.__all__ == ["compare_deep_findings_impl"]
