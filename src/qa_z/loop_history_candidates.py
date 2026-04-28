"""Loop-history candidate input helpers for autonomy selection health."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.backlog_core import slugify
from qa_z.improvement_state import is_empty_loop_entry, load_history_entries
from qa_z.task_selection import selected_task_fallback_families

__all__ = [
    "discover_empty_loop_candidate_inputs",
    "discover_repeated_fallback_family_candidate_inputs",
]

EMPTY_LOOP_CHAIN_LENGTH = 3
FALLBACK_REPEAT_WINDOW = 3


def discover_empty_loop_candidate_inputs(root: Path) -> list[dict[str, Any]]:
    """Return candidate packets from repeated empty-loop history chains."""
    history_path = root / ".qa-z" / "loops" / "history.jsonl"
    entries = load_history_entries(history_path)
    if len(entries) < EMPTY_LOOP_CHAIN_LENGTH:
        return []
    recent = entries[-EMPTY_LOOP_CHAIN_LENGTH:]
    if not all(is_empty_loop_entry(entry) for entry in recent):
        return []
    loop_ids = recent_loop_ids(recent)
    states = [str(entry.get("state") or "unknown") for entry in recent]
    return [
        {
            "id": "autonomy_selection_gap-empty-loop-chain",
            "title": "Prevent repeated empty autonomy selection loops",
            "category": "autonomy_selection_gap",
            "evidence": [
                {
                    "source": "loop_history",
                    "path": history_path,
                    "summary": (
                        f"recent_empty_loops={len(recent)}; "
                        f"loop_ids={', '.join(loop_ids)}; "
                        f"states={', '.join(states)}"
                    ),
                }
            ],
            "impact": 4,
            "likelihood": 4,
            "confidence": 4,
            "repair_cost": 2,
            "recommendation": "improve_empty_loop_handling",
            "signals": ["recent_empty_loop_chain", "service_readiness_gap"],
        }
    ]


def discover_repeated_fallback_family_candidate_inputs(
    root: Path,
) -> list[dict[str, Any]]:
    """Return candidate packets from repeated fallback-family reuse."""
    history_path = root / ".qa-z" / "loops" / "history.jsonl"
    entries = load_history_entries(history_path)
    if len(entries) < FALLBACK_REPEAT_WINDOW:
        return []
    recent = entries[-FALLBACK_REPEAT_WINDOW:]
    families = [
        selected_task_fallback_families(entry, open_items=[]) for entry in recent
    ]
    if not all(len(item) == 1 for item in families):
        return []
    family = next(iter(families[0]))
    if not all(next(iter(item)) == family for item in families[1:]):
        return []
    loop_ids = recent_loop_ids(recent)
    states = [str(entry.get("state") or "unknown") for entry in recent]
    return [
        {
            "id": f"autonomy_selection_gap-repeated-fallback-{slugify(family)}",
            "title": "Diversify repeated fallback selections across task families",
            "category": "autonomy_selection_gap",
            "evidence": [
                {
                    "source": "loop_history",
                    "path": history_path,
                    "summary": (
                        f"recent_fallback_family={family}; loops={len(recent)}; "
                        f"loop_ids={', '.join(loop_ids)}; "
                        f"states={', '.join(states)}"
                    ),
                }
            ],
            "impact": 4,
            "likelihood": 4,
            "confidence": 4,
            "repair_cost": 2,
            "recommendation": "improve_fallback_diversity",
            "signals": ["recent_fallback_family_repeat", "service_readiness_gap"],
        }
    ]


def recent_loop_ids(entries: list[dict[str, Any]]) -> list[str]:
    """Return stable loop ids from a recent history window."""
    return [
        str(entry.get("loop_id") or "unknown")
        for entry in entries
        if str(entry.get("loop_id") or "").strip()
    ]
