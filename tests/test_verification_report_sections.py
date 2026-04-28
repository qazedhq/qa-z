from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import qa_z.verification_report_sections as report_sections_module
from qa_z.verification_models import VerificationComparison


def test_render_overview_lines_summarizes_verdict_and_blocking_counts() -> None:
    comparison = cast(
        VerificationComparison,
        SimpleNamespace(
            verdict="improved",
            baseline=SimpleNamespace(run_dir=".qa-z/runs/baseline"),
            candidate=SimpleNamespace(run_dir=".qa-z/runs/candidate"),
            summary={
                "blocking_before": 2,
                "blocking_after": 0,
                "resolved_count": 2,
                "new_issue_count": 0,
            },
        ),
    )

    lines = report_sections_module.render_overview_lines(comparison)

    assert lines == [
        "# QA-Z Repair Verification",
        "",
        "- Final verdict: `improved`",
        "- Baseline run: `.qa-z/runs/baseline`",
        "- Candidate run: `.qa-z/runs/candidate`",
        "- Blocking before: 2",
        "- Blocking after: 0",
        "- Resolved: 2",
        "- New or regressed issues: 0",
        "",
    ]


def test_render_reproduction_lines_keep_manual_repro_steps() -> None:
    assert report_sections_module.render_reproduction_lines() == [
        "## Reproduction",
        "",
        "Run the same fast and deep commands that produced the baseline and candidate summaries, then rerun `qa-z verify` with the same run ids.",
    ]
