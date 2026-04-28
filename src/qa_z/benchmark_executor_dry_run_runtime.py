"""Executor dry-run fixture runtime helpers for benchmarks."""

from __future__ import annotations

from pathlib import Path

from qa_z.executor_dry_run import run_executor_result_dry_run


def execute_executor_dry_run_fixture(*, workspace: Path, session_id: str):
    return run_executor_result_dry_run(root=workspace, session_ref=session_id)
