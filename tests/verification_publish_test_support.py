"""Shared fixture writers for verification-publish tests."""

from __future__ import annotations

import json
from pathlib import Path


def executor_attempt(
    session_id: str,
    attempt_id: str,
    *,
    recorded_at: str,
    bridge_id: str,
    result_status: str = "partial",
    ingest_status: str = "accepted_partial",
    verify_resume_status: str = "verify_blocked",
    verification_hint: str = "skip",
    verification_triggered: bool = False,
    verification_verdict: str | None = None,
    validation_status: str = "failed",
    warning_ids: list[str] | None = None,
    backlog_categories: list[str] | None = None,
    changed_files_count: int = 1,
    notes_count: int = 1,
    freshness_status: str = "passed",
    freshness_reason: str | None = None,
    provenance_status: str = "passed",
    provenance_reason: str | None = None,
) -> dict[str, object]:
    """Build a compact executor-result history attempt payload."""
    return {
        "attempt_id": attempt_id,
        "recorded_at": recorded_at,
        "bridge_id": bridge_id,
        "source_loop_id": None,
        "result_status": result_status,
        "ingest_status": ingest_status,
        "verify_resume_status": verify_resume_status,
        "verification_hint": verification_hint,
        "verification_triggered": verification_triggered,
        "verification_verdict": verification_verdict,
        "validation_status": validation_status,
        "warning_ids": warning_ids or [],
        "backlog_categories": backlog_categories or ["partial_completion_gap"],
        "changed_files_count": changed_files_count,
        "notes_count": notes_count,
        "attempt_path": f".qa-z/sessions/{session_id}/executor_results/attempts/{attempt_id}.json",
        "ingest_artifact_path": "",
        "ingest_report_path": "",
        "freshness_status": freshness_status,
        "freshness_reason": freshness_reason,
        "provenance_status": provenance_status,
        "provenance_reason": provenance_reason,
    }


def write_verify_artifacts(
    root: Path,
    verify_dir: Path,
    *,
    verdict: str,
    baseline_run_id: str = "baseline",
    candidate_run_id: str = "candidate",
    blocking_after: int,
    resolved_count: int,
    regression_count: int,
    new_issue_count: int | None = None,
) -> None:
    """Write compact verification artifacts for publishing tests."""
    verify_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "kind": "qa_z.verify_summary",
        "schema_version": 1,
        "repair_improved": verdict == "improved",
        "verdict": verdict,
        "blocking_before": 3,
        "blocking_after": blocking_after,
        "resolved_count": resolved_count,
        "new_issue_count": (
            regression_count if new_issue_count is None else new_issue_count
        ),
        "regression_count": regression_count,
        "not_comparable_count": 0,
    }
    compare = {
        "kind": "qa_z.verify_compare",
        "schema_version": 1,
        "baseline_run_id": baseline_run_id,
        "candidate_run_id": candidate_run_id,
        "baseline": {"run_dir": f".qa-z/runs/{baseline_run_id}"},
        "candidate": {"run_dir": f".qa-z/runs/{candidate_run_id}"},
        "verdict": verdict,
        "summary": {
            "blocking_before": 3,
            "blocking_after": blocking_after,
            "resolved_count": resolved_count,
            "new_issue_count": (
                regression_count if new_issue_count is None else new_issue_count
            ),
            "regression_count": regression_count,
        },
    }
    (verify_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (verify_dir / "compare.json").write_text(
        json.dumps(compare, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (verify_dir / "report.md").write_text(
        "# QA-Z Repair Verification\n", encoding="utf-8"
    )


def write_executor_result_history(
    root: Path,
    session_id: str,
    *,
    attempts: list[dict[str, object]],
) -> None:
    """Write a compact session-local executor-result history artifact."""
    path = (
        root / ".qa-z" / "sessions" / session_id / "executor_results" / "history.json"
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


def write_validation_rejected_history(root: Path, session_id: str) -> None:
    """Write mixed validation-conflict plus repeated-rejected history."""
    write_executor_result_history(
        root,
        session_id,
        attempts=[
            executor_attempt(
                session_id,
                "attempt-rejected-1",
                recorded_at="2026-04-18T02:00:00Z",
                bridge_id="bridge-rejected",
                ingest_status="rejected_stale",
            ),
            executor_attempt(
                session_id,
                "attempt-rejected-2",
                recorded_at="2026-04-18T02:05:00Z",
                bridge_id="bridge-rejected",
                ingest_status="rejected_mismatch",
                warning_ids=["validation_summary_conflicts_with_results"],
            ),
        ],
    )


def write_session_manifest(
    root: Path,
    session_id: str,
    *,
    state: str = "completed",
) -> None:
    """Write a compact repair-session manifest for publish tests."""
    session_dir = root / ".qa-z" / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "kind": "qa_z.repair_session",
                "schema_version": 1,
                "session_id": session_id,
                "session_dir": f".qa-z/sessions/{session_id}",
                "state": state,
                "baseline_run_dir": ".qa-z/runs/baseline",
                "candidate_run_dir": ".qa-z/runs/candidate",
                "verify_dir": f".qa-z/sessions/{session_id}/verify",
                "verify_artifacts": {
                    "summary_json": (
                        f".qa-z/sessions/{session_id}/verify/summary.json"
                    ),
                    "compare_json": (
                        f".qa-z/sessions/{session_id}/verify/compare.json"
                    ),
                    "report_markdown": (
                        f".qa-z/sessions/{session_id}/verify/report.md"
                    ),
                },
                "outcome_path": f".qa-z/sessions/{session_id}/outcome.md",
                "summary_path": f".qa-z/sessions/{session_id}/summary.json",
                "handoff_dir": f".qa-z/sessions/{session_id}/handoff",
                "handoff_artifacts": {
                    "handoff_json": (
                        f".qa-z/sessions/{session_id}/handoff/handoff.json"
                    )
                },
                "executor_guide_path": (
                    f".qa-z/sessions/{session_id}/executor_guide.md"
                ),
                "created_at": "2026-04-14T00:00:00Z",
                "updated_at": "2026-04-14T00:00:01Z",
                "baseline_fast_summary_path": ".qa-z/runs/baseline/fast/summary.json",
                "provenance": {},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_session_summary(
    root: Path,
    session_id: str,
    *,
    verdict: str,
    blocking_before: int,
    blocking_after: int,
    resolved_count: int,
    remaining_issue_count: int,
    new_issue_count: int,
    regression_count: int,
    next_recommendation: str,
) -> None:
    """Write a compact repair-session summary for publish tests."""
    session_dir = root / ".qa-z" / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "summary.json").write_text(
        json.dumps(
            {
                "kind": "qa_z.repair_session_summary",
                "schema_version": 1,
                "session_id": session_id,
                "state": "completed",
                "baseline_run_dir": ".qa-z/runs/baseline",
                "candidate_run_dir": ".qa-z/runs/candidate",
                "verify_dir": f".qa-z/sessions/{session_id}/verify",
                "outcome_path": f".qa-z/sessions/{session_id}/outcome.md",
                "verdict": verdict,
                "blocking_before": blocking_before,
                "blocking_after": blocking_after,
                "resolved_count": resolved_count,
                "remaining_issue_count": remaining_issue_count,
                "new_issue_count": new_issue_count,
                "regression_count": regression_count,
                "not_comparable_count": 0,
                "next_recommendation": next_recommendation,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
