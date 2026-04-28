"""Thin public wrappers for executor-ingest runtime seams."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.executor_ingest import ExecutorResultIngestOutcome
from qa_z.executor_ingest_flow import (
    ingest_executor_result_artifact as ingest_executor_result_artifact_impl,
)
from qa_z.executor_ingest_verification import (
    verify_repair_session as verify_repair_session_impl,
)
from qa_z.repair_session import RepairSession

from qa_z import executor_ingest_candidate as executor_ingest_candidate_module


def ingest_executor_result_artifact(
    *,
    root: Path,
    config: dict[str, Any],
    result_path: str | Path,
    now: str | None = None,
) -> ExecutorResultIngestOutcome:
    """Ingest an external executor result and optionally resume verification."""
    return ingest_executor_result_artifact_impl(
        root=root,
        config=config,
        result_path=result_path,
        now=now,
    )


def verify_repair_session(
    *,
    session: RepairSession,
    root: Path,
    config: dict[str, Any],
    candidate_run: str | None,
    rerun: bool,
    rerun_output_dir: str | None,
    strict_no_tests: bool,
    output_dir: str | None,
) -> tuple[RepairSession, dict[str, Any], Any]:
    """Run the shared repair-session verification flow."""
    return verify_repair_session_impl(
        session=session,
        root=root,
        config=config,
        candidate_run=candidate_run,
        rerun=rerun,
        rerun_output_dir=rerun_output_dir,
        strict_no_tests=strict_no_tests,
        output_dir=output_dir,
    )


create_verify_candidate_run = (
    executor_ingest_candidate_module.create_verify_candidate_run
)
write_verify_rerun_review_artifacts = (
    executor_ingest_candidate_module.write_verify_rerun_review_artifacts
)
resolve_fast_selection_mode = (
    executor_ingest_candidate_module.resolve_fast_selection_mode
)
resolve_deep_selection_mode = (
    executor_ingest_candidate_module.resolve_deep_selection_mode
)
