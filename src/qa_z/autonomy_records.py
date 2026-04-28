"""Artifact and history persistence helpers for autonomy workflows."""

from __future__ import annotations

import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "loops_root",
    "read_json_object",
    "record_executor_result",
    "write_outcome_artifact",
]


def update_history_entry(
    history_path: Path, *, loop_id: str, outcome: dict[str, Any]
) -> None:
    """Merge autonomy outcome fields into the existing selection history line."""
    if not history_path.is_file():
        return
    lines = history_path.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []
    updated = False
    for line in lines:
        entry = parse_json_line(line)
        if (
            not updated
            and entry.get("kind") == "qa_z.loop_history_entry"
            and entry.get("loop_id") == loop_id
        ):
            session_ids = outcome.get("created_session_ids") or []
            entry["resulting_session_id"] = session_ids[0] if session_ids else None
            entry["prepared_actions"] = [
                action.get("type") for action in outcome.get("actions_prepared", [])
            ]
            verification_evidence = outcome.get("verification_evidence", [])
            entry["verify_verdict"] = first_verify_verdict(verification_evidence)
            entry["outcome_path"] = outcome.get("artifacts", {}).get("outcome")
            entry["state"] = outcome.get("state")
            entry["state_transitions"] = outcome.get("state_transitions", [])
            entry["loop_elapsed_seconds"] = int_value(
                outcome.get("loop_elapsed_seconds")
            )
            entry["cumulative_elapsed_seconds"] = int_value(
                outcome.get("cumulative_elapsed_seconds")
            )
            entry["runtime_remaining_seconds"] = int_value(
                outcome.get("runtime_remaining_seconds")
            )
            entry["runtime_budget_met"] = bool(outcome.get("runtime_budget_met"))
            entry["backlog_open_count_before_inspection"] = int_value(
                outcome.get("backlog_open_count_before_inspection")
            )
            entry["backlog_open_count_after_inspection"] = int_value(
                outcome.get("backlog_open_count_after_inspection")
            )
            if outcome.get("selection_gap_reason"):
                entry["selection_gap_reason"] = str(outcome["selection_gap_reason"])
            if isinstance(outcome.get("loop_health"), dict):
                entry["loop_health"] = outcome["loop_health"]
            entry["next_recommendations"] = outcome.get("next_recommendations", [])
            updated_lines.append(json.dumps(entry, sort_keys=True))
            updated = True
        else:
            updated_lines.append(line)
    history_path.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")


def record_executor_result(
    history_path: Path,
    *,
    loop_id: str,
    result_status: str,
    ingest_status: str,
    verify_resume_status: str,
    result_path: str,
    validation_status: str,
    changed_files: list[str],
    verification_hint: str,
    verification_verdict: str | None,
    next_recommendation: str,
) -> None:
    """Merge executor-result fields into the matching loop history line."""
    if not history_path.is_file():
        return
    lines = history_path.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []
    updated = False
    for line in lines:
        entry = parse_json_line(line)
        if (
            not updated
            and entry.get("kind") == "qa_z.loop_history_entry"
            and entry.get("loop_id") == loop_id
        ):
            entry["executor_result_status"] = result_status
            entry["executor_ingest_status"] = ingest_status
            entry["executor_result_path"] = result_path
            entry["executor_validation_status"] = validation_status
            entry["executor_changed_files"] = list(changed_files)
            entry["executor_verification_hint"] = verification_hint
            entry["executor_verify_resume_status"] = verify_resume_status
            if verification_verdict:
                entry["verify_verdict"] = verification_verdict
            entry["next_recommendations"] = [next_recommendation]
            updated_lines.append(json.dumps(entry, sort_keys=True))
            updated = True
        else:
            updated_lines.append(line)
    history_path.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")


def first_verify_verdict(verification_evidence: object) -> str | None:
    """Return the first recorded verification verdict from outcome evidence."""
    if not isinstance(verification_evidence, list):
        return None
    for entry in verification_evidence:
        if isinstance(entry, dict) and entry.get("verdict"):
            return str(entry["verdict"])
    return None


def autonomy_loop_id(generated_at: str, index: int) -> str:
    """Create a stable loop id from a timestamp and loop ordinal."""
    digits = re.sub(r"\D", "", generated_at)
    if len(digits) < 14:
        digits = re.sub(r"\D", "", utc_now()).ljust(14, "0")
    return f"loop-{digits[:8]}-{digits[8:14]}-{index:02d}"


def loops_root(root: Path) -> Path:
    """Return the autonomy loops directory."""
    return root / ".qa-z" / "loops"


def with_runtime_fields(
    *,
    outcome: dict[str, Any],
    loop_started_at: str,
    loop_finished_at: str,
    loop_elapsed_seconds: int,
    cumulative_elapsed_seconds: int,
    runtime_target_seconds: int,
    min_loop_seconds: int,
    runtime_budget_met: bool,
) -> dict[str, Any]:
    """Attach runtime-budget accounting fields to one autonomy outcome."""
    enriched = dict(outcome)
    enriched["loop_started_at"] = loop_started_at
    enriched["loop_finished_at"] = loop_finished_at
    enriched["loop_elapsed_seconds"] = loop_elapsed_seconds
    enriched["cumulative_elapsed_seconds"] = cumulative_elapsed_seconds
    enriched["runtime_target_seconds"] = runtime_target_seconds
    enriched["runtime_remaining_seconds"] = max(
        runtime_target_seconds - cumulative_elapsed_seconds, 0
    )
    enriched["min_loop_seconds"] = min_loop_seconds
    enriched["runtime_budget_met"] = runtime_budget_met
    return enriched


def write_outcome_artifact(root: Path, outcome: dict[str, Any]) -> None:
    """Rewrite the loop and latest outcome artifacts after runtime enrichment."""
    outcome_path = outcome.get("artifacts", {}).get("outcome")
    if not outcome_path:
        return
    path = resolve_evidence_path(root, str(outcome_path))
    write_json(path, outcome)
    latest_dir = loops_root(root) / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    copy_artifact(path, latest_dir / "outcome.json")


def resolve_evidence_path(root: Path, value: str) -> Path:
    """Resolve an evidence path relative to the repository root."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def copy_artifact(source: Path, target: Path) -> None:
    """Copy an artifact to a loop directory, preserving exact bytes."""
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def read_json_object(path: Path) -> dict[str, Any]:
    """Read an optional JSON object."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a stable JSON object artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_json_line(line: str) -> dict[str, Any]:
    """Parse one JSONL line, returning an empty mapping on failure."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def utc_now() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def coerce_duration_seconds(value: object) -> int:
    """Return a non-negative integer number of seconds."""
    try:
        seconds = float(str(value))
    except (TypeError, ValueError):
        return 0
    if seconds <= 0:
        return 0
    return int(math.ceil(seconds))


def int_value(value: object) -> int:
    """Coerce numeric-looking values into deterministic integers."""
    if value is None or value is False:
        return 0
    if value is True:
        return 1
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        try:
            return int(float(text))
        except ValueError:
            return 0
    return 0
