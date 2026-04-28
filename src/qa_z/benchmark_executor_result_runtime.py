"""Executor-result fixture runtime helpers for benchmarks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z import benchmark_executor_loop_context
from qa_z import benchmark_executor_session_setup
from qa_z.executor_bridge import create_executor_bridge
from qa_z.executor_ingest import (
    ExecutorResultIngestRejected,
    ingest_executor_result_artifact,
)


def execute_executor_result_fixture(
    *,
    workspace: Path,
    config: dict[str, Any],
    baseline_run: str,
    session_id: str,
    bridge_id: str,
    result_path: str,
    loop_id: str | None = None,
):
    fixed_now = benchmark_executor_session_setup.seed_executor_session(
        workspace=workspace,
        config=config,
        baseline_run=baseline_run,
        session_id=session_id,
    )
    if loop_id:
        benchmark_executor_loop_context.write_benchmark_loop_context(
            workspace=workspace,
            loop_id=loop_id,
            session_id=session_id,
            fixed_now=fixed_now,
            context_paths=[],
        )
        create_executor_bridge(
            root=workspace,
            from_loop=loop_id,
            bridge_id=bridge_id,
            now=fixed_now,
        )
    else:
        create_executor_bridge(
            root=workspace,
            from_session=session_id,
            bridge_id=bridge_id,
            now=fixed_now,
        )
    try:
        return ingest_executor_result_artifact(
            root=workspace,
            config=config,
            result_path=workspace / result_path,
            now=fixed_now,
        )
    except ExecutorResultIngestRejected as exc:
        return exc.outcome
