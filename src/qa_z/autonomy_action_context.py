"""Context path helpers for autonomy prepared actions."""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "loop_local_self_inspection_context_paths",
    "merge_context_paths",
    "recommendation_context_paths",
    "task_context_paths",
]


def task_context_paths(task: dict[str, object]) -> list[str]:
    """Return unique non-root evidence paths from a selected task."""
    evidence = task.get("evidence", [])
    if not isinstance(evidence, list):
        return []
    return merge_context_paths(
        [
            str(entry.get("path") or "").strip()
            for entry in evidence
            if isinstance(entry, dict)
            and str(entry.get("path") or "").strip()
            and str(entry.get("path") or "").strip() != "."
        ]
    )


def recommendation_context_paths(recommendation: str) -> list[str]:
    """Return default report context for known recommendations."""
    by_recommendation = {
        "improve_empty_loop_handling": [
            "docs/reports/current-state-analysis.md",
            "docs/reports/next-improvement-roadmap.md",
        ],
        "improve_fallback_diversity": [
            "docs/reports/current-state-analysis.md",
            "docs/reports/next-improvement-roadmap.md",
        ],
        "audit_worktree_integration": [
            "docs/reports/current-state-analysis.md",
            "docs/reports/worktree-triage.md",
            "docs/reports/worktree-commit-plan.md",
        ],
        "reduce_integration_risk": [
            "docs/reports/worktree-commit-plan.md",
            "docs/reports/worktree-triage.md",
            "scripts/runtime_artifact_cleanup.py",
        ],
        "isolate_foundation_commit": ["docs/reports/worktree-commit-plan.md"],
        "separate_runtime_from_source_artifacts": [
            "docs/reports/worktree-triage.md",
            "scripts/runtime_artifact_cleanup.py",
        ],
        "clarify_generated_vs_frozen_evidence_policy": [
            "docs/generated-vs-frozen-evidence-policy.md",
            "docs/reports/worktree-triage.md",
            "docs/reports/current-state-analysis.md",
            "scripts/runtime_artifact_cleanup.py",
        ],
        "triage_and_isolate_changes": [
            "docs/generated-vs-frozen-evidence-policy.md",
            "docs/reports/worktree-triage.md",
            "docs/reports/worktree-commit-plan.md",
            "scripts/runtime_artifact_cleanup.py",
        ],
    }
    return by_recommendation.get(recommendation, [])


def loop_local_self_inspection_context_paths(root: Path, loop_id: str) -> list[str]:
    """Return the loop-local self-inspection artifact when it exists."""
    path = root / ".qa-z" / "loops" / loop_id / "self_inspect.json"
    if not path.is_file():
        return []
    return [f".qa-z/loops/{loop_id}/self_inspect.json"]


def merge_context_paths(*groups: list[str]) -> list[str]:
    """Return stable sorted unique context paths."""
    merged = {
        path.strip()
        for group in groups
        for path in group
        if isinstance(path, str) and path.strip()
    }
    return sorted(merged)
