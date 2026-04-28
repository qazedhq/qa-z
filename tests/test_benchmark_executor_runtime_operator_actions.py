from __future__ import annotations

from pathlib import Path

from qa_z.benchmark import run_benchmark
from tests.benchmark_test_support import (
    write_config,
    write_contract,
    write_expected,
    write_json,
)


def test_run_benchmark_executes_mixed_partial_rejected_executor_dry_run_fixture(
    tmp_path: Path,
) -> None:
    fixture = (
        tmp_path / "fixtures" / "executor_dry_run_repeated_rejected_operator_actions"
    )
    repo = fixture / "repo"
    write_contract(
        repo,
        related_files=["src/app.py"],
        title="Dry-run repeated rejected operator benchmark fixture",
    )
    repo.joinpath("src").mkdir(parents=True, exist_ok=True)
    repo.joinpath("src", "app.py").write_text(
        "def answer() -> int:\n    return 42\n", encoding="utf-8"
    )
    write_config(repo, [])
    write_json(
        repo / ".qa-z" / "sessions" / "session-rejected" / "session.json",
        {
            "kind": "qa_z.repair_session",
            "schema_version": 1,
            "session_id": "session-rejected",
            "session_dir": ".qa-z/sessions/session-rejected",
            "baseline_run_dir": ".qa-z/runs/baseline",
            "baseline_fast_summary_path": ".qa-z/runs/baseline/fast/summary.json",
            "baseline_deep_summary_path": None,
            "handoff_dir": ".qa-z/sessions/session-rejected/handoff",
            "handoff_artifacts": {},
            "executor_guide_path": ".qa-z/sessions/session-rejected/executor_guide.md",
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
            "created_at": "2026-04-18T01:00:00Z",
            "updated_at": "2026-04-18T01:05:00Z",
        },
    )
    write_json(
        repo
        / ".qa-z"
        / "sessions"
        / "session-rejected"
        / "executor_results"
        / "history.json",
        {
            "kind": "qa_z.executor_result_history",
            "schema_version": 1,
            "session_id": "session-rejected",
            "updated_at": "2026-04-18T01:05:00Z",
            "attempt_count": 2,
            "latest_attempt_id": "attempt-rejected-2",
            "attempts": [
                {
                    "attempt_id": "attempt-rejected-1",
                    "recorded_at": "2026-04-18T01:00:00Z",
                    "bridge_id": "bridge-rejected",
                    "source_loop_id": None,
                    "result_status": "partial",
                    "ingest_status": "rejected_stale",
                    "verify_resume_status": "verify_blocked",
                    "verification_hint": "skip",
                    "verification_triggered": False,
                    "verification_verdict": None,
                    "validation_status": "failed",
                    "warning_ids": [],
                    "backlog_categories": [
                        "partial_completion_gap",
                        "evidence_freshness_gap",
                    ],
                    "changed_files_count": 1,
                    "notes_count": 1,
                    "attempt_path": ".qa-z/sessions/session-rejected/executor_results/attempts/attempt-rejected-1.json",
                    "ingest_artifact_path": ".qa-z/executor-results/attempt-rejected-1/ingest.json",
                    "ingest_report_path": ".qa-z/executor-results/attempt-rejected-1/ingest_report.md",
                    "freshness_status": "failed",
                    "freshness_reason": "result_too_old",
                    "provenance_status": "passed",
                    "provenance_reason": None,
                },
                {
                    "attempt_id": "attempt-rejected-2",
                    "recorded_at": "2026-04-18T01:05:00Z",
                    "bridge_id": "bridge-rejected-other",
                    "source_loop_id": None,
                    "result_status": "partial",
                    "ingest_status": "rejected_mismatch",
                    "verify_resume_status": "verify_blocked",
                    "verification_hint": "skip",
                    "verification_triggered": False,
                    "verification_verdict": None,
                    "validation_status": "failed",
                    "warning_ids": [],
                    "backlog_categories": [
                        "partial_completion_gap",
                        "provenance_gap",
                    ],
                    "changed_files_count": 1,
                    "notes_count": 1,
                    "attempt_path": ".qa-z/sessions/session-rejected/executor_results/attempts/attempt-rejected-2.json",
                    "ingest_artifact_path": ".qa-z/executor-results/attempt-rejected-2/ingest.json",
                    "ingest_report_path": ".qa-z/executor-results/attempt-rejected-2/ingest_report.md",
                    "freshness_status": "passed",
                    "freshness_reason": None,
                    "provenance_status": "failed",
                    "provenance_reason": "bridge_id_mismatch",
                },
            ],
        },
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_dry_run_repeated_rejected_operator_actions",
            "run": {
                "executor_result_dry_run": {
                    "session_id": "session-rejected",
                }
            },
            "expect_executor_dry_run": {
                "verdict": "attention_required",
                "verdict_reason": "manual_retry_review_required",
                "evaluated_attempt_count": 2,
                "latest_result_status": "partial",
                "latest_ingest_status": "rejected_mismatch",
                "history_signals": [
                    "repeated_partial_attempts",
                    "repeated_rejected_attempts",
                ],
                "attention_rule_ids": ["retry_boundary_is_manual"],
                "attention_rule_count": 1,
                "clear_rule_count": 6,
                "blocked_rule_count": 0,
                "operator_decision": "inspect_rejected_results",
                "recommended_action_ids": [
                    "inspect_rejected_results",
                    "inspect_partial_attempts",
                ],
                "expected_recommendation": "inspect repeated rejected executor results before another retry",
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
    assert fixture_result["actual"]["executor_dry_run"]["operator_decision"] == (
        "inspect_rejected_results"
    )
    assert fixture_result["actual"]["executor_dry_run"]["recommended_action_ids"] == [
        "inspect_rejected_results",
        "inspect_partial_attempts",
    ]
    assert fixture_result["actual"]["executor_dry_run"]["latest_result_status"] == (
        "partial"
    )
    assert fixture_result["categories"]["policy"] is True


def test_run_benchmark_executes_blocked_mixed_history_executor_dry_run_fixture(
    tmp_path: Path,
) -> None:
    summary = run_benchmark(
        fixtures_dir=Path("benchmarks") / "fixtures",
        results_dir=tmp_path / "results",
        fixture_names=["executor_dry_run_blocked_mixed_history_operator_actions"],
    )

    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_dry_run"]["operator_decision"] == (
        "resolve_verification_blockers"
    )
    assert fixture_result["actual"]["executor_dry_run"]["operator_summary"] == (
        "A completed executor attempt is still blocked by verification evidence; "
        "validation conflicts and retry pressure still need review before another "
        "retry."
    )
    assert fixture_result["actual"]["executor_dry_run"]["recommended_action_ids"] == [
        "resolve_verification_blockers",
        "review_validation_conflict",
        "inspect_partial_attempts",
    ]
    assert fixture_result["categories"]["policy"] is True
