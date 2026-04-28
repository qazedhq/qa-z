"""Helper utilities for benchmark summaries and artifact coercion."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def format_path(path: Path, root: Path) -> str:
    """Return a slash-separated path relative to root when possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def read_json_object(path: Path) -> dict[str, Any]:
    """Read an optional JSON object artifact."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def coerce_mapping(value: object) -> dict[str, Any]:
    """Return a dict copy for JSON-like mappings."""
    if isinstance(value, dict):
        return dict(value)
    return {}


def string_list(value: object) -> list[str]:
    """Return non-empty strings from a JSON-like list."""
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def coerce_number(value: object) -> float | None:
    """Coerce a JSON-like numeric value."""
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def aggregate_filter_reasons(checks: list[Any]) -> dict[str, int]:
    """Aggregate deep filter reasons across checks."""
    reasons: Counter[str] = Counter()
    for check in checks:
        for key, value in check.filter_reasons.items():
            reasons[str(key)] += int(value)
    return dict(sorted(reasons.items()))


def unique_strings(values: list[str]) -> list[str]:
    """Return unique non-empty strings in first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
