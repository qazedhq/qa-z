"""Tests for repair-oriented execution candidate discovery."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.execution_repair_candidates import discover_verification_candidates


def write_json(path: Path, payload: dict[str, object]) -> None:
    """Write a deterministic JSON object fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_verification_failed_candidate_is_not_classified_as_regression(
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

    candidates = [
        candidate.to_dict() for candidate in discover_verification_candidates(tmp_path)
    ]

    assert candidates == [
        {
            "id": "verify_failure-candidate",
            "title": "Stabilize failed verification artifacts: candidate",
            "category": "verification_failure",
            "evidence": [
                {
                    "source": "verification",
                    "path": ".qa-z/runs/candidate/verify/summary.json",
                    "summary": (
                        "verdict=verification_failed; regressions=0; "
                        "new_issues=0; not_comparable=1"
                    ),
                }
            ],
            "impact": 4,
            "likelihood": 4,
            "confidence": 4,
            "repair_cost": 4,
            "priority_score": 61,
            "recommendation": "stabilize_verification_surface",
            "signals": ["regression_prevention", "verify_failed"],
            "recurrence_count": 1,
        }
    ]


def test_verification_candidate_preserves_compare_context_for_handoff(
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
            "baseline": {"run_dir": ".qa-z/runs/baseline"},
            "candidate": {"run_dir": ".qa-z/runs/candidate"},
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

    candidates = [
        candidate.to_dict() for candidate in discover_verification_candidates(tmp_path)
    ]

    assert candidates[0]["evidence"] == [
        {
            "source": "verification",
            "path": ".qa-z/runs/candidate/verify/summary.json",
            "summary": (
                "verdict=verification_failed; regressions=0; "
                "new_issues=0; not_comparable=1"
            ),
            "compare_path": ".qa-z/runs/candidate/verify/compare.json",
            "baseline_run": ".qa-z/runs/baseline",
            "candidate_run": ".qa-z/runs/candidate",
            "not_comparable_reason": (
                "Deep comparison requires both baseline and candidate "
                "deep/summary.json artifacts, or neither."
            ),
        }
    ]
