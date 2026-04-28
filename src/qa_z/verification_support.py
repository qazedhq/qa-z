"""Shared support helpers for verification comparisons and finding parsing."""

from __future__ import annotations

from typing import Any

from qa_z.runners.models import CheckResult
from qa_z.verification_models import (
    FastCheckDelta,
    VerificationCategory,
    VerificationFindingDelta,
)


def fast_delta_message(
    classification: VerificationCategory,
    baseline: CheckResult | None,
    candidate: CheckResult | None,
) -> str:
    """Return a compact explanation for a fast-check delta."""
    if classification == "resolved":
        return "Previously blocking check now passes or warns."
    if classification == "still_failing":
        return "Check remains blocking after repair."
    if classification == "regressed":
        return "Previously non-blocking check is now blocking."
    if classification == "newly_introduced":
        return "Candidate run has a new blocking check."
    if baseline is None or candidate is None:
        return "Check exists in only one run and cannot be compared directly."
    return "Check was skipped in at least one run and cannot verify repair."


def normalize_path(path: str) -> str:
    """Normalize paths to stable slash-separated repository paths."""
    return path.replace("\\", "/").strip()


def normalize_message(message: str) -> str:
    """Normalize message text for strict identity without fuzzy matching."""
    return " ".join(message.split()).strip().lower()


def first_nonempty(*values: object) -> str:
    """Return the first non-empty value as text."""
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def coerce_positive_int(value: object) -> int | None:
    """Return a positive integer, otherwise None."""
    try:
        number = int(str(value))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def empty_categories(
    _item_type: type[FastCheckDelta] | type[VerificationFindingDelta],
) -> dict[VerificationCategory, list[Any]]:
    """Return all verification categories with stable ordering."""
    return {
        "resolved": [],
        "still_failing": [],
        "regressed": [],
        "newly_introduced": [],
        "skipped_or_not_comparable": [],
    }
