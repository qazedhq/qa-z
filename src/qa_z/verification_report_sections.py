"""Shared section builders for verification reports."""

from __future__ import annotations

from qa_z.verification_models import VerificationComparison


def render_overview_lines(comparison: VerificationComparison) -> list[str]:
    return [
        "# QA-Z Repair Verification",
        "",
        f"- Final verdict: `{comparison.verdict}`",
        f"- Baseline run: `{comparison.baseline.run_dir}`",
        f"- Candidate run: `{comparison.candidate.run_dir}`",
        f"- Blocking before: {comparison.summary['blocking_before']}",
        f"- Blocking after: {comparison.summary['blocking_after']}",
        f"- Resolved: {comparison.summary['resolved_count']}",
        f"- New or regressed issues: {comparison.summary['new_issue_count']}",
        "",
    ]


def render_reproduction_lines() -> list[str]:
    return [
        "## Reproduction",
        "",
        "Run the same fast and deep commands that produced the baseline and candidate summaries, then rerun `qa-z verify` with the same run ids.",
    ]
