"""Fixture execution helpers for benchmark runs."""

from __future__ import annotations
from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    resolve_run_source,
    write_latest_run_manifest,
)
from qa_z.repair_handoff import build_repair_handoff, write_repair_handoff_artifact
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.reporters.repair_prompt import build_repair_packet, write_repair_artifacts
from qa_z.reporters.run_summary import write_run_summary_artifacts
from qa_z.reporters.sarif import write_sarif_artifact
from qa_z.runners.deep import run_deep
from qa_z.runners.fast import run_fast
from qa_z.verification import (
    compare_verification_runs,
    load_verification_run,
    write_verification_artifacts,
)

__all__ = [
    "execute_fast_fixture",
    "execute_deep_fixture",
    "execute_handoff_fixture",
    "execute_verify_fixture",
]


def execute_fast_fixture(workspace: Path, config: dict[str, Any], run_dir: Path):
    """Run the fast QA-Z path for one fixture."""
    fast_run = run_fast(
        root=workspace,
        config=config,
        output_dir=run_dir,
        selection_mode="full",
    )
    summary_path = write_run_summary_artifacts(fast_run.summary, run_dir / "fast")
    write_latest_run_manifest(workspace, config, run_dir)
    return load_run_summary(summary_path)


def execute_deep_fixture(
    *,
    workspace: Path,
    config: dict[str, Any],
    run_dir: Path,
    attach_to_fast: bool,
):
    """Run the deep QA-Z path for one fixture."""
    deep_run = run_deep(
        root=workspace,
        config=config,
        from_run=str(run_dir) if attach_to_fast else None,
        output_dir=None if attach_to_fast else run_dir,
        selection_mode="full",
    )
    summary_path = write_run_summary_artifacts(
        deep_run.summary, deep_run.resolution.deep_dir
    )
    write_sarif_artifact(
        deep_run.summary, deep_run.resolution.deep_dir / "results.sarif"
    )
    return load_run_summary(summary_path)


def execute_handoff_fixture(workspace: Path, config: dict[str, Any], run_dir: Path):
    """Generate repair packet and handoff artifacts for one fixture."""
    run_source = resolve_run_source(workspace, config, str(run_dir))
    summary = load_run_summary(run_source.summary_path)
    deep_summary = load_sibling_deep_summary(run_source)
    contract_path = resolve_contract_source(workspace, config, summary=summary)
    contract = load_contract_context(contract_path, workspace)
    packet = build_repair_packet(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=workspace,
        deep_summary=deep_summary,
    )
    handoff = build_repair_handoff(
        repair_packet=packet,
        summary=summary,
        run_source=run_source,
        root=workspace,
        deep_summary=deep_summary,
    )
    output_dir = run_dir / "repair"
    write_repair_artifacts(packet, output_dir)
    write_repair_handoff_artifact(handoff, output_dir)
    return handoff


def execute_verify_fixture(
    *,
    workspace: Path,
    config: dict[str, Any],
    baseline_run: str,
    candidate_run: str,
):
    """Compare pre-seeded baseline and candidate run artifacts."""
    baseline, _baseline_source = load_verification_run(
        root=workspace,
        config=config,
        from_run=baseline_run,
    )
    candidate, candidate_source = load_verification_run(
        root=workspace,
        config=config,
        from_run=candidate_run,
    )
    comparison = compare_verification_runs(baseline, candidate)
    write_verification_artifacts(comparison, candidate_source.run_dir / "verify")
    return comparison
