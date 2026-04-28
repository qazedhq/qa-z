from __future__ import annotations

import qa_z.autonomy_action_cleanup as autonomy_action_cleanup_module

from qa_z.autonomy import action_for_task
from qa_z.autonomy_actions import cleanup_action, workflow_gap_action


def test_autonomy_action_cleanup_module_exports_match_autonomy_surface() -> None:
    assert autonomy_action_cleanup_module.cleanup_action is cleanup_action
    assert autonomy_action_cleanup_module.workflow_gap_action is workflow_gap_action


def test_cleanup_action_keeps_runtime_cleanup_follow_through_packet(
    tmp_path,
) -> None:
    action = autonomy_action_cleanup_module.cleanup_action(
        root=tmp_path,
        loop_id="loop-one",
        task_id="runtime_artifact_cleanup_gap-generated-results",
        task={
            "category": "runtime_artifact_cleanup_gap",
            "evidence": [
                {
                    "source": "runtime_artifacts",
                    "path": "benchmarks/results-analysis/report.md",
                }
            ],
        },
        recommendation="triage_and_isolate_changes",
    )

    assert action["type"] == "integration_cleanup_plan"
    assert action["commands"] == [
        "git status --short",
        "python scripts/runtime_artifact_cleanup.py --json",
        "python scripts/runtime_artifact_cleanup.py --apply --json",
        "python -m qa_z self-inspect --json",
    ]
    assert action["next_recommendation"] == (
        "clear policy-managed runtime artifacts before rerunning self-inspection"
    )


def test_action_mapping_specializes_cleanup_packets_by_recommendation(
    tmp_path,
) -> None:
    artifact = tmp_path / ".qa-z" / "loops" / "loop-one" / "self_inspect.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text('{"kind":"qa_z.self_inspection"}\n', encoding="utf-8")

    cleanup_packet = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "worktree_risk-dirty-worktree",
            "category": "worktree_risk",
            "recommendation": "reduce_integration_risk",
            "signals": ["dirty_worktree_large", "worktree_integration_risk"],
            "evidence": [
                {
                    "source": "git_status",
                    "path": ".",
                    "summary": "modified=25; untracked=344; staged=0",
                }
            ],
        },
    )
    isolation_packet = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "commit_isolation_gap-foundation-order",
            "category": "commit_isolation_gap",
            "recommendation": "isolate_foundation_commit",
            "signals": ["commit_order_dependency_exists"],
            "evidence": [
                {
                    "source": "worktree_commit_plan",
                    "path": "docs/reports/worktree-commit-plan.md",
                    "summary": "corrected commit order still requires isolation",
                }
            ],
        },
    )

    assert cleanup_packet["type"] == "integration_cleanup_plan"
    assert cleanup_packet["commands"] == [
        "git status --short",
        "python scripts/runtime_artifact_cleanup.py --json",
        "python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json",
        "python -m qa_z backlog --json",
        "python -m qa_z self-inspect --json",
    ]
    assert cleanup_packet["context_paths"] == [
        ".qa-z/loops/loop-one/self_inspect.json",
        "docs/reports/worktree-commit-plan.md",
        "docs/reports/worktree-triage.md",
        "scripts/runtime_artifact_cleanup.py",
    ]
    assert isolation_packet["type"] == "integration_cleanup_plan"
    assert isolation_packet["context_paths"] == [
        ".qa-z/loops/loop-one/self_inspect.json",
        "docs/reports/worktree-commit-plan.md",
    ]


def test_deferred_cleanup_action_includes_generated_policy_context_path(
    tmp_path,
) -> None:
    action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "deferred_cleanup_gap-worktree-deferred-items",
            "category": "deferred_cleanup_gap",
            "recommendation": "triage_and_isolate_changes",
            "signals": ["deferred_cleanup_items_open"],
            "evidence": [
                {
                    "source": "current_state",
                    "path": "docs/reports/current-state-analysis.md",
                },
                {
                    "source": "generated_outputs",
                    "path": "benchmarks/results/report.md",
                },
            ],
        },
    )

    assert action["context_paths"] == [
        "benchmarks/results/report.md",
        "docs/generated-vs-frozen-evidence-policy.md",
        "docs/reports/current-state-analysis.md",
        "docs/reports/worktree-commit-plan.md",
        "docs/reports/worktree-triage.md",
        "scripts/runtime_artifact_cleanup.py",
    ]


def test_runtime_artifact_cleanup_action_adds_review_and_apply_commands(
    tmp_path,
) -> None:
    action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "artifact_hygiene_gap-runtime-source-separation",
            "category": "artifact_hygiene_gap",
            "recommendation": "separate_runtime_from_source_artifacts",
            "signals": ["generated_artifact_policy_ambiguity"],
            "evidence": [
                {
                    "source": "runtime_artifacts",
                    "path": "benchmarks/results-analysis/report.md",
                }
            ],
        },
    )

    assert action["commands"] == [
        "git status --short",
        "python scripts/runtime_artifact_cleanup.py --json",
        "python scripts/runtime_artifact_cleanup.py --apply --json",
        "python -m qa_z self-inspect --json",
    ]


def test_action_mapping_specializes_integration_gap_packets_from_reports(
    tmp_path,
) -> None:
    artifact = tmp_path / ".qa-z" / "loops" / "loop-one" / "self_inspect.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text('{"kind":"qa_z.self_inspection"}\n', encoding="utf-8")

    action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "integration_gap-worktree-integration-risk",
            "category": "integration_gap",
            "recommendation": "audit_worktree_integration",
            "signals": ["worktree_integration_risk"],
            "evidence": [
                {
                    "source": "current_state",
                    "path": "docs/reports/current-state-analysis.md",
                },
                {
                    "source": "worktree_triage",
                    "path": "docs/reports/worktree-triage.md",
                },
                {
                    "source": "worktree_commit_plan",
                    "path": "docs/reports/worktree-commit-plan.md",
                },
            ],
        },
    )

    assert action["type"] == "workflow_gap_plan"
    assert action["commands"] == [
        "git status --short",
        "python -m qa_z backlog --json",
        "python -m qa_z self-inspect --json",
    ]
    assert action["context_paths"] == [
        ".qa-z/loops/loop-one/self_inspect.json",
        "docs/reports/current-state-analysis.md",
        "docs/reports/worktree-commit-plan.md",
        "docs/reports/worktree-triage.md",
    ]
