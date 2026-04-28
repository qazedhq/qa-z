"""Contract tests for shared runner models."""

from __future__ import annotations

import pytest

from qa_z.runners.models import CheckResult
from qa_z.runners.models import CheckSpec
from qa_z.runners.models import RunSummary


def test_check_spec_tool_uses_executable_name_from_command_path() -> None:
    spec = CheckSpec(
        id="pytest",
        command=["C:/Python312/python.exe", "-m", "pytest"],
        kind="python",
    )

    assert spec.tool == "python.exe"
    assert spec.to_dict()["tool"] == "python.exe"


def test_check_result_from_dict_requires_command_list() -> None:
    with pytest.raises(ValueError, match="command must be a list"):
        CheckResult.from_dict(
            {
                "id": "pytest",
                "tool": "pytest",
                "command": "python -m pytest",
                "kind": "python",
                "status": "failed",
                "duration_ms": 10,
            }
        )


def test_run_summary_from_dict_round_trips_selection_and_diagnostics() -> None:
    summary = RunSummary.from_dict(
        {
            "mode": "fast",
            "contract_path": ".qa-z/contracts/example.md",
            "project_root": ".",
            "status": "passed",
            "started_at": "2026-04-23T00:00:00Z",
            "finished_at": "2026-04-23T00:00:05Z",
            "checks": [],
            "schema_version": 2,
            "selection": {
                "mode": "smart",
                "input_source": "cli_diff",
                "changed_files": [
                    {
                        "path": "src/app.py",
                        "old_path": None,
                        "status": "modified",
                        "additions": 3,
                        "deletions": 1,
                        "language": "python",
                        "kind": "source",
                    }
                ],
                "high_risk_reasons": ["python_source_changed"],
                "selected_checks": ["pytest"],
                "full_checks": [],
                "targeted_checks": ["pytest"],
                "skipped_checks": [],
            },
            "diagnostics": {"scan_quality": {"status": "warning"}},
            "policy": {"selection_mode": "smart"},
        }
    )

    rendered = summary.to_dict()

    assert summary.selection is not None
    assert summary.selection.changed_files[0].path == "src/app.py"
    assert rendered["selection"]["changed_files"][0]["path"] == "src/app.py"
    assert rendered["diagnostics"] == {"scan_quality": {"status": "warning"}}
    assert rendered["policy"] == {"selection_mode": "smart"}
