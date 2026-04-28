from __future__ import annotations

from pathlib import Path


def test_benchmark_executor_execution_surface_targets_loop_context_module() -> None:
    result_source = Path("src/qa_z/benchmark_executor_result_runtime.py").read_text(
        encoding="utf-8"
    )
    bridge_source = Path("src/qa_z/benchmark_executor_bridge_runtime.py").read_text(
        encoding="utf-8"
    )

    assert "benchmark_executor_loop_context" in result_source
    assert "benchmark_executor_loop_context" in bridge_source


def test_benchmark_executor_loop_context_layout_budget_stays_small() -> None:
    line_count = len(
        Path("src/qa_z/benchmark_executor_loop_context.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 90, (
        f"benchmark_executor_loop_context.py exceeded budget: {line_count}"
    )
