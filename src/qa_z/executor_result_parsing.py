"""Parsing helpers for executor-result schema validation."""

from __future__ import annotations

from typing import Any

from qa_z.artifacts import ArtifactLoadError


def required_string(data: dict[str, Any], field_name: str) -> str:
    """Return a required non-empty string field."""
    value = optional_string(data.get(field_name))
    if value is None:
        raise ArtifactLoadError(
            f"Executor result is missing required field: {field_name}"
        )
    return value


def optional_string(value: object) -> str | None:
    """Return a stripped string value or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def optional_int(value: object, *, field_name: str) -> int | None:
    """Return an integer when present and valid."""
    if value is None or value == "":
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise ArtifactLoadError(
            f"Executor result field {field_name} must be an integer."
        ) from exc


def string_list(value: object, *, field_name: str) -> list[str]:
    """Return a normalized list of strings."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise ArtifactLoadError(f"Executor result field {field_name} must be a list.")
    return [str(item).strip() for item in value if str(item).strip()]


def list_of_string_lists(value: object, *, field_name: str) -> list[list[str]]:
    """Return a normalized list of argv arrays."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise ArtifactLoadError(f"Executor result field {field_name} must be a list.")
    commands: list[list[str]] = []
    for item in value:
        commands.append(string_list(item, field_name=field_name))
    return commands
