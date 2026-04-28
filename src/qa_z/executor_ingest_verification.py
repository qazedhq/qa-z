"""Shared verification flow for executor-result ingest and repair sessions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.executor_ingest_candidate import create_verify_candidate_run
from qa_z.executor_ingest_support import resolve_relative_path
from qa_z.repair_session import RepairSession, complete_session_verification
from qa_z.verification import (
    compare_verification_runs,
    load_verification_run,
    write_verification_artifacts,
)


def verify_repair_session(
    *,
    session: RepairSession,
    root: Path,
    config: dict[str, Any],
    candidate_run: str | None,
    rerun: bool,
    rerun_output_dir: str | None,
    strict_no_tests: bool,
    output_dir: str | None,
) -> tuple[RepairSession, dict[str, Any], Any]:
    """Run the shared repair-session verification flow."""
    baseline, _baseline_source = load_verification_run(
        root=root,
        config=config,
        from_run=session.baseline_run_dir,
    )
    if rerun:
        session_dir = resolve_relative_path(root, session.session_dir)
        resolved_rerun_output_dir = (
            resolve_relative_path(root, rerun_output_dir)
            if rerun_output_dir
            else session_dir / "candidate"
        )
        resolved_candidate_run = create_verify_candidate_run(
            root=root,
            config=config,
            rerun_output_dir=resolved_rerun_output_dir,
            strict_no_tests=strict_no_tests,
            baseline=baseline,
        )
    else:
        if candidate_run is None:
            raise ValueError("candidate_run is required when rerun is not requested.")
        resolved_candidate_run = candidate_run

    candidate, candidate_source = load_verification_run(
        root=root,
        config=config,
        from_run=resolved_candidate_run,
    )
    comparison = compare_verification_runs(baseline, candidate)
    resolved_output_dir = (
        resolve_relative_path(root, output_dir)
        if output_dir
        else resolve_relative_path(root, session.session_dir) / "verify"
    )
    paths = write_verification_artifacts(comparison, resolved_output_dir)
    updated, summary = complete_session_verification(
        session=session,
        root=root,
        candidate_run_dir=candidate_source.run_dir,
        verify_paths=paths,
        comparison=comparison,
    )
    return updated, summary, comparison
