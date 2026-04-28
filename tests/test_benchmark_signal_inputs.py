"""Tests for benchmark signal-input helpers."""

from __future__ import annotations

from pathlib import Path

import qa_z.benchmark_signals as benchmark_signals_module
from tests.self_improvement_test_support import (
    write_aggregate_only_failed_benchmark_summary,
)


def test_discover_benchmark_candidate_inputs_synthesizes_summary_level_failure(
    tmp_path: Path,
) -> None:
    write_aggregate_only_failed_benchmark_summary(tmp_path)

    candidates = benchmark_signals_module.discover_benchmark_candidate_inputs(tmp_path)

    assert candidates == [
        {
            "path": tmp_path / "benchmarks" / "results" / "summary.json",
            "fixture_name": "summary",
            "failures": [
                "benchmark summary reports 1 failed fixture without fixture details"
            ],
            "snapshot": "1/2 fixtures, overall_rate 0.5",
        }
    ]
