"""Layout guards for verification model seams."""

from __future__ import annotations

from pathlib import Path

import qa_z.verification_delta_models as verification_delta_models_module
import qa_z.verification_models as verification_models_module
import qa_z.verification_run_models as verification_run_models_module


def test_verification_model_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/verification_models.py": 80,
        "src/qa_z/verification_run_models.py": 120,
        "src/qa_z/verification_delta_models.py": 150,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )


def test_verification_models_surface_targets_split_modules() -> None:
    source = Path("src/qa_z/verification_models.py").read_text(encoding="utf-8")

    assert "verification_run_models" in source
    assert "verification_delta_models" in source
    assert "importlib" not in source
    assert "class VerificationRun" not in source
    assert "class VerificationFindingDelta" not in source


def test_verification_models_surface_imports_split_models_directly() -> None:
    assert (
        verification_models_module.VerificationRun
        is verification_run_models_module.VerificationRun
    )
    assert (
        verification_models_module.VerificationComparison
        is verification_run_models_module.VerificationComparison
    )
    assert (
        verification_models_module.VerificationFindingDelta
        is verification_delta_models_module.VerificationFindingDelta
    )
