"""Tests for report signal-input helpers."""

from __future__ import annotations

from pathlib import Path

import qa_z.report_signals as report_signals_module
from tests.self_improvement_test_support import write_report


def test_discover_docs_drift_candidate_inputs_records_report_freshness_proof(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text(
        "\n".join(
            [
                "# QA-Z",
                "Use `self-inspect`, `select-next`, and `backlog` to inspect planner state.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "artifact-schema-v1.md").write_text(
        "# Artifact Schema\n\n## Self-Improvement\n\nDocumented.\n",
        encoding="utf-8",
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        Date: 2026-04-15
        Branch: `codex/report-freshness`
        Head: `1234567890abcdef1234567890abcdef12345678`

        The current-truth sync audit should stay in sync with the current command surface.
        """,
    )

    candidates = report_signals_module.discover_docs_drift_candidate_inputs(
        tmp_path,
        expected_command_doc_terms=("self-inspect", "select-next", "backlog"),
        report_evidence_files={
            "current_state": Path("docs/reports/current-state-analysis.md"),
        },
        generated_at="2026-04-15T09:00:00Z",
        current_branch="codex/report-freshness",
        current_head="1234567890abcdef1234567890abcdef12345678",
    )

    docs_candidate = next(
        item for item in candidates if item["id"] == "docs_drift-current_truth_sync"
    )

    assert docs_candidate["signals"] == ["roadmap_gap", "schema_doc_drift"]
    assert docs_candidate["evidence"] == [
        {
            "source": "current_state",
            "path": tmp_path / "docs" / "reports" / "current-state-analysis.md",
            "summary": "report calls out current-truth drift or an explicit sync audit",
        },
        {
            "source": "current_state",
            "path": tmp_path / "docs" / "reports" / "current-state-analysis.md",
            "summary": (
                "report freshness verified: date=2026-04-15; "
                "branch=codex/report-freshness; "
                "head=1234567890abcdef1234567890abcdef12345678"
            ),
        },
    ]


def test_discover_docs_drift_candidate_inputs_skips_future_dated_report_evidence(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text(
        "\n".join(
            [
                "# QA-Z",
                "Use `self-inspect`, `select-next`, and `backlog` to inspect planner state.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "artifact-schema-v1.md").write_text(
        "# Artifact Schema\n\n## Self-Improvement\n\nDocumented.\n",
        encoding="utf-8",
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        Date: 2026-04-16
        Branch: `codex/report-freshness`
        Head: `1234567890abcdef1234567890abcdef12345678`

        The current-truth sync audit should stay in sync with the current command surface.
        """,
    )

    candidates = report_signals_module.discover_docs_drift_candidate_inputs(
        tmp_path,
        expected_command_doc_terms=("self-inspect", "select-next", "backlog"),
        report_evidence_files={
            "current_state": Path("docs/reports/current-state-analysis.md"),
        },
        generated_at="2026-04-15T09:00:00Z",
        current_branch="codex/report-freshness",
        current_head="1234567890abcdef1234567890abcdef12345678",
    )

    assert [
        item["id"]
        for item in candidates
        if item["id"] == "docs_drift-current_truth_sync"
    ] == []
