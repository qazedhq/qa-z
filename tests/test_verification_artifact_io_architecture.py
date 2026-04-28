from __future__ import annotations

from pathlib import Path


def test_verification_artifacts_surface_targets_loading_and_writing_modules() -> None:
    source = Path("src/qa_z/verification_artifacts.py").read_text(encoding="utf-8")

    assert "verification_artifact_loading" in source
    assert "verification_artifact_writing" in source


def test_verification_artifact_io_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/verification_artifact_loading.py": 60,
        "src/qa_z/verification_artifact_writing.py": 60,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )
