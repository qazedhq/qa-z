"""Support helpers for executor-bridge ids and artifacts."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactSourceNotFound


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def normalize_bridge_id(bridge_id: str) -> str:
    """Validate a bridge id so it cannot escape the executor directory."""
    normalized = bridge_id.strip()
    if not normalized or normalized in {".", ".."}:
        from qa_z.executor_bridge import ExecutorBridgeError

        raise ExecutorBridgeError("Bridge id must not be empty.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", normalized):
        from qa_z.executor_bridge import ExecutorBridgeError

        raise ExecutorBridgeError(
            "Bridge id may contain only letters, numbers, dot, underscore, and dash."
        )
    return normalized


def default_bridge_id(generated_at: str, loop_id: str | None, session_id: str) -> str:
    """Return a compact deterministic bridge id."""
    digits = re.sub(r"\D", "", generated_at)
    if len(digits) < 14:
        digits = re.sub(r"\D", "", utc_now()).ljust(14, "0")
    source = loop_id or session_id
    return f"bridge-{digits[:8]}-{digits[8:14]}-{slugify(source)}"


def slugify(value: str) -> str:
    """Create a stable id fragment."""
    slug = re.sub(r"[^A-Za-z0-9_]+", "-", value.strip().lower()).strip("-")
    return slug or "unknown"


def format_command(command: list[str]) -> str:
    """Render an argv command for Markdown."""
    return " ".join(command)


def resolve_bridge_dir(*, root: Path, output_dir: Path | None, bridge_id: str) -> Path:
    """Resolve the bridge output directory."""
    if output_dir is not None:
        path = output_dir.expanduser()
        if not path.is_absolute():
            path = root / path
        return path.resolve()
    return (root / ".qa-z" / "executor" / bridge_id).resolve()


def ensure_session_exists(root: Path, session_ref: str) -> None:
    """Raise source-not-found when a repair-session manifest is absent."""
    from qa_z.repair_session import resolve_session_dir

    manifest_path = resolve_session_dir(root, session_ref) / "session.json"
    if not manifest_path.is_file():
        raise ArtifactSourceNotFound(f"Repair session not found: {manifest_path}")


def utc_now() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
