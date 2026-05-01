"""UTF-8 stable git command helpers for lightweight repository signals."""

from __future__ import annotations

import subprocess
from pathlib import Path

from qa_z.runners.subprocess import utf8_subprocess_env

__all__ = ["git_stdout"]


def git_stdout(root: Path, args: list[str]) -> str | None:
    """Return stdout without trailing whitespace, or ``None`` on failure."""
    command = ["git", *args]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            env=utf8_subprocess_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    stdout = completed.stdout.rstrip()
    return stdout or None
