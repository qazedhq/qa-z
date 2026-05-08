from __future__ import annotations

from pathlib import Path

from qa_z.autonomy import action_for_task
from qa_z.operator_commands import AUTONOMY_ONE_LOOP_COMMAND
from qa_z.operator_commands import AUTONOMY_STATUS_JSON_COMMAND
from qa_z.operator_commands import BACKLOG_JSON_COMMAND
from qa_z.operator_commands import BACKLOG_REFRESH_JSON_COMMAND
from qa_z.operator_commands import BENCHMARK_COMMAND
from qa_z.operator_commands import BENCHMARK_JSON_COMMAND
from qa_z.operator_commands import RUNTIME_ARTIFACT_CLEANUP_COMMAND
from qa_z.operator_commands import RUNTIME_ARTIFACT_CLEANUP_APPLY_COMMAND
from qa_z.operator_commands import SELF_INSPECT_COMMAND
from qa_z.operator_commands import SELF_INSPECT_JSON_COMMAND
from qa_z.operator_commands import SELECT_NEXT_COUNT_JSON_COMMAND
from qa_z.operator_commands import STRICT_WORKTREE_COMMIT_PLAN_COMMAND
from qa_z.task_selection_render import selected_task_action_hint
from qa_z.task_selection_render import selected_task_validation_command


def test_operator_commands_feed_selected_task_validation() -> None:
    assert RUNTIME_ARTIFACT_CLEANUP_COMMAND == (
        "python scripts/runtime_artifact_cleanup.py --json"
    )
    assert RUNTIME_ARTIFACT_CLEANUP_APPLY_COMMAND == (
        "python scripts/runtime_artifact_cleanup.py --apply --json"
    )
    assert STRICT_WORKTREE_COMMIT_PLAN_COMMAND == (
        "python scripts/worktree_commit_plan.py --summary-only --json "
        "--fail-on-generated --fail-on-cross-cutting "
        "--output .qa-z/tmp/worktree-commit-plan.json"
    )
    assert (
        selected_task_validation_command({"recommendation": "reduce_integration_risk"})
        == STRICT_WORKTREE_COMMIT_PLAN_COMMAND
    )


def test_operator_commands_cover_common_autonomy_action_sequences(
    tmp_path: Path,
) -> None:
    action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "autonomy_selection_gap-repeated-fallback-cleanup",
            "category": "autonomy_selection_gap",
            "recommendation": "improve_fallback_diversity",
            "signals": ["recent_fallback_family_repeat"],
            "evidence": [
                {
                    "source": "loop_history",
                    "path": ".qa-z/loops/history.jsonl",
                    "summary": "recent_fallback_family=cleanup; loops=2",
                }
            ],
        },
    )

    assert SELF_INSPECT_COMMAND == "python -m qa_z self-inspect"
    assert SELF_INSPECT_JSON_COMMAND == "python -m qa_z self-inspect --json"
    assert SELECT_NEXT_COUNT_JSON_COMMAND == (
        "python -m qa_z select-next --count 3 --json"
    )
    assert AUTONOMY_ONE_LOOP_COMMAND == "python -m qa_z autonomy --loops 1 --json"
    assert AUTONOMY_STATUS_JSON_COMMAND == "python -m qa_z autonomy status --json"
    assert BACKLOG_JSON_COMMAND == "python -m qa_z backlog --json"
    assert BACKLOG_REFRESH_JSON_COMMAND == "python -m qa_z backlog --refresh --json"
    assert BENCHMARK_COMMAND == "python -m qa_z benchmark"
    assert BENCHMARK_JSON_COMMAND == "python -m qa_z benchmark --json"
    assert action["commands"] == [
        SELF_INSPECT_JSON_COMMAND,
        SELECT_NEXT_COUNT_JSON_COMMAND,
        AUTONOMY_ONE_LOOP_COMMAND,
        AUTONOMY_STATUS_JSON_COMMAND,
    ]


def test_operator_commands_feed_selected_task_validation_variants() -> None:
    assert (
        selected_task_validation_command({"recommendation": "add_benchmark_fixture"})
        == BENCHMARK_JSON_COMMAND
    )
    assert (
        selected_task_validation_command(
            {"recommendation": "improve_fallback_diversity"}
        )
        == AUTONOMY_ONE_LOOP_COMMAND
    )
    assert (
        selected_task_validation_command(
            {"recommendation": "audit_worktree_integration"}
        )
        == SELF_INSPECT_COMMAND
    )


def test_operator_commands_cover_empty_loop_handling_guidance() -> None:
    task = {
        "recommendation": "improve_empty_loop_handling",
        "evidence": [
            {
                "source": "loop_history",
                "path": ".qa-z/loops/history.jsonl",
                "summary": "recent_empty_loops=3",
            }
        ],
    }

    assert selected_task_action_hint(task) == (
        "inspect `.qa-z/loops/history.jsonl`, confirm whether the repeated "
        "empty-loop chain still has no open backlog, then run "
        "`python -m qa_z autonomy --loops 1 --json` and inspect autonomy status"
    )
    assert selected_task_validation_command(task) == AUTONOMY_ONE_LOOP_COMMAND
