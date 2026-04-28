"""Architecture tests for executor-ingest session helpers."""

from __future__ import annotations

import qa_z.executor_ingest_session as executor_ingest_session_module


def test_executor_ingest_session_module_exposes_persistence_helpers() -> None:
    assert callable(executor_ingest_session_module.persist_ingested_result)
    assert callable(executor_ingest_session_module.resume_verification_if_ready)
    assert callable(executor_ingest_session_module.record_loop_executor_result)
