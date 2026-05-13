"""Shared helpers for CLI command modules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from qa_z.config import ConfigError, load_config


def write_text_if_missing(path: Path, content: str) -> bool:
    """Create a text file only when it does not exist yet."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def format_relative_path(path: Path, root: Path) -> str:
    """Render a stable relative path for CLI output."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def resolve_cli_path(root: Path, value: str) -> Path:
    """Resolve a CLI path relative to the project root when it is not absolute."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def load_cli_config(
    root: Path,
    args: argparse.Namespace,
    command: str,
    *,
    json_error_kind: str | None = None,
    json_error_command: str | None = None,
    json_error_when: bool | None = None,
) -> dict[str, Any] | None:
    """Load config for a CLI command and print normalized errors."""
    config_path = resolve_cli_path(root, args.config) if args.config else None
    try:
        return load_config(root, config_path=config_path)
    except ConfigError as exc:
        message = f"qa-z {command}: configuration error: {exc}"
        json_mode = (
            getattr(args, "json", False) if json_error_when is None else json_error_when
        )
        if json_error_kind and json_mode:
            payload: dict[str, Any] = {
                "kind": json_error_kind,
                "error": "configuration_error",
                "exit_code": 2,
                "message": message,
            }
            if json_error_command:
                payload["command"] = json_error_command
            print(json.dumps(payload, sort_keys=True))
        else:
            print(message)
        return None
