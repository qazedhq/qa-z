"""JSON I/O helpers for executor-result artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a required JSON object artifact."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactSourceNotFound(f"Could not read artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(f"Artifact is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ArtifactLoadError(f"Artifact must contain an object: {path}")
    return data
