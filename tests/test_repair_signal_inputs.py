"""Tests for repair-related self-improvement signal inputs."""

from __future__ import annotations

from pathlib import Path

import qa_z.repair_signals as repair_signals_module
from tests.self_improvement_test_support import write_json


def test_discover_verification_candidate_inputs_normalizes_verdict_text(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json",
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "verdict": " regressed ",
            "regression_count": "2",
            "new_issue_count": "1",
        },
    )

    candidates = repair_signals_module.discover_verification_candidate_inputs(tmp_path)

    assert candidates == [
        {
            "run_id": "candidate",
            "path": tmp_path
            / ".qa-z"
            / "runs"
            / "candidate"
            / "verify"
            / "summary.json",
            "verdict": "regressed",
            "signals": ["regression_prevention", "verify_regressed"],
            "summary": "verdict=regressed; regressions=2; new_issues=1",
            "impact": 5,
        }
    ]


def test_discover_verification_candidate_inputs_marks_verification_failed_without_regression(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json",
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "verdict": "verification_failed",
            "regression_count": 0,
            "new_issue_count": 0,
            "not_comparable_count": 1,
        },
    )

    candidates = repair_signals_module.discover_verification_candidate_inputs(tmp_path)

    assert candidates == [
        {
            "run_id": "candidate",
            "path": tmp_path
            / ".qa-z"
            / "runs"
            / "candidate"
            / "verify"
            / "summary.json",
            "verdict": "verification_failed",
            "signals": ["regression_prevention", "verify_failed"],
            "summary": (
                "verdict=verification_failed; regressions=0; "
                "new_issues=0; not_comparable=1"
            ),
            "impact": 4,
        }
    ]


def test_discover_verification_candidate_inputs_carries_compare_context(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json",
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "verdict": "verification_failed",
            "regression_count": 0,
            "new_issue_count": 0,
            "not_comparable_count": 1,
        },
    )
    write_json(
        tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "compare.json",
        {
            "kind": "qa_z.verify_compare",
            "schema_version": 1,
            "baseline_run_id": "baseline",
            "candidate_run_id": "candidate",
            "deep_findings": {
                "skipped_or_not_comparable": [
                    {
                        "message": (
                            "Deep comparison requires both baseline and candidate "
                            "deep/summary.json artifacts, or neither."
                        )
                    }
                ]
            },
        },
    )

    candidates = repair_signals_module.discover_verification_candidate_inputs(tmp_path)

    assert candidates == [
        {
            "run_id": "candidate",
            "path": tmp_path
            / ".qa-z"
            / "runs"
            / "candidate"
            / "verify"
            / "summary.json",
            "verdict": "verification_failed",
            "signals": ["regression_prevention", "verify_failed"],
            "summary": (
                "verdict=verification_failed; regressions=0; "
                "new_issues=0; not_comparable=1"
            ),
            "impact": 4,
            "compare_path": tmp_path
            / ".qa-z"
            / "runs"
            / "candidate"
            / "verify"
            / "compare.json",
            "baseline_run": ".qa-z/runs/baseline",
            "candidate_run": ".qa-z/runs/candidate",
            "not_comparable_reason": (
                "Deep comparison requires both baseline and candidate "
                "deep/summary.json artifacts, or neither."
            ),
        }
    ]


def test_discover_verification_candidate_inputs_ignores_generated_scratch_runs(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path
        / ".qa-z"
        / "tmp"
        / "benchmark-final"
        / "work"
        / "fixture"
        / "repo"
        / ".qa-z"
        / "runs"
        / "candidate"
        / "verify"
        / "summary.json",
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "verdict": "mixed",
            "regression_count": 1,
            "new_issue_count": 1,
        },
    )

    candidates = repair_signals_module.discover_verification_candidate_inputs(tmp_path)

    assert candidates == []


def test_discover_verification_candidate_inputs_keeps_session_verify_summaries(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "sessions" / "session-one" / "verify" / "summary.json",
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "verdict": "mixed",
            "regression_count": 1,
            "new_issue_count": 0,
        },
    )

    candidates = repair_signals_module.discover_verification_candidate_inputs(tmp_path)

    assert candidates == [
        {
            "run_id": "session-one",
            "path": tmp_path
            / ".qa-z"
            / "sessions"
            / "session-one"
            / "verify"
            / "summary.json",
            "verdict": "mixed",
            "signals": ["regression_prevention", "verify_mixed"],
            "summary": "verdict=mixed; regressions=1; new_issues=0",
            "impact": 4,
        }
    ]


def test_discover_session_candidate_inputs_normalizes_incomplete_state_text(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "sessions" / "session-one" / "session.json",
        {
            "kind": "qa_z.repair_session",
            "schema_version": 1,
            "state": " verification_complete ",
        },
    )

    candidates = repair_signals_module.discover_session_candidate_inputs(tmp_path)

    assert candidates == [
        {
            "session_id": "session-one",
            "path": tmp_path / ".qa-z" / "sessions" / "session-one" / "session.json",
            "state": "verification_complete",
        }
    ]
