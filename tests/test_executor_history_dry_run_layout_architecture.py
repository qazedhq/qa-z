"""Layout guards for executor-history and executor dry-run seams."""

from __future__ import annotations

from pathlib import Path


def test_executor_history_and_dry_run_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/executor_history.py": 70,
        "src/qa_z/executor_history_support.py": 60,
        "src/qa_z/executor_history_store.py": 280,
        "src/qa_z/executor_dry_run.py": 80,
        "src/qa_z/executor_dry_run_summary.py": 70,
        "src/qa_z/executor_dry_run_render.py": 75,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )


def test_executor_dry_run_surface_only_targets_split_seams() -> None:
    source = Path("src/qa_z/executor_dry_run.py").read_text(encoding="utf-8")

    assert "executor_dry_run_summary" in source
    assert "executor_dry_run_render" in source
    assert "def load_safety_package" not in source
    assert "def dry_run_summary" not in source
    assert "def render_dry_run_report" not in source
    assert "def normalize_recommended_actions" not in source


def test_executor_history_store_routes_helper_work_to_support_module() -> None:
    source = Path("src/qa_z/executor_history_store.py").read_text(encoding="utf-8")

    assert "executor_history_support" in source
    assert "write_json(" in source
    assert "allocate_attempt_id(" in source
    assert "legacy_attempt_base(" in source
