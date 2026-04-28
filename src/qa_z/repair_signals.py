"""Verification and repair-session observation helpers for planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "discover_session_candidate_inputs",
    "discover_verification_candidate_inputs",
]

INCOMPLETE_SESSION_STATES = {
    "created",
    "handoff_ready",
    "waiting_for_external_repair",
    "candidate_generated",
    "verification_complete",
    "failed",
}
VERIFICATION_PROBLEM_VERDICTS = {"mixed", "regressed", "verification_failed"}


def discover_verification_candidate_inputs(root: Path) -> list[dict[str, Any]]:
    """Return normalized verification-regression packets from local artifacts."""
    qa_root = root / ".qa-z"
    if not qa_root.exists():
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(qa_root.rglob("verify/summary.json")):
        summary = read_json_object(path)
        if summary.get("kind") != "qa_z.verify_summary":
            continue
        verdict = str(summary.get("verdict") or "").strip()
        if verdict not in VERIFICATION_PROBLEM_VERDICTS:
            continue
        signals = ["regression_prevention"]
        if verdict == "mixed":
            signals.append("verify_mixed")
        else:
            signals.append("verify_regressed")
        candidates.append(
            {
                "run_id": path.parent.parent.name,
                "path": path,
                "verdict": verdict,
                "signals": signals,
                "summary": (
                    f"verdict={verdict}; "
                    f"regressions={int_value(summary.get('regression_count'))}; "
                    f"new_issues={int_value(summary.get('new_issue_count'))}"
                ),
                "impact": 5 if verdict == "regressed" else 4,
            }
        )
    return candidates


def discover_session_candidate_inputs(root: Path) -> list[dict[str, Any]]:
    """Return normalized incomplete repair-session packets from local artifacts."""
    sessions_root = root / ".qa-z" / "sessions"
    if not sessions_root.is_dir():
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(sessions_root.glob("*/session.json")):
        manifest = read_json_object(path)
        if manifest.get("kind") != "qa_z.repair_session":
            continue
        state = str(manifest.get("state") or "").strip()
        if state not in INCOMPLETE_SESSION_STATES:
            continue
        session_id = str(manifest.get("session_id") or path.parent.name).strip()
        candidates.append(
            {
                "session_id": session_id or path.parent.name,
                "path": path,
                "state": state,
            }
        )
    return candidates


def read_json_object(path: Path) -> dict[str, Any]:
    """Return a JSON object, or an empty dict when loading fails."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def int_value(value: object) -> int:
    """Return an integer value, or zero when absent or invalid."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
