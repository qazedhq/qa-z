"""Internal render helpers for executor-ingest human surfaces."""

from __future__ import annotations


def ingest_text_field(value: object, fallback: str) -> str:
    """Return a stable one-line ingest stdout field."""
    text = str(value or "").strip()
    return text or fallback


def ingest_check_stdout_line(label: str, value: object) -> str:
    """Render a compact ingest check status for operator stdout."""
    if not isinstance(value, dict):
        return f"{label}: unknown"
    status = ingest_text_field(value.get("status"), "unknown")
    reason = str(value.get("reason") or "").strip()
    if reason:
        return f"{label}: {status} ({reason})"
    return f"{label}: {status}"


def ingest_warning_stdout_summary(value: object) -> str | None:
    """Return a compact warnings summary for ingest stdout."""
    if not isinstance(value, list) or not value:
        return None
    warnings = [str(item).strip() for item in value if str(item).strip()]
    return ", ".join(warnings) if warnings else None


def ingest_implication_stdout_summary(value: object) -> str | None:
    """Return a compact backlog implication summary for ingest stdout."""
    if not isinstance(value, list) or not value:
        return None
    categories: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        category = str(item.get("category") or "").strip()
        if category and category not in seen:
            categories.append(category)
            seen.add(category)
    return ", ".join(categories) if categories else None
