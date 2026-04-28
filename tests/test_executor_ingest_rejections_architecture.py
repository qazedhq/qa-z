"""Architecture tests for executor-ingest rejection helpers."""

from __future__ import annotations

from pathlib import Path


def test_executor_ingest_rejections_module_exists() -> None:
    assert Path("src/qa_z/executor_ingest_rejections.py").exists()


def test_executor_ingest_flow_routes_rejections_through_helper_module() -> None:
    source = Path("src/qa_z/executor_ingest_flow.py").read_text(encoding="utf-8")

    assert "executor_ingest_rejections" in source
    assert "rejected_ingest_outcome(" not in source
    assert "ExecutorResultIngestRejected(" not in source
