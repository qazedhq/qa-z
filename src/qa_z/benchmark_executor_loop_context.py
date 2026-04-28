"""Loop-context helpers for benchmark executor fixtures."""

from __future__ import annotations

from pathlib import Path

from qa_z.executor_result import write_json


def write_benchmark_loop_context(
    *,
    workspace: Path,
    loop_id: str,
    session_id: str,
    fixed_now: str,
    context_paths: list[str],
) -> None:
    loop_dir = workspace / ".qa-z" / "loops" / loop_id
    live_repository = {
        "modified_count": 2,
        "untracked_count": 1,
        "staged_count": 0,
        "runtime_artifact_count": 0,
        "benchmark_result_count": 0,
        "current_branch": "codex/qa-z-bootstrap",
        "current_head": "1234567890abcdef1234567890abcdef12345678",
        "generated_artifact_policy_explicit": True,
        "dirty_area_summary": "source:2, tests:1",
    }
    write_json(
        loop_dir / "self_inspect.json",
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": loop_id,
            "generated_at": fixed_now,
            "live_repository": live_repository,
            "candidates": [],
        },
    )
    write_json(
        loop_dir / "outcome.json",
        {
            "kind": "qa_z.autonomy_outcome",
            "schema_version": 1,
            "loop_id": loop_id,
            "generated_at": fixed_now,
            "source_self_inspection": f".qa-z/loops/{loop_id}/self_inspect.json",
            "source_self_inspection_loop_id": loop_id,
            "source_self_inspection_generated_at": fixed_now,
            "live_repository": live_repository,
            "state": "completed",
            "selected_task_ids": ["verify_regression-candidate"],
            "actions_prepared": [
                {
                    "type": "repair_session",
                    "task_id": "verify_regression-candidate",
                    "session_id": session_id,
                    "session_dir": f".qa-z/sessions/{session_id}",
                    "context_paths": list(context_paths),
                }
            ],
            "next_recommendations": ["run external repair, then repair-session verify"],
            "artifacts": {"outcome": f".qa-z/loops/{loop_id}/outcome.json"},
        },
    )
