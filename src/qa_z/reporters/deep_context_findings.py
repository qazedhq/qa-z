"""Finding normalization helpers for deep-context summaries."""

from __future__ import annotations

from typing import Any


def normalize_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Return a stable finding mapping for renderer consumption."""
    return {
        "rule_id": str(finding.get("rule_id") or "unknown"),
        "severity": str(finding.get("severity") or "UNKNOWN"),
        "path": str(finding.get("path") or ""),
        "line": finding.get("line"),
        "message": str(finding.get("message") or ""),
    }


def normalize_grouped_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Return a stable grouped finding mapping for renderer consumption."""
    return {
        "rule_id": str(finding.get("rule_id") or "unknown"),
        "severity": str(finding.get("severity") or "UNKNOWN"),
        "path": str(finding.get("path") or ""),
        "count": coerce_count(finding.get("count")),
        "representative_line": finding.get("representative_line"),
        "message": str(finding.get("message") or ""),
    }


def coerce_count(value: Any) -> int:
    """Return a positive occurrence count for grouped findings."""
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 1
    return count if count > 0 else 1


def unique_preserve_order(items: list[str]) -> list[str]:
    """Return unique strings in first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
