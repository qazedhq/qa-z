from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import qa_z.verification_artifact_loading as loading_module
import qa_z.verification_artifact_writing as writing_module
from qa_z.verification_models import VerificationComparison


def test_load_verification_run_requires_fast_summary(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        loading_module,
        "resolve_run_source",
        lambda root, config, from_run: SimpleNamespace(
            summary_path=tmp_path / "summary.json",
            run_dir=tmp_path / "candidate",
        ),
    )
    monkeypatch.setattr(
        loading_module,
        "load_run_summary",
        lambda path: SimpleNamespace(mode="deep"),
    )

    with pytest.raises(ValueError, match="Expected a fast summary"):
        loading_module.load_verification_run(
            root=tmp_path, config={"checks": []}, from_run=".qa-z/runs/candidate"
        )


def test_write_verification_artifacts_writes_summary_compare_and_report(
    monkeypatch, tmp_path: Path
) -> None:
    comparison = cast(
        VerificationComparison,
        SimpleNamespace(
            to_dict=lambda: {"kind": "qa_z.verify_compare"},
            verdict="improved",
            summary={
                "blocking_before": 1,
                "blocking_after": 0,
                "resolved_count": 1,
                "new_issue_count": 0,
            },
        ),
    )
    monkeypatch.setattr(
        writing_module,
        "verification_summary_dict",
        lambda comparison: {"kind": "qa_z.verify_summary", "verdict": "improved"},
    )
    monkeypatch.setattr(
        writing_module,
        "render_verification_report_impl",
        lambda comparison: "# QA-Z Repair Verification\n",
    )

    paths = writing_module.write_verification_artifacts(comparison, tmp_path / "verify")

    assert paths.summary_path == tmp_path / "verify" / "summary.json"
    assert paths.compare_path == tmp_path / "verify" / "compare.json"
    assert paths.report_path == tmp_path / "verify" / "report.md"
    assert paths.summary_path.read_text(encoding="utf-8").startswith("{\n")
    assert paths.compare_path.read_text(encoding="utf-8").startswith("{\n")
    assert (
        paths.report_path.read_text(encoding="utf-8") == "# QA-Z Repair Verification\n"
    )
