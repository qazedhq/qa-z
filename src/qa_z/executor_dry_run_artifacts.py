"""Path-aware executor dry-run artifact writers."""

from __future__ import annotations

from pathlib import Path


def write_dry_run_report(path: Path, text: str) -> None:
    """Write the dry-run Markdown report with path-aware failures."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise OSError(
            f"could not write executor-result dry-run report {path}: {exc}"
        ) from exc
