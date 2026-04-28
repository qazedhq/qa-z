from __future__ import annotations

from pathlib import Path

import qa_z.autonomy_action_context as autonomy_action_context_module

from qa_z.autonomy import action_for_task
from qa_z.autonomy_actions import (
    loop_local_self_inspection_context_paths,
    merge_context_paths,
    recommendation_context_paths,
    task_context_paths,
)


def test_autonomy_action_context_module_exports_match_autonomy_surface() -> None:
    assert autonomy_action_context_module.merge_context_paths is merge_context_paths
    assert autonomy_action_context_module.task_context_paths is task_context_paths
    assert (
        autonomy_action_context_module.recommendation_context_paths
        is recommendation_context_paths
    )
    assert (
        autonomy_action_context_module.loop_local_self_inspection_context_paths
        is loop_local_self_inspection_context_paths
    )


def test_merge_context_paths_stays_sorted_and_unique() -> None:
    assert autonomy_action_context_module.merge_context_paths(
        ["docs/reports/worktree-triage.md", "docs/reports/worktree-triage.md"],
        ["docs/reports/current-state-analysis.md"],
        [""],
    ) == [
        "docs/reports/current-state-analysis.md",
        "docs/reports/worktree-triage.md",
    ]


def test_loop_local_self_inspection_context_paths_returns_loop_local_artifact(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / ".qa-z" / "loops" / "loop-one" / "self_inspect.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text('{"kind":"qa_z.self_inspection"}\n', encoding="utf-8")

    assert autonomy_action_context_module.loop_local_self_inspection_context_paths(
        tmp_path, "loop-one"
    ) == [".qa-z/loops/loop-one/self_inspect.json"]


def test_action_mapping_loop_health_plan_includes_task_context_paths(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / ".qa-z" / "loops" / "loop-one" / "self_inspect.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text('{"kind":"qa_z.self_inspection"}\n', encoding="utf-8")

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
                    "summary": (
                        "recent_fallback_family=cleanup; loops=3; "
                        "states=unknown, completed, unknown"
                    ),
                }
            ],
        },
    )

    assert action["type"] == "loop_health_plan"
    assert action["commands"] == [
        "python -m qa_z self-inspect",
        "python -m qa_z autonomy --loops 1",
    ]
    assert action["context_paths"] == [
        ".qa-z/loops/history.jsonl",
        ".qa-z/loops/loop-one/self_inspect.json",
        "docs/reports/current-state-analysis.md",
        "docs/reports/next-improvement-roadmap.md",
    ]
