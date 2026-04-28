"""Behavior tests for report freshness date windows."""

from __future__ import annotations

from qa_z.report_freshness import (
    report_freshness_summary,
    report_is_stale_for_inspection,
)


UTC_LATE = "2026-04-22T20:21:42Z"


def test_report_freshness_accepts_adjacent_local_date_on_matching_branch() -> None:
    text = """
    # Current State

    Date: 2026-04-23
    Branch context: `codex/qa-z-bootstrap`
    """

    assert (
        report_is_stale_for_inspection(
            text,
            UTC_LATE,
            current_branch="codex/qa-z-bootstrap",
        )
        is False
    )
    assert (
        report_freshness_summary(
            text,
            UTC_LATE,
            current_branch="codex/qa-z-bootstrap",
        )
        == "report freshness verified: date~=2026-04-23; branch=codex/qa-z-bootstrap"
    )


def test_report_freshness_rejects_dates_outside_possible_timezone_window() -> None:
    text = """
    # Current State

    Date: 2026-04-24
    Branch context: `codex/qa-z-bootstrap`
    """

    assert report_is_stale_for_inspection(
        text,
        UTC_LATE,
        current_branch="codex/qa-z-bootstrap",
    )
