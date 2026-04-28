"""Human-readable verification report builder."""

from __future__ import annotations

from qa_z.verification_compare import compare_deep_findings  # noqa: F401
from qa_z.verification_models import VerificationComparison
from qa_z.verification_render import render_fast_category, render_finding_category
from qa_z.verification_report_sections import (
    render_overview_lines,
    render_reproduction_lines,
)


def render_verification_report_impl(comparison: VerificationComparison) -> str:
    """Render a human-readable verification report."""
    lines = [*render_overview_lines(comparison), "## Fast Checks", ""]
    lines.extend(render_fast_category("Resolved", comparison.fast_checks["resolved"]))
    lines.extend(
        render_fast_category("Still failing", comparison.fast_checks["still_failing"])
    )
    lines.extend(render_fast_category("Regressed", comparison.fast_checks["regressed"]))
    lines.extend(
        render_fast_category(
            "Newly introduced", comparison.fast_checks["newly_introduced"]
        )
    )
    lines.extend(
        render_fast_category(
            "Skipped or not comparable",
            comparison.fast_checks["skipped_or_not_comparable"],
        )
    )
    lines.extend(["## Deep Findings", ""])
    lines.extend(
        render_finding_category("Resolved", comparison.deep_findings["resolved"])
    )
    lines.extend(
        render_finding_category(
            "Still failing", comparison.deep_findings["still_failing"]
        )
    )
    lines.extend(
        render_finding_category("Regressed", comparison.deep_findings["regressed"])
    )
    lines.extend(
        render_finding_category(
            "Newly introduced", comparison.deep_findings["newly_introduced"]
        )
    )
    lines.extend(
        render_finding_category(
            "Skipped or not comparable",
            comparison.deep_findings["skipped_or_not_comparable"],
        )
    )
    lines.extend(render_reproduction_lines())
    return "\n".join(lines).strip() + "\n"
