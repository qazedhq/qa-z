"""Loop and JSON input helpers for executor-bridge packaging."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound


def load_loop_outcome(root: Path, from_loop: str) -> dict[str, Any]:
    """Load an autonomy outcome by loop id, loop directory, or outcome path."""
    path = resolve_loop_outcome_path(root, from_loop)
    data = read_json_object(path)
    if data.get("kind") != "qa_z.autonomy_outcome":
        raise ArtifactLoadError(f"Unsupported autonomy outcome artifact: {path}")
    return data


def resolve_loop_outcome_path(root: Path, from_loop: str) -> Path:
    """Resolve loop id, loop directory, or outcome artifact to outcome.json."""
    path = Path(from_loop).expanduser()
    if path.name == "outcome.json":
        candidate = path
    elif not path.is_absolute() and len(path.parts) == 1:
        candidate = root / ".qa-z" / "loops" / path / "outcome.json"
    else:
        candidate = path / "outcome.json"
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise ArtifactSourceNotFound(f"Autonomy outcome not found: {candidate}")
    return candidate


def repair_session_action(loop_outcome: dict[str, Any]) -> dict[str, Any]:
    """Return the first repair_session action from an autonomy outcome."""
    actions = loop_outcome.get("actions_prepared")
    if not isinstance(actions, list):
        actions = []
    for action in actions:
        if isinstance(action, dict) and action.get("type") == "repair_session":
            return action
    from qa_z.executor_bridge import ExecutorBridgeError

    raise ExecutorBridgeError("Loop outcome does not contain a repair_session action.")


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a required JSON object artifact."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactSourceNotFound(f"Could not read bridge input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(f"Bridge input is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ArtifactLoadError(f"Bridge input must contain an object: {path}")
    return data
