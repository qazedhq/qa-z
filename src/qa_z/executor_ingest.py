"""Public surface for executor-result ingest and repair-session verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qa_z.verification import VerificationVerdict


@dataclass(frozen=True)
class ExecutorResultIngestOutcome:
    """Structured result for one executor-result ingest pass."""

    summary: dict[str, Any]
    verification_verdict: VerificationVerdict | None


class ExecutorResultIngestRejected(ValueError):
    """Raised when a structured executor result is recorded but not accepted."""

    def __init__(
        self,
        *,
        outcome: ExecutorResultIngestOutcome,
        message: str,
        exit_code: int = 2,
    ) -> None:
        super().__init__(message)
        self.outcome = outcome
        self.exit_code = exit_code


from qa_z.executor_ingest_render import (  # noqa: E402
    render_executor_result_ingest_stdout,
    render_ingest_report,
)
from qa_z.executor_ingest_runtime import (  # noqa: E402
    create_verify_candidate_run,
    ingest_executor_result_artifact,
    resolve_deep_selection_mode,
    resolve_fast_selection_mode,
    verify_repair_session,
    write_verify_rerun_review_artifacts,
)

__all__ = [
    "ExecutorResultIngestOutcome",
    "ExecutorResultIngestRejected",
    "ingest_executor_result_artifact",
    "verify_repair_session",
    "create_verify_candidate_run",
    "write_verify_rerun_review_artifacts",
    "resolve_fast_selection_mode",
    "resolve_deep_selection_mode",
    "render_executor_result_ingest_stdout",
    "render_ingest_report",
]
