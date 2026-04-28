"""Summary helpers for executor-bridge manifests and guides."""

from __future__ import annotations

from typing import Any


def bridge_evidence_summary(
    loop_outcome: dict[str, Any] | None,
    session,
    handoff: dict[str, Any],
) -> dict[str, Any]:
    """Return compact bridge evidence context."""
    repair = handoff.get("repair") if isinstance(handoff, dict) else {}
    targets = repair.get("targets") if isinstance(repair, dict) else []
    return {
        "why_selected": (
            loop_outcome.get("next_recommendations", []) if loop_outcome else []
        ),
        "session_state": session.state,
        "baseline_status": session.provenance.get("baseline_status"),
        "repair_needed": session.provenance.get("repair_needed"),
        "target_count": len(targets) if isinstance(targets, list) else 0,
    }


def bridge_safety_package_summary(
    *, copied_inputs: dict[str, Any], safety_policy: dict[str, Any]
) -> dict[str, Any]:
    """Return the compact bridge-local view of the copied safety package."""
    rules = safety_policy.get("rules")
    rule_ids: list[str] = []
    if isinstance(rules, list):
        rule_ids = [
            str(rule.get("id"))
            for rule in rules
            if isinstance(rule, dict) and str(rule.get("id") or "").strip()
        ]
    return {
        "package_id": safety_policy.get("package_id"),
        "status": safety_policy.get("status"),
        "policy_json": copied_inputs.get("executor_safety_json"),
        "policy_markdown": copied_inputs.get("executor_safety_markdown"),
        "rule_ids": rule_ids,
        "rule_count": len(rule_ids),
    }


def bridge_safety_rule_count(manifest: dict[str, Any]) -> int | str:
    """Return the displayable safety rule count for bridge guides."""
    safety_package = manifest.get("safety_package")
    if not isinstance(safety_package, dict):
        return "unknown"
    rule_count = safety_package.get("rule_count")
    if isinstance(rule_count, int):
        return rule_count
    rule_ids = safety_package.get("rule_ids")
    if isinstance(rule_ids, list):
        return len(rule_ids)
    return "unknown"
