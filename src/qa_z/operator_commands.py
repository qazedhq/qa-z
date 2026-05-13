"""Stable local operator commands shared by QA-Z action surfaces."""

from __future__ import annotations

AUTONOMY_ONE_LOOP_COMMAND = "python -m qa_z autonomy --loops 1 --json"
AUTONOMY_STATUS_JSON_COMMAND = "python -m qa_z autonomy status --json"
BACKLOG_JSON_COMMAND = "python -m qa_z backlog --json"
BACKLOG_REFRESH_JSON_COMMAND = "python -m qa_z backlog --refresh --json"
BENCHMARK_COMMAND = "python -m qa_z benchmark"
BENCHMARK_JSON_COMMAND = "python -m qa_z benchmark --json"
RUNTIME_ARTIFACT_CLEANUP_COMMAND = "python scripts/runtime_artifact_cleanup.py --json"
RUNTIME_ARTIFACT_CLEANUP_APPLY_COMMAND = (
    "python scripts/runtime_artifact_cleanup.py --apply --json"
)
SELF_INSPECT_COMMAND = "python -m qa_z self-inspect"
SELF_INSPECT_JSON_COMMAND = "python -m qa_z self-inspect --json"
SELECT_NEXT_COUNT_JSON_COMMAND = "python -m qa_z select-next --count 3 --json"
SELECT_NEXT_REFRESH_COUNT_JSON_COMMAND = (
    "python -m qa_z select-next --refresh --count 3 --json"
)

STRICT_WORKTREE_COMMIT_PLAN_COMMAND = (
    "python scripts/worktree_commit_plan.py --summary-only --json "
    "--fail-on-generated --fail-on-cross-cutting "
    "--output .qa-z/tmp/worktree-commit-plan.json"
)

__all__ = [
    "AUTONOMY_ONE_LOOP_COMMAND",
    "AUTONOMY_STATUS_JSON_COMMAND",
    "BACKLOG_JSON_COMMAND",
    "BACKLOG_REFRESH_JSON_COMMAND",
    "BENCHMARK_COMMAND",
    "BENCHMARK_JSON_COMMAND",
    "RUNTIME_ARTIFACT_CLEANUP_APPLY_COMMAND",
    "RUNTIME_ARTIFACT_CLEANUP_COMMAND",
    "SELF_INSPECT_COMMAND",
    "SELF_INSPECT_JSON_COMMAND",
    "SELECT_NEXT_COUNT_JSON_COMMAND",
    "SELECT_NEXT_REFRESH_COUNT_JSON_COMMAND",
    "STRICT_WORKTREE_COMMIT_PLAN_COMMAND",
]
