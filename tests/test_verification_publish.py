"""Tests for verification publish summaries."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.reporters.verification_publish import (
    build_publish_summary,
    publish_summary_json,
    render_publish_summary,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_verify_summary(tmp_path: Path) -> Path:
    path = tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json"
    write_json(
        path,
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "repair_improved": True,
            "verdict": "improved",
            "blocking_before": 1,
            "blocking_after": 0,
            "resolved_count": 1,
            "remaining_issue_count": 0,
            "new_issue_count": 0,
            "regression_count": 0,
            "not_comparable_count": 0,
        },
    )
    return path


def test_publish_summary_from_verify_artifact(tmp_path: Path) -> None:
    summary_path = write_verify_summary(tmp_path)

    summary = build_publish_summary(root=tmp_path, from_verify=str(summary_path))
    payload = json.loads(publish_summary_json(summary))
    markdown = render_publish_summary(summary)

    assert summary.kind == "qa_z.verification_publish_summary"
    assert summary.source_type == "verify"
    assert summary.verdict == "improved"
    assert summary.resolved_count == 1
    assert payload["recommendation"] == "merge_candidate"
    assert "# QA-Z Verification Summary" in markdown
    assert "- Verdict: improved" in markdown
    assert "- Recommendation: merge_candidate" in markdown


def test_publish_summary_from_repair_session_summary(tmp_path: Path) -> None:
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    write_json(
        session_dir / "summary.json",
        {
            "kind": "qa_z.repair_session_summary",
            "schema_version": 1,
            "session_id": "session-one",
            "state": "verification_complete",
            "verdict": "mixed",
            "repair_improved": False,
            "resolved_count": 1,
            "remaining_issue_count": 1,
            "new_issue_count": 1,
            "regression_count": 1,
            "not_comparable_count": 0,
        },
    )

    summary = build_publish_summary(root=tmp_path, from_session="session-one")

    assert summary.source_type == "repair_session"
    assert summary.session_id == "session-one"
    assert summary.verdict == "mixed"
    assert summary.recommendation == "continue_repair"
