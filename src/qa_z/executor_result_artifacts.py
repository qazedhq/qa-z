"""Artifact helpers for executor-result contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound
from qa_z.executor_result_io import read_json_object, write_json
from qa_z.executor_result_models import (
    EXECUTOR_RESULT_KIND,
    EXECUTOR_RESULT_SCHEMA_VERSION,
    ExecutorResult,
    PLACEHOLDER_SUMMARY,
)


def executor_result_template(
    *,
    bridge_id: str,
    created_at: str,
    source_session_id: str,
    source_loop_id: str | None,
    validation_commands: list[list[str]],
    verification_hint: str = "rerun",
) -> dict[str, Any]:
    """Return a bridge-local template for the expected executor result."""
    return {
        "kind": EXECUTOR_RESULT_KIND,
        "schema_version": EXECUTOR_RESULT_SCHEMA_VERSION,
        "bridge_id": bridge_id,
        "source_session_id": source_session_id,
        "source_loop_id": source_loop_id,
        "created_at": created_at,
        "status": "partial",
        "summary": PLACEHOLDER_SUMMARY,
        "verification_hint": verification_hint,
        "candidate_run_dir": None,
        "changed_files": [],
        "validation": {
            "status": "not_run",
            "commands": [list(command) for command in validation_commands],
            "results": [],
        },
        "notes": [],
    }


def load_executor_result(path: Path) -> ExecutorResult:
    """Load an executor result artifact from disk."""
    data = read_json_object(path)
    return ExecutorResult.from_dict(data)


def resolve_bridge_manifest_path(root: Path, bridge_id: str) -> Path:
    """Resolve a bridge id to its bridge manifest path."""
    path = (root / ".qa-z" / "executor" / bridge_id / "bridge.json").resolve()
    if not path.is_file():
        raise ArtifactSourceNotFound(f"Executor bridge not found: {path}")
    return path


def load_bridge_manifest(root: Path, bridge_id: str) -> dict[str, Any]:
    """Load and validate a bridge manifest."""
    path = resolve_bridge_manifest_path(root, bridge_id)
    data = read_json_object(path)
    if data.get("kind") != "qa_z.executor_bridge":
        raise ArtifactLoadError(f"Unsupported executor bridge artifact: {path}")
    return data


def store_executor_result(
    root: Path, session_dir: Path, result: ExecutorResult
) -> Path:
    """Persist an ingested executor result under its owning session."""
    path = session_dir / "executor_result.json"
    write_json(path, result.to_dict())
    return path
