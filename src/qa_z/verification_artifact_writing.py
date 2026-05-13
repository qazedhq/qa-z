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
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OSError(
            f"could not create verification artifact directory {output_dir}: {exc}"
        ) from exc
    summary_path = output_dir / "summary.json"
    compare_path = output_dir / "compare.json"
    report_path = output_dir / "report.md"
    write_verification_artifact_text(
        summary_path,
        json.dumps(verification_summary_dict(comparison), indent=2, sort_keys=True)
        + "\n",
    )
    write_verification_artifact_text(
        compare_path,
        json.dumps(comparison.to_dict(), indent=2, sort_keys=True) + "\n",
    )
    write_verification_artifact_text(
        report_path,
        render_verification_report_impl(comparison),
    )
    return VerificationArtifactPaths(
        summary_path=summary_path,
        compare_path=compare_path,
        report_path=report_path,
    )


def write_verification_artifact_text(path: Path, text: str) -> None:
    """Write one verification artifact with path-aware errors."""
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise OSError(f"could not write verification artifact {path}: {exc}") from exc
