"""Architecture tests for executor-ingest candidate rerun helpers."""

from __future__ import annotations

import qa_z.executor_ingest_candidate as executor_ingest_candidate_module


def test_executor_ingest_candidate_module_exposes_rerun_helpers() -> None:
    assert callable(executor_ingest_candidate_module.create_verify_candidate_run)
    assert callable(
        executor_ingest_candidate_module.write_verify_rerun_review_artifacts
    )
    assert callable(executor_ingest_candidate_module.resolve_fast_selection_mode)
    assert callable(executor_ingest_candidate_module.resolve_deep_selection_mode)
