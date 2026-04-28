"""Tests for self-improvement selection output and action hints."""

from __future__ import annotations

from pathlib import Path

from qa_z.self_improvement import (
    compact_backlog_evidence_summary,
    render_loop_plan,
    select_next_tasks,
    selected_task_action_hint,
    selected_task_validation_command,
    worktree_action_areas,
)
from tests.self_improvement_test_support import write_json


NOW = "2026-04-15T00:00:00Z"


def test_loop_plan_states_external_executor_boundary(tmp_path: Path) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "handoff-gap",
                    "title": "Create repair session for unresolved blocker",
                    "category": "session_gap",
                    "evidence": [{"source": "session", "path": ".qa-z/sessions/s"}],
                    "impact": 3,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 45,
                    "status": "open",
                    "recommendation": "create_repair_session",
                    "signals": ["regression_prevention"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                }
            ],
        },
    )

    paths = select_next_tasks(root=tmp_path, count=1, now=NOW, loop_id="boundary")
    plan = paths.loop_plan_path.read_text(encoding="utf-8")

    assert "does not call Codex or Claude APIs" in plan
    assert "external executor" in plan
    assert "create_repair_session" in plan


def test_loop_plan_preserves_selection_score_and_penalty_residue() -> None:
    plan = render_loop_plan(
        loop_id="loop-penalty",
        generated_at=NOW,
        selected_items=[
            {
                "id": "worktree_risk-dirty-worktree",
                "title": "Reduce dirty worktree integration risk",
                "category": "worktree_risk",
                "recommendation": "reduce_integration_risk",
                "priority_score": 65,
                "selection_priority_score": 60,
                "selection_penalty": 5,
                "selection_penalty_reasons": [
                    "recent_task_reselected",
                    "recent_category_reselected",
                ],
                "evidence": [
                    {
                        "source": "git_status",
                        "path": ".",
                        "summary": "modified=25; untracked=352; staged=0",
                    }
                ],
            }
        ],
    )

    assert "selection score: 60" in plan
    assert (
        "selection penalty: 5 (`recent_task_reselected`, "
        "`recent_category_reselected`)" in plan
    )


def test_selected_task_action_hint_specializes_closure_recommendations() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "isolate_foundation_commit",
            "evidence": [
                {
                    "source": "worktree_commit_plan",
                    "path": "docs/reports/worktree-commit-plan.md",
                    "summary": "alpha closure readiness snapshot pins full gate pass",
                }
            ],
        }
    ) == (
        "follow docs/reports/worktree-commit-plan.md to split the foundation "
        "commit, then rerun self-inspection"
    )


def test_worktree_action_areas_reads_area_summary_from_evidence() -> None:
    assert worktree_action_areas(
        {
            "evidence": [
                {
                    "source": "git_status",
                    "summary": (
                        "modified=31; untracked=488; staged=0; "
                        "areas=benchmark:271, docs:160, source:42; "
                        "sample=.github/workflows/ci.yml, README.md"
                    ),
                }
            ]
        }
    ) == ["benchmark", "docs", "source"]


def test_worktree_action_areas_ignores_missing_or_malformed_area_summary() -> None:
    assert worktree_action_areas({"evidence": [{"summary": "modified=1"}]}) == []
    assert worktree_action_areas({"evidence": [{"summary": "areas=, broken"}]}) == []


def test_selected_task_action_hint_uses_dirty_worktree_area_evidence() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "reduce_integration_risk",
            "evidence": [
                {
                    "source": "git_status",
                    "summary": "modified=31; areas=benchmark:271, docs:160, source:42",
                }
            ],
        }
    ) == (
        "triage benchmark and docs changes first, run "
        "`python scripts/runtime_artifact_cleanup.py --json` plus "
        "`python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json`, then rerun "
        "self-inspection"
    )


def test_selected_task_action_hint_keeps_fallback_without_area_evidence() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "reduce_integration_risk",
            "evidence": [{"source": "git_status", "summary": "modified=31"}],
        }
    ) == (
        "inspect the dirty worktree, run "
        "`python scripts/runtime_artifact_cleanup.py --json` plus "
        "`python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json`, then rerun "
        "self-inspection"
    )


def test_selected_task_action_hint_uses_commit_isolation_area_evidence() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "isolate_foundation_commit",
            "evidence": [
                {
                    "source": "git_status",
                    "summary": (
                        "dirty worktree still spans modified=3; untracked=1; "
                        "areas=docs:2, source:1"
                    ),
                }
            ],
        }
    ) == (
        "follow docs/reports/worktree-commit-plan.md and isolate docs and source "
        "changes into the foundation split, then rerun self-inspection"
    )


def test_selected_task_action_hint_keeps_commit_isolation_fallback_without_area_evidence() -> (
    None
):
    assert selected_task_action_hint(
        {
            "recommendation": "isolate_foundation_commit",
            "evidence": [{"source": "git_status", "summary": "dirty worktree"}],
        }
    ) == (
        "follow docs/reports/worktree-commit-plan.md to split the foundation "
        "commit, then rerun self-inspection"
    )


def test_selected_task_action_hint_names_generated_snapshot_decision() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "triage_and_isolate_changes",
            "evidence": [
                {
                    "source": "runtime_artifacts",
                    "summary": (
                        "generated runtime artifacts need explicit cleanup handling: "
                        "benchmarks/results-p12-dry-run/report.md"
                    ),
                }
            ],
        }
    ) == (
        "run `python scripts/runtime_artifact_cleanup.py --json`, decide whether "
        "generated artifacts stay local-only or become intentional frozen "
        "evidence, then rerun self-inspection"
    )


def test_selected_task_action_hint_specializes_runtime_artifact_cleanup_items() -> None:
    assert selected_task_action_hint(
        {
            "category": "runtime_artifact_cleanup_gap",
            "recommendation": "triage_and_isolate_changes",
            "signals": ["policy_managed_runtime_artifacts"],
            "evidence": [
                {
                    "source": "runtime_artifacts",
                    "summary": (
                        "generated runtime artifacts need explicit cleanup handling: "
                        "benchmarks/results-analysis/report.md"
                    ),
                }
            ],
        }
    ) == (
        "run `python scripts/runtime_artifact_cleanup.py --json`, clear "
        "policy-managed runtime artifacts before source integration, keep frozen "
        "evidence only when intentional, then rerun self-inspection"
    )


def test_selected_task_action_hint_specializes_runtime_artifact_cleanup_recommendations() -> (
    None
):
    assert selected_task_action_hint(
        {"recommendation": "separate_runtime_from_source_artifacts"}
    ) == (
        "run `python scripts/runtime_artifact_cleanup.py --json` to review "
        "policy-managed runtime artifacts, apply cleanup if safe, then rerun "
        "self-inspection"
    )


def test_selected_task_action_hint_specializes_fallback_diversity_recommendations() -> (
    None
):
    assert selected_task_action_hint(
        {
            "recommendation": "improve_fallback_diversity",
            "evidence": [
                {
                    "source": "loop_history",
                    "summary": "recent_fallback_family=cleanup; loops=3",
                }
            ],
        }
    ) == (
        "surface a non-cleanup fallback family before selecting more cleanup "
        "work, then rerun autonomy"
    )


def test_selected_task_validation_command_specializes_known_recommendations() -> None:
    assert (
        selected_task_validation_command(
            {"recommendation": "isolate_foundation_commit"}
        )
        == "python -m qa_z self-inspect"
    )
    assert (
        selected_task_validation_command(
            {"recommendation": "separate_runtime_from_source_artifacts"}
        )
        == "python -m qa_z self-inspect"
    )
    assert (
        selected_task_validation_command({"recommendation": "add_benchmark_fixture"})
        == "python -m qa_z benchmark --json"
    )


def test_loop_plan_includes_selected_task_action_hint() -> None:
    plan = render_loop_plan(
        loop_id="loop-action-hint",
        generated_at=NOW,
        selected_items=[
            {
                "id": "commit_isolation_gap-foundation-order",
                "title": "Isolate the foundation commit before later batches",
                "category": "commit_isolation_gap",
                "recommendation": "isolate_foundation_commit",
                "priority_score": 64,
                "evidence": [
                    {
                        "source": "worktree_commit_plan",
                        "path": "docs/reports/worktree-commit-plan.md",
                        "summary": (
                            "alpha closure readiness snapshot pins full gate pass"
                        ),
                    }
                ],
            }
        ],
    )

    assert (
        "   - action: follow docs/reports/worktree-commit-plan.md to split the "
        "foundation commit, then rerun self-inspection" in plan
    )
    assert "   - validation: `python -m qa_z self-inspect`" in plan


def test_compact_evidence_summary_prioritizes_alpha_closure_snapshot() -> None:
    item = {
        "id": "commit_isolation_gap-foundation-order",
        "evidence": [
            {
                "source": "current_state",
                "path": "docs/reports/current-state-analysis.md",
                "summary": (
                    "report calls out commit-order dependency or commit-isolation work"
                ),
            },
            {
                "source": "worktree_commit_plan",
                "path": "docs/reports/worktree-commit-plan.md",
                "summary": (
                    "alpha closure readiness snapshot pins full gate pass and "
                    "commit-split action"
                ),
            },
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "worktree_commit_plan: alpha closure readiness snapshot pins full gate "
        "pass and commit-split action"
    )


def test_compact_evidence_summary_appends_area_action_basis() -> None:
    item = {
        "id": "commit_isolation_gap-foundation-order",
        "evidence": [
            {
                "source": "worktree_commit_plan",
                "path": "docs/reports/worktree-commit-plan.md",
                "summary": (
                    "alpha closure readiness snapshot pins full gate pass and "
                    "commit-split action"
                ),
            },
            {
                "source": "git_status",
                "path": ".",
                "summary": (
                    "dirty worktree still spans modified=3; untracked=1; "
                    "areas=docs:2, source:1"
                ),
            },
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "worktree_commit_plan: alpha closure readiness snapshot pins full gate "
        "pass and commit-split action; action basis: git_status: dirty worktree "
        "still spans modified=3; untracked=1; areas=docs:2, source:1"
    )


def test_compact_evidence_summary_does_not_duplicate_primary_area_summary() -> None:
    item = {
        "evidence": [
            {
                "source": "git_status",
                "summary": "modified=1; areas=docs:1",
            }
        ]
    }

    assert compact_backlog_evidence_summary(item) == (
        "git_status: modified=1; areas=docs:1"
    )


def test_compact_evidence_summary_appends_generated_action_basis() -> None:
    item = {
        "id": "deferred_cleanup_gap-worktree-deferred-items",
        "recommendation": "triage_and_isolate_changes",
        "evidence": [
            {
                "source": "current_state",
                "path": "docs/reports/current-state-analysis.md",
                "summary": (
                    "report calls out deferred cleanup work or generated outputs "
                    "to isolate"
                ),
            },
            {
                "source": "generated_outputs",
                "path": "benchmarks/results/report.md",
                "summary": (
                    "generated benchmark outputs still present: "
                    "benchmarks/results/report.md, benchmarks/results/summary.json"
                ),
            },
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "current_state: report calls out deferred cleanup work or generated "
        "outputs to isolate; action basis: generated_outputs: generated "
        "benchmark outputs still present: benchmarks/results/report.md, "
        "benchmarks/results/summary.json"
    )


def test_compact_evidence_summary_does_not_duplicate_generated_primary() -> None:
    item = {
        "recommendation": "triage_and_isolate_changes",
        "evidence": [
            {
                "source": "generated_outputs",
                "summary": (
                    "generated benchmark outputs still present: "
                    "benchmarks/results/report.md"
                ),
            }
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "generated_outputs: generated benchmark outputs still present: "
        "benchmarks/results/report.md"
    )
