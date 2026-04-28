"""Layout guards for benchmark execution seams."""

from __future__ import annotations

from pathlib import Path


def test_benchmark_execution_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/benchmark_execution.py": 130,
        "src/qa_z/benchmark_executor_execution.py": 200,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )


def test_benchmark_execution_surface_targets_executor_split_module() -> None:
    source = Path("src/qa_z/benchmark_execution.py").read_text(encoding="utf-8")

    assert "__all__" in source
    assert "def execute_executor_result_fixture" not in source
    assert "def execute_executor_bridge_fixture" not in source
    assert "def write_benchmark_loop_context" not in source
    assert "def execute_executor_dry_run_fixture" not in source
