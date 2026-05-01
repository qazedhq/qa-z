"""Context and path helpers for executor-bridge orchestration."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactSourceNotFound, format_path


def resolve_path(root: Path, value: str) -> Path:
    """Resolve a path relative to the repository root."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def path_is_within(root: Path, path: Path) -> bool:
    """Return whether path is inside the repository root."""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def context_source_label(root: Path, source_text: str, source_path: Path) -> str:
    """Return a stable manifest label for a context source path."""
    if path_is_within(root, source_path):
        return format_path(source_path, root)
    return source_text


def safe_context_input_name(name: str) -> str:
    """Return a filename-safe context input basename."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip()).strip("-")
    if not safe or safe in {".", ".."}:
        return "context"
    return safe


def bridge_action_context_inputs(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Return copied action-context input records from a bridge manifest."""
    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict):
        return []
    context = inputs.get("action_context")
    if not isinstance(context, list):
        return []
    records: list[dict[str, str]] = []
    for item in context:
        if not isinstance(item, dict):
            continue
        source_path = item.get("source_path")
        copied_path = item.get("copied_path")
        if isinstance(source_path, str) and isinstance(copied_path, str):
            records.append({"source_path": source_path, "copied_path": copied_path})
    return records


def bridge_missing_action_context_inputs(manifest: dict[str, Any]) -> list[str]:
    """Return missing action-context input paths from a bridge manifest."""
    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict):
        return []
    missing = inputs.get("action_context_missing")
    if not isinstance(missing, list):
        return []
    return [str(item) for item in missing if str(item).strip()]


def copy_input(*, root: Path, source: Path, target: Path) -> None:
    """Copy one required bridge input."""
    root = root.resolve()
    source = source.resolve()
    if not path_is_within(root, source):
        raise ArtifactSourceNotFound(
            f"Required bridge input is outside repository root: {source}"
        )
    if not source.is_file():
        raise ArtifactSourceNotFound(f"Required bridge input not found: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def copy_action_context_inputs(
    *, root: Path, inputs_dir: Path, action: dict[str, Any] | None
) -> tuple[list[dict[str, str]], list[str]]:
    """Copy optional prepared-action context inputs into the bridge package."""
    context_paths = action_context_paths(action)
    copied: list[dict[str, str]] = []
    missing: list[str] = []
    for index, source_text in enumerate(context_paths, start=1):
        source_path = resolve_path(root, source_text)
        source_label = context_source_label(root, source_text, source_path)
        if not path_is_within(root, source_path) or not source_path.is_file():
            missing.append(source_label)
            continue
        target = (
            inputs_dir
            / "context"
            / f"{index:03d}-{safe_context_input_name(source_path.name)}"
        )
        copy_input(root=root, source=source_path, target=target)
        copied.append(
            {
                "source_path": source_label,
                "copied_path": format_path(target, root),
            }
        )
    return copied, missing


def action_context_paths(action: dict[str, Any] | None) -> list[str]:
    """Return ordered non-empty context paths from a prepared action."""
    if not isinstance(action, dict):
        return []
    values = action.get("context_paths")
    if not isinstance(values, list):
        return []
    paths: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        path = value.strip()
        if not path or path in seen:
            continue
        seen.add(path)
        paths.append(path)
    return paths
