"""Bridge output warning helpers for executor-result ingest."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.executor_bridge_support import bridge_output_warnings
from qa_z.executor_ingest_support import optional_text
from qa_z.executor_result import resolve_bridge_manifest_path


def bridge_output_warning_ids(bridge: dict[str, Any]) -> list[str]:
    """Return warning ids carried by the source bridge manifest."""
    ids: list[str] = []
    raw_warnings = bridge.get("warnings")
    if not isinstance(raw_warnings, list):
        return ids
    for warning in raw_warnings:
        if isinstance(warning, dict):
            warning_id = optional_text(warning.get("id"))
        else:
            warning_id = optional_text(warning)
        if warning_id:
            ids.append(warning_id)
    return ids


def bridge_output_warning_ids_for_manifest(
    root: Path, result_path: Path, bridge_id: str
) -> list[str]:
    """Return output warning ids recomputed from the bridge manifest location."""
    manifest_path = resolve_bridge_manifest_path(
        root, bridge_id, result_path=result_path
    )
    return bridge_output_warning_ids(
        {"warnings": bridge_output_warnings(root=root, bridge_dir=manifest_path.parent)}
    )


def unique_warning_ids(warnings: list[str]) -> list[str]:
    """Return warning ids without duplicates while preserving order."""
    unique: list[str] = []
    seen: set[str] = set()
    for warning in warnings:
        if warning in seen:
            continue
        seen.add(warning)
        unique.append(warning)
    return unique
