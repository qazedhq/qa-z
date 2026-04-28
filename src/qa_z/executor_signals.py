"""Executor-result and ingest observation helpers for planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "discover_executor_ingest_candidate_inputs",
    "discover_executor_result_candidate_inputs",
]


def discover_executor_result_candidate_inputs(root: Path) -> list[dict[str, Any]]:
    """Return normalized executor-result follow-up packets from session manifests."""
    sessions_root = root / ".qa-z" / "sessions"
    if not sessions_root.is_dir():
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(sessions_root.glob("*/session.json")):
        manifest = read_json_object(path)
        if manifest.get("kind") != "qa_z.repair_session":
            continue
        session_id = str(manifest.get("session_id") or path.parent.name).strip()
        result_status = str(manifest.get("executor_result_status") or "").strip()
        if result_status not in {"partial", "failed", "no_op"}:
            continue
        result_path = resolve_optional_artifact_path(
            root, str(manifest.get("executor_result_path") or "")
        )
        result = (
            read_json_object(result_path)
            if result_path is not None and result_path.is_file()
            else {}
        )
        validation = result.get("validation")
        validation_status = (
            str(validation.get("status") or "").strip()
            if isinstance(validation, dict)
            else str(manifest.get("executor_result_validation_status") or "").strip()
        )
        candidates.append(
            {
                "session_id": session_id or path.parent.name,
                "path": result_path if result_path is not None and result else path,
                "result_status": result_status,
                "validation_status": validation_status,
                "verification_hint": (
                    str(result.get("verification_hint") or "").strip() or "skip"
                ),
                "recommendation": recommendation_for_executor_result(result_status),
                "title": title_for_executor_result(
                    result_status, session_id or path.parent.name
                ),
                "signals": executor_result_signals(
                    result_status, validation_status=validation_status
                ),
                "impact": 4 if result_status in {"failed", "no_op"} else 3,
                "confidence": 4 if validation_status else 3,
            }
        )
    return candidates


def discover_executor_ingest_candidate_inputs(root: Path) -> list[dict[str, Any]]:
    """Return normalized backlog implication packets from executor ingest artifacts."""
    ingest_root = root / ".qa-z" / "executor-results"
    if not ingest_root.is_dir():
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(ingest_root.glob("*/ingest.json")):
        ingest = read_json_object(path)
        if ingest.get("kind") != "qa_z.executor_result_ingest":
            continue
        implications = ingest.get("backlog_implications")
        if not isinstance(implications, list):
            continue
        for implication in implications:
            if not isinstance(implication, dict):
                continue
            candidate_id = str(implication.get("id") or "").strip()
            category = str(implication.get("category") or "").strip()
            recommendation = str(implication.get("recommendation") or "").strip()
            title = str(implication.get("title") or "").strip()
            if not candidate_id or not category or not recommendation or not title:
                continue
            candidates.append(
                {
                    "id": candidate_id,
                    "title": title,
                    "category": category,
                    "path": path,
                    "summary": str(
                        implication.get("summary")
                        or ingest.get("ingest_status")
                        or "executor ingest implication"
                    ).strip(),
                    "impact": max(int_value(implication.get("impact")), 1),
                    "likelihood": max(int_value(implication.get("likelihood")), 1),
                    "confidence": max(int_value(implication.get("confidence")), 1),
                    "repair_cost": max(int_value(implication.get("repair_cost")), 1),
                    "recommendation": recommendation,
                    "signals": implication_signals(implication.get("signals")),
                }
            )
    return candidates


def executor_result_signals(result_status: str, *, validation_status: str) -> list[str]:
    """Return stable signal tags for one executor-result follow-up packet."""
    signals = [f"executor_result_{result_status}"]
    if validation_status == "failed":
        signals.append("executor_validation_failed")
    return signals


def recommendation_for_executor_result(result_status: str) -> str:
    """Return the deterministic next action for an executor-result status."""
    if result_status == "partial":
        return "resume_executor_repair"
    if result_status == "failed":
        return "triage_executor_failure"
    return "inspect_executor_no_op"


def title_for_executor_result(result_status: str, session_id: str) -> str:
    """Return a human-readable backlog title for executor-result follow-up."""
    if result_status == "partial":
        return f"Resume partial executor result: {session_id}"
    if result_status == "failed":
        return f"Triage failed executor result: {session_id}"
    return f"Inspect executor no-op result: {session_id}"


def implication_signals(value: object) -> list[str]:
    """Return stable implication signals from a JSON-safe value."""
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def resolve_optional_artifact_path(root: Path, value: str) -> Path | None:
    """Resolve an optional artifact path relative to the repository root."""
    text = value.strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


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
