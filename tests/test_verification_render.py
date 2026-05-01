"""Behavior tests for verification render helpers."""

from __future__ import annotations

from qa_z.verification_models import FastCheckDelta, VerificationFindingDelta
from qa_z.verification_render import render_fast_category, render_finding_category


def test_render_fast_category_lists_delta_transitions() -> None:
    lines = render_fast_category(
        "Resolved",
        [
            FastCheckDelta(
                id="py_test",
                classification="resolved",
                baseline_status="failed",
                candidate_status="passed",
                baseline_exit_code=1,
                candidate_exit_code=0,
                kind="test",
                message="resolved",
            )
        ],
    )

    assert lines == ["### Resolved", "", "- `py_test`: failed -> passed", ""]


def test_render_finding_category_uses_unknown_location_for_missing_path() -> None:
    lines = render_finding_category(
        "Regressed",
        [
            VerificationFindingDelta(
                id="check:rule:unknown:0",
                classification="regressed",
                source="check",
                rule_id="rule.id",
                path="",
                line=None,
                match="strict",
                baseline_severity="ERROR",
                candidate_severity="ERROR",
                baseline_blocking=True,
                candidate_blocking=True,
                message="after",
            )
        ],
    )

    assert lines == [
        "### Regressed",
        "",
        "- `rule.id` in `unknown` (ERROR -> ERROR, match: strict)",
        "",
    ]


def test_render_finding_category_explains_not_comparable_findings() -> None:
    lines = render_finding_category(
        "Skipped or not comparable",
        [
            VerificationFindingDelta(
                id="deep:summary",
                classification="skipped_or_not_comparable",
                source="deep",
                rule_id="summary",
                path="",
                line=None,
                match="none",
                message="Deep comparison requires both run summaries.",
            )
        ],
    )

    assert lines == [
        "### Skipped or not comparable",
        "",
        (
            "- `summary` in `unknown` (missing -> missing, match: none): "
            "Deep comparison requires both run summaries."
        ),
        "",
    ]
