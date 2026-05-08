"""Report-evidence helpers for worktree-related self-improvement discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.backlog_core import format_report_evidence
from qa_z.report_freshness import (
    report_freshness_summary,
    report_is_stale_for_inspection,
)
from qa_z.report_matching import matching_report_evidence, report_documents
from qa_z.self_improvement_constants import REPORT_EVIDENCE_FILES


def integration_gap_evidence(
    root: Path,
    *,
    generated_at: str | None = None,
    current_branch: str | None = None,
    current_head: str | None = None,
) -> list[dict[str, Any]]:
    """Collect report evidence for worktree integration risk."""
    return format_report_evidence(
        root,
        matching_report_evidence(
            root,
            report_evidence_files=REPORT_EVIDENCE_FILES,
            sources={"worktree_triage", "worktree_commit_plan", "current_state"},
            terms=(
                "dirty worktree",
                "commit split",
                "commit plan",
                "integration caveats",
                "worktree triage",
            ),
            summary="report calls out worktree integration or commit-split risk",
            generated_at=generated_at,
            current_branch=current_branch,
            current_head=current_head,
        ),
    )


def worktree_commit_plan_json_evidence(
    root: Path, *, current_head: str | None = None
) -> list[dict[str, Any]]:
    """Return compact evidence from the latest strict commit-plan JSON artifact."""
    path = root / ".qa-z" / "tmp" / "worktree-commit-plan.json"
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    if not isinstance(payload, dict):
        return []
    repository = payload.get("repository")
    if current_head and isinstance(repository, dict):
        artifact_head = str(repository.get("head") or "").strip()
        if artifact_head and artifact_head != current_head:
            return []
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    attention_reasons = [
        str(reason)
        for reason in payload.get("attention_reasons", [])
        if isinstance(reason, str) and reason.strip()
    ]
    attention = ", ".join(attention_reasons) if attention_reasons else "none"
    evidence: dict[str, Any] = {
        "source": "worktree_commit_plan_json",
        "path": format_path(path, root),
        "summary": (
            f"strict commit-plan status={payload.get('status', 'unknown')}; "
            f"attention={attention}; "
            f"unassigned={int_value(summary.get('unassigned_source_path_count'))}; "
            f"cross_cutting={int_value(summary.get('cross_cutting_count'))}; "
            f"patch_add_groups={int_value(summary.get('cross_cutting_group_count'))}; "
            f"shared_patch_add={int_value(summary.get('shared_patch_add_count'))}; "
            f"generated={int_value(summary.get('generated_artifact_count'))}"
        ),
    }
    patch_command_texts = cross_cutting_patch_command_texts(payload)
    if patch_command_texts:
        evidence["patch_command_texts"] = patch_command_texts
    return [evidence]


def cross_cutting_patch_command_texts(payload: dict[str, Any]) -> list[str]:
    """Return scoped patch-add commands from strict worktree plan evidence."""
    groups = payload.get("cross_cutting_groups")
    if not isinstance(groups, list):
        return []
    commands: list[str] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        command = str(group.get("patch_command_text") or "").strip()
        if command:
            commands.append(command)
    return commands


def int_value(value: object) -> int:
    """Return a safe integer for compact report evidence fields."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def deferred_cleanup_evidence(
    root: Path,
    *,
    generated_at: str | None = None,
    current_branch: str | None = None,
    current_head: str | None = None,
) -> list[dict[str, Any]]:
    """Collect report evidence for deferred cleanup work."""
    return format_report_evidence(
        root,
        matching_report_evidence(
            root,
            report_evidence_files=REPORT_EVIDENCE_FILES,
            sources={"worktree_triage", "current_state"},
            terms=(
                "deferred cleanup",
                "defer or ignore",
                "generated runtime artifacts",
                "generated benchmark outputs",
                "deferred generated artifacts",
            ),
            exclude_terms=(
                "report-only evidence is not enough",
                "not enough for those candidates",
                "not enough to reopen",
                "not enough to reseed",
                "deferred generated cleanup action packets now",
                "deferred cleanup action hints name",
                "deferred cleanup compact evidence",
            ),
            summary="report calls out deferred cleanup work or generated outputs to isolate",
            generated_at=generated_at,
            current_branch=current_branch,
            current_head=current_head,
            require_head_when_available=True,
        ),
    )


def commit_isolation_evidence(
    root: Path,
    *,
    generated_at: str | None = None,
    current_branch: str | None = None,
    current_head: str | None = None,
) -> list[dict[str, Any]]:
    """Collect report evidence for commit-order isolation risk."""
    matches: list[dict[str, Any]] = []
    lowered_terms = tuple(
        term.lower()
        for term in (
            "commit order dependency",
            "corrected commit sequence",
            "foundation-before-benchmark",
            "commit split",
            "git add -p",
            "alpha closure readiness snapshot",
        )
    )
    for source, path, text in report_documents(root, REPORT_EVIDENCE_FILES):
        if source not in {"worktree_commit_plan", "current_state"}:
            continue
        if report_is_stale_for_inspection(
            text,
            generated_at,
            current_branch=current_branch,
            current_head=current_head,
            require_head_when_available=True,
        ):
            continue
        lowered = text.lower()
        if any(term in lowered for term in lowered_terms):
            summary = closure_aware_commit_isolation_summary(path, text)
            matches.append(
                {
                    "source": source,
                    "path": format_path(path, root),
                    "summary": (
                        summary
                        or "report calls out commit-order dependency or commit-isolation work"
                    ),
                }
            )
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
                        "path": format_path(path, root),
                        "summary": freshness_summary,
                    }
                )
    return matches


def alpha_closure_snapshot_is_present(text: str) -> bool:
    """Return whether a report pins the alpha closure gate snapshot."""
    lowered = text.lower()
    return all(
        term in lowered
        for term in (
            "alpha closure readiness snapshot",
            "latest full local gate pass",
            "split the worktree by this commit plan",
        )
    )


def closure_aware_commit_isolation_summary(path: Path, text: str) -> str | None:
    """Return a precise commit-isolation summary for closure-ready reports."""
    if path.name == "worktree-commit-plan.md" and alpha_closure_snapshot_is_present(
        text
    ):
        return (
            "alpha closure readiness snapshot pins full gate pass and "
            "commit-split action"
        )
    return None


def artifact_hygiene_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect report evidence for runtime/source artifact separation gaps."""
    return format_report_evidence(
        root,
        matching_report_evidence(
            root,
            report_evidence_files=REPORT_EVIDENCE_FILES,
            sources={"worktree_triage", "current_state", "roadmap"},
            terms=(
                "runtime artifacts",
                "generated artifact policy",
                "source-like areas",
                "tracked vs generated",
                "generated benchmark outputs",
            ),
            summary="report calls out runtime or generated artifacts mixed with source evidence",
        ),
    )


def evidence_freshness_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect report evidence for generated-versus-frozen evidence ambiguity."""
    return format_report_evidence(
        root,
        matching_report_evidence(
            root,
            report_evidence_files=REPORT_EVIDENCE_FILES,
            sources={"current_state", "worktree_triage", "roadmap"},
            terms=(
                "frozen evidence",
                "runtime result",
                "generated versus frozen",
                "generated vs frozen",
                "benchmark outputs",
            ),
            summary="report calls out ambiguity between runtime results and frozen evidence",
        ),
    )
