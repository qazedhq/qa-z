"""Layout guards for benchmark summary seams."""

from __future__ import annotations

from pathlib import Path


def test_benchmark_summary_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/benchmark_summaries.py": 80,
        "src/qa_z/benchmark_run_summaries.py": 170,
        "src/qa_z/benchmark_executor_summaries.py": 230,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )


def test_benchmark_summaries_surface_targets_split_modules() -> None:
    source = Path("src/qa_z/benchmark_summaries.py").read_text(encoding="utf-8")

    assert "benchmark_run_summaries" in source
    assert "benchmark_executor_summaries" in source
    assert "def summarize_fast_actual" not in source
    assert "def summarize_executor_result_actual" not in source
