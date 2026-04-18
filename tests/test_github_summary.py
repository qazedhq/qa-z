"""Tests for GitHub Actions summary rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from qa_z.artifacts import RunSource
from qa_z.cli import main
from qa_z.diffing.models import ChangedFile
from qa_z.reporters.github_summary import render_github_summary
from qa_z.runners.models import CheckResult, RunSummary, SelectionSummary


def write_config(tmp_path: Path) -> None:
    """Write a minimal qa-z config for GitHub summary CLI tests."""
    config = {
        "project": {"name": "qa-z-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {"output_dir": ".qa-z/runs"},
    }
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_contract(tmp_path: Path) -> None:
    """Write a minimal contract referenced by summary artifacts."""
    contract_dir = tmp_path / "qa" / "contracts"
    contract_dir.mkdir(parents=True, exist_ok=True)
    (contract_dir / "auth.md").write_text(
        "# QA Contract: Auth\n\n## Acceptance Checks\n\n- run fast checks\n",
        encoding="utf-8",
    )


def write_summary(tmp_path: Path, run_id: str) -> None:
    """Write a v2 failed fast summary artifact."""
    payload: dict[str, Any] = {
        "schema_version": 2,
        "mode": "fast",
        "contract_path": "qa/contracts/auth.md",
        "project_root": str(tmp_path),
        "status": "failed",
        "started_at": "2026-04-11T17:38:52Z",
        "finished_at": "2026-04-11T17:39:11Z",
        "artifact_dir": f".qa-z/runs/{run_id}/fast",
        "selection": {
            "mode": "smart",
            "input_source": "cli_diff",
            "changed_files": [
                {
                    "path": "src/qa_z/cli.py",
                    "old_path": "src/qa_z/cli.py",
                    "status": "modified",
                    "additions": 8,
                    "deletions": 2,
                    "language": "python",
                    "kind": "source",
                }
            ],
            "high_risk_reasons": [],
            "selected_checks": ["py_lint", "py_test"],
            "full_checks": ["py_type"],
            "targeted_checks": ["py_lint", "py_test"],
            "skipped_checks": ["ts_lint"],
        },
        "checks": [
            {
                "id": "py_lint",
                "tool": "ruff",
                "command": ["ruff", "check", "src/qa_z/cli.py"],
                "kind": "lint",
                "status": "passed",
                "exit_code": 0,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
                "execution_mode": "targeted",
                "target_paths": ["src/qa_z/cli.py"],
                "selection_reason": "python source/test files changed",
                "high_risk_reasons": [],
            },
            {
                "id": "py_type",
                "tool": "mypy",
                "command": ["mypy", "src", "tests"],
                "kind": "typecheck",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 941,
                "stdout_tail": "src/qa_z/cli.py:10: error: bad return\n",
                "stderr_tail": "",
                "execution_mode": "full",
                "target_paths": [],
                "selection_reason": "type checks run full",
                "high_risk_reasons": [],
                "message": "mypy exited with code 1.",
            },
            {
                "id": "ts_lint",
                "tool": "eslint",
                "command": ["eslint", "."],
                "kind": "lint",
                "status": "skipped",
                "exit_code": None,
                "duration_ms": 0,
                "stdout_tail": "",
                "stderr_tail": "",
                "execution_mode": "skipped",
                "target_paths": [],
                "selection_reason": "python-only change",
                "high_risk_reasons": [],
            },
        ],
        "totals": {"passed": 1, "failed": 1, "skipped": 1, "warning": 0},
    }
    summary_path = tmp_path / ".qa-z" / "runs" / run_id / "fast" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / ".qa-z" / "runs" / "latest-run.json").write_text(
        json.dumps({"run_dir": f".qa-z/runs/{run_id}"}) + "\n", encoding="utf-8"
    )


def write_deep_summary(tmp_path: Path, run_id: str, *, skipped: bool = False) -> None:
    """Write a sibling deep summary artifact."""
    check: dict[str, Any]
    if skipped:
        check = {
            "id": "sg_scan",
            "tool": "semgrep",
            "command": ["semgrep", "--config", "auto", "--json"],
            "kind": "static-analysis",
            "status": "skipped",
            "exit_code": None,
            "duration_ms": 0,
            "stdout_tail": "",
            "stderr_tail": "",
            "execution_mode": "skipped",
            "target_paths": [],
            "selection_reason": "docs-only change",
            "high_risk_reasons": [],
        }
    else:
        check = {
            "id": "sg_scan",
            "tool": "semgrep",
            "command": [
                "semgrep",
                "--config",
                "auto",
                "--json",
                "src/app.py",
                "src/db.ts",
            ],
            "kind": "static-analysis",
            "status": "failed",
            "exit_code": 0,
            "duration_ms": 321,
            "stdout_tail": "",
            "stderr_tail": "",
            "execution_mode": "targeted",
            "target_paths": ["src/app.py", "src/db.ts"],
            "selection_reason": "source files changed",
            "high_risk_reasons": [],
            "findings_count": 2,
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
                    "path": "src/db.ts",
                    "line": 12,
                    "message": "Possible SQL injection",
                },
            ],
        }
    payload: dict[str, Any] = {
        "schema_version": 2,
        "mode": "deep",
        "contract_path": "qa/contracts/auth.md",
        "project_root": str(tmp_path),
        "status": "passed" if skipped else "failed",
        "started_at": "2026-04-11T17:40:00Z",
        "finished_at": "2026-04-11T17:40:05Z",
        "artifact_dir": f".qa-z/runs/{run_id}/deep",
        "selection": {
            "mode": "smart",
            "input_source": "cli_diff",
            "changed_files": [],
            "high_risk_reasons": [],
            "selected_checks": [] if skipped else ["sg_scan"],
            "full_checks": [],
            "targeted_checks": [] if skipped else ["sg_scan"],
            "skipped_checks": ["sg_scan"] if skipped else [],
        },
        "checks": [check],
        "totals": {
            "passed": 0,
            "failed": 0 if skipped else 1,
            "skipped": 1 if skipped else 0,
            "warning": 0,
        },
    }
    summary_path = tmp_path / ".qa-z" / "runs" / run_id / "deep" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload), encoding="utf-8")


def write_grouped_deep_summary(tmp_path: Path, run_id: str) -> None:
    """Write a sibling deep summary with grouped Semgrep findings."""
    payload: dict[str, Any] = {
        "schema_version": 2,
        "mode": "deep",
        "contract_path": "qa/contracts/auth.md",
        "project_root": str(tmp_path),
        "status": "failed",
        "started_at": "2026-04-11T17:40:00Z",
        "finished_at": "2026-04-11T17:40:05Z",
        "artifact_dir": f".qa-z/runs/{run_id}/deep",
        "policy": {
            "config": "auto",
            "fail_on_severity": ["ERROR"],
            "ignore_rules": [],
            "exclude_paths": [],
        },
        "selection": {
            "mode": "smart",
            "input_source": "cli_diff",
            "changed_files": [],
            "high_risk_reasons": [],
            "selected_checks": ["sg_scan"],
            "full_checks": [],
            "targeted_checks": ["sg_scan"],
            "skipped_checks": [],
        },
        "checks": [
            {
                "id": "sg_scan",
                "tool": "semgrep",
                "command": ["semgrep", "--config", "auto", "--json"],
                "kind": "static-analysis",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 321,
                "stdout_tail": "",
                "stderr_tail": "",
                "execution_mode": "targeted",
                "target_paths": ["src/app.py", "src/db.ts"],
                "selection_reason": "source files changed",
                "high_risk_reasons": [],
                "findings_count": 5,
                "blocking_findings_count": 3,
                "filtered_findings_count": 0,
                "filter_reasons": {},
                "severity_summary": {"ERROR": 3, "WARNING": 2},
                "policy": {
                    "config": "auto",
                    "fail_on_severity": ["ERROR"],
                    "ignore_rules": [],
                    "exclude_paths": [],
                },
                "grouped_findings": [
                    {
                        "rule_id": "python.lang.security.audit.eval",
                        "severity": "ERROR",
                        "path": "src/app.py",
                        "count": 3,
                        "representative_line": 42,
                        "message": "Avoid use of eval",
                    },
                    {
                        "rule_id": "typescript.sql.injection",
                        "severity": "WARNING",
                        "path": "src/db.ts",
                        "count": 2,
                        "representative_line": 12,
                        "message": "Possible SQL injection",
                    },
                ],
                "findings": [],
            }
        ],
        "totals": {"passed": 0, "failed": 1, "skipped": 0, "warning": 0},
    }
    summary_path = tmp_path / ".qa-z" / "runs" / run_id / "deep" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload), encoding="utf-8")


def write_session_outcome_for_run(
    tmp_path: Path,
    *,
    session_id: str,
    candidate_run: str,
    verdict: str = "improved",
    executor_dry_run_verdict: str | None = None,
    executor_dry_run_reason: str | None = None,
    executor_dry_run_source: str | None = None,
    executor_dry_run_attempt_count: int | None = None,
    executor_dry_run_history_signals: list[str] | None = None,
) -> None:
    """Write a compact repair-session outcome tied to a candidate run."""
    session_dir = tmp_path / ".qa-z" / "sessions" / session_id
    verify_dir = session_dir / "verify"
    verify_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "kind": "qa_z.repair_session_summary",
        "schema_version": 1,
        "session_id": session_id,
        "state": "completed",
        "baseline_run_dir": ".qa-z/runs/baseline",
        "candidate_run_dir": f".qa-z/runs/{candidate_run}",
        "verify_dir": f".qa-z/sessions/{session_id}/verify",
        "outcome_path": f".qa-z/sessions/{session_id}/outcome.md",
        "verdict": verdict,
        "blocking_before": 3,
        "blocking_after": 1,
        "resolved_count": 2,
        "remaining_issue_count": 1,
        "new_issue_count": 0,
        "regression_count": 0,
        "not_comparable_count": 0,
        "next_recommendation": "merge candidate",
    }
    if executor_dry_run_verdict is not None:
        summary["executor_dry_run_verdict"] = executor_dry_run_verdict
    if executor_dry_run_reason is not None:
        summary["executor_dry_run_reason"] = executor_dry_run_reason
    if executor_dry_run_source is not None:
        summary["executor_dry_run_source"] = executor_dry_run_source
    if executor_dry_run_attempt_count is not None:
        summary["executor_dry_run_attempt_count"] = executor_dry_run_attempt_count
    if executor_dry_run_history_signals is not None:
        summary["executor_dry_run_history_signals"] = executor_dry_run_history_signals
    manifest = {
        "kind": "qa_z.repair_session",
        "schema_version": 1,
        "session_id": session_id,
        "session_dir": f".qa-z/sessions/{session_id}",
        "state": "completed",
        "baseline_run_dir": ".qa-z/runs/baseline",
        "baseline_fast_summary_path": ".qa-z/runs/baseline/fast/summary.json",
        "handoff_dir": f".qa-z/sessions/{session_id}/handoff",
        "handoff_artifacts": {
            "handoff_json": f".qa-z/sessions/{session_id}/handoff/handoff.json"
        },
        "executor_guide_path": f".qa-z/sessions/{session_id}/executor_guide.md",
        "candidate_run_dir": f".qa-z/runs/{candidate_run}",
        "verify_dir": f".qa-z/sessions/{session_id}/verify",
        "verify_artifacts": {
            "summary_json": f".qa-z/sessions/{session_id}/verify/summary.json",
            "compare_json": f".qa-z/sessions/{session_id}/verify/compare.json",
            "report_markdown": f".qa-z/sessions/{session_id}/verify/report.md",
        },
        "outcome_path": f".qa-z/sessions/{session_id}/outcome.md",
        "summary_path": f".qa-z/sessions/{session_id}/summary.json",
        "created_at": "2026-04-14T00:00:00Z",
        "updated_at": "2026-04-14T00:00:01Z",
        "provenance": {},
    }
    compare = {
        "kind": "qa_z.verify_compare",
        "schema_version": 1,
        "baseline_run_id": "baseline",
        "candidate_run_id": candidate_run,
        "baseline": {"run_dir": ".qa-z/runs/baseline"},
        "candidate": {"run_dir": f".qa-z/runs/{candidate_run}"},
        "verdict": verdict,
        "summary": {
            "blocking_before": 3,
            "blocking_after": 1,
            "resolved_count": 2,
            "new_issue_count": 0,
            "regression_count": 0,
        },
    }
    (session_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (session_dir / "session.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (verify_dir / "summary.json").write_text(
        json.dumps(
            {
                "kind": "qa_z.verify_summary",
                "schema_version": 1,
                "repair_improved": verdict == "improved",
                "verdict": verdict,
                "blocking_before": 3,
                "blocking_after": 1,
                "resolved_count": 2,
                "new_issue_count": 0,
                "regression_count": 0,
                "not_comparable_count": 0,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (verify_dir / "compare.json").write_text(
        json.dumps(compare, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (verify_dir / "report.md").write_text(
        "# QA-Z Repair Verification\n", encoding="utf-8"
    )


def write_executor_result_history(
    tmp_path: Path,
    *,
    session_id: str,
    attempts: list[dict[str, object]],
) -> None:
    """Write a compact session-local executor-result history artifact."""
    path = (
        tmp_path
        / ".qa-z"
        / "sessions"
        / session_id
        / "executor_results"
        / "history.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "kind": "qa_z.executor_result_history",
                "schema_version": 1,
                "session_id": session_id,
                "updated_at": "2026-04-16T00:00:02Z",
                "attempt_count": len(attempts),
                "latest_attempt_id": attempts[-1]["attempt_id"] if attempts else None,
                "attempts": attempts,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_github_summary_renders_compact_failed_run() -> None:
    root = Path("/repo")
    summary = RunSummary(
        mode="fast",
        contract_path="qa/contracts/auth.md",
        project_root=str(root),
        status="failed",
        started_at="2026-04-11T17:38:52Z",
        finished_at="2026-04-11T17:39:11Z",
        artifact_dir=".qa-z/runs/ci/fast",
        schema_version=2,
        selection=SelectionSummary(
            mode="smart",
            input_source="cli_diff",
            changed_files=[
                ChangedFile(
                    path="src/qa_z/cli.py",
                    old_path="src/qa_z/cli.py",
                    status="modified",
                    additions=8,
                    deletions=2,
                    language="python",
                    kind="source",
                )
            ],
            full_checks=["py_type"],
            targeted_checks=["py_lint", "py_test"],
            skipped_checks=["ts_lint"],
        ),
        checks=[
            CheckResult(
                id="py_type",
                tool="mypy",
                command=["mypy", "src", "tests"],
                kind="typecheck",
                status="failed",
                exit_code=1,
                duration_ms=941,
                execution_mode="full",
                selection_reason="type checks run full",
                message="mypy exited with code 1.",
            )
        ],
    )
    run_source = RunSource(
        run_dir=root / ".qa-z" / "runs" / "ci",
        fast_dir=root / ".qa-z" / "runs" / "ci" / "fast",
        summary_path=root / ".qa-z" / "runs" / "ci" / "fast" / "summary.json",
    )

    markdown = render_github_summary(summary=summary, run_source=run_source, root=root)

    assert "# QA-Z Summary" in markdown
    assert "**Fast:** failed" in markdown
    assert "**Deep:** not run" in markdown
    assert "**Selection:** smart" in markdown
    assert "## Fast QA" in markdown
    assert "- Passed: 0" in markdown
    assert "- Failed: 1" in markdown
    assert "- `py_type` - full - mypy exited with code 1." in markdown
    assert "- `src/qa_z/cli.py`" in markdown
    assert "- Review packet: `.qa-z/runs/ci/review/review.md`" in markdown
    assert "- Repair prompt: `.qa-z/runs/ci/repair/prompt.md`" in markdown
    assert "Repair Session Outcome" not in markdown


def test_github_summary_cli_writes_output_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    output_path = tmp_path / ".qa-z" / "runs" / "ci" / "github-summary.md"

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            "latest",
            "--output",
            str(output_path),
        ]
    )
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert "# QA-Z Summary" in stdout
    assert output_path.exists()
    assert "## Failed Checks" in output_path.read_text(encoding="utf-8")
    assert "Repair Session Outcome" not in stdout


def test_github_summary_includes_repair_session_outcome_when_present(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "candidate")
    write_session_outcome_for_run(
        tmp_path,
        session_id="session-one",
        candidate_run="candidate",
        executor_dry_run_verdict="blocked",
        executor_dry_run_reason="completed_attempt_not_verification_clean",
        executor_dry_run_source="materialized",
        executor_dry_run_attempt_count=2,
        executor_dry_run_history_signals=["repeated_partial_attempts"],
    )

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/candidate",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Repair Session Outcome" in output
    assert "- Verdict: improved" in output
    assert "- Resolved blockers: 2" in output
    assert "- Remaining blockers: 1" in output
    assert "- Regressions: 0" in output
    assert "- Recommendation: safe_to_review" in output
    assert "- Executor dry-run: blocked" in output
    assert "- Dry-run reason: completed_attempt_not_verification_clean" in output
    assert "- Dry-run source: materialized" in output
    assert "- Executor attempts: 2" in output
    assert "- Executor history signals: repeated_partial_attempts" in output
    assert "- Session: `.qa-z/sessions/session-one/session.json`" in output


def test_github_summary_synthesizes_dry_run_from_history_when_summary_lacks_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "candidate")
    write_session_outcome_for_run(
        tmp_path,
        session_id="session-one",
        candidate_run="candidate",
    )
    write_executor_result_history(
        tmp_path,
        session_id="session-one",
        attempts=[
            {
                "attempt_id": "attempt-1",
                "recorded_at": "2026-04-16T00:00:01Z",
                "bridge_id": "bridge-session",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-1.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "passed",
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "recorded_at": "2026-04-16T00:00:02Z",
                "bridge_id": "bridge-session",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-2.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "passed",
                "provenance_reason": None,
            },
        ],
    )

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/candidate",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Repair Session Outcome" in output
    assert "- Executor dry-run: attention_required" in output
    assert "- Dry-run reason: manual_retry_review_required" in output
    assert "- Dry-run source: history_fallback" in output
    assert "- Executor attempts: 2" in output
    assert "- Executor history signals: repeated_partial_attempts" in output


def test_github_summary_can_render_explicit_session_outcome(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "candidate")
    write_session_outcome_for_run(
        tmp_path, session_id="session-one", candidate_run="candidate"
    )

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/candidate",
            "--from-session",
            ".qa-z/sessions/session-one",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Repair Session Outcome" in output
    assert "- Outcome: `.qa-z/sessions/session-one/outcome.md`" in output


def test_github_summary_explicit_session_uses_verify_fallback_when_summary_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "candidate")
    write_session_outcome_for_run(
        tmp_path,
        session_id="session-one",
        candidate_run="candidate",
        verdict="mixed",
    )
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    (session_dir / "summary.json").unlink()
    write_executor_result_history(
        tmp_path,
        session_id="session-one",
        attempts=[
            {
                "attempt_id": "attempt-1",
                "recorded_at": "2026-04-16T00:00:01Z",
                "bridge_id": "bridge-session",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 2,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-1.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "failed",
                "provenance_reason": "scope_validation_failed",
            }
        ],
    )

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/candidate",
            "--from-session",
            ".qa-z/sessions/session-one",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Repair Session Outcome" in output
    assert "- Verdict: mixed" in output
    assert "- Recommendation: review_required" in output
    assert "- Executor dry-run: blocked" in output
    assert "- Dry-run reason: scope_validation_failed" in output
    assert "- Dry-run source: history_fallback" in output
    assert "- Executor attempts: 1" in output
    assert "- Executor history signals: scope_validation_failed" in output
    assert "Verification artifacts could not be read." not in output


def test_github_summary_includes_deep_section(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    write_deep_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(
        ["github-summary", "--path", str(tmp_path), "--from-run", "latest"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "**Fast:** failed" in output
    assert "**Deep:** failed" in output
    assert "## Deep QA" in output
    assert "- Status: failed" in output
    assert "- Findings: 2" in output
    assert "- Highest severity: ERROR" in output
    assert "- Mode: targeted" in output
    assert "- Files affected: 2" in output
    assert "- `src/app.py:42` ERROR - Avoid use of eval" in output


def test_github_summary_uses_grouped_deep_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    write_grouped_deep_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(
        ["github-summary", "--path", str(tmp_path), "--from-run", "latest"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "- Blocking: 3" in output
    assert "### Top Deep Findings" in output
    assert "- `python.lang.security.audit.eval` - `src/app.py` - 3 hits" in output


def test_github_summary_handles_deep_skipped_or_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "missing-deep")

    missing_exit = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/missing-deep",
        ]
    )
    missing_output = capsys.readouterr().out

    write_summary(tmp_path, "skipped-deep")
    write_deep_summary(tmp_path, "skipped-deep", skipped=True)
    skipped_exit = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/skipped-deep",
        ]
    )
    skipped_output = capsys.readouterr().out

    assert missing_exit == 0
    assert "**Deep:** not run" in missing_output
    assert "## Deep QA" not in missing_output
    assert skipped_exit == 0
    assert "**Deep:** passed" in skipped_output
    assert "## Deep QA" in skipped_output
    assert "- Status: passed" in skipped_output
    assert "- Findings: 0" in skipped_output
    assert "- Mode: skipped" in skipped_output


def test_github_summary_cli_reports_missing_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)

    exit_code = main(["github-summary", "--path", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 4
    assert "source not found" in output
