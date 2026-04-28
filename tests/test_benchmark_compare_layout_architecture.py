"""Layout guards for benchmark comparison seams."""

from __future__ import annotations

from pathlib import Path


def test_benchmark_compare_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/benchmark_compare.py": 110,
        "src/qa_z/benchmark_compare_support.py": 110,
        "src/qa_z/benchmark_expectation_keys.py": 80,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )


def test_benchmark_compare_surface_targets_split_support_modules() -> None:
    compare_source = Path("src/qa_z/benchmark_compare.py").read_text(encoding="utf-8")
    summary_source = Path("src/qa_z/benchmark_summary.py").read_text(encoding="utf-8")

    assert "benchmark_compare_support" in compare_source
    assert "benchmark_expectation_keys" in compare_source
    assert "def compare_absent_list" not in compare_source
    assert "def compare_expected_list" not in compare_source
    assert "def compare_minimum" not in compare_source
    assert "def compare_maximum" not in compare_source
    assert "def expectation_actual_key" not in compare_source
    assert "def has_policy_expectation" not in compare_source
    assert "benchmark_expectation_keys" in summary_source
