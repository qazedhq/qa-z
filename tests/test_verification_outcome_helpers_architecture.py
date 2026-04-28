from __future__ import annotations

from pathlib import Path


def test_verification_outcome_surface_targets_helper_modules() -> None:
    source = Path("src/qa_z/verification_outcome.py").read_text(encoding="utf-8")

    assert "verification_outcome_summary" in source
    assert "verification_outcome_render" in source


def test_verification_outcome_helper_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/verification_outcome_summary.py": 60,
        "src/qa_z/verification_outcome_render.py": 40,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )
