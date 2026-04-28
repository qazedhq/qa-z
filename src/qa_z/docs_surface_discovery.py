"""Docs-drift discovery helpers for self-improvement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.backlog_core import BacklogCandidate, unique_candidates
from qa_z.docs_drift_signals import discover_docs_drift_candidate_inputs
from qa_z.self_improvement_constants import (
    EXPECTED_COMMAND_DOC_TERMS,
    REPORT_EVIDENCE_FILES,
)

__all__ = [
    "discover_docs_drift_candidates",
]


def discover_docs_drift_candidates(root: Path) -> list[Any]:
    """Create candidates when public docs omit the self-improvement surface."""
    candidates: list[Any] = []
    for candidate_input in discover_docs_drift_candidate_inputs(
        root,
        expected_command_doc_terms=EXPECTED_COMMAND_DOC_TERMS,
        report_evidence_files=REPORT_EVIDENCE_FILES,
    ):
        evidence = [
            {
                "source": str(item["source"]),
                "path": format_path(item["path"], root),
                "summary": str(item["summary"]),
            }
            for item in candidate_input["evidence"]
        ]
        candidates.append(
            BacklogCandidate(
                id=str(candidate_input["id"]),
                title=str(candidate_input["title"]),
                category=str(candidate_input["category"]),
                evidence=evidence,
                impact=int(candidate_input["impact"]),
                likelihood=int(candidate_input["likelihood"]),
                confidence=int(candidate_input["confidence"]),
                repair_cost=int(candidate_input["repair_cost"]),
                recommendation=str(candidate_input["recommendation"]),
                signals=list(candidate_input["signals"]),
            )
        )
    return unique_candidates(candidates)
