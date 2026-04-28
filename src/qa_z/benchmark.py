"""Reproducible benchmark corpus runner for QA-Z artifacts."""

from __future__ import annotations

from pathlib import Path

from qa_z.benchmark_compare import compare_expected, compare_section
from qa_z.benchmark_compare_support import (
    compare_absent_list,
    compare_expected_list,
    compare_maximum,
    compare_minimum,
)
from qa_z.benchmark_contracts import (
    BenchmarkError,
    BenchmarkExpectation,
    BenchmarkFixture,
    BenchmarkFixtureResult,
)
from qa_z.benchmark_discovery import discover_fixtures, load_fixture_expectation
from qa_z.benchmark_execution import (
    execute_deep_fixture,
    execute_fast_fixture,
    execute_handoff_fixture,
    execute_verify_fixture,
)
from qa_z.benchmark_executor_execution import (
    execute_executor_bridge_fixture,
    execute_executor_dry_run_fixture,
    execute_executor_result_fixture,
)
from qa_z.benchmark_executor_loop_context import write_benchmark_loop_context
from qa_z.benchmark_expectation_keys import (
    expectation_actual_key,
    has_policy_expectation,
)
from qa_z.benchmark_helpers import (
    aggregate_filter_reasons,
    coerce_number,
    format_path,
    read_json_object,
    unique_strings,
)
from qa_z.benchmark_metrics import category_coverage_label, category_rate, rate
from qa_z.benchmark_reporting import (
    render_benchmark_report,
    write_benchmark_artifacts,
)
from qa_z.benchmark_runtime import run_benchmark, run_fixture
from qa_z.benchmark_summaries import (
    summarize_artifact_actual,
    summarize_deep_actual,
    summarize_executor_bridge_actual,
    summarize_executor_dry_run_actual,
    summarize_executor_result_actual,
    summarize_fast_actual,
    summarize_handoff_actual,
    summarize_verify_actual,
    summarize_verify_summary_actual,
)
from qa_z.benchmark_summary import (
    benchmark_snapshot,
    build_benchmark_summary,
    category_status,
    categorize_result,
)
from qa_z.benchmark_workspace import (
    benchmark_results_lock,
    fixture_path_environment,
    install_support_files,
    prepare_workspace,
    reset_directory,
    rmtree_with_retries,
    unlink_with_retries,
)

DEFAULT_FIXTURES_DIR = Path("benchmarks") / "fixtures"
DEFAULT_RESULTS_DIR = Path("benchmarks") / "results"

__all__ = [
    "DEFAULT_FIXTURES_DIR",
    "DEFAULT_RESULTS_DIR",
    "BenchmarkError",
    "BenchmarkExpectation",
    "BenchmarkFixture",
    "BenchmarkFixtureResult",
    "aggregate_filter_reasons",
    "benchmark_results_lock",
    "benchmark_snapshot",
    "build_benchmark_summary",
    "categorize_result",
    "category_coverage_label",
    "category_rate",
    "category_status",
    "coerce_number",
    "compare_absent_list",
    "compare_expected",
    "compare_expected_list",
    "compare_maximum",
    "compare_minimum",
    "compare_section",
    "discover_fixtures",
    "execute_deep_fixture",
    "execute_executor_bridge_fixture",
    "execute_executor_dry_run_fixture",
    "execute_executor_result_fixture",
    "execute_fast_fixture",
    "execute_handoff_fixture",
    "execute_verify_fixture",
    "expectation_actual_key",
    "fixture_path_environment",
    "format_path",
    "has_policy_expectation",
    "install_support_files",
    "load_fixture_expectation",
    "prepare_workspace",
    "rate",
    "read_json_object",
    "render_benchmark_report",
    "reset_directory",
    "rmtree_with_retries",
    "run_benchmark",
    "run_fixture",
    "summarize_artifact_actual",
    "summarize_deep_actual",
    "summarize_executor_bridge_actual",
    "summarize_executor_dry_run_actual",
    "summarize_executor_result_actual",
    "summarize_fast_actual",
    "summarize_handoff_actual",
    "summarize_verify_actual",
    "summarize_verify_summary_actual",
    "unique_strings",
    "unlink_with_retries",
    "write_benchmark_artifacts",
    "write_benchmark_loop_context",
]
