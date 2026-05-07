"""Review-packet coverage for deep scan-quality warnings."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.cli import main
from tests.repair_prompt_test_support import (
    write_config,
    write_contract,
    write_deep_summary,
    write_summary,
)


def test_review_packet_surfaces_deep_scan_warnings_without_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Auth token refresh flow")
    write_summary(tmp_path, "2026-04-11T17-38-52Z", status="passed", checks=[])
    payload = write_deep_summary(tmp_path, "2026-04-11T17-38-52Z")
    payload["status"] = "passed"
    payload["diagnostics"] = {
        "scan_quality": {
            "status": "warning",
            "warning_count": 2,
            "warning_types": ["Fixpoint timeout"],
            "warning_paths": ["src/app.py", "src/db.py"],
            "check_ids": ["sg_scan"],
        }
    }
    payload["checks"][0].update(
        {
            "status": "passed",
            "findings_count": 0,
            "blocking_findings_count": 0,
            "filtered_findings_count": 0,
            "severity_summary": {},
            "findings": [],
            "scan_warning_count": 2,
            "scan_warnings": [
                {
                    "error_type": "Fixpoint timeout",
                    "path": "src/app.py",
                    "severity": "WARN",
                }
            ],
        }
    )
    deep_summary_path = (
        tmp_path / ".qa-z" / "runs" / "2026-04-11T17-38-52Z" / "deep" / "summary.json"
    )
    deep_summary_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = main(["review", "--path", str(tmp_path), "--from-run", "latest"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "- Scan quality: warning (2 warnings)" in output
    assert "- Scan warning types: Fixpoint timeout" in output
    assert "- Scan warning paths: `src/app.py`, `src/db.py`" in output
    assert "- Scan warning checks: sg_scan" in output
    assert "No Semgrep findings were reported." in output
