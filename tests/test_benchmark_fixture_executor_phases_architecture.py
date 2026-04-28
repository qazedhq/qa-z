from __future__ import annotations

from pathlib import Path


def test_benchmark_fixture_runtime_surface_targets_executor_phase_module() -> None:
    runtime_source = Path("src/qa_z/benchmark_fixture_runtime.py").read_text(
        encoding="utf-8"
    )

    assert "benchmark_fixture_executor_phases" in runtime_source
    assert "execute_executor_bridge_fixture(" not in runtime_source
    assert "execute_executor_result_fixture(" not in runtime_source
    assert "execute_executor_dry_run_fixture(" not in runtime_source


def test_benchmark_fixture_executor_phases_layout_budget_stays_small() -> None:
    line_count = len(
        Path("src/qa_z/benchmark_fixture_executor_phases.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 220, (
        f"benchmark_fixture_executor_phases.py exceeded budget: {line_count}"
    )
