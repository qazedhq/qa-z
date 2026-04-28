"""Tests for Semgrep normalization in deep runs."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from qa_z.cli import main
from qa_z.runners.models import CheckResult, SemgrepCheckPolicy
from qa_z.runners.subprocess import TAIL_LIMIT, tail_text
from qa_z.runners.semgrep import (
    default_semgrep_spec_for_name,
    normalize_semgrep_result,
    semgrep_command_with_config,
)


def write_deep_config(
    root: Path,
    *,
    run: list[str] | None = None,
    semgrep: dict[str, Any] | None = None,
    exclude_paths: list[str] | None = None,
) -> None:
    """Write a minimal config that enables the Semgrep deep check."""
    config: dict[str, Any] = {
        "project": {"name": "qa-z-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {"output_dir": ".qa-z/runs"},
        "deep": {
            "selection": {"exclude_paths": exclude_paths or []},
            "checks": [
                {
                    "id": "sg_scan",
                    "enabled": True,
                    "run": run or ["semgrep", "--config", "auto", "--json"],
                    "kind": "static-analysis",
                    "semgrep": semgrep or {"config": "auto"},
                }
            ],
        },
    }
    (root / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def real_semgrep_scan_is_usable(
    rules_path: Path, target_path: Path
) -> tuple[bool, str]:
    executable = shutil.which("semgrep")
    if executable is None:
        return False, "semgrep not installed"

    completed = subprocess.run(
        [executable, "--json", "--config", str(rules_path), str(target_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode in {0, 1}:
        try:
            payload = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            return True, ""

    detail = tail_text(completed.stderr or completed.stdout)
    return False, detail or f"exit {completed.returncode}"


def semgrep_raw_result(stdout: str, *, exit_code: int = 0) -> CheckResult:
    """Build a raw subprocess-style Semgrep result."""
    return CheckResult(
        id="sg_scan",
        tool="semgrep",
        command=["semgrep", "--config", "auto", "--json"],
        kind="static-analysis",
        status="passed" if exit_code == 0 else "failed",
        exit_code=exit_code,
        duration_ms=12,
        stdout_tail=stdout,
    )


def test_semgrep_normalization_uses_full_stdout_when_tail_is_truncated() -> None:
    findings = [
        {
            "check_id": "python.lang.security.audit.eval",
            "path": f"src/generated_{index}.py",
            "start": {"line": index + 1},
            "extra": {"severity": "ERROR", "message": "Avoid use of eval"},
        }
        for index in range(120)
    ]
    payload = json.dumps({"results": findings})
    assert len(payload) > TAIL_LIMIT

    result = CheckResult(
        id="sg_scan",
        tool="semgrep",
        command=["semgrep", "--config", "auto", "--json"],
        kind="static-analysis",
        status="failed",
        exit_code=1,
        duration_ms=12,
        stdout=payload,
        stdout_tail=tail_text(payload),
    )

    normalized = normalize_semgrep_result(result)

    assert result.stdout_tail != payload
    assert normalized.status == "failed"
    assert normalized.findings_count == len(findings)
    assert normalized.blocking_findings_count == len(findings)


def test_semgrep_zero_findings_results_in_passed_status() -> None:
    result = normalize_semgrep_result(semgrep_raw_result('{"results": []}'))

    assert result.status == "passed"
    assert result.findings_count == 0
    assert result.blocking_findings_count == 0
    assert result.filtered_findings_count == 0
    assert result.severity_summary == {}
    assert result.grouped_findings == []
    assert result.findings == []
    assert result.message == "Semgrep reported 0 findings; 0 blocking."


def test_semgrep_scan_warnings_are_preserved_without_blocking() -> None:
    payload = {
        "results": [],
        "errors": [
            {
                "error_type": "Fixpoint timeout",
                "severity": "warn",
                "message": "Fixpoint timeout while performing taint analysis",
                "location": {
                    "path": "src/app.py",
                    "start": {"line": 5, "col": 4},
                },
            }
        ],
    }

    result = normalize_semgrep_result(semgrep_raw_result(json.dumps(payload)))

    assert result.status == "passed"
    assert result.findings_count == 0
    assert result.blocking_findings_count == 0
    assert result.scan_warning_count == 1
    assert result.scan_warnings == [
        {
            "error_type": "Fixpoint timeout",
            "severity": "WARN",
            "message": "Fixpoint timeout while performing taint analysis",
            "path": "src/app.py",
            "line": 5,
        }
    ]
    assert result.message == (
        "Semgrep reported 0 findings; 0 blocking. 1 scan warning."
    )


def test_semgrep_nested_timing_warnings_are_preserved_without_blocking() -> None:
    payload = {
        "results": [],
        "errors": [],
        "time": {
            "fixpoint_timeouts": [
                {
                    "error_type": "Fixpoint timeout",
                    "severity": "warn",
                    "message": "Fixpoint timeout while performing taint analysis",
                    "location": {
                        "path": "src/app.py",
                        "start": {"line": 5, "col": 4},
                    },
                }
            ]
        },
    }

    result = normalize_semgrep_result(semgrep_raw_result(json.dumps(payload)))

    assert result.status == "passed"
    assert result.scan_warning_count == 1
    assert result.scan_warnings[0]["error_type"] == "Fixpoint timeout"
    assert result.scan_warnings[0]["path"] == "src/app.py"


def test_semgrep_wrapper_commands_are_not_rewritten_with_semgrep_flags() -> None:
    command = semgrep_command_with_config(
        ["python", ".qa-z-benchmark/fake_semgrep.py"],
        "auto",
    )

    assert command == ["python", ".qa-z-benchmark/fake_semgrep.py"]


def test_semgrep_findings_are_normalized_into_check_result() -> None:
    payload = {
        "results": [
            {
                "check_id": "python.lang.security.audit.eval",
                "path": "src/app.py",
                "start": {"line": 42},
                "extra": {
                    "severity": "ERROR",
                    "message": "Avoid use of eval",
                },
            }
        ]
    }

    result = normalize_semgrep_result(semgrep_raw_result(json.dumps(payload)))

    assert result.status == "failed"
    assert result.findings_count == 1
    assert result.blocking_findings_count == 1
    assert result.filtered_findings_count == 0
    assert result.severity_summary == {"ERROR": 1}
    assert result.grouped_findings == [
        {
            "rule_id": "python.lang.security.audit.eval",
            "severity": "ERROR",
            "path": "src/app.py",
            "count": 1,
            "representative_line": 42,
            "message": "Avoid use of eval",
        }
    ]
    assert result.findings == [
        {
            "rule_id": "python.lang.security.audit.eval",
            "severity": "ERROR",
            "path": "src/app.py",
            "line": 42,
            "message": "Avoid use of eval",
        }
    ]
    assert result.message == "Semgrep reported 1 finding; 1 blocking."


def test_semgrep_warning_findings_do_not_fail_error_only_threshold() -> None:
    payload = {
        "results": [
            {
                "check_id": "generic.secrets.security.detected-token",
                "path": "src/settings.py",
                "start": {"line": 7},
                "extra": {
                    "severity": "WARNING",
                    "message": "Possible hardcoded token",
                },
            }
        ]
    }

    result = normalize_semgrep_result(
        semgrep_raw_result(json.dumps(payload)),
        SemgrepCheckPolicy(fail_on_severity=["ERROR"]),
    )

    assert result.status == "passed"
    assert result.findings_count == 1
    assert result.blocking_findings_count == 0
    assert result.severity_summary == {"WARNING": 1}
    assert result.message == "Semgrep reported 1 finding; 0 blocking."


def test_semgrep_groups_duplicate_findings_by_rule_path_severity() -> None:
    payload = {
        "results": [
            {
                "check_id": "python.lang.security.audit.eval",
                "path": "src/app.py",
                "start": {"line": 42},
                "extra": {"severity": "ERROR", "message": "Avoid use of eval"},
            },
            {
                "check_id": "python.lang.security.audit.eval",
                "path": "src/app.py",
                "start": {"line": 44},
                "extra": {"severity": "ERROR", "message": "Avoid use of eval"},
            },
            {
                "check_id": "python.lang.security.audit.eval",
                "path": "src/other.py",
                "start": {"line": 5},
                "extra": {"severity": "ERROR", "message": "Avoid use of eval"},
            },
        ]
    }

    result = normalize_semgrep_result(semgrep_raw_result(json.dumps(payload)))

    assert result.grouped_findings == [
        {
            "rule_id": "python.lang.security.audit.eval",
            "severity": "ERROR",
            "path": "src/app.py",
            "count": 2,
            "representative_line": 42,
            "message": "Avoid use of eval",
        },
        {
            "rule_id": "python.lang.security.audit.eval",
            "severity": "ERROR",
            "path": "src/other.py",
            "count": 1,
            "representative_line": 5,
            "message": "Avoid use of eval",
        },
    ]


def test_semgrep_filters_excluded_paths_and_ignored_rules() -> None:
    payload = {
        "results": [
            {
                "check_id": "generic.generated.issue",
                "path": "dist/app.generated.py",
                "start": {"line": 1},
                "extra": {"severity": "ERROR", "message": "Generated file"},
            },
            {
                "check_id": "generic.secrets.security.detected-private-key",
                "path": "src/settings.py",
                "start": {"line": 8},
                "extra": {"severity": "ERROR", "message": "Private key"},
            },
            {
                "check_id": "python.lang.security.audit.eval",
                "path": "src/app.py",
                "start": {"line": 42},
                "extra": {"severity": "WARNING", "message": "Avoid use of eval"},
            },
        ]
    }

    result = normalize_semgrep_result(
        semgrep_raw_result(json.dumps(payload)),
        SemgrepCheckPolicy(
            fail_on_severity=["ERROR"],
            ignore_rules=["generic.secrets.security.detected-private-key"],
            exclude_paths=["dist/**", "**/*.generated.*"],
        ),
    )

    assert result.status == "passed"
    assert result.findings_count == 3
    assert result.filtered_findings_count == 2
    assert result.filter_reasons == {"excluded_path": 1, "ignored_rule": 1}
    assert result.blocking_findings_count == 0
    assert [finding["path"] for finding in result.findings] == ["src/app.py"]
    assert result.grouped_findings[0]["count"] == 1


def test_deep_writes_findings_artifact_when_semgrep_reports_issues(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(tmp_path)
    payload = {
        "results": [
            {
                "check_id": "generic.secrets.security.detected-token",
                "path": "src/settings.py",
                "start": {"line": 7},
                "extra": {
                    "severity": "ERROR",
                    "message": "Possible hardcoded token",
                },
            }
        ]
    }

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fake_run)

    exit_code = main(["deep", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)
    check_path = tmp_path / output["artifact_dir"] / "checks" / "sg_scan.json"
    check_artifact = json.loads(check_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert output["status"] == "failed"
    assert output["checks"][0]["id"] == "sg_scan"
    assert output["checks"][0]["findings_count"] == 1
    assert output["checks"][0]["blocking_findings_count"] == 1
    assert check_artifact["grouped_findings"][0]["count"] == 1
    assert check_artifact["findings"][0]["path"] == "src/settings.py"


def test_deep_warning_findings_are_non_blocking_by_default(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(tmp_path)
    payload = {
        "results": [
            {
                "check_id": "generic.secrets.security.detected-token",
                "path": "src/settings.py",
                "start": {"line": 7},
                "extra": {
                    "severity": "WARNING",
                    "message": "Possible hardcoded token",
                },
            }
        ]
    }

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fake_run)

    exit_code = main(["deep", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "passed"
    assert output["checks"][0]["findings_count"] == 1
    assert output["checks"][0]["blocking_findings_count"] == 0


def test_deep_writes_scan_warning_diagnostics(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(tmp_path)
    payload = {
        "results": [],
        "errors": [
            {
                "error_type": "Fixpoint timeout",
                "severity": "warn",
                "message": "Fixpoint timeout while performing taint analysis",
                "location": {
                    "path": "src/app.py",
                    "start": {"line": 5, "col": 4},
                },
            }
        ],
    }

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fake_run)

    exit_code = main(["deep", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)
    artifact_dir = tmp_path / output["artifact_dir"]
    check_artifact = json.loads(
        (artifact_dir / "checks" / "sg_scan.json").read_text(encoding="utf-8")
    )
    summary_md = (artifact_dir / "summary.md").read_text(encoding="utf-8")

    assert exit_code == 0
    assert output["status"] == "passed"
    assert output["checks"][0]["scan_warning_count"] == 1
    assert output["checks"][0]["scan_warnings"][0]["path"] == "src/app.py"
    assert output["diagnostics"]["scan_quality"] == {
        "status": "warning",
        "warning_count": 1,
        "warning_types": ["Fixpoint timeout"],
        "warning_paths": ["src/app.py"],
        "check_ids": ["sg_scan"],
    }
    summary_json = json.loads((artifact_dir / "summary.json").read_text("utf-8"))
    assert summary_json["diagnostics"]["scan_quality"]["warning_count"] == 1
    assert check_artifact["scan_warning_count"] == 1
    assert "scan warning" in summary_md
    assert summary_md.count("1 scan warning.") == 1
    assert "## Diagnostics" in summary_md
    assert "- Scan quality: warning (1 warning)" in summary_md
    assert "- Warning types: Fixpoint timeout" in summary_md
    assert "- Warning paths: src/app.py" in summary_md
    assert "- Warning checks: sg_scan" in summary_md


def test_deep_uses_custom_semgrep_config_when_provided(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(
        tmp_path,
        run=["semgrep", "--json"],
        semgrep={"config": "p/security-audit", "fail_on_severity": ["ERROR"]},
    )
    commands: list[list[str]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        command = list(args[0])
        commands.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout='{"results": []}',
            stderr="",
        )

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fake_run)

    exit_code = main(["deep", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert commands == [["semgrep", "--config", "p/security-audit", "--json"]]
    assert output["policy"]["config"] == "p/security-audit"
    assert output["checks"][0]["policy"]["config"] == "p/security-audit"


def test_default_semgrep_check_has_timeout() -> None:
    spec = default_semgrep_spec_for_name("sg_scan")

    assert spec is not None
    assert spec.timeout_seconds == 600


def test_deep_applies_configured_suppression_policy(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(
        tmp_path,
        semgrep={
            "config": "auto",
            "fail_on_severity": ["ERROR"],
            "ignore_rules": ["generic.secrets.security.detected-private-key"],
        },
        exclude_paths=["dist/**"],
    )
    payload = {
        "results": [
            {
                "check_id": "generic.generated.issue",
                "path": "dist/app.py",
                "start": {"line": 1},
                "extra": {"severity": "ERROR", "message": "Generated file"},
            },
            {
                "check_id": "generic.secrets.security.detected-private-key",
                "path": "src/settings.py",
                "start": {"line": 8},
                "extra": {"severity": "ERROR", "message": "Private key"},
            },
        ]
    }

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fake_run)

    exit_code = main(["deep", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)
    check = output["checks"][0]

    assert exit_code == 0
    assert output["status"] == "passed"
    assert check["findings_count"] == 2
    assert check["filtered_findings_count"] == 2
    assert check["filter_reasons"] == {"excluded_path": 1, "ignored_rule": 1}
    assert check["findings"] == []


@pytest.mark.skipif(
    shutil.which("semgrep") is None,
    reason="real Semgrep executable is not installed",
)
def test_deep_smoke_with_real_semgrep(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rules_path = tmp_path / "semgrep-smoke.yml"
    rules_path.write_text(
        "\n".join(
            [
                "rules:",
                "  - id: qa-z-smoke.eval",
                "    languages: [python]",
                "    message: Avoid eval in smoke test",
                "    severity: ERROR",
                "    pattern: eval(...)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "app.py").write_text(
        "def unsafe(value):\n    return eval(value)\n",
        encoding="utf-8",
    )
    write_deep_config(
        tmp_path,
        run=["semgrep", "--json"],
        semgrep={"config": str(rules_path), "fail_on_severity": ["ERROR"]},
    )
    usable, reason = real_semgrep_scan_is_usable(rules_path, tmp_path)
    if not usable:
        pytest.skip(f"real Semgrep executable is not operable: {reason}")

    exit_code = main(
        [
            "deep",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / ".qa-z" / "runs" / "semgrep-smoke"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["status"] == "failed"
    assert output["checks"][0]["findings_count"] >= 1
    assert output["checks"][0]["blocking_findings_count"] >= 1
    assert output["checks"][0]["findings"][0]["rule_id"] == "qa-z-smoke.eval"


def test_deep_preserves_summary_when_semgrep_fails(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(tmp_path)

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=2,
            stdout="not json",
            stderr="semgrep crashed",
        )

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fake_run)

    exit_code = main(["deep", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)
    artifact_dir = tmp_path / output["artifact_dir"]
    summary = json.loads((artifact_dir / "summary.json").read_text(encoding="utf-8"))
    check_artifact = json.loads(
        (artifact_dir / "checks" / "sg_scan.json").read_text(encoding="utf-8")
    )

    assert exit_code == 1
    assert output["status"] == "failed"
    assert (artifact_dir / "summary.md").exists()
    assert summary["checks"][0]["id"] == "sg_scan"
    assert check_artifact["status"] == "failed"
    assert check_artifact["stderr_tail"] == "semgrep crashed"


def test_deep_marks_invalid_semgrep_config_as_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(
        tmp_path,
        run=["semgrep", "--json"],
        semgrep={"config": ".semgrep/missing.yml"},
    )

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=2,
            stdout="",
            stderr="config .semgrep/missing.yml not found",
        )

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fake_run)

    exit_code = main(["deep", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)
    check = output["checks"][0]

    assert exit_code == 3
    assert output["status"] == "error"
    assert check["status"] == "error"
    assert check["error_type"] == "semgrep_config_error"
    assert check["policy"]["config"] == ".semgrep/missing.yml"
    assert "config .semgrep/missing.yml not found" in check["stderr_tail"]
