"""Session-scoped executor-result attempt history helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactLoadError, format_path

EXECUTOR_RESULT_HISTORY_KIND = "qa_z.executor_result_history"
EXECUTOR_RESULT_DRY_RUN_KIND = "qa_z.executor_result_dry_run"
EXECUTOR_RESULT_HISTORY_SCHEMA_VERSION = 1


def executor_results_dir(session_dir: Path) -> Path:
    """Return the session-local executor-results directory."""
    return session_dir / "executor_results"


def executor_result_attempts_dir(session_dir: Path) -> Path:
    """Return the attempt artifact directory for a session."""
    return executor_results_dir(session_dir) / "attempts"


def executor_result_history_path(session_dir: Path) -> Path:
    """Return the session-local history artifact path."""
    return executor_results_dir(session_dir) / "history.json"


def executor_result_dry_run_summary_path(session_dir: Path) -> Path:
    """Return the session-local dry-run summary path."""
    return executor_results_dir(session_dir) / "dry_run_summary.json"


def executor_result_dry_run_report_path(session_dir: Path) -> Path:
    """Return the session-local dry-run report path."""
    return executor_results_dir(session_dir) / "dry_run_report.md"


def executor_result_history_payload(
    *, session_id: str, attempts: list[dict[str, Any]], updated_at: str
) -> dict[str, Any]:
    """Return the stable executor-result history artifact."""
    latest_attempt_id = None
    if attempts:
        latest_attempt_id = str(attempts[-1].get("attempt_id") or "").strip() or None
    return {
        "kind": EXECUTOR_RESULT_HISTORY_KIND,
        "schema_version": EXECUTOR_RESULT_HISTORY_SCHEMA_VERSION,
        "session_id": session_id,
        "updated_at": updated_at,
        "attempt_count": len(attempts),
        "latest_attempt_id": latest_attempt_id,
        "attempts": list(attempts),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write one deterministic JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def load_executor_result_history(
    path: Path, *, session_id: str | None = None
) -> dict[str, Any]:
    """Load a session-local history artifact or return an empty one when absent."""
    if not path.is_file():
        return executor_result_history_payload(
            session_id=session_id or path.parent.parent.name,
            attempts=[],
            updated_at="",
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ArtifactLoadError("Executor-result history must contain an object.")
    if data.get("kind") != EXECUTOR_RESULT_HISTORY_KIND:
        raise ArtifactLoadError("Executor-result history has an unsupported kind.")
    if int(data.get("schema_version", 0)) != EXECUTOR_RESULT_HISTORY_SCHEMA_VERSION:
        raise ArtifactLoadError(
            "Executor-result history has an unsupported schema version."
        )
    attempts = data.get("attempts")
    if not isinstance(attempts, list):
        data["attempts"] = []
    return data


def append_executor_result_attempt(
    *,
    root: Path,
    session_dir: Path,
    session_id: str,
    result_payload: dict[str, Any],
    ingest_summary: dict[str, Any],
) -> dict[str, Any]:
    """Append one readable executor-result attempt to session history."""
    history_path = executor_result_history_path(session_dir)
    history = load_executor_result_history(history_path, session_id=session_id)
    attempts = [item for item in history.get("attempts", []) if isinstance(item, dict)]
    used_ids = {
        str(item.get("attempt_id") or "").strip()
        for item in attempts
        if str(item.get("attempt_id") or "").strip()
    }
    attempt_id = allocate_attempt_id(
        base=str(ingest_summary.get("result_id") or "attempt"), used_ids=used_ids
    )
    attempt_path = executor_result_attempts_dir(session_dir) / f"{attempt_id}.json"
    write_json(attempt_path, result_payload)

    freshness = ingest_summary.get("freshness_check")
    provenance = ingest_summary.get("provenance_check")
    record = {
        "attempt_id": attempt_id,
        "recorded_at": (
            str(freshness.get("ingested_at") or "").strip()
            if isinstance(freshness, dict)
            else ""
        )
        or str(result_payload.get("created_at") or "").strip(),
        "bridge_id": str(ingest_summary.get("bridge_id") or "").strip(),
        "source_loop_id": ingest_summary.get("source_loop_id"),
        "result_status": str(ingest_summary.get("result_status") or "").strip(),
        "ingest_status": str(ingest_summary.get("ingest_status") or "").strip(),
        "verify_resume_status": str(
            ingest_summary.get("verify_resume_status") or ""
        ).strip(),
        "verification_hint": str(ingest_summary.get("verification_hint") or "").strip(),
        "verification_triggered": bool(
            ingest_summary.get("verification_triggered", False)
        ),
        "verification_verdict": ingest_summary.get("verification_verdict"),
        "validation_status": str(
            (
                (result_payload.get("validation") or {})
                if isinstance(result_payload.get("validation"), dict)
                else {}
            ).get("status")
            or ""
        ).strip(),
        "warning_ids": [
            str(item)
            for item in ingest_summary.get("warnings", [])
            if str(item).strip()
        ],
        "backlog_categories": [
            str(item.get("category"))
            for item in ingest_summary.get("backlog_implications", [])
            if isinstance(item, dict) and str(item.get("category") or "").strip()
        ],
        "changed_files_count": len(
            result_payload.get("changed_files", [])
            if isinstance(result_payload.get("changed_files"), list)
            else []
        ),
        "notes_count": len(
            result_payload.get("notes", [])
            if isinstance(result_payload.get("notes"), list)
            else []
        ),
        "attempt_path": format_path(attempt_path, root),
        "ingest_artifact_path": str(
            ingest_summary.get("ingest_artifact_path") or ""
        ).strip(),
        "ingest_report_path": str(
            ingest_summary.get("ingest_report_path") or ""
        ).strip(),
        "freshness_status": (
            str(freshness.get("status") or "").strip()
            if isinstance(freshness, dict)
            else ""
        ),
        "freshness_reason": (
            str(freshness.get("reason") or "").strip() or None
            if isinstance(freshness, dict)
            else None
        ),
        "provenance_status": (
            str(provenance.get("status") or "").strip()
            if isinstance(provenance, dict)
            else ""
        ),
        "provenance_reason": (
            str(provenance.get("reason") or "").strip() or None
            if isinstance(provenance, dict)
            else None
        ),
    }
    attempts.append(record)
    recorded_at = str(
        record.get("recorded_at") or result_payload.get("created_at") or ""
    )
    updated = executor_result_history_payload(
        session_id=session_id,
        attempts=attempts,
        updated_at=recorded_at,
    )
    write_json(history_path, updated)
    return record


def ensure_session_executor_history(
    *,
    root: Path,
    session_dir: Path,
    session_id: str,
    updated_at: str,
    latest_result_path: str | None,
) -> dict[str, Any]:
    """Return a session history, backfilling one legacy latest result when needed."""
    history_path = executor_result_history_path(session_dir)
    if history_path.is_file():
        return load_executor_result_history(history_path, session_id=session_id)

    result_payload: dict[str, Any] | None = None
    if latest_result_path:
        candidate = resolve_path(root, latest_result_path)
        if candidate.is_file():
            loaded = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                result_payload = loaded

    if result_payload is None:
        empty = executor_result_history_payload(
            session_id=session_id,
            attempts=[],
            updated_at=updated_at,
        )
        write_json(history_path, empty)
        return empty

    attempt_id = allocate_attempt_id(
        base=legacy_attempt_base(result_payload), used_ids=set()
    )
    attempt_path = executor_result_attempts_dir(session_dir) / f"{attempt_id}.json"
    write_json(attempt_path, result_payload)
    attempts: list[dict[str, Any]] = [
        {
            "attempt_id": attempt_id,
            "recorded_at": str(result_payload.get("created_at") or updated_at),
            "bridge_id": str(result_payload.get("bridge_id") or "").strip(),
            "source_loop_id": result_payload.get("source_loop_id"),
            "result_status": str(result_payload.get("status") or "").strip(),
            "ingest_status": "accepted_legacy",
            "verify_resume_status": "unknown",
            "verification_hint": str(
                result_payload.get("verification_hint") or ""
            ).strip(),
            "verification_triggered": False,
            "verification_verdict": None,
            "validation_status": str(
                (
                    (result_payload.get("validation") or {})
                    if isinstance(result_payload.get("validation"), dict)
                    else {}
                ).get("status")
                or ""
            ).strip(),
            "warning_ids": [],
            "backlog_categories": [],
            "changed_files_count": len(
                result_payload.get("changed_files", [])
                if isinstance(result_payload.get("changed_files"), list)
                else []
            ),
            "notes_count": len(
                result_payload.get("notes", [])
                if isinstance(result_payload.get("notes"), list)
                else []
            ),
            "attempt_path": format_path(attempt_path, root),
            "ingest_artifact_path": "",
            "ingest_report_path": "",
            "freshness_status": "",
            "freshness_reason": None,
            "provenance_status": "",
            "provenance_reason": None,
        }
    ]
    payload = executor_result_history_payload(
        session_id=session_id,
        attempts=attempts,
        updated_at=str(result_payload.get("created_at") or updated_at),
    )
    write_json(history_path, payload)
    return payload


def allocate_attempt_id(*, base: str, used_ids: set[str]) -> str:
    """Allocate a stable attempt id that does not collide within history."""
    candidate = base.strip() or "attempt"
    if candidate not in used_ids:
        return candidate
    index = 2
    while f"{candidate}-{index}" in used_ids:
        index += 1
    return f"{candidate}-{index}"


def legacy_attempt_base(result_payload: dict[str, Any]) -> str:
    """Build a stable attempt-id base for one backfilled legacy result."""
    bridge_id = str(result_payload.get("bridge_id") or "bridge").strip() or "bridge"
    created_at = str(result_payload.get("created_at") or "unknown")
    compact = "".join(
        character.lower() for character in created_at if character.isalnum()
    )
    return f"{slugify(bridge_id)}-{compact or 'unknown'}"


def slugify(value: str) -> str:
    """Create a stable identifier fragment."""
    cleaned = "".join(
        character.lower() if character.isalnum() else "-" for character in value.strip()
    )
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "unknown"


def resolve_path(root: Path, value: str) -> Path:
    """Resolve a path relative to the repository root."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()
