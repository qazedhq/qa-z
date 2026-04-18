"""Tests for SARIF reporting from normalized deep findings."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.reporters.sarif import build_sarif_log, sarif_json, sarif_level_for_severity
from qa_z.runners.models import CheckResult, RunSummary


def deep_summary_with_checks(checks: list[CheckResult]) -> RunSummary:
    """Build a minimal deep run summary for SARIF reporter tests."""
    return RunSummary(
        mode="deep",
        contract_path="qa/contracts/security.md",
        project_root=str(Path("/repo")),
        status="failed" if checks else "passed",
        started_at="2026-04-14T00:00:00Z",
        finished_at="2026-04-14T00:00:01Z",
        checks=checks,
        artifact_dir=".qa-z/runs/local/deep",
        schema_version=2,
    )


def semgrep_check(**overrides: object) -> CheckResult:
    """Build a Semgrep deep check result with representative findings."""
    defaults: dict[str, object] = {
        "id": "sg_scan",
        "tool": "semgrep",
        "command": ["semgrep", "--config", "auto", "--json"],
        "kind": "static-analysis",
        "status": "failed",
        "exit_code": 1,
        "duration_ms": 123,
        "findings_count": 2,
        "blocking_findings_count": 1,
        "filtered_findings_count": 0,
        "severity_summary": {"ERROR": 1, "WARNING": 1},
        "findings": [
            {
                "rule_id": "python.lang.security.audit.eval",
                "severity": "ERROR",
                "path": "src/app.py",
                "line": 42,
                "message": "Avoid use of eval",
            },
            {
                "rule_id": "typescript.sql.injection",
                "severity": "WARNING",
                "path": "src\\db.ts",
                "line": 12,
                "message": "Possible SQL injection",
            },
        ],
        "policy": {
            "config": "auto",
            "fail_on_severity": ["ERROR"],
            "ignore_rules": [],
            "exclude_paths": [],
        },
    }
    defaults.update(overrides)
    return CheckResult(**defaults)  # type: ignore[arg-type]


def test_sarif_reporter_maps_deep_findings_to_results() -> None:
    sarif = build_sarif_log(deep_summary_with_checks([semgrep_check()]))

    assert sarif["version"] == "2.1.0"
    assert sarif["$schema"] == "https://json.schemastore.org/sarif-2.1.0.json"
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "QA-Z"
    assert [rule["id"] for rule in run["tool"]["driver"]["rules"]] == [
        "python.lang.security.audit.eval",
        "typescript.sql.injection",
    ]

    first_result = run["results"][0]
    assert first_result["ruleId"] == "python.lang.security.audit.eval"
    assert first_result["level"] == "error"
    assert first_result["message"]["text"] == "Avoid use of eval"
    assert first_result["locations"] == [
        {
            "physicalLocation": {
                "artifactLocation": {"uri": "src/app.py"},
                "region": {"startLine": 42},
            }
        }
    ]
    assert first_result["properties"] == {
        "qa_z_check_id": "sg_scan",
        "qa_z_check_status": "failed",
        "severity": "ERROR",
    }

    second_result = run["results"][1]
    assert second_result["level"] == "warning"
    assert second_result["locations"][0]["physicalLocation"]["artifactLocation"] == {
        "uri": "src/db.ts"
    }


def test_sarif_json_is_deterministic_and_parseable() -> None:
    text = sarif_json(deep_summary_with_checks([semgrep_check()]))

    assert text.endswith("\n")
    parsed = json.loads(text)
    assert parsed["runs"][0]["results"][0]["ruleId"] == (
        "python.lang.security.audit.eval"
    )


def test_sarif_severity_mapping_is_conservative() -> None:
    assert sarif_level_for_severity("ERROR") == "error"
    assert sarif_level_for_severity("critical") == "error"
    assert sarif_level_for_severity("WARNING") == "warning"
    assert sarif_level_for_severity("medium") == "warning"
    assert sarif_level_for_severity("INFO") == "note"
    assert sarif_level_for_severity("low") == "note"
    assert sarif_level_for_severity("unknown") == "warning"


def test_sarif_empty_deep_summary_is_valid_with_no_results() -> None:
    sarif = build_sarif_log(deep_summary_with_checks([]))

    run = sarif["runs"][0]
    assert run["tool"]["driver"]["rules"] == []
    assert run["results"] == []
    assert run["properties"]["qa_z_status"] == "passed"


def test_sarif_uses_grouped_findings_when_active_findings_are_absent() -> None:
    check = semgrep_check(
        findings=[],
        grouped_findings=[
            {
                "rule_id": "python.lang.security.audit.eval",
                "severity": "ERROR",
                "path": "src/app.py",
                "count": 3,
                "representative_line": 21,
                "message": "Avoid use of eval",
            }
        ],
    )

    result = build_sarif_log(deep_summary_with_checks([check]))["runs"][0]["results"][0]

    assert result["ruleId"] == "python.lang.security.audit.eval"
    assert result["message"]["text"] == "Avoid use of eval (3 occurrences)"
    assert result["locations"][0]["physicalLocation"]["region"] == {"startLine": 21}
    assert result["properties"]["qa_z_grouped_count"] == 3


def test_sarif_omits_region_when_line_is_unavailable() -> None:
    check = semgrep_check(
        findings=[
            {
                "rule_id": "generic.project.issue",
                "severity": "WARNING",
                "path": "src/settings.py",
                "line": None,
                "message": "Project-level warning",
            }
        ]
    )

    result = build_sarif_log(deep_summary_with_checks([check]))["runs"][0]["results"][0]

    assert result["locations"] == [
        {"physicalLocation": {"artifactLocation": {"uri": "src/settings.py"}}}
    ]
