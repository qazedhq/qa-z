"""Shared subprocess environment helpers for deterministic QA-Z tooling."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Mapping

RUFF_CACHE_SUBDIR = "qa-z-ruff-cache"


def build_tool_subprocess_env(
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return a subprocess environment with stable encoding and safe tool caches."""
    env = dict(os.environ if base_env is None else base_env)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    cache_dir = env.get("RUFF_CACHE_DIR") or resolve_ruff_cache_dir(env)
    if cache_dir:
        env["RUFF_CACHE_DIR"] = cache_dir
    return env


def resolve_ruff_cache_dir(base_env: Mapping[str, str]) -> str | None:
    """Resolve a Ruff cache directory under a writable temp root when possible."""
    temp_root = (
        base_env.get("TEMP")
        or base_env.get("TMP")
        or base_env.get("LOCALAPPDATA")
        or base_env.get("USERPROFILE")
    )
    if not temp_root:
        return None
    if _looks_like_windows_path(temp_root):
        return str(PureWindowsPath(temp_root) / RUFF_CACHE_SUBDIR)
    if temp_root.startswith("/"):
        return str(PurePosixPath(temp_root) / RUFF_CACHE_SUBDIR)
    return str(Path(temp_root) / RUFF_CACHE_SUBDIR)


def _looks_like_windows_path(path: str) -> bool:
    return "\\" in path or (len(path) >= 2 and path[1] == ":")
