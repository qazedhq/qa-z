"""Candidate rerun and review-artifact helpers for executor-ingest flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    RunSource,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    write_latest_run_manifest,
)
from qa_z.config import get_nested
from qa_z.executor_ingest_support import format_relative_path, resolve_relative_path
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.reporters.review_packet import (
    render_run_review_packet,
    run_review_packet_json,
    write_review_artifacts,
)
from qa_z.reporters.run_summary import write_run_summary_artifacts
from qa_z.reporters.sarif import write_sarif_artifact
from qa_z.runners.deep import run_deep
from qa_z.runners.fast import run_fast
from qa_z.runners.models import RunSummary
from qa_z.verification_models import VerificationRun


def create_verify_candidate_run(
    *,
    root: Path,
    config: dict[str, Any],
    rerun_output_dir: Path,
    strict_no_tests: bool,
    baseline: VerificationRun,
) -> str:
    """Run fast and deep checks to create candidate evidence for verification."""
    contract_path = None
    if baseline.fast_summary.contract_path:
        candidate_contract = resolve_relative_path(
            root, baseline.fast_summary.contract_path
        )
        if candidate_contract.is_file():
            contract_path = candidate_contract

    fast_run = run_fast(
        root=root,
        config=config,
        contract_path=contract_path,
        output_dir=rerun_output_dir,
        strict_no_tests=strict_no_tests,
        selection_mode=resolve_fast_selection_mode(config),
    )
    artifact_dir = Path(fast_run.summary.artifact_dir or "")
    if not artifact_dir.is_absolute():
        artifact_dir = root / artifact_dir
    summary_path = write_run_summary_artifacts(fast_run.summary, artifact_dir)
    run_dir = artifact_dir.parent
    write_latest_run_manifest(root, config, run_dir)

    deep_run = run_deep(
        root=root,
        config=config,
        from_run=str(run_dir),
        selection_mode=resolve_deep_selection_mode(config),
    )
    write_run_summary_artifacts(deep_run.summary, deep_run.resolution.deep_dir)
    write_sarif_artifact(
        deep_run.summary, deep_run.resolution.deep_dir / "results.sarif"
    )
    candidate_source = RunSource(
        run_dir=run_dir,
        fast_dir=summary_path.parent,
        summary_path=summary_path,
    )
    write_verify_rerun_review_artifacts(
        root=root,
        config=config,
        run_source=candidate_source,
        summary=load_run_summary(summary_path),
        deep_summary=load_sibling_deep_summary(candidate_source) or deep_run.summary,
    )
    return format_relative_path(run_dir, root)


def write_verify_rerun_review_artifacts(
    *,
    root: Path,
    config: dict[str, Any],
    run_source: RunSource,
    summary: RunSummary,
    deep_summary: RunSummary,
) -> None:
    """Write run-aware review artifacts for a freshly rerun candidate."""
    contract_path = resolve_contract_source(root, config, summary=summary)
    contract = load_contract_context(contract_path, root)
    markdown = render_run_review_packet(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    json_text = run_review_packet_json(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    write_review_artifacts(markdown, json_text, run_source.run_dir / "review")


def resolve_fast_selection_mode(config: dict[str, Any]) -> str:
    """Resolve the configured fast selection mode."""
    configured = str(
        get_nested(config, "fast", "selection", "default_mode", default="full")
    )
    return configured if configured in {"full", "smart"} else "full"


def resolve_deep_selection_mode(config: dict[str, Any]) -> str:
    """Resolve the configured deep selection mode."""
    configured = str(
        get_nested(config, "deep", "selection", "default_mode", default="full")
    )
    return configured if configured in {"full", "smart"} else "full"
