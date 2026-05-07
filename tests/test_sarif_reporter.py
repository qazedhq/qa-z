"""Tests for SARIF reporting from normalized deep findings."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.reporters.sarif import build_sarif_log, sarif_json, sarif_level_for_severity
from qa_z.runners.models import CheckResult, RunSummary


def deep_summary_with_checks(
    checks: list[CheckResult],
    *,
    project_root: str | None = None,
    artifact_dir: str | None = None,
    contract_path: str = "qa/contracts/security.md",
) -> RunSummary:
    """Build a minimal deep run summary for SARIF reporter tests."""
    return RunSummary(
        mode="deep",
        contract_path=contract_path,
        project_root=project_root or str(Path("/repo")),
        status="failed" if checks else "passed",
        started_at="2026-04-14T00:00:00Z",
        finished_at="2026-04-14T00:00:01Z",
        checks=checks,
        artifact_dir=artifact_dir or ".qa-z/runs/local/deep",
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


def test_sarif_redacts_secret_like_finding_messages() -> None:
    check = semgrep_check(
        findings=[
            {
                "rule_id": "generic.secret",
                "severity": "ERROR",
                "path": "src/settings.py",
                "line": 7,
                "message": "Authorization: Bearer abc.def.ghi",
            }
        ]
    )

    sarif = build_sarif_log(deep_summary_with_checks([check]))
    text = json.dumps(sarif)
    result = sarif["runs"][0]["results"][0]

    assert "abc.def.ghi" not in text
    assert result["message"]["text"] == "Authorization: [REDACTED_TOKEN]"


def test_sarif_redacts_url_userinfo_credentials() -> None:
    check = semgrep_check(
        findings=[
            {
                "rule_id": "generic.secret_url",
                "severity": "ERROR",
                "path": "src/settings.py",
                "line": 7,
                "message": "remote https://git-user:url-token@example.test/repo.git",
            }
        ]
    )

    sarif = build_sarif_log(deep_summary_with_checks([check]))
    text = json.dumps(sarif)
    result = sarif["runs"][0]["results"][0]

    assert "git-user" not in text
    assert "url-token" not in text
    assert (
        result["message"]["text"]
        == "remote https://[REDACTED_SECRET]@example.test/repo.git"
    )


def test_sarif_redacts_prefixed_env_secret_names() -> None:
    check = semgrep_check(
        findings=[
            {
                "rule_id": "generic.secret",
                "severity": "ERROR",
                "path": "src/settings.py",
                "line": 7,
                "message": "OPENAI_API_KEY=openai-raw",
            }
        ]
    )

    sarif = build_sarif_log(deep_summary_with_checks([check]))
    text = json.dumps(sarif)
    result = sarif["runs"][0]["results"][0]

    assert "openai-raw" not in text
    assert result["message"]["text"] == "OPENAI_API_KEY=[REDACTED_SECRET]"


def test_sarif_relativizes_absolute_project_paths(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"
    check = semgrep_check(
        findings=[
            {
                "rule_id": "generic.absolute",
                "severity": "ERROR",
                "path": str(project_root / "src" / "app.py"),
                "line": 9,
                "message": "Absolute path should not leak",
            }
        ]
    )

    sarif = build_sarif_log(
        deep_summary_with_checks(
            [check],
            project_root=str(project_root),
            artifact_dir=str(project_root / ".qa-z" / "runs" / "local" / "deep"),
        )
    )
    rendered = json.dumps(sarif)

    assert str(project_root) not in rendered
    assert sarif["runs"][0]["results"][0]["locations"] == [
        {
            "physicalLocation": {
                "artifactLocation": {"uri": "src/app.py"},
                "region": {"startLine": 9},
            }
        }
    ]
    assert sarif["runs"][0]["properties"]["qa_z_artifact_dir"] == (
        ".qa-z/runs/local/deep"
    )


def test_sarif_omits_out_of_project_absolute_paths(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"
    outside_root = tmp_path / "outside"
    check = semgrep_check(
        findings=[
            {
                "rule_id": "generic.outside",
                "severity": "ERROR",
                "path": str(outside_root / "src" / "app.py"),
                "line": 9,
                "message": "Outside path should not leak",
            }
        ]
    )

    sarif = build_sarif_log(
        deep_summary_with_checks(
            [check],
            project_root=str(project_root),
            artifact_dir=str(outside_root / ".qa-z" / "runs" / "local" / "deep"),
        )
    )
    rendered = json.dumps(sarif)
    result = sarif["runs"][0]["results"][0]
    run_properties = sarif["runs"][0]["properties"]

    assert str(outside_root) not in rendered
    assert "locations" not in result
    assert result["properties"]["qa_z_path_outside_project"] is True
    assert "qa_z_artifact_dir" not in run_properties
    assert run_properties["qa_z_artifact_dir_outside_project"] is True


def test_sarif_omits_parent_traversal_relative_paths(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"
    check = semgrep_check(
        findings=[
            {
                "rule_id": "generic.relative_escape",
                "severity": "ERROR",
                "path": "../outside/secrets.py",
                "line": 9,
                "message": "Relative traversal should not leak",
            }
        ]
    )

    sarif = build_sarif_log(
        deep_summary_with_checks(
            [check],
            project_root=str(project_root),
            artifact_dir="../outside/.qa-z/runs/local/deep",
        )
    )
    rendered = json.dumps(sarif)
    result = sarif["runs"][0]["results"][0]
    run_properties = sarif["runs"][0]["properties"]

    assert "../outside" not in rendered
    assert "locations" not in result
    assert result["properties"]["qa_z_path_outside_project"] is True
    assert "qa_z_artifact_dir" not in run_properties
    assert run_properties["qa_z_artifact_dir_outside_project"] is True


def test_sarif_omits_out_of_project_contract_paths(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"

    sarif = build_sarif_log(
        deep_summary_with_checks(
            [],
            project_root=str(project_root),
            contract_path="../outside/security.md",
        )
    )
    rendered = json.dumps(sarif)
    run_properties = sarif["runs"][0]["properties"]

    assert "../outside" not in rendered
    assert "qa_z_contract_path" not in run_properties
    assert run_properties["qa_z_contract_path_outside_project"] is True


def test_sarif_omits_windows_drive_relative_paths(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"
    check = semgrep_check(
        findings=[
            {
                "rule_id": "generic.windows_drive",
                "severity": "ERROR",
                "path": "C:Users\\operator\\secrets.py",
                "line": 9,
                "message": "Drive-qualified path should not leak",
            }
        ]
    )

    sarif = build_sarif_log(
        deep_summary_with_checks([check], project_root=str(project_root))
    )
    rendered = json.dumps(sarif)
    result = sarif["runs"][0]["results"][0]

    assert "C:Users" not in rendered
    assert "locations" not in result
    assert result["properties"]["qa_z_path_outside_project"] is True


def test_semgrep_finding_redacts_secret_like_metadata_keys() -> None:
    from qa_z.runners.models import SemgrepFinding

    finding = SemgrepFinding(
        rule_id="generic.secret",
        severity="ERROR",
        path="src/settings.py",
        line=7,
        message="Project metadata warning",
        metadata={
            "GITHUB_TOKEN": "github-raw",
            "nested": {"CLIENT_SECRET": "client-raw"},
            "token_count": 3,
        },
    )

    payload = finding.to_dict()

    assert "github-raw" not in str(payload)
    assert "client-raw" not in str(payload)
    assert payload["metadata"]["GITHUB_TOKEN"] == "[REDACTED_TOKEN]"
    assert payload["metadata"]["nested"]["CLIENT_SECRET"] == "[REDACTED_SECRET]"
    assert payload["metadata"]["token_count"] == 3
