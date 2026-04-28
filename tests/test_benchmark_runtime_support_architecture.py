from __future__ import annotations

from pathlib import Path


def test_benchmark_runtime_surface_targets_support_module() -> None:
    source = Path("src/qa_z/benchmark_runtime.py").read_text(encoding="utf-8")

    assert "benchmark_runtime_support" in source
    assert "benchmark_fixture_runtime" in source
    assert "requested =" not in source
    assert "reset_directory(" not in source
    assert "run_fixture as run_fixture_impl" in source


def test_benchmark_runtime_support_layout_budget_stays_small() -> None:
    line_count = len(
        Path("src/qa_z/benchmark_runtime_support.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 120, (
        f"benchmark_runtime_support.py exceeded budget: {line_count}"
    )
