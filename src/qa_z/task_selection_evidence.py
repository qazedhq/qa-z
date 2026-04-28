"""Evidence compaction helpers for self-improvement task selection."""

from __future__ import annotations

from typing import Any

__all__ = [
    "compact_backlog_evidence_summary",
    "worktree_action_areas",
]


def compact_backlog_evidence_summary(item: dict[str, Any]) -> str:
    """Return one compact evidence summary for a backlog item."""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return "none recorded"
    entry = compact_evidence_entry(evidence)
    if entry is None:
        return "none recorded"
    source = str(entry.get("source") or "artifact").strip() or "artifact"
    summary = str(entry.get("summary") or "").strip()
    path = str(entry.get("path") or "").strip()
    if summary:
        compact_summary = f"{source}: {summary}"
        basis = compact_action_basis(item, compact_summary)
        if basis:
            return f"{compact_summary}; action basis: {basis}"
        return compact_summary
    if path:
        compact_summary = f"{source}: {path}"
        basis = compact_action_basis(item, compact_summary)
        if basis:
            return f"{compact_summary}; action basis: {basis}"
        return compact_summary
    return "none recorded"


def compact_action_basis(item: dict[str, Any], primary_summary: str) -> str:
    """Return secondary evidence that explains specialized action hints."""
    area_basis = compact_area_action_basis(item, primary_summary)
    if area_basis:
        return area_basis
    return compact_generated_action_basis(item, primary_summary)


def compact_area_action_basis(item: dict[str, Any], primary_summary: str) -> str:
    """Return secondary area evidence that explains area-aware action hints."""
    if "areas=" in primary_summary:
        return ""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return ""
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        summary = str(entry.get("summary") or "").strip()
        if "areas=" not in summary:
            continue
        source = str(entry.get("source") or "artifact").strip() or "artifact"
        return f"{source}: {summary}"
    return ""


def compact_generated_action_basis(item: dict[str, Any], primary_summary: str) -> str:
    """Return generated artifact evidence behind deferred cleanup actions."""
    recommendation = str(item.get("recommendation") or "").strip()
    if recommendation != "triage_and_isolate_changes":
        return ""
    if (
        "generated_outputs:" in primary_summary
        or "runtime_artifacts:" in primary_summary
    ):
        return ""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return ""
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        source = str(entry.get("source") or "artifact").strip() or "artifact"
        if source not in {"generated_outputs", "runtime_artifacts"}:
            continue
        summary = str(entry.get("summary") or "").strip()
        path = str(entry.get("path") or "").strip()
        if summary:
            return f"{source}: {summary}"
        if path:
            return f"{source}: {path}"
    return ""


def worktree_action_areas(item: dict[str, Any]) -> list[str]:
    """Return ordered dirty worktree areas from compact evidence summaries."""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return []
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        summary = str(entry.get("summary") or "")
        marker = "areas="
        if marker not in summary:
            continue
        area_segment = summary.split(marker, maxsplit=1)[1].split(";", maxsplit=1)[0]
        areas: list[str] = []
        for pair in area_segment.split(","):
            if ":" not in pair:
                continue
            name = pair.strip().split(":", maxsplit=1)[0].strip()
            if name:
                areas.append(name)
        return areas
    return []


def compact_evidence_entry(evidence: list[Any]) -> dict[str, Any] | None:
    """Pick the best evidence entry for one-line human summaries."""
    entries = [entry for entry in evidence if isinstance(entry, dict)]
    if not entries:
        return None
    return sorted(
        enumerate(entries),
        key=lambda pair: (compact_evidence_priority(pair[1]), pair[0]),
    )[0][1]


def compact_evidence_priority(entry: dict[str, Any]) -> int:
    """Return a lower priority value for more useful compact evidence."""
    summary = str(entry.get("summary") or "").lower()
    if "alpha closure readiness snapshot" in summary:
        return 0
    return 1
