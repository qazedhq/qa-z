"""Operator-facing task rendering helpers for selected backlog items."""

from __future__ import annotations

from typing import Any

from qa_z.live_repository import render_live_repository_summary
from qa_z.task_selection_core import repeated_fallback_family_from_item
from qa_z.task_selection_evidence import worktree_action_areas


def render_loop_plan(
    *,
    loop_id: str,
    generated_at: str,
    selected_items: list[dict[str, Any]],
    live_repository: object | None = None,
) -> str:
    """Render a concise Markdown plan for the selected self-improvement tasks."""
    lines = [
        "# QA-Z Self-Improvement Loop Plan",
        "",
        f"- Loop id: `{loop_id}`",
        f"- Generated at: `{generated_at}`",
        "- Boundary: QA-Z selects evidence-backed work; an external executor edits code.",
        "- This plan does not call Codex or Claude APIs, schedule jobs, or repair code by itself.",
    ]
    if isinstance(live_repository, dict):
        lines.extend(
            [
                "",
                "## Live Repository Context",
                "",
                f"- {render_live_repository_summary(live_repository)}",
            ]
        )
    lines.extend(
        [
            "",
            "## Selected Tasks",
            "",
        ]
    )
    if not selected_items:
        lines.append("- No open backlog tasks were selected.")
    for index, item in enumerate(selected_items, start=1):
        lines.extend(
            [
                f"{index}. {item.get('title', item.get('id', 'untitled'))}",
                f"   - id: `{item.get('id', '')}`",
                f"   - category: `{item.get('category', '')}`",
                f"   - recommendation: `{item.get('recommendation', '')}`",
                f"   - action: {selected_task_action_hint(item)}",
                f"   - validation: `{selected_task_validation_command(item)}`",
                f"   - priority score: {item.get('priority_score', 0)}",
            ]
        )
        if item.get("selection_priority_score") is not None:
            lines.append(
                f"   - selection score: {item.get('selection_priority_score', 0)}"
            )
        selection_penalty = item.get("selection_penalty")
        penalty_reasons = [
            str(reason)
            for reason in item.get("selection_penalty_reasons", [])
            if isinstance(reason, str) and reason.strip()
        ]
        if selection_penalty:
            if penalty_reasons:
                lines.append(
                    "   - selection penalty: "
                    f"{selection_penalty} "
                    f"({', '.join(f'`{reason}`' for reason in penalty_reasons)})"
                )
            else:
                lines.append(f"   - selection penalty: {selection_penalty}")
        lines.append("   - evidence:")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            lines.append("     - none recorded")
        else:
            for entry in evidence:
                if not isinstance(entry, dict):
                    continue
                lines.append(
                    "     - "
                    f"{entry.get('source', 'artifact')}: "
                    f"`{entry.get('path', 'unknown')}` "
                    f"{entry.get('summary', '')}".rstrip()
                )
        lines.append("")
    lines.extend(
        [
            "## Verification After External Repair",
            "",
            "- Run deterministic QA-Z verification commands that match the selected task evidence.",
            "- Feed the resulting verify, benchmark, or session artifacts into the next self-inspection loop.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def selected_task_action_hint(item: dict[str, Any]) -> str:
    """Return a deterministic first action hint for a selected task."""
    category = str(item.get("category") or "").strip()
    recommendation = str(item.get("recommendation") or "").strip()
    cleanup_review = "`python scripts/runtime_artifact_cleanup.py --json`"
    worktree_plan_review = (
        "`python scripts/worktree_commit_plan.py --json "
        "--output .qa-z/tmp/worktree-commit-plan.json`"
    )
    if recommendation == "improve_fallback_diversity":
        repeated_family = repeated_fallback_family_from_item(item)
        if repeated_family:
            return (
                f"surface a non-{repeated_family} fallback family before selecting "
                f"more {repeated_family} work, then rerun autonomy"
            )
        return (
            "surface a non-repeated fallback family before selecting more of the "
            "same family, then rerun autonomy"
        )
    if recommendation == "reduce_integration_risk":
        area_phrase = join_action_areas(worktree_action_areas(item))
        if area_phrase:
            return (
                f"triage {area_phrase} changes first, run {cleanup_review} plus "
                f"{worktree_plan_review}, then rerun self-inspection"
            )
    if recommendation == "isolate_foundation_commit":
        area_phrase = join_action_areas(worktree_action_areas(item))
        if area_phrase:
            return (
                "follow docs/reports/worktree-commit-plan.md and isolate "
                f"{area_phrase} changes into the foundation split, "
                "then rerun self-inspection"
            )
    if recommendation == "audit_worktree_integration":
        area_phrase = join_action_areas(worktree_action_areas(item), limit=4)
        if area_phrase:
            return f"audit {area_phrase} integration first, then rerun self-inspection"
    if (
        recommendation == "triage_and_isolate_changes"
        and category == "runtime_artifact_cleanup_gap"
    ):
        return (
            f"run {cleanup_review}, clear policy-managed runtime artifacts before "
            "source integration, keep frozen evidence only when intentional, "
            "then rerun self-inspection"
        )
    hints = {
        "reduce_integration_risk": (
            f"inspect the dirty worktree, run {cleanup_review} plus "
            f"{worktree_plan_review}, then rerun self-inspection"
        ),
        "separate_runtime_from_source_artifacts": (
            f"run {cleanup_review} to review policy-managed runtime artifacts, "
            "apply cleanup if safe, then rerun self-inspection"
        ),
        "triage_and_isolate_changes": (
            f"run {cleanup_review}, decide whether generated artifacts stay "
            "local-only or become intentional frozen evidence, then rerun "
            "self-inspection"
        ),
        "isolate_foundation_commit": (
            "follow docs/reports/worktree-commit-plan.md to split the foundation "
            "commit, then rerun self-inspection"
        ),
        "clarify_generated_vs_frozen_evidence_policy": (
            "review docs/generated-vs-frozen-evidence-policy.md against "
            f"{cleanup_review}, then rerun self-inspection"
        ),
        "audit_worktree_integration": (
            "inspect current-state, triage, and commit-plan reports, then rerun "
            "self-inspection"
        ),
    }
    if recommendation in hints:
        return hints[recommendation]
    if recommendation:
        return f"turn {recommendation.replace('_', ' ')} into a scoped repair plan"
    return "turn selected evidence into a scoped repair plan"


def selected_task_validation_command(item: dict[str, Any]) -> str:
    """Return the deterministic command for refreshing evidence after a task."""
    recommendation = str(item.get("recommendation") or "").strip()
    commands = {
        "add_benchmark_fixture": "python -m qa_z benchmark --json",
        "reduce_integration_risk": "python -m qa_z self-inspect",
        "isolate_foundation_commit": "python -m qa_z self-inspect",
        "audit_worktree_integration": "python -m qa_z self-inspect",
        "improve_fallback_diversity": "python -m qa_z autonomy --loops 1",
        "stabilize_verification_surface": (
            "python -m qa_z verify --baseline-run <baseline> "
            "--candidate-run <candidate>"
        ),
        "create_repair_session": (
            "python -m qa_z repair-session status --session <session>"
        ),
    }
    return commands.get(recommendation, "python -m qa_z self-inspect")


def join_action_areas(areas: list[str], *, limit: int = 2) -> str:
    """Join the first dirty worktree areas for a concise action hint."""
    selected = [area for area in areas if area.strip()][:limit]
    if not selected:
        return ""
    if len(selected) == 1:
        return selected[0]
    if len(selected) == 2:
        return " and ".join(selected)
    return ", ".join(selected[:-1]) + f", and {selected[-1]}"
