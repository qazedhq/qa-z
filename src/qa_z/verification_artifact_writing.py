"""Writing helpers for verification artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.verification_models import VerificationArtifactPaths, VerificationComparison
from qa_z.verification_outcome import verification_summary_dict
from qa_z.verification_report import render_verification_report_impl


def write_verification_artifacts(
    comparison: VerificationComparison, output_dir: Path
) -> VerificationArtifactPaths:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    compare_path = output_dir / "compare.json"
    report_path = output_dir / "report.md"
    summary_path.write_text(
        json.dumps(verification_summary_dict(comparison), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    compare_path.write_text(
        json.dumps(comparison.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(
        render_verification_report_impl(comparison), encoding="utf-8"
    )
    return VerificationArtifactPaths(
        summary_path=summary_path,
        compare_path=compare_path,
        report_path=report_path,
    )
