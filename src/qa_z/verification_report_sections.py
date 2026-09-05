"""Shared section builders for verification reports."""

from __future__ import annotations

from qa_z.verification_models import VerificationComparison
from qa_z.verification_outcome_summary import recommendation_for_verdict


def render_overview_lines(comparison: VerificationComparison) -> list[str]:
    return [
        "# QA-Z Repair Verification",
        "",
        f"- Final verdict: `{comparison.verdict}`",
        f"- Baseline run: `{comparison.baseline.run_dir}`",
        f"- Candidate run: `{comparison.candidate.run_dir}`",
        f"- Recommendation: `{recommendation_for_verdict(comparison.verdict)}`",
        f"- Blocking before: {comparison.summary['blocking_before']}",
        f"- Blocking after: {comparison.summary['blocking_after']}",
        f"- Resolved: {comparison.summary['resolved_count']}",
        f"- New or regressed issues: {comparison.summary['new_issue_count']}",
        "",
    ]


def render_review_summary_lines(comparison: VerificationComparison) -> list[str]:
    recommendation = recommendation_for_verdict(comparison.verdict)
    summary = comparison.summary
    new_or_regressed = summary["new_issue_count"] + summary["regression_count"]
    return [
        "## Review Summary",
        "",
        "```text",
        f"qa-z verify: {comparison.verdict}",
        f"recommendation: {recommendation}",
        f"blocking: {summary['blocking_before']} -> {summary['blocking_after']}",
        f"resolved: {summary['resolved_count']}",
        f"new_or_regressed: {new_or_regressed}",
        "```",
        "",
    ]


def render_reproduction_lines() -> list[str]:
    return [
        "## Reproduction",
        "",
        "Run the same fast and deep commands that produced the baseline and candidate summaries, then rerun `qa-z verify` with the same run ids.",
    ]
