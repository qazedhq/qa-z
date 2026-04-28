"""Loading helpers for verification artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import RunSource, format_path, load_run_summary, resolve_run_source
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.verification_models import VerificationRun


def load_verification_run(
    *, root: Path, config: dict[str, Any], from_run: str | None
) -> tuple[VerificationRun, RunSource]:
    source = resolve_run_source(root, config, from_run)
    fast_summary = load_run_summary(source.summary_path)
    if fast_summary.mode != "fast":
        raise ValueError(f"Expected a fast summary at {source.summary_path}.")
    deep_summary = load_sibling_deep_summary(source)
    return (
        VerificationRun(
            run_id=source.run_dir.name,
            run_dir=format_path(source.run_dir, root),
            fast_summary=fast_summary,
            deep_summary=deep_summary,
        ),
        source,
    )
