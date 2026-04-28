"""Internal backlog implication helpers for executor-ingest flows."""

from __future__ import annotations

from typing import Any


def backlog_implications_for_ingest(
    *,
    result: Any,
    result_id: str,
    ingest_status: str,
    freshness_reason: str | None,
    provenance_reason: str | None,
    warnings: list[str],
) -> list[dict[str, Any]]:
    """Translate ingest outcomes into structural backlog implications."""
    items: list[dict[str, Any]] = []
    if (
        freshness_reason
        in {
            "session_newer_than_result",
            "result_before_bridge",
            "result_from_future",
        }
        or ingest_status == "rejected_stale"
    ):
        items.append(
            backlog_implication(
                implication_id=f"evidence_freshness_gap-{result_id}",
                title="Harden executor result freshness handling",
                category="evidence_freshness_gap",
                recommendation="harden_executor_result_freshness",
                signals=["executor_result_stale"],
                impact=3,
                likelihood=4,
                confidence=4,
                repair_cost=3,
                summary="timestamp ordering blocked verification resume",
            )
        )
    if ingest_status == "rejected_mismatch" or provenance_reason:
        items.append(
            backlog_implication(
                implication_id=f"provenance_gap-{result_id}",
                title="Harden executor provenance validation",
                category="provenance_gap",
                recommendation="audit_executor_contract",
                signals=["executor_result_provenance_mismatch"],
                impact=4,
                likelihood=4,
                confidence=4,
                repair_cost=3,
                summary="bridge/session provenance mismatch rejected ingest",
            )
        )
    if ingest_status == "accepted_partial":
        items.append(
            backlog_implication(
                implication_id=f"partial_completion_gap-{result_id}",
                title="Harden partial completion ingest handling",
                category="partial_completion_gap",
                recommendation="harden_partial_completion_handling",
                signals=["executor_result_partial"],
                impact=3,
                likelihood=4,
                confidence=4,
                repair_cost=3,
                summary="partial result blocked immediate verify",
            )
        )
    if result.status in {"no_op", "not_applicable"} or (
        "completed_without_changed_files" in warnings
        or "no_op_without_explanation" in warnings
    ):
        items.append(
            backlog_implication(
                implication_id=f"no_op_safeguard_gap-{result_id}",
                title="Harden no-op executor result safeguards",
                category="no_op_safeguard_gap",
                recommendation="harden_executor_no_op_safeguards",
                signals=["executor_result_no_op"],
                impact=3,
                likelihood=3,
                confidence=4,
                repair_cost=2,
                summary="no-op style result lacked a strong explanation or file trace",
            )
        )
    if {
        "validation_summary_conflicts_with_results",
        "validation_result_command_not_declared",
    } & set(warnings):
        items.append(
            backlog_implication(
                implication_id=f"workflow_gap-{result_id}",
                title="Harden executor validation evidence consistency",
                category="workflow_gap",
                recommendation="audit_executor_contract",
                signals=["executor_validation_failed"],
                impact=3,
                likelihood=3,
                confidence=4,
                repair_cost=2,
                summary="validation metadata conflicted with detailed executor results",
            )
        )
    return unique_implications(items)


def backlog_implication(
    *,
    implication_id: str,
    title: str,
    category: str,
    recommendation: str,
    signals: list[str],
    impact: int,
    likelihood: int,
    confidence: int,
    repair_cost: int,
    summary: str,
) -> dict[str, Any]:
    """Build one structured backlog implication entry."""
    return {
        "id": implication_id,
        "title": title,
        "category": category,
        "recommendation": recommendation,
        "signals": list(signals),
        "impact": impact,
        "likelihood": likelihood,
        "confidence": confidence,
        "repair_cost": repair_cost,
        "summary": summary,
    }


def unique_implications(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate implication entries by id."""
    seen: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = str(item.get("id") or "")
        if item_id and item_id not in seen:
            seen[item_id] = item
    return [seen[key] for key in sorted(seen)]


def stable_unique_strings(values: list[str]) -> list[str]:
    """Return de-duplicated strings in first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered
