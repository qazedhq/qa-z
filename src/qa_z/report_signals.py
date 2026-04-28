"""Report-document freshness and docs-drift observation helpers."""

from __future__ import annotations

from qa_z.docs_drift_signals import discover_docs_drift_candidate_inputs
from qa_z.report_freshness import (
    inspection_date,
    report_document_branch,
    report_document_date,
    report_document_head,
    report_freshness_summary,
    report_is_stale_for_inspection,
)
from qa_z.report_matching import matching_report_evidence, report_documents

__all__ = [
    "discover_docs_drift_candidate_inputs",
    "inspection_date",
    "matching_report_evidence",
    "report_document_branch",
    "report_document_date",
    "report_document_head",
    "report_documents",
    "report_freshness_summary",
    "report_is_stale_for_inspection",
]
