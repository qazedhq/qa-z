"""Path-aware benchmark artifact writing helpers."""

from __future__ import annotations

from pathlib import Path


def write_benchmark_summary(path: Path, text: str) -> None:
    """Write the benchmark summary JSON with path-aware failures."""
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise OSError(
            f"could not write benchmark summary artifact {path}: {exc}"
        ) from exc


def write_benchmark_report(path: Path, text: str) -> None:
    """Write the benchmark Markdown report with path-aware failures."""
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise OSError(
            f"could not write benchmark report artifact {path}: {exc}"
        ) from exc
