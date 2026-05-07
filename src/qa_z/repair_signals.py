"""Verification and repair-session observation helpers for planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "discover_session_candidate_inputs",
    "discover_verification_candidate_inputs",
    "iter_live_verification_summary_paths",
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
    candidates: list[dict[str, Any]] = []
    for path in iter_live_verification_summary_paths(root):
        summary = read_json_object(path)
        if summary.get("kind") != "qa_z.verify_summary":
            continue
        verdict = str(summary.get("verdict") or "").strip()
        if verdict not in VERIFICATION_PROBLEM_VERDICTS:
            continue
        signals = ["regression_prevention"]
        if verdict == "mixed":
            signals.append("verify_mixed")
        elif verdict == "regressed":
            signals.append("verify_regressed")
        else:
            signals.append("verify_failed")
        summary_text = (
            f"verdict={verdict}; "
            f"regressions={int_value(summary.get('regression_count'))}; "
            f"new_issues={int_value(summary.get('new_issue_count'))}"
        )
        if verdict == "verification_failed":
            summary_text += (
                f"; not_comparable={int_value(summary.get('not_comparable_count'))}"
            )
        candidate = {
            "run_id": path.parent.parent.name,
            "path": path,
            "verdict": verdict,
            "signals": signals,
            "summary": summary_text,
            "impact": 5 if verdict == "regressed" else 4,
        }
        candidate.update(verification_compare_context(path.with_name("compare.json")))
        candidates.append(candidate)
    return candidates


def iter_live_verification_summary_paths(root: Path) -> list[Path]:
    """Return live run/session verify summaries, excluding generated scratch repos."""
    qa_root = root / ".qa-z"
    if not qa_root.exists():
        return []
    paths: list[Path] = []
    for artifact_root in (qa_root / "runs", qa_root / "sessions"):
        if not artifact_root.is_dir():
            continue
        paths.extend(sorted(artifact_root.glob("*/verify/summary.json")))
    return paths


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


def verification_compare_context(compare_path: Path) -> dict[str, Any]:
    """Return concise repair context from a verification compare artifact."""
    compare = read_json_object(compare_path)
    if compare.get("kind") != "qa_z.verify_compare":
        return {}
    context: dict[str, Any] = {"compare_path": compare_path}
    baseline_run = compare_run_path(compare, "baseline", "baseline_run_id")
    candidate_run = compare_run_path(compare, "candidate", "candidate_run_id")
    if baseline_run:
        context["baseline_run"] = baseline_run
    if candidate_run:
        context["candidate_run"] = candidate_run
    reason = not_comparable_reason(compare)
    if reason:
        context["not_comparable_reason"] = reason
    return context


def compare_run_path(compare: dict[str, Any], section: str, run_id_key: str) -> str:
    """Return a stable run path from compare run metadata."""
    run = compare.get(section)
    if isinstance(run, dict):
        run_dir = str(run.get("run_dir") or "").strip()
        if run_dir:
            return run_dir
    run_id = str(compare.get(run_id_key) or "").strip()
    if run_id:
        return f".qa-z/runs/{run_id}"
    return ""


def not_comparable_reason(compare: dict[str, Any]) -> str:
    """Return the first human-readable not-comparable reason from a compare."""
    for section in ("fast_checks", "deep_findings"):
        groups = compare.get(section)
        if not isinstance(groups, dict):
            continue
        findings = groups.get("skipped_or_not_comparable")
        if not isinstance(findings, list):
            continue
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            message = str(finding.get("message") or "").strip()
            if message:
                return " ".join(message.split())
    return ""


def int_value(value: object) -> int:
    """Return an integer value, or zero when absent or invalid."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
