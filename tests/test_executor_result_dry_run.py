"""Dry-run focused executor-result tests."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.cli import main

from tests.executor_result_test_support import (
    NOW,
    python_command,
    read_json,
    start_session_and_bridge,
    write_config,
    write_contract,
    write_deep_summary,
    write_executor_result,
    write_fast_summary,
    write_json,
)


def test_executor_result_dry_run_reports_clear_for_verified_completed_history(
    tmp_path: Path, capsys
) -> None:
    write_config(
        tmp_path,
        checks=[{"id": "py_test", "run": python_command(""), "kind": "test"}],
    )
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_deep_summary(tmp_path, "baseline")
    start_session_and_bridge(tmp_path, capsys)

    result_path = tmp_path / "dry-run-clear.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": NOW,
            "status": "completed",
            "summary": "Applied the scoped repair cleanly.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Updated ingest behavior.",
                }
            ],
            "validation": {"status": "passed", "commands": [], "results": []},
            "notes": ["verification rerun is expected"],
        },
    )
    assert (
        main(
            [
                "executor-result",
                "ingest",
                "--path",
                str(tmp_path),
                "--result",
                str(result_path),
            ]
        )
        == 0
    )
    capsys.readouterr()

    dry_run_exit = main(
        [
            "executor-result",
            "dry-run",
            "--path",
            str(tmp_path),
            "--session",
            "session-one",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    persisted = read_json(
        tmp_path
        / ".qa-z"
        / "sessions"
        / "session-one"
        / "executor_results"
        / "dry_run_summary.json"
    )

    assert dry_run_exit == 0
    assert output["verdict"] == "clear"
    assert output["operator_decision"] == "continue_standard_verification"
    assert persisted["summary_source"] == "materialized"


def test_executor_result_dry_run_reports_attention_for_repeated_partial_history(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    start_session_and_bridge(tmp_path, capsys)

    for index in (1, 2):
        result_path = tmp_path / f"partial-{index}.json"
        write_executor_result(
            result_path,
            {
                "kind": "qa_z.executor_result",
                "schema_version": 1,
                "bridge_id": "bridge-session",
                "source_session_id": "session-one",
                "source_loop_id": None,
                "created_at": f"2026-04-16T00:00:0{index}Z",
                "status": "partial",
                "summary": f"Partial attempt {index}",
                "verification_hint": "skip",
                "candidate_run_dir": None,
                "changed_files": [
                    {
                        "path": "src/qa_z/executor_result.py",
                        "status": "modified",
                        "old_path": None,
                        "summary": "Started a repair.",
                    }
                ],
                "validation": {"status": "failed", "commands": [], "results": []},
                "notes": [f"needs follow-up {index}"],
            },
        )
        assert (
            main(
                [
                    "executor-result",
                    "ingest",
                    "--path",
                    str(tmp_path),
                    "--result",
                    str(result_path),
                ]
            )
            == 0
        )
        capsys.readouterr()

    dry_run_exit = main(
        [
            "executor-result",
            "dry-run",
            "--path",
            str(tmp_path),
            "--session",
            "session-one",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    text_exit = main(
        [
            "executor-result",
            "dry-run",
            "--path",
            str(tmp_path),
            "--session",
            "session-one",
        ]
    )
    text_output = capsys.readouterr().out

    assert dry_run_exit == 0
    assert text_exit == 0
    assert output["verdict_reason"] == "manual_retry_review_required"
    assert "repeated_partial_attempts" in output["history_signals"]
    assert "Decision: inspect_partial_attempts" in text_output


def test_executor_result_dry_run_reports_blocked_for_completed_verify_blocked_history(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    start_session_and_bridge(tmp_path, capsys)

    result_path = tmp_path / "completed-warning.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": NOW,
            "status": "completed",
            "summary": "Claims completion but validation evidence conflicts.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Touched ingest handling.",
                }
            ],
            "validation": {
                "status": "passed",
                "commands": [["python", "-m", "pytest"]],
                "results": [
                    {
                        "command": ["python", "-m", "pytest"],
                        "status": "failed",
                        "exit_code": 1,
                        "summary": "pytest still fails",
                    }
                ],
            },
            "notes": ["needs manual review"],
        },
    )
    assert (
        main(
            [
                "executor-result",
                "ingest",
                "--path",
                str(tmp_path),
                "--result",
                str(result_path),
            ]
        )
        == 0
    )
    capsys.readouterr()

    dry_run_exit = main(
        [
            "executor-result",
            "dry-run",
            "--path",
            str(tmp_path),
            "--session",
            "session-one",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert dry_run_exit == 0
    assert output["verdict"] == "blocked"
    assert output["operator_decision"] == "resolve_verification_blockers"


def test_executor_result_dry_run_reports_blocked_mixed_history_attention_residue(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    session_dir, _ = start_session_and_bridge(
        tmp_path,
        capsys,
        session_id="session-blocked-mixed",
        bridge_id="bridge-blocked-mixed",
    )
    write_json(
        session_dir / "executor_results" / "history.json",
        {
            "kind": "qa_z.executor_result_history",
            "schema_version": 1,
            "session_id": "session-blocked-mixed",
            "updated_at": "2026-04-16T00:15:00Z",
            "attempt_count": 3,
            "latest_attempt_id": "attempt-blocked-mixed-3",
            "attempts": [
                {
                    "attempt_id": "attempt-blocked-mixed-1",
                    "recorded_at": "2026-04-16T00:00:00Z",
                    "bridge_id": "bridge-blocked-mixed",
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
                    "attempt_path": ".qa-z/sessions/session-blocked-mixed/executor_results/attempts/attempt-blocked-mixed-1.json",
                    "ingest_artifact_path": ".qa-z/executor-results/attempt-blocked-mixed-1/ingest.json",
                    "ingest_report_path": ".qa-z/executor-results/attempt-blocked-mixed-1/ingest_report.md",
                    "freshness_status": "passed",
                    "freshness_reason": None,
                    "provenance_status": "passed",
                    "provenance_reason": None,
                },
                {
                    "attempt_id": "attempt-blocked-mixed-2",
                    "recorded_at": "2026-04-16T00:05:00Z",
                    "bridge_id": "bridge-blocked-mixed",
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
                    "attempt_path": ".qa-z/sessions/session-blocked-mixed/executor_results/attempts/attempt-blocked-mixed-2.json",
                    "ingest_artifact_path": ".qa-z/executor-results/attempt-blocked-mixed-2/ingest.json",
                    "ingest_report_path": ".qa-z/executor-results/attempt-blocked-mixed-2/ingest_report.md",
                    "freshness_status": "passed",
                    "freshness_reason": None,
                    "provenance_status": "passed",
                    "provenance_reason": None,
                },
                {
                    "attempt_id": "attempt-blocked-mixed-3",
                    "recorded_at": "2026-04-16T00:15:00Z",
                    "bridge_id": "bridge-blocked-mixed",
                    "source_loop_id": None,
                    "result_status": "completed",
                    "ingest_status": "accepted_with_warning",
                    "verify_resume_status": "verify_blocked",
                    "verification_hint": "rerun",
                    "verification_triggered": False,
                    "verification_verdict": "mixed",
                    "validation_status": "failed",
                    "warning_ids": ["completed_validation_failed"],
                    "backlog_categories": [
                        "partial_completion_gap",
                        "workflow_gap",
                    ],
                    "changed_files_count": 1,
                    "notes_count": 1,
                    "attempt_path": ".qa-z/sessions/session-blocked-mixed/executor_results/attempts/attempt-blocked-mixed-3.json",
                    "ingest_artifact_path": ".qa-z/executor-results/attempt-blocked-mixed-3/ingest.json",
                    "ingest_report_path": ".qa-z/executor-results/attempt-blocked-mixed-3/ingest_report.md",
                    "freshness_status": "passed",
                    "freshness_reason": None,
                    "provenance_status": "passed",
                    "provenance_reason": None,
                },
            ],
        },
    )

    dry_run_exit = main(
        [
            "executor-result",
            "dry-run",
            "--path",
            str(tmp_path),
            "--session",
            "session-blocked-mixed",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert dry_run_exit == 0
    assert output["verdict"] == "blocked"
    assert output["history_signals"] == [
        "repeated_partial_attempts",
        "completed_verify_blocked",
        "validation_conflict",
    ]
    assert output["operator_summary"] == (
        "A completed executor attempt is still blocked by verification evidence; "
        "validation conflicts and retry pressure still need review before another "
        "retry."
    )
    assert [action["id"] for action in output["recommended_actions"]] == [
        "resolve_verification_blockers",
        "review_validation_conflict",
        "inspect_partial_attempts",
    ]
