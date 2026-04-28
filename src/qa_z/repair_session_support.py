"""Support helpers for repair-session manifests and ids."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from qa_z.artifacts import format_path, resolve_path
from qa_z.executor_safety import write_executor_safety_artifacts

if TYPE_CHECKING:
    from qa_z.repair_session import RepairSession


def write_session_manifest(session: object, root: Path) -> Path:
    """Persist a repair-session manifest."""
    session_dir = resolve_path(root, str(getattr(session, "session_dir")))
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / "session.json"
    payload = getattr(session, "to_dict")()
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def ensure_session_safety_artifacts(session: object, root: Path):
    """Backfill session safety artifacts for manifests created before P9."""
    typed_session = cast("RepairSession", session)
    safety_artifacts = dict(getattr(session, "safety_artifacts", {}))
    json_path_text = safety_artifacts.get("policy_json")
    markdown_path_text = safety_artifacts.get("policy_markdown")
    if json_path_text and markdown_path_text:
        json_path = resolve_path(root, json_path_text)
        markdown_path = resolve_path(root, markdown_path_text)
        if json_path.is_file() and markdown_path.is_file():
            return session

    session_dir = resolve_path(root, str(getattr(session, "session_dir")))
    updated = replace(
        typed_session,
        safety_artifacts=write_executor_safety_artifacts(
            root=root, output_dir=session_dir
        ),
        updated_at=utc_now(),
    )
    write_session_manifest(updated, root)
    return updated


def handoff_artifact_paths(handoff_dir: Path, root: Path) -> dict[str, str]:
    """Return stable handoff artifact paths for the manifest."""
    return {
        "packet_json": format_path(handoff_dir / "packet.json", root),
        "prompt_markdown": format_path(handoff_dir / "prompt.md", root),
        "handoff_json": format_path(handoff_dir / "handoff.json", root),
        "codex_markdown": format_path(handoff_dir / "codex.md", root),
        "claude_markdown": format_path(handoff_dir / "claude.md", root),
    }


def resolve_session_dir(root: Path, session: str) -> Path:
    """Resolve a session id, directory, or session.json file."""
    path = Path(session).expanduser()
    if path.name == "session.json":
        path = path.parent
    elif not path.is_absolute() and len(path.parts) == 1:
        path = sessions_dir(root) / path
    elif not path.is_absolute():
        path = root / path
    return path.resolve()


def sessions_dir(root: Path) -> Path:
    """Return the default local repair-session directory."""
    return (root / ".qa-z" / "sessions").resolve()


def create_session_id() -> str:
    """Create a compact unique repair-session id."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{uuid4().hex[:6]}"


def normalize_session_id(session_id: str) -> str:
    """Validate a session id so it cannot escape the sessions directory."""
    normalized = session_id.strip()
    if not normalized or normalized in {".", ".."}:
        raise ValueError("Repair session id must not be empty.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", normalized):
        raise ValueError(
            "Repair session id may contain only letters, numbers, dot, underscore, and dash."
        )
    return normalized


def utc_now() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def optional_string(value: object) -> str | None:
    """Return a string value or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def string_mapping(value: object) -> dict[str, str]:
    """Return a string-to-string mapping."""
    if not isinstance(value, dict):
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if str(key).strip() and item is not None
    }
