"""Tests for artifact-consistency discovery signal hygiene."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.artifact_consistency_discovery import (
    discover_artifact_consistency_candidates,
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    """Write a deterministic JSON object fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_artifact_consistency_discovery_ignores_generated_scratch_runs(
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
        },
    )

    candidates = discover_artifact_consistency_candidates(tmp_path)

    assert candidates == []


def test_artifact_consistency_discovery_keeps_live_run_companion_gaps(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json",
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "verdict": "mixed",
        },
    )

    candidates = [
        candidate.to_dict()
        for candidate in discover_artifact_consistency_candidates(tmp_path)
    ]

    assert candidates == [
        {
            "id": "artifact_consistency-candidate",
            "title": "Restore verification companion artifacts for candidate",
            "category": "artifact_consistency",
            "evidence": [
                {
                    "source": "verification",
                    "path": ".qa-z/runs/candidate/verify/summary.json",
                    "summary": "missing companions: compare.json, report.md",
                }
            ],
            "impact": 3,
            "likelihood": 3,
            "confidence": 4,
            "repair_cost": 2,
            "priority_score": 34,
            "recommendation": "sync_contract_and_docs",
            "signals": [],
            "recurrence_count": 1,
        }
    ]
