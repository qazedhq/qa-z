"""Terminal rendering for QA-Z guard."""

from __future__ import annotations

from qa_z.guard.verdict import GuardVerdict


def render_guard_stdout(verdict: GuardVerdict) -> str:
    """Render a concise human verdict."""
    risk_categories = verdict.risk.get("categories", [])
    changed_count = len(verdict.risk.get("changed_files", []))
    lines = [
        "QA-Z Guard",
        "",
        "Change:",
        f"  {changed_count} files changed",
        f"  Risk: {', '.join(risk_categories) if risk_categories else 'none detected'}",
        "",
        "Checks:",
        f"  fast: {verdict.fast.get('status')}",
        f"  deep: {verdict.deep.get('status', 'not_run')}",
        "",
        "Verdict:",
        f"  {human_status(verdict.status)}",
    ]
    if verdict.repair.get("written"):
        lines.extend(
            ["", "Next:", "  qa-z repair-prompt --from-run latest --adapter codex"]
        )
    return "\n".join(lines).rstrip() + "\n"


def human_status(status: str) -> str:
    mapping = {
        "merge_ok": "MERGE OK",
        "do_not_merge": "DO NOT MERGE YET",
        "needs_review": "NEEDS REVIEW",
        "error": "ERROR",
    }
    return mapping.get(status, status.upper())
