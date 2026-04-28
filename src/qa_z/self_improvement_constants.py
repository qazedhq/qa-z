"""Shared constants for self-improvement workflows."""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "BACKLOG_KIND",
    "DIRTY_WORKTREE_MODIFIED_THRESHOLD",
    "DIRTY_WORKTREE_TOTAL_THRESHOLD",
    "EXPECTED_COMMAND_DOC_TERMS",
    "LOOP_HISTORY_KIND",
    "REPORT_EVIDENCE_FILES",
    "SELF_IMPROVEMENT_SCHEMA_VERSION",
    "SELF_INSPECTION_KIND",
]

SELF_INSPECTION_KIND = "qa_z.self_inspection"
BACKLOG_KIND = "qa_z.improvement_backlog"
LOOP_HISTORY_KIND = "qa_z.loop_history_entry"
SELF_IMPROVEMENT_SCHEMA_VERSION = 1

EXPECTED_COMMAND_DOC_TERMS = ("self-inspect", "select-next", "backlog")
REPORT_EVIDENCE_FILES = {
    "current_state": Path("docs/reports/current-state-analysis.md"),
    "roadmap": Path("docs/reports/next-improvement-roadmap.md"),
    "worktree_triage": Path("docs/reports/worktree-triage.md"),
    "worktree_commit_plan": Path("docs/reports/worktree-commit-plan.md"),
}

DIRTY_WORKTREE_MODIFIED_THRESHOLD = 10
DIRTY_WORKTREE_TOTAL_THRESHOLD = 30
