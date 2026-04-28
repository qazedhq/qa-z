"""Selection scoring and diversity helpers for backlog task choice."""

from __future__ import annotations

from typing import Any

INTRA_SELECTION_FAMILY_PENALTY = 2
REPEATED_FAMILY_RECOVERY_PENALTY = 50
RECENT_SELECTION_WINDOW = 2
FALLBACK_FAMILY_BY_CATEGORY = {
    "autonomy_selection_gap": "loop_health",
    "backlog_reseeding_gap": "loop_health",
    "coverage_gap": "benchmark_expansion",
    "docs_drift": "docs_sync",
    "schema_drift": "docs_sync",
    "workflow_gap": "workflow_remediation",
    "integration_gap": "workflow_remediation",
    "provenance_gap": "workflow_remediation",
    "partial_completion_gap": "workflow_remediation",
    "no_op_safeguard_gap": "workflow_remediation",
    "worktree_risk": "cleanup",
    "commit_isolation_gap": "cleanup",
    "artifact_hygiene_gap": "cleanup",
    "runtime_artifact_cleanup_gap": "cleanup",
    "deferred_cleanup_gap": "cleanup",
    "evidence_freshness_gap": "cleanup",
}


def apply_selection_penalty(
    item: dict[str, Any],
    *,
    recent_entries: list[dict[str, Any]],
    open_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Attach a light reselection penalty using recent loop history."""
    enriched = dict(item)
    penalty, reasons = selection_penalty_for_item(
        item=item,
        recent_entries=recent_entries,
        open_items=open_items,
    )
    enriched["selection_penalty"] = penalty
    enriched["selection_penalty_reasons"] = reasons
    enriched["selection_priority_score"] = max(
        _int_value(item.get("priority_score")) - penalty,
        0,
    )
    return enriched


def select_items_with_batch_diversity(
    *, scored_items: list[dict[str, Any]], count: int
) -> list[dict[str, Any]]:
    """Select tasks greedily while lightly diversifying fallback families."""
    remaining = [dict(item) for item in scored_items]
    selected: list[dict[str, Any]] = []
    while remaining and len(selected) < count:
        rescored = [
            apply_intra_selection_penalty(
                apply_initial_repeated_family_recovery_penalty(
                    item,
                    remaining_items=remaining,
                    selected_items=selected,
                ),
                selected_items=selected,
                remaining_items=remaining,
            )
            for item in remaining
        ]
        chosen = sorted(
            rescored,
            key=lambda item: (
                -_int_value(
                    item.get("selection_priority_score", item.get("priority_score"))
                ),
                _int_value(item.get("selection_penalty")),
                str(item.get("category", "")),
                str(item.get("id", "")),
            ),
        )[0]
        selected.append(chosen)
        chosen_id = str(chosen.get("id") or "")
        remaining = [
            item for item in remaining if str(item.get("id") or "") != chosen_id
        ]
    return selected


def apply_initial_repeated_family_recovery_penalty(
    item: dict[str, Any],
    *,
    remaining_items: list[dict[str, Any]],
    selected_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Prefer a concrete alternative family before repeated-family recovery meta work."""
    if selected_items:
        return item
    repeated_families = repeated_fallback_families_from_items(remaining_items)
    if not repeated_families:
        return item
    alternative_families = {
        other_family
        for other in remaining_items
        if str(other.get("id") or "") != str(item.get("id") or "")
        if (
            other_family := fallback_family_for_category(
                str(other.get("category") or "")
            )
        )
        if other_family not in repeated_families and other_family != "loop_health"
    }
    if not alternative_families:
        return item
    repeated_family = repeated_fallback_family_from_item(item)
    if repeated_family and repeated_family in repeated_families:
        return add_selection_penalty(
            item,
            amount=REPEATED_FAMILY_RECOVERY_PENALTY,
            reason="current_batch_repeated_fallback_gap_deprioritized",
        )
    family = fallback_family_for_category(str(item.get("category") or ""))
    if family and family in repeated_families:
        return add_selection_penalty(
            item,
            amount=REPEATED_FAMILY_RECOVERY_PENALTY,
            reason="current_batch_repeated_fallback_family_suppressed",
        )
    return item


def apply_intra_selection_penalty(
    item: dict[str, Any],
    *,
    selected_items: list[dict[str, Any]],
    remaining_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Apply a light within-batch family penalty when alternatives exist."""
    enriched = dict(item)
    if not selected_items:
        return enriched
    family = fallback_family_for_category(str(item.get("category") or ""))
    if not family:
        return enriched
    selected_families = set(fallback_families_for_items(selected_items))
    alternative_families = {
        other_family
        for other in remaining_items
        if str(other.get("id") or "") != str(item.get("id") or "")
        if (
            other_family := fallback_family_for_category(
                str(other.get("category") or "")
            )
        )
        if other_family != family
    }
    repeated_families = repeated_fallback_families_from_items(selected_items)
    if family not in selected_families or not alternative_families:
        return apply_repeated_family_recovery_penalty(
            enriched,
            family=family,
            repeated_families=repeated_families,
            remaining_items=remaining_items,
            selected_items=selected_items,
        )
    base_penalty = _int_value(enriched.get("selection_penalty"))
    reasons = [
        str(reason)
        for reason in enriched.get("selection_penalty_reasons", [])
        if str(reason).strip()
    ]
    reasons.append("current_batch_fallback_family_reselected")
    enriched["selection_penalty"] = base_penalty + INTRA_SELECTION_FAMILY_PENALTY
    enriched["selection_penalty_reasons"] = reasons
    enriched["selection_priority_score"] = max(
        _int_value(
            enriched.get("selection_priority_score", enriched.get("priority_score"))
        )
        - INTRA_SELECTION_FAMILY_PENALTY,
        0,
    )
    return apply_repeated_family_recovery_penalty(
        enriched,
        family=family,
        repeated_families=repeated_families,
        remaining_items=remaining_items,
        selected_items=selected_items,
    )


def selection_penalty_for_item(
    *,
    item: dict[str, Any],
    recent_entries: list[dict[str, Any]],
    open_items: list[dict[str, Any]],
) -> tuple[int, list[str]]:
    """Return a deterministic diversity penalty for immediate reselection."""
    if len(recent_entries) < RECENT_SELECTION_WINDOW:
        return 0, []
    item_id = str(item.get("id") or "")
    category = str(item.get("category") or "")
    fallback_family = fallback_family_for_category(category)
    available_fallback_families = {
        family
        for open_item in open_items
        if (
            family := fallback_family_for_category(str(open_item.get("category") or ""))
        )
    }
    penalty = 0
    reasons: list[str] = []
    if item_id and all(item_id in selected_task_ids(entry) for entry in recent_entries):
        penalty += 2
        reasons.append("recent_task_reselected")
    if category and all(
        category in selected_task_categories(entry, open_items=open_items)
        for entry in recent_entries
    ):
        penalty += 1
        reasons.append("recent_category_reselected")
    if (
        fallback_family
        and len(available_fallback_families) > 1
        and all(
            fallback_family
            in selected_task_fallback_families(entry, open_items=open_items)
            for entry in recent_entries
        )
    ):
        penalty += 2
        reasons.append("recent_fallback_family_reselected")
    return penalty, reasons


def apply_repeated_family_recovery_penalty(
    item: dict[str, Any],
    *,
    family: str | None,
    repeated_families: set[str],
    remaining_items: list[dict[str, Any]],
    selected_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Push one alternative family into the batch after a repeat-gap task."""
    if (
        not family
        or family not in repeated_families
        or selected_non_repeated_families(selected_items, repeated_families)
    ):
        return item
    alternative_families = {
        other_family
        for other in remaining_items
        if str(other.get("id") or "") != str(item.get("id") or "")
        if (
            other_family := fallback_family_for_category(
                str(other.get("category") or "")
            )
        )
        if other_family not in repeated_families and other_family != "loop_health"
    }
    if not alternative_families:
        return item
    return add_selection_penalty(
        item,
        amount=REPEATED_FAMILY_RECOVERY_PENALTY,
        reason="current_batch_repeated_fallback_family_suppressed",
    )


def fallback_family_for_category(category: str) -> str | None:
    """Return the fallback family for one backlog category, when applicable."""
    return FALLBACK_FAMILY_BY_CATEGORY.get(category.strip())


def repeated_fallback_family_from_item(item: dict[str, Any]) -> str | None:
    """Return the repeated fallback family named in a loop-health item, if any."""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return None
    marker = "recent_fallback_family="
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        summary = str(entry.get("summary") or "")
        if marker not in summary:
            continue
        family = summary.split(marker, maxsplit=1)[1].split(";", maxsplit=1)[0].strip()
        if family:
            return family
    return None


def repeated_fallback_families_from_items(items: list[dict[str, Any]]) -> set[str]:
    """Return repeated fallback families explicitly named by selected items."""
    return {
        family for item in items if (family := repeated_fallback_family_from_item(item))
    }


def selected_non_repeated_families(
    items: list[dict[str, Any]], repeated_families: set[str]
) -> set[str]:
    """Return already-selected non-loop-health families outside the repeated set."""
    return {
        family
        for family in fallback_families_for_items(items)
        if family not in repeated_families and family != "loop_health"
    }


def selected_task_ids(entry: dict[str, Any]) -> set[str]:
    """Return selected task ids from one loop-history entry."""
    selected_tasks = entry.get("selected_tasks")
    if not isinstance(selected_tasks, list):
        return set()
    return {str(item) for item in selected_tasks if str(item).strip()}


def selected_task_categories(
    entry: dict[str, Any], *, open_items: list[dict[str, Any]]
) -> set[str]:
    """Return selected categories from history, deriving them when needed."""
    selected_categories = entry.get("selected_categories")
    if isinstance(selected_categories, list):
        return {str(item) for item in selected_categories if str(item).strip()}
    categories_by_id = {
        str(item.get("id")): str(item.get("category") or "")
        for item in open_items
        if isinstance(item, dict) and item.get("id")
    }
    return {
        categories_by_id[item_id]
        for item_id in selected_task_ids(entry)
        if categories_by_id.get(item_id)
    }


def selected_task_fallback_families(
    entry: dict[str, Any], *, open_items: list[dict[str, Any]]
) -> set[str]:
    """Return selected fallback families from history, deriving them when needed."""
    selected_fallback_families = entry.get("selected_fallback_families")
    if isinstance(selected_fallback_families, list):
        return {str(item) for item in selected_fallback_families if str(item).strip()}
    return {
        family
        for category in selected_task_categories(entry, open_items=open_items)
        if (family := fallback_family_for_category(category))
    }


def fallback_families_for_items(items: list[dict[str, Any]]) -> list[str]:
    """Return stable fallback families represented by selected backlog items."""
    return sorted(
        {
            family
            for item in items
            if (family := fallback_family_for_category(str(item.get("category") or "")))
        }
    )


def evidence_paths(items: list[dict[str, Any]]) -> list[str]:
    """Return unique evidence paths from backlog items."""
    paths: set[str] = set()
    for item in items:
        evidence = item.get("evidence")
        if not isinstance(evidence, list):
            continue
        for entry in evidence:
            if isinstance(entry, dict) and entry.get("path"):
                paths.add(str(entry["path"]))
    return sorted(paths)


def add_selection_penalty(
    item: dict[str, Any], *, amount: int, reason: str
) -> dict[str, Any]:
    """Return a copy of one item with an additive selection penalty applied."""
    enriched = dict(item)
    reasons = [
        str(existing)
        for existing in enriched.get("selection_penalty_reasons", [])
        if str(existing).strip()
    ]
    if reason not in reasons:
        reasons.append(reason)
    enriched["selection_penalty"] = (
        _int_value(enriched.get("selection_penalty")) + amount
    )
    enriched["selection_penalty_reasons"] = reasons
    enriched["selection_priority_score"] = max(
        _int_value(
            enriched.get("selection_priority_score", enriched.get("priority_score"))
        )
        - amount,
        0,
    )
    return enriched


def _int_value(value: object) -> int:
    """Return an integer value, or zero when absent or invalid."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
