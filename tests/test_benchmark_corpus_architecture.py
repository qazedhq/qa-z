from __future__ import annotations

from pathlib import Path


def test_benchmark_corpus_and_summary_tests_live_in_split_file() -> None:
    split_source = Path("tests/test_benchmark_corpus.py").read_text(encoding="utf-8")
    benchmark_source = Path("tests/test_benchmark.py").read_text(encoding="utf-8")

    for test_name in (
        "test_build_benchmark_summary_calculates_category_rates",
        "test_build_benchmark_summary_counts_executor_dry_run_fixtures_under_policy",
        "test_categorize_result_counts_executor_result_only_expectations",
        "test_build_benchmark_summary_counts_executor_result_category",
        "test_typescript_benchmark_results_are_counted_in_summary",
        "test_committed_benchmark_corpus_has_initial_high_signal_set",
        "test_committed_benchmark_corpus_has_executor_dry_run_fixture_set",
        "test_committed_executor_dry_run_fixtures_pin_complete_rule_buckets",
    ):
        assert test_name in split_source
        assert test_name not in benchmark_source


def test_benchmark_main_test_file_stays_under_split_budget() -> None:
    line_count = len(
        Path("tests/test_benchmark.py").read_text(encoding="utf-8").splitlines()
    )

    assert line_count <= 800
