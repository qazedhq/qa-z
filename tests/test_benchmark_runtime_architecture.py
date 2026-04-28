"""Layout guards for benchmark runtime seams."""

from __future__ import annotations

from pathlib import Path

import qa_z.benchmark_fixture_runtime as fixture_runtime_module
import qa_z.benchmark_runtime as runtime_module


def test_benchmark_runtime_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/benchmark_runtime.py": 80,
        "src/qa_z/benchmark_fixture_runtime.py": 260,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )


def test_benchmark_runtime_surface_targets_split_fixture_runner() -> None:
    source = Path("src/qa_z/benchmark_runtime.py").read_text(encoding="utf-8")

    assert "benchmark_fixture_runtime" in source
    assert "run_fixture as run_fixture_impl" in source
    assert "importlib" not in source


def test_benchmark_runtime_seams_import_directly() -> None:
    assert callable(runtime_module.run_fixture)
    assert callable(fixture_runtime_module.run_fixture)
