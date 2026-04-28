"""Architecture tests for executor-ingest finalize helpers."""

from __future__ import annotations

from pathlib import Path


def test_executor_ingest_finalize_module_exists() -> None:
    assert Path("src/qa_z/executor_ingest_finalize.py").exists()


def test_executor_ingest_flow_routes_success_tail_through_finalize_module() -> None:
    source = Path("src/qa_z/executor_ingest_flow.py").read_text(encoding="utf-8")

    assert "executor_ingest_finalize" in source
    assert "finalized_ingest_outcome(" not in source
    assert "record_loop_executor_result(" not in source
