"""Layout guards for verification seam modules."""

from __future__ import annotations

from pathlib import Path


def test_verification_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/verification.py": 100,
        "src/qa_z/verification_findings.py": 110,
        "src/qa_z/verification_finding_support.py": 110,
        "src/qa_z/verification_finding_compare_support.py": 70,
        "src/qa_z/verification_status.py": 100,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )


def test_verification_surface_targets_split_finding_support() -> None:
    source = Path("src/qa_z/verification.py").read_text(encoding="utf-8")

    assert "verification_finding_support" in source
    assert "verification_findings" in source
    assert '"qa_z.verification_findings"\n).find_matching_candidate' not in source
    assert '"qa_z.verification_findings"\n).extract_deep_findings' not in source
    assert "importlib.import_module" not in source
    assert "import importlib" not in source
