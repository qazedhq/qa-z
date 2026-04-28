"""History and contract follow-up candidate helpers for execution discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.backlog_core import (
    BacklogCandidate,
    format_report_evidence,
    unique_candidates,
)
from qa_z.executor_history_signals import discover_executor_history_candidate_inputs
from qa_z.report_matching import matching_report_evidence
from qa_z.self_improvement_constants import REPORT_EVIDENCE_FILES

__all__ = [
    "discover_executor_contract_candidates",
    "discover_executor_history_candidates",
]


def discover_executor_history_candidates(root: Path) -> list[Any]:
    """Create candidates from repeated executor-result attempt history patterns."""
    candidates: list[Any] = []
    for candidate_input in discover_executor_history_candidate_inputs(root):
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


def discover_executor_contract_candidates(root: Path) -> list[Any]:
    """Create candidates from executor contract and ingest/resume gaps."""
    evidence = executor_contract_gap_evidence(root)
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="workflow_gap-executor-contract-completeness",
            title="Audit executor contract completeness and resume coverage",
            category="workflow_gap",
            evidence=evidence,
            impact=3,
            likelihood=3,
            confidence=3,
            repair_cost=3,
            recommendation="audit_executor_contract",
            signals=["roadmap_gap", "service_readiness_gap"],
        )
    ]


def executor_contract_gap_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect report evidence for executor contract completeness work."""
    return format_report_evidence(
        root,
        matching_report_evidence(
            root,
            report_evidence_files=REPORT_EVIDENCE_FILES,
            sources={"current_state", "roadmap"},
            terms=(
                "executor result contract",
                "executor result ingest",
                "ingest and resume workflow",
                "ingest or resume layer",
            ),
            summary="report calls out executor result contract or ingest/resume completeness work",
        ),
    )
