"""Shared refresh helpers for planning CLI commands."""

from __future__ import annotations

from pathlib import Path

from qa_z.self_improvement import run_self_inspection


def refresh_backlog_if_requested(*, root: Path, refresh: bool) -> None:
    """Refresh self-inspection artifacts before reading backlog state."""
    if refresh:
        run_self_inspection(root=root)
