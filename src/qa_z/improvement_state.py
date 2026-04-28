"""Persistent backlog and loop-history state for QA-Z self-improvement."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.task_selection import evidence_paths, fallback_families_for_items

BACKLOG_KIND = "qa_z.improvement_backlog"
LOOP_HISTORY_KIND = "qa_z.loop_history_entry"
OPEN_STATUSES = {"open", "selected", "in_progress"}
SELF_IMPROVEMENT_SCHEMA_VERSION = 1

__all__ = [
    "append_history",
    "backlog_file",
    "empty_backlog",
    "is_empty_loop_entry",
    "load_backlog",
    "load_history_entries",
    "open_backlog_items",
]


def load_backlog(root: Path) -> dict[str, Any]:
    """Load the improvement backlog, returning an empty stable artifact if absent."""
    path = backlog_file(root)
    if not path.is_file():
        return empty_backlog()
    loaded = _read_json_object(path)
    if loaded.get("kind") != BACKLOG_KIND:
        return empty_backlog()
    items = loaded.get("items")
    if not isinstance(items, list):
        return empty_backlog()
    return loaded


def append_history(
    history_path: Path,
    *,
    loop_id: str,
    generated_at: str,
    selected_items: list[dict[str, Any]],
    open_items: list[dict[str, Any]],
    selection_context: dict[str, Any] | None = None,
) -> None:
    """Append one JSONL loop-memory record."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    selected_ids = [str(item.get("id")) for item in selected_items]
    selected_id_set = set(selected_ids)
    entry = {
        "kind": LOOP_HISTORY_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "loop_id": loop_id,
        "created_at": generated_at,
        "selected_tasks": selected_ids,
        "selected_categories": [
            str(item.get("category") or "")
            for item in selected_items
            if str(item.get("category") or "").strip()
        ],
        "selected_fallback_families": fallback_families_for_items(selected_items),
        "evidence_used": evidence_paths(selected_items),
        "resulting_session_id": None,
        "verify_verdict": None,
        "benchmark_delta": None,
        "next_candidates": [
            str(item.get("id"))
            for item in sorted(
                open_items,
                key=lambda item: (
                    -_int_value(
                        item.get("selection_priority_score", item.get("priority_score"))
                    ),
                    _int_value(item.get("selection_penalty")),
                    str(item.get("id", "")),
                ),
            )
            if str(item.get("id")) not in selected_id_set
        ],
    }
    if selection_context:
        source_self_inspection = str(
            selection_context.get("source_self_inspection") or ""
        ).strip()
        if source_self_inspection:
            entry["source_self_inspection"] = source_self_inspection
        live_repository = selection_context.get("live_repository")
        if isinstance(live_repository, dict):
            entry["live_repository"] = dict(live_repository)
        for key in (
            "source_self_inspection_loop_id",
            "source_self_inspection_generated_at",
        ):
            value = str(selection_context.get(key) or "").strip()
            if value:
                entry[key] = value
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def load_history_entries(path: Path) -> list[dict[str, Any]]:
    """Read loop history JSONL entries."""
    if not path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("kind") == LOOP_HISTORY_KIND:
            entries.append(data)
    return entries


def is_empty_loop_entry(entry: dict[str, Any]) -> bool:
    """Return whether a history entry represents an empty loop."""
    selected_tasks = entry.get("selected_tasks")
    if isinstance(selected_tasks, list) and selected_tasks:
        return False
    state = str(entry.get("state") or "")
    return state in {"blocked_no_candidates", "completed", "fallback_selected", ""}


def empty_backlog() -> dict[str, Any]:
    """Return an empty backlog object."""
    return {
        "kind": BACKLOG_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "updated_at": None,
        "items": [],
    }


def backlog_file(root: Path) -> Path:
    """Return the default improvement backlog path."""
    return root / ".qa-z" / "improvement" / "backlog.json"


def open_backlog_items(backlog: dict[str, Any]) -> list[dict[str, Any]]:
    """Return open backlog items from a backlog artifact."""
    return [
        item
        for item in backlog.get("items", [])
        if isinstance(item, dict) and str(item.get("status", "open")) in OPEN_STATUSES
    ]


def _read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object, returning an empty mapping for optional bad artifacts."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _int_value(value: object) -> int:
    """Return an integer value, or zero when absent or invalid."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
