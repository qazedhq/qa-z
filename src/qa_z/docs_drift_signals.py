"""Docs-drift candidate helpers derived from report signals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.report_matching import matching_report_evidence, read_text

__all__ = [
    "discover_docs_drift_candidate_inputs",
]


def discover_docs_drift_candidate_inputs(
    root: Path,
    *,
    expected_command_doc_terms: tuple[str, ...],
    report_evidence_files: dict[str, Path],
    generated_at: str | None = None,
    current_branch: str | None = None,
    current_head: str | None = None,
) -> list[dict[str, Any]]:
    """Return normalized docs/schema drift candidate packets."""
    candidates: list[dict[str, Any]] = []
    readme = root / "README.md"
    if readme.is_file():
        text = read_text(readme)
        missing = [term for term in expected_command_doc_terms if term not in text]
        if missing:
            candidates.append(
                {
                    "id": "docs_drift-self_improvement_commands",
                    "title": "Document self-improvement CLI commands",
                    "category": "docs_drift",
                    "evidence": [
                        {
                            "source": "docs",
                            "path": readme,
                            "summary": "missing terms: " + ", ".join(missing),
                        }
                    ],
                    "impact": 3,
                    "likelihood": 3,
                    "confidence": 3,
                    "repair_cost": 2,
                    "recommendation": "sync_contract_and_docs",
                    "signals": ["schema_doc_drift"],
                }
            )

    schema_doc = root / "docs" / "artifact-schema-v1.md"
    if schema_doc.is_file() and "Self-Improvement" not in read_text(schema_doc):
        candidates.append(
            {
                "id": "schema_drift-self_improvement_artifacts",
                "title": "Document self-improvement artifact schemas",
                "category": "schema_drift",
                "evidence": [
                    {
                        "source": "schema_doc",
                        "path": schema_doc,
                        "summary": "self-improvement artifacts are not documented",
                    }
                ],
                "impact": 3,
                "likelihood": 3,
                "confidence": 3,
                "repair_cost": 2,
                "recommendation": "sync_contract_and_docs",
                "signals": ["schema_doc_drift"],
            }
        )

    report_evidence = docs_drift_report_evidence(
        root,
        report_evidence_files=report_evidence_files,
        generated_at=generated_at,
        current_branch=current_branch,
        current_head=current_head,
    )
    if report_evidence:
        candidates.append(
            {
                "id": "docs_drift-current_truth_sync",
                "title": "Run a current-truth docs and schema sync audit",
                "category": "docs_drift",
                "evidence": report_evidence,
                "impact": 2,
                "likelihood": 3,
                "confidence": 4,
                "repair_cost": 2,
                "recommendation": "sync_contract_and_docs",
                "signals": ["roadmap_gap", "schema_doc_drift"],
            }
        )
    return candidates


def docs_drift_report_evidence(
    root: Path,
    *,
    report_evidence_files: dict[str, Path],
    generated_at: str | None = None,
    current_branch: str | None = None,
    current_head: str | None = None,
) -> list[dict[str, Any]]:
    """Collect current-truth drift and sync-audit evidence from reports."""
    return matching_report_evidence(
        root,
        report_evidence_files=report_evidence_files,
        sources={"current_state", "roadmap", "worktree_triage"},
        terms=(
            "current-truth drift risk",
            "current-truth sync audit",
            "current-truth audit",
            "stay in sync with the current command surface",
        ),
        summary="report calls out current-truth drift or an explicit sync audit",
        generated_at=generated_at,
        current_branch=current_branch,
        current_head=current_head,
    )
