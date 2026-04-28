"""Generic report document loading and term-matching helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.report_freshness import (
    report_freshness_summary,
    report_is_stale_for_inspection,
)

__all__ = [
    "matching_report_evidence",
    "read_text",
    "report_documents",
]


def matching_report_evidence(
    root: Path,
    *,
    report_evidence_files: dict[str, Path],
    sources: set[str],
    terms: tuple[str, ...],
    summary: str,
    exclude_terms: tuple[str, ...] = (),
    generated_at: str | None = None,
    current_branch: str | None = None,
    current_head: str | None = None,
    require_head_when_available: bool = False,
) -> list[dict[str, Any]]:
    """Collect report evidence that matches any of the given terms."""
    matches: list[dict[str, Any]] = []
    lowered_terms = tuple(term.lower() for term in terms)
    lowered_exclude_terms = tuple(term.lower() for term in exclude_terms)
    for source, path, text in report_documents(root, report_evidence_files):
        if source not in sources:
            continue
        if report_is_stale_for_inspection(
            text,
            generated_at,
            current_branch=current_branch,
            current_head=current_head,
            require_head_when_available=require_head_when_available,
        ):
            continue
        lowered = text.lower()
        if lowered_exclude_terms and any(
            term in lowered for term in lowered_exclude_terms
        ):
            continue
        if any(term in lowered for term in lowered_terms):
            matches.append({"source": source, "path": path, "summary": summary})
            freshness_summary = report_freshness_summary(
                text,
                generated_at,
                current_branch=current_branch,
                current_head=current_head,
            )
            if freshness_summary:
                matches.append(
                    {
                        "source": source,
                        "path": path,
                        "summary": freshness_summary,
                    }
                )
    return matches


def report_documents(
    root: Path, report_evidence_files: dict[str, Path]
) -> list[tuple[str, Path, str]]:
    """Return known report documents that can seed structural candidates."""
    documents: list[tuple[str, Path, str]] = []
    for source, relative_path in report_evidence_files.items():
        path = root / relative_path
        text = read_text(path)
        if text:
            documents.append((source, path, text))
    return documents


def read_text(path: Path) -> str:
    """Read text for optional report checks."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
