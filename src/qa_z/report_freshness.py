"""Freshness and git-context parsing helpers for report evidence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re

__all__ = [
    "inspection_date",
    "report_document_branch",
    "report_document_date",
    "report_document_head",
    "report_freshness_summary",
    "report_is_stale_for_inspection",
]

REPORT_DATE_PATTERN = re.compile(
    r"(?im)^\s*(?:date|verified on|audit date)\s*:\s*(\d{4}-\d{2}-\d{2})\b"
)
REPORT_BRANCH_PATTERN = re.compile(
    r"(?im)^\s*(?:branch|branch context|current branch)\s*:\s*`?([^`\n]+?)`?\s*$"
)
REPORT_HEAD_PATTERN = re.compile(
    r"(?im)^\s*(?:head|commit|head commit)\s*:\s*`?([0-9a-f]{7,40})`?\s*$"
)
LOCAL_DATE_WINDOW_OFFSETS_MINUTES = tuple(range(-12 * 60, (14 * 60) + 1, 15))


def report_document_date(text: str) -> str | None:
    """Return the declared report date when one is present."""
    match = REPORT_DATE_PATTERN.search(text)
    if not match:
        return None
    return match.group(1)


def report_document_branch(text: str) -> str | None:
    """Return the declared branch context when one is present."""
    match = REPORT_BRANCH_PATTERN.search(text)
    if not match:
        return None
    return match.group(1).strip()


def report_document_head(text: str) -> str | None:
    """Return the declared commit context when one is present."""
    match = REPORT_HEAD_PATTERN.search(text)
    if not match:
        return None
    return match.group(1).strip()


def inspection_date(generated_at: str | None) -> str | None:
    """Return the current inspection date for report freshness checks."""
    text = str(generated_at or "").strip()
    if len(text) < 10:
        return None
    return text[:10]


def possible_inspection_dates(generated_at: str | None) -> set[str]:
    """Return report dates that can legitimately match the inspection timestamp."""
    current_date = inspection_date(generated_at)
    if not current_date:
        return set()
    dates = {current_date}
    text = str(generated_at or "").strip()
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return dates
    if parsed.tzinfo is None:
        return dates
    utc = parsed.astimezone(timezone.utc)
    for offset_minutes in LOCAL_DATE_WINDOW_OFFSETS_MINUTES:
        dates.add((utc + timedelta(minutes=offset_minutes)).date().isoformat())
    return dates


def report_freshness_summary(
    text: str,
    generated_at: str | None,
    *,
    current_branch: str | None = None,
    current_head: str | None = None,
) -> str | None:
    """Render a compact freshness proof for a report that matched live context."""
    details: list[str] = []
    report_date = report_document_date(text)
    current_date = inspection_date(generated_at)
    possible_dates = possible_inspection_dates(generated_at)
    if report_date and report_date in possible_dates:
        if current_date and report_date == current_date:
            details.append(f"date={report_date}")
        else:
            details.append(f"date~={report_date}")
    report_branch = report_document_branch(text)
    if (
        report_branch
        and current_branch
        and current_branch != "HEAD"
        and report_branch == current_branch
    ):
        details.append(f"branch={report_branch}")
    report_head = report_document_head(text)
    if report_head and current_head and report_head == current_head:
        details.append(f"head={report_head}")
    if not details:
        return None
    return "report freshness verified: " + "; ".join(details)


def report_is_stale_for_inspection(
    text: str,
    generated_at: str | None,
    *,
    current_branch: str | None = None,
    current_head: str | None = None,
    require_head_when_available: bool = False,
) -> bool:
    """Return whether a report date or git context no longer matches inspection."""
    report_date = report_document_date(text)
    possible_dates = possible_inspection_dates(generated_at)
    if report_date and possible_dates and report_date not in possible_dates:
        return True
    report_branch = report_document_branch(text)
    if (
        report_branch
        and current_branch
        and current_branch != "HEAD"
        and report_branch != current_branch
    ):
        return True
    report_head = report_document_head(text)
    if require_head_when_available and current_head and not report_head:
        return True
    if report_head and current_head and report_head != current_head:
        return True
    return False
