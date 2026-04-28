"""Thin public wrappers for deep-runner runtime seams."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from qa_z.diffing.models import ChangeSet
from qa_z.runners.models import RunSummary

if TYPE_CHECKING:
    from qa_z.runners.deep import DeepRun, DeepRunResolution


def run_deep(
    *,
    root: Path,
    config: dict[str, Any],
    output_dir: Path | None = None,
    from_run: str | None = None,
    diff_path: Path | None = None,
    selection_mode: str = "full",
) -> DeepRun:
    """Run configured deep checks and return a normalized summary."""
    from qa_z.runners import deep as deep_module

    return deep_module._run_deep_impl(
        root=root,
        config=config,
        output_dir=output_dir,
        from_run=from_run,
        diff_path=diff_path,
        selection_mode=selection_mode,
    )


def resolve_deep_run_dir(
    *,
    root: Path,
    config: dict[str, Any],
    output_dir: Path | None,
    from_run: str | None,
) -> DeepRunResolution:
    """Resolve the run and deep artifact directories for a deep invocation."""
    from qa_z.runners import deep as deep_module

    return deep_module._resolve_deep_run_dir_impl(
        root=root,
        config=config,
        output_dir=output_dir,
        from_run=from_run,
    )


def resolve_deep_change_set(
    *,
    diff_path: Path | None,
    fast_summary: RunSummary | None,
) -> ChangeSet | None:
    """Resolve change metadata for deep selection."""
    from qa_z.runners import deep as deep_module

    return deep_module._resolve_deep_change_set_impl(
        diff_path=diff_path,
        fast_summary=fast_summary,
    )
