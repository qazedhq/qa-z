from __future__ import annotations

from pathlib import Path


def test_benchmark_executor_result_runtime_uses_session_setup_module() -> None:
    source = Path("src/qa_z/benchmark_executor_result_runtime.py").read_text(
        encoding="utf-8"
    )

    assert "benchmark_executor_session_setup" in source
    assert "create_repair_session(" not in source
    assert "seed_executor_session(" in source
    assert "session_manifest_path = (" not in source


def test_benchmark_executor_session_setup_layout_budget_stays_small() -> None:
    line_count = len(
        Path("src/qa_z/benchmark_executor_session_setup.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 80, (
        f"benchmark_executor_session_setup.py exceeded budget: {line_count}"
    )
