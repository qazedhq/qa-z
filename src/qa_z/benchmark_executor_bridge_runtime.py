"""Executor-bridge fixture runtime helpers for benchmarks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z import benchmark_executor_loop_context
from qa_z import benchmark_executor_session_setup
from qa_z.executor_bridge import create_executor_bridge

from qa_z.benchmark_helpers import read_json_object


def execute_executor_bridge_fixture(
    *,
    workspace: Path,
    config: dict[str, Any],
    baseline_run: str,
    session_id: str,
    bridge_id: str,
    loop_id: str,
    context_paths: list[str],
) -> tuple[dict[str, Any], str]:
    fixed_now = benchmark_executor_session_setup.seed_executor_session(
        workspace=workspace,
        config=config,
        baseline_run=baseline_run,
        session_id=session_id,
    )
    benchmark_executor_loop_context.write_benchmark_loop_context(
        workspace=workspace,
        loop_id=loop_id,
        session_id=session_id,
        fixed_now=fixed_now,
        context_paths=context_paths,
    )
    paths = create_executor_bridge(
        root=workspace,
        from_loop=loop_id,
        bridge_id=bridge_id,
        now=fixed_now,
    )
    return (
        read_json_object(paths.manifest_path),
        paths.executor_guide_path.read_text(encoding="utf-8"),
    )
