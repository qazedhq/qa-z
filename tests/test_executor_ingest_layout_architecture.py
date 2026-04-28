"""Layout guards for executor-ingest seam modules."""

from __future__ import annotations

from pathlib import Path


def test_executor_ingest_layout_budgets_stay_small() -> None:
    budgets = {
        "src/qa_z/executor_ingest.py": 80,
        "src/qa_z/executor_ingest_flow.py": 300,
        "src/qa_z/executor_ingest_rejections.py": 120,
        "src/qa_z/executor_ingest_finalize.py": 120,
        "src/qa_z/executor_ingest_runtime.py": 90,
        "src/qa_z/executor_ingest_verification.py": 100,
    }

    for relative_path, budget in budgets.items():
        line_count = len(Path(relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= budget, (
            f"{relative_path} exceeded budget: {line_count}>{budget}"
        )


def test_executor_ingest_runtime_only_targets_split_seams() -> None:
    source = Path("src/qa_z/executor_ingest_runtime.py").read_text(encoding="utf-8")

    assert "executor_ingest_flow" in source
    assert "executor_ingest_verification" in source
    assert "_ingest_executor_result_artifact_impl" not in source
    assert "_verify_repair_session_impl" not in source
