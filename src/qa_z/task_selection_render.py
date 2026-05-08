"""Operator-facing task rendering helpers for selected backlog items."""

from __future__ import annotations

from typing import Any

from qa_z.live_repository import render_live_repository_summary
from qa_z.operator_commands import AUTONOMY_ONE_LOOP_COMMAND
from qa_z.operator_commands import BENCHMARK_JSON_COMMAND
from qa_z.operator_commands import RUNTIME_ARTIFACT_CLEANUP_COMMAND
from qa_z.operator_commands import SELF_INSPECT_COMMAND
from qa_z.operator_commands import STRICT_WORKTREE_COMMIT_PLAN_COMMAND
from qa_z.task_selection_core import repeated_fallback_family_from_item
from qa_z.task_selection_evidence import verification_not_comparable_reason
from qa_z.task_selection_evidence import worktree_action_areas


INLINE_PATCH_COMMAND_LIMIT = 3


def render_loop_plan(
    *,
    loop_id: str,
    generated_at: str,
    selected_items: list[dict[str, Any]],
    live_repository: object | None = None,
    state: str | None = None,
    selection_gap_reason: str | None = None,
    open_backlog_count: int | None = None,
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
        if state:
            lines.append(f"- State: `{state}`")
        if selection_gap_reason:
            lines.append(f"- Selection gap reason: `{selection_gap_reason}`")
        if open_backlog_count is not None:
            lines.append(f"- Open backlog items: {open_backlog_count}")
        lines.append("")
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
        patch_commands = worktree_patch_add_command_texts(item)
        if patch_commands:
            lines.append("   - patch-add commands:")
            lines.extend(f"     - `{command}`" for command in patch_commands)
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
    cleanup_review = f"`{RUNTIME_ARTIFACT_CLEANUP_COMMAND}`"
    worktree_plan_review = f"`{STRICT_WORKTREE_COMMIT_PLAN_COMMAND}`"
    if recommendation == "improve_fallback_diversity":
        repeated_family = repeated_fallback_family_from_item(item)
        if repeated_family:
            return (
                f"surface a non-{repeated_family} fallback family before selecting "
                f"more {repeated_family} work, then rerun autonomy and inspect "
                "autonomy status"
            )
        return (
            "surface a non-repeated fallback family before selecting more of the "
            "same family, then rerun autonomy and inspect autonomy status"
        )
    if recommendation == "improve_empty_loop_handling":
        history_path = loop_history_evidence_path(item)
        return (
            f"inspect `{history_path}`, confirm whether the repeated empty-loop "
            f"chain still has no open backlog, then run "
            f"`{AUTONOMY_ONE_LOOP_COMMAND}` and inspect autonomy status"
        )
    if recommendation == "reduce_integration_risk":
        area_phrase = join_action_areas(worktree_action_areas(item))
        if area_phrase:
            patch_add_group_count = worktree_patch_add_group_count(item)
            if patch_add_group_count > 0:
                group_label = (
                    "cross-cutting group"
                    if patch_add_group_count == 1
                    else "cross-cutting groups"
                )
                patch_command_hint = worktree_patch_add_command_hint(item)
                return (
                    f"triage {area_phrase} changes first, patch-add "
                    f"{patch_add_group_count} {group_label}, using "
                    f"{patch_command_hint}, rerun "
                    f"{worktree_plan_review}, then rerun self-inspection"
                )
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
    if recommendation == "stabilize_verification_surface":
        compare_path = verification_compare_path(item)
        reason = verification_not_comparable_reason(item)
        suffix = f"; not comparable: {reason}" if reason else ""
        if compare_path:
            return (
                f"inspect `{compare_path}`, restore comparable baseline/candidate "
                f"fast and deep evidence, then rerun verification{suffix}"
            )
        return (
            "inspect the verification report, restore comparable baseline/candidate "
            f"fast and deep evidence, then rerun verification{suffix}"
        )
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
    if recommendation == "stabilize_verification_surface":
        run_pair = verification_run_pair(item)
        if run_pair is not None:
            baseline_run, candidate_run = run_pair
            return (
                f"python -m qa_z verify --baseline-run {baseline_run} "
                f"--candidate-run {candidate_run}"
            )
    commands = {
        "add_benchmark_fixture": BENCHMARK_JSON_COMMAND,
        "reduce_integration_risk": STRICT_WORKTREE_COMMIT_PLAN_COMMAND,
        "isolate_foundation_commit": SELF_INSPECT_COMMAND,
        "audit_worktree_integration": SELF_INSPECT_COMMAND,
        "improve_empty_loop_handling": AUTONOMY_ONE_LOOP_COMMAND,
        "improve_fallback_diversity": AUTONOMY_ONE_LOOP_COMMAND,
        "stabilize_verification_surface": (
            "python -m qa_z verify --baseline-run <baseline> "
            "--candidate-run <candidate>"
        ),
        "create_repair_session": (
            "python -m qa_z repair-session status --session <session>"
        ),
    }
    return commands.get(recommendation, SELF_INSPECT_COMMAND)


def loop_history_evidence_path(item: dict[str, Any]) -> str:
    """Return the loop-history path referenced by empty-loop evidence."""
    for entry in item_evidence_entries(item):
        if str(entry.get("source") or "").strip() != "loop_history":
            continue
        path = str(entry.get("path") or "").strip()
        if path:
            return path
    return ".qa-z/loops/history.jsonl"


def verification_compare_path(item: dict[str, Any]) -> str:
    """Return the compare artifact path referenced by verification evidence."""
    for entry in item_evidence_entries(item):
        compare_path = str(entry.get("compare_path") or "").strip()
        if compare_path:
            return compare_path
    return ""


def verification_run_pair(item: dict[str, Any]) -> tuple[str, str] | None:
    """Return baseline and candidate runs referenced by verification evidence."""
    for entry in item_evidence_entries(item):
        baseline_run = str(entry.get("baseline_run") or "").strip()
        candidate_run = str(entry.get("candidate_run") or "").strip()
        if baseline_run and candidate_run:
            return baseline_run, candidate_run
    return None


def item_evidence_entries(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Return typed evidence entries from a selected task."""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return []
    return [entry for entry in evidence if isinstance(entry, dict)]


def worktree_patch_add_group_count(item: dict[str, Any]) -> int:
    """Return patch-add group count when strict worktree evidence is otherwise clean."""
    fields: dict[str, int] = {}
    for entry in item_evidence_entries(item):
        if str(entry.get("source") or "").strip() != "worktree_commit_plan_json":
            continue
        fields = summary_int_fields(str(entry.get("summary") or ""))
        break
    if not fields:
        return 0
    if fields.get("generated", 0) or fields.get("unassigned", 0):
        return 0
    return fields.get("patch_add_groups", 0)


def worktree_commit_plan_json_path(item: dict[str, Any]) -> str:
    """Return the strict worktree commit-plan evidence path for operator hints."""
    for entry in item_evidence_entries(item):
        if str(entry.get("source") or "").strip() != "worktree_commit_plan_json":
            continue
        path = str(entry.get("path") or "").strip()
        if path:
            return path
    return ".qa-z/tmp/worktree-commit-plan.json"


def worktree_patch_add_command_hint(item: dict[str, Any]) -> str:
    """Return inline patch-add commands, falling back to the JSON evidence path."""
    commands = worktree_patch_add_command_texts(item)
    if commands:
        visible_commands = commands[:INLINE_PATCH_COMMAND_LIMIT]
        hint = "; ".join(f"`{command}`" for command in visible_commands)
        truncated_count = len(commands) - len(visible_commands)
        if truncated_count > 0:
            hint = (
                f"{hint}; plus {truncated_count} more in "
                f"`{worktree_commit_plan_json_path(item)}`"
            )
        return hint
    return (
        f"`{worktree_commit_plan_json_path(item)}` "
        "`cross_cutting_groups[].patch_command_text`"
    )


def worktree_patch_add_command_texts(item: dict[str, Any]) -> list[str]:
    """Return structured patch-add command text from strict worktree evidence."""
    for entry in item_evidence_entries(item):
        if str(entry.get("source") or "").strip() != "worktree_commit_plan_json":
            continue
        commands = entry.get("patch_command_texts")
        if not isinstance(commands, list):
            return []
        return [
            str(command).strip()
            for command in commands
            if isinstance(command, str) and command.strip()
        ]
    return []


def summary_int_fields(summary: str) -> dict[str, int]:
    """Parse key=value integer fields from compact evidence summaries."""
    fields: dict[str, int] = {}
    for segment in summary.split(";"):
        if "=" not in segment:
            continue
        key, value = segment.strip().split("=", maxsplit=1)
        value = value.strip().split(maxsplit=1)[0]
        try:
            fields[key.strip()] = int(value)
        except ValueError:
            continue
    return fields


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
