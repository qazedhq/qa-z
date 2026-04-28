from __future__ import annotations

import sys
from pathlib import Path

from qa_z.benchmark import run_benchmark
from tests.benchmark_test_support import (
    write_config,
    write_contract,
    write_expected,
    write_fast_summary,
    write_json,
    write_mixed_fast_summary,
)


def test_run_benchmark_executes_executor_result_candidate_run_fixture(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixtures" / "executor_result_mixed_candidate_run"
    repo = fixture / "repo"
    repo.joinpath("src").mkdir(parents=True)
    repo.joinpath("src", "app.py").write_text("def answer():\n    return 42\n")
    repo.joinpath("src", "invoice.ts").write_text(
        "export const total: number = 1;\n", encoding="utf-8"
    )
    write_contract(
        repo,
        related_files=["src/app.py", "src/invoice.ts"],
        title="Executor result mixed candidate benchmark fixture",
    )
    write_config(
        repo,
        [{"id": "py_test", "kind": "test", "run": [sys.executable, "-c", ""]}],
        languages=["python", "typescript"],
    )
    write_mixed_fast_summary(
        repo,
        "baseline",
        py_status="failed",
        py_exit_code=1,
        ts_status="passed",
        ts_exit_code=0,
    )
    write_mixed_fast_summary(
        repo,
        "candidate",
        py_status="passed",
        py_exit_code=0,
        ts_status="failed",
        ts_exit_code=1,
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_result_mixed_candidate_run",
            "run": {
                "executor_result": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "bridge_id": "bridge-session",
                    "result_path": "external-result.json",
                    "session_id": "session-one",
                }
            },
            "expect_executor_result": {
                "result_status": "completed",
                "session_id": "session-one",
                "session_state": "completed",
                "verification_hint": "candidate_run",
                "verification_triggered": True,
                "verification_verdict": "mixed",
                "next_recommendation": "inspect regressions",
                "verify_summary_path": ".qa-z/sessions/session-one/verify/summary.json",
                "schema_version": 1,
            },
            "expect_verify": {
                "verdict": "mixed",
                "blocking_before": 1,
                "blocking_after": 1,
                "resolved_count": 1,
                "regression_count": 1,
                "new_issue_count": 1,
                "schema_version": 1,
            },
        },
    )
    write_expected(
        repo / "external-result.json",
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": "2026-04-16T00:00:00Z",
            "status": "completed",
            "summary": "Resolved the Python failure, but the TypeScript typecheck regressed.",
            "verification_hint": "candidate_run",
            "candidate_run_dir": ".qa-z/runs/candidate",
            "changed_files": [
                {
                    "path": "src/app.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Adjusted Python logic during repair.",
                },
                {
                    "path": "src/invoice.ts",
                    "status": "modified",
                    "old_path": None,
                    "summary": "TypeScript edits introduced a new failure.",
                },
            ],
            "validation": {
                "status": "failed",
                "commands": [["python", "-m", "pytest"], ["tsc", "--noEmit"]],
                "results": [
                    {
                        "command": ["python", "-m", "pytest"],
                        "status": "passed",
                        "exit_code": 0,
                        "summary": "pytest passed locally",
                    },
                    {
                        "command": ["tsc", "--noEmit"],
                        "status": "failed",
                        "exit_code": 1,
                        "summary": "ts_type still fails",
                    },
                ],
            },
            "notes": ["candidate run should attach mixed verification evidence"],
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_result"]["result_status"] == "completed"
    assert (
        fixture_result["actual"]["executor_result"]["verification_verdict"] == "mixed"
    )
    assert fixture_result["actual"]["verify"]["verdict"] == "mixed"
    assert fixture_result["categories"]["verify"] is True


def test_run_benchmark_executes_executor_result_future_timestamp_rejection_fixture(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixtures" / "executor_result_future_timestamp_rejected"
    repo = fixture / "repo"
    repo.joinpath("src").mkdir(parents=True)
    repo.joinpath("src", "app.py").write_text("def answer():\n    return 42\n")
    write_contract(
        repo,
        related_files=["src/app.py"],
        title="Executor result future timestamp rejection fixture",
    )
    write_config(
        repo,
        [{"id": "py_test", "kind": "test", "run": [sys.executable, "-c", ""]}],
    )
    write_fast_summary(
        repo, "baseline", check_id="py_test", status="failed", exit_code=1
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_result_future_timestamp_rejected",
            "run": {
                "executor_result": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "bridge_id": "bridge-future",
                    "result_path": "external-result.json",
                    "session_id": "session-future",
                }
            },
            "expect_executor_result": {
                "result_status": "completed",
                "expected_ingest_status": "rejected_invalid",
                "session_id": "session-future",
                "verification_hint": "rerun",
                "verification_triggered": False,
                "verify_resume_status": "verify_blocked",
                "expected_recommendation": "fix executor result timestamps",
                "freshness_reason": "result_from_future",
                "backlog_categories": ["evidence_freshness_gap"],
                "schema_version": 1,
            },
        },
    )
    write_expected(
        repo / "external-result.json",
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-future",
            "source_session_id": "session-future",
            "source_loop_id": None,
            "created_at": "2026-04-16T00:10:00Z",
            "status": "completed",
            "summary": "Claims completion from a timestamp after benchmark ingest begins.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/app.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Adjusted Python logic.",
                }
            ],
            "validation": {"status": "passed", "commands": [], "results": []},
            "notes": ["should be rejected as future-dated evidence"],
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_result"]["ingest_status"] == (
        "rejected_invalid"
    )
    assert fixture_result["actual"]["executor_result"]["freshness_reason"] == (
        "result_from_future"
    )


def test_run_benchmark_executes_executor_result_partial_fixture_with_realism_fields(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixtures" / "executor_result_partial_mixed_verify_candidate"
    repo = fixture / "repo"
    repo.joinpath("src").mkdir(parents=True)
    repo.joinpath("src", "app.py").write_text("def answer():\n    return 42\n")
    repo.joinpath("src", "invoice.ts").write_text(
        "export const total: number = 1;\n", encoding="utf-8"
    )
    write_contract(
        repo,
        related_files=["src/app.py", "src/invoice.ts"],
        title="Executor result partial mixed verify fixture",
    )
    write_config(
        repo,
        [{"id": "py_test", "kind": "test", "run": [sys.executable, "-c", ""]}],
        languages=["python", "typescript"],
    )
    write_mixed_fast_summary(
        repo,
        "baseline",
        py_status="failed",
        py_exit_code=1,
        ts_status="passed",
        ts_exit_code=0,
    )
    write_mixed_fast_summary(
        repo,
        "candidate",
        py_status="passed",
        py_exit_code=0,
        ts_status="failed",
        ts_exit_code=1,
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_result_partial_mixed_verify_candidate",
            "run": {
                "verify": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "candidate_run": ".qa-z/runs/candidate",
                },
                "executor_result": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "bridge_id": "bridge-partial",
                    "loop_id": "loop-partial",
                    "result_path": "external-result.json",
                    "session_id": "session-partial",
                },
            },
            "expect_executor_result": {
                "result_status": "partial",
                "expected_ingest_status": "accepted_partial",
                "session_id": "session-partial",
                "session_state": "candidate_generated",
                "verification_hint": "candidate_run",
                "verification_triggered": False,
                "expected_recommendation": "continue repair",
                "backlog_categories": ["partial_completion_gap"],
                "warning_ids_absent": ["no_op_without_explanation"],
                "source_self_inspection": ".qa-z/loops/loop-partial/self_inspect.json",
                "source_self_inspection_loop_id": "loop-partial",
                "source_self_inspection_generated_at": "2026-04-16T00:00:00Z",
                "live_repository_modified_count": 2,
                "live_repository_current_branch": "codex/qa-z-bootstrap",
                "live_repository_current_head": "1234567890abcdef1234567890abcdef12345678",
                "source_context_fields_recorded": True,
                "live_repository_context_recorded": True,
                "check_statuses_recorded": True,
                "backlog_implications_recorded": True,
                "schema_version": 1,
            },
            "expect_verify": {
                "verdict": "mixed",
                "blocking_before": 1,
                "blocking_after": 1,
                "resolved_count": 1,
                "regression_count": 1,
                "new_issue_count": 1,
                "schema_version": 1,
            },
        },
    )
    write_expected(
        repo / "external-result.json",
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-partial",
            "source_session_id": "session-partial",
            "source_loop_id": "loop-partial",
            "created_at": "2026-04-16T00:00:00Z",
            "status": "partial",
            "summary": "Resolved the Python issue, but the TypeScript regression still needs follow-up.",
            "verification_hint": "candidate_run",
            "candidate_run_dir": ".qa-z/runs/candidate",
            "changed_files": [
                {
                    "path": "src/app.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Adjusted Python logic.",
                },
                {
                    "path": "src/invoice.ts",
                    "status": "modified",
                    "old_path": None,
                    "summary": "TypeScript still needs another pass.",
                },
            ],
            "validation": {
                "status": "failed",
                "commands": [["python", "-m", "pytest"], ["tsc", "--noEmit"]],
                "results": [
                    {
                        "command": ["python", "-m", "pytest"],
                        "status": "passed",
                        "exit_code": 0,
                        "summary": "pytest passed locally",
                    },
                    {
                        "command": ["tsc", "--noEmit"],
                        "status": "failed",
                        "exit_code": 1,
                        "summary": "ts_type still fails",
                    },
                ],
            },
            "notes": ["needs another repair loop"],
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_result"]["ingest_status"] == (
        "accepted_partial"
    )
    assert fixture_result["actual"]["executor_result"]["backlog_categories"] == [
        "partial_completion_gap"
    ]
    assert fixture_result["actual"]["executor_result"]["source_self_inspection"] == (
        ".qa-z/loops/loop-partial/self_inspect.json"
    )
    assert (
        fixture_result["actual"]["executor_result"]["source_self_inspection_loop_id"]
        == "loop-partial"
    )
    assert (
        fixture_result["actual"]["executor_result"]["live_repository_modified_count"]
        == 2
    )
    assert (
        fixture_result["actual"]["executor_result"]["source_context_fields_recorded"]
        is True
    )
    assert (
        fixture_result["actual"]["executor_result"]["live_repository_context_recorded"]
        is True
    )
    assert (
        fixture_result["actual"]["executor_result"]["check_statuses_recorded"] is True
    )
    assert (
        fixture_result["actual"]["executor_result"]["backlog_implications_recorded"]
        is True
    )
    assert fixture_result["actual"]["verify"]["verdict"] == "mixed"


def test_run_benchmark_executes_executor_result_validation_conflict_fixture(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixtures" / "executor_result_validation_conflict_blocked"
    repo = fixture / "repo"
    repo.joinpath("src").mkdir(parents=True)
    repo.joinpath("src", "app.py").write_text("def answer():\n    return 42\n")
    write_contract(
        repo,
        related_files=["src/app.py"],
        title="Executor result validation conflict fixture",
    )
    write_config(
        repo,
        [{"id": "py_test", "kind": "test", "run": [sys.executable, "-c", ""]}],
    )
    write_fast_summary(
        repo, "baseline", check_id="py_test", status="failed", exit_code=1
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_result_validation_conflict_blocked",
            "run": {
                "executor_result": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "bridge_id": "bridge-validation",
                    "result_path": "external-result.json",
                    "session_id": "session-validation",
                }
            },
            "expect_executor_result": {
                "result_status": "completed",
                "expected_ingest_status": "accepted_with_warning",
                "session_id": "session-validation",
                "session_state": "candidate_generated",
                "verification_hint": "rerun",
                "verification_triggered": False,
                "verify_resume_status": "verify_blocked",
                "expected_recommendation": "inspect executor result warnings",
                "warning_ids_present": ["validation_summary_conflicts_with_results"],
                "backlog_categories": ["workflow_gap"],
                "schema_version": 1,
            },
        },
    )
    write_expected(
        repo / "external-result.json",
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-validation",
            "source_session_id": "session-validation",
            "source_loop_id": None,
            "created_at": "2026-04-16T00:00:00Z",
            "status": "completed",
            "summary": "Claims a passing summary while the detailed validation still fails.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/app.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Adjusted Python logic.",
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
            "notes": ["validation evidence should block optimistic verify resume"],
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_result"]["verify_resume_status"] == (
        "verify_blocked"
    )
    assert (
        "validation_summary_conflicts_with_results"
        in fixture_result["actual"]["executor_result"]["warning_ids"]
    )


def test_run_benchmark_executes_executor_dry_run_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "fixtures" / "executor_dry_run_repeated_partial_attention"
    repo = fixture / "repo"
    write_contract(
        repo, related_files=["src/app.py"], title="Dry-run benchmark fixture"
    )
    repo.joinpath("src").mkdir(parents=True, exist_ok=True)
    repo.joinpath("src", "app.py").write_text(
        "def answer() -> int:\n    return 42\n", encoding="utf-8"
    )
    write_config(repo, [])
    write_json(
        repo / ".qa-z" / "sessions" / "session-one" / "session.json",
        {
            "kind": "qa_z.repair_session",
            "schema_version": 1,
            "session_id": "session-one",
            "session_dir": ".qa-z/sessions/session-one",
            "baseline_run_dir": ".qa-z/runs/baseline",
            "baseline_fast_summary_path": ".qa-z/runs/baseline/fast/summary.json",
            "baseline_deep_summary_path": None,
            "handoff_dir": ".qa-z/sessions/session-one/handoff",
            "handoff_artifacts": {},
            "executor_guide_path": ".qa-z/sessions/session-one/executor_guide.md",
            "candidate_run_dir": None,
            "verify_dir": None,
            "verify_artifacts": {},
            "outcome_path": None,
            "summary_path": None,
            "provenance": {"repair_needed": True},
            "safety_artifacts": {},
            "executor_result_path": None,
            "executor_result_status": None,
            "executor_result_validation_status": None,
            "executor_result_bridge_id": None,
            "state": "waiting_for_external_repair",
            "created_at": "2026-04-16T00:00:00Z",
            "updated_at": "2026-04-16T00:00:00Z",
        },
    )
    write_json(
        repo
        / ".qa-z"
        / "sessions"
        / "session-one"
        / "executor_results"
        / "history.json",
        {
            "kind": "qa_z.executor_result_history",
            "schema_version": 1,
            "session_id": "session-one",
            "updated_at": "2026-04-16T00:00:00Z",
            "attempt_count": 2,
            "latest_attempt_id": "attempt-2",
            "attempts": [
                {
                    "attempt_id": "attempt-1",
                    "recorded_at": "2026-04-16T00:00:00Z",
                    "bridge_id": "bridge-one",
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
                    "ingest_artifact_path": ".qa-z/executor-results/attempt-1/ingest.json",
                    "ingest_report_path": ".qa-z/executor-results/attempt-1/ingest_report.md",
                    "freshness_status": "passed",
                    "freshness_reason": None,
                    "provenance_status": "passed",
                    "provenance_reason": None,
                },
                {
                    "attempt_id": "attempt-2",
                    "recorded_at": "2026-04-16T00:05:00Z",
                    "bridge_id": "bridge-one",
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
                    "ingest_artifact_path": ".qa-z/executor-results/attempt-2/ingest.json",
                    "ingest_report_path": ".qa-z/executor-results/attempt-2/ingest_report.md",
                    "freshness_status": "passed",
                    "freshness_reason": None,
                    "provenance_status": "passed",
                    "provenance_reason": None,
                },
            ],
        },
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_dry_run_repeated_partial_attention",
            "run": {
                "executor_result_dry_run": {
                    "session_id": "session-one",
                }
            },
            "expect_executor_dry_run": {
                "verdict": "attention_required",
                "verdict_reason": "manual_retry_review_required",
                "evaluated_attempt_count": 2,
                "latest_result_status": "partial",
                "history_signals": ["repeated_partial_attempts"],
                "attention_rule_ids": ["retry_boundary_is_manual"],
                "attention_rule_count": 1,
                "clear_rule_count": 6,
                "blocked_rule_count": 0,
                "expected_recommendation": "inspect repeated partial attempts before another retry",
                "schema_version": 1,
            },
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_dry_run"]["verdict"] == (
        "attention_required"
    )
    assert (
        fixture_result["actual"]["executor_dry_run"]["verdict_reason"]
        == "manual_retry_review_required"
    )
    assert fixture_result["actual"]["executor_dry_run"]["history_signals"] == [
        "repeated_partial_attempts"
    ]
    assert fixture_result["actual"]["executor_dry_run"]["attention_rule_count"] == 1
    assert fixture_result["categories"]["policy"] is True
