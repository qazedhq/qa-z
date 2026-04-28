"""Shared session seeding helpers for benchmark executor fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.executor_result import write_json
from qa_z.repair_session import create_repair_session

from qa_z.benchmark_helpers import read_json_object

FIXED_BENCHMARK_NOW = "2026-04-16T00:00:00Z"


def seed_executor_session(
    *,
    workspace: Path,
    config: dict[str, Any],
    baseline_run: str,
    session_id: str,
) -> str:
    create_repair_session(
        root=workspace,
        config=config,
        baseline_run=baseline_run,
        session_id=session_id,
    )
    session_manifest_path = (
        workspace / ".qa-z" / "sessions" / session_id / "session.json"
    )
    session_manifest = read_json_object(session_manifest_path)
    session_manifest["created_at"] = FIXED_BENCHMARK_NOW
    session_manifest["updated_at"] = FIXED_BENCHMARK_NOW
    write_json(session_manifest_path, session_manifest)
    return FIXED_BENCHMARK_NOW
