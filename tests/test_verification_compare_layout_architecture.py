"""Layout guards for verification compare seams."""

from __future__ import annotations

from pathlib import Path

import qa_z.verification_compare as verification_compare_module
import qa_z.verification_fast_compare as verification_fast_compare_module


def test_verification_compare_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/verification_compare.py": 70,
        "src/qa_z/verification_fast_compare.py": 90,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )


def test_verification_compare_surface_targets_fast_compare_module() -> None:
    source = Path("src/qa_z/verification_compare.py").read_text(encoding="utf-8")

    assert "verification_fast_compare" in source
    assert "importlib" not in source
    assert "def compare_fast_checks" not in source
    assert "def classify_fast_check" not in source


def test_verification_compare_surface_imports_direct_fast_compare() -> None:
    assert (
        verification_compare_module.compare_fast_checks
        is verification_fast_compare_module.compare_fast_checks
    )
