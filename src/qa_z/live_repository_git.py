"""Git-facing helpers for live repository signal collection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.git_runtime import git_stdout


def git_worktree_snapshot(root: Path) -> dict[str, Any]:
    """Return a lightweight git-status snapshot for the current repository."""
    output = git_stdout(root, ["status", "--short", "--untracked-files=all"])
    if output is None:
        return empty_live_repository_signals()
    return parse_git_status_output(output)


def git_current_branch(root: Path) -> str | None:
    """Return the current branch name when it can be resolved."""
    return git_stdout(root, ["rev-parse", "--abbrev-ref", "HEAD"])


def git_current_head(root: Path) -> str | None:
    """Return the current HEAD revision when it can be resolved."""
    return git_stdout(root, ["rev-parse", "HEAD"])


def parse_git_status_output(output: str) -> dict[str, Any]:
    """Parse `git status --short` output into stable count signals."""
    modified_paths: list[str] = []
    untracked_paths: list[str] = []
    staged_count = 0
    for line in output.splitlines():
        if len(line) < 3:
            continue
        status = line[:2]
        path_text = normalize_git_status_path(line[3:].strip())
        if not path_text:
            continue
        if status == "??":
            untracked_paths.append(path_text)
            continue
        if status == "!!":
            continue
        modified_paths.append(path_text)
        if status[0] not in {" ", "?", "!"}:
            staged_count += 1
    return {
        "modified_count": len(modified_paths),
        "untracked_count": len(untracked_paths),
        "staged_count": staged_count,
        "modified_paths": modified_paths,
        "untracked_paths": untracked_paths,
    }


def normalize_git_status_path(path_text: str) -> str:
    """Normalize one git-status path, preferring the destination on renames."""
    if " -> " in path_text:
        return path_text.split(" -> ", maxsplit=1)[1].strip()
    return path_text


def empty_live_repository_signals() -> dict[str, Any]:
    """Return an empty live repository signal snapshot."""
    return {
        "modified_count": 0,
        "untracked_count": 0,
        "staged_count": 0,
        "modified_paths": [],
        "untracked_paths": [],
    }
