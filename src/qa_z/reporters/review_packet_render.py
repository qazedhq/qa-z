"""Thin public wrappers for review-packet render seams."""

from __future__ import annotations

from pathlib import Path

from qa_z.artifacts import ContractContext, RunSource
from qa_z.runners.models import RunSummary


def render_review_packet(contract_path: Path, root: Path) -> str:
    """Render a review packet from a generated contract."""
    from qa_z.reporters import review_packet as review_packet_module

    return review_packet_module._render_review_packet_impl(contract_path, root)


def review_packet_json(contract_path: Path, root: Path) -> str:
    """Render the contract-only review packet as JSON."""
    from qa_z.reporters import review_packet as review_packet_module

    return review_packet_module._review_packet_json_impl(contract_path, root)


def render_run_review_packet(
    *,
    summary: RunSummary,
    run_source: RunSource,
    contract: ContractContext,
    root: Path,
    deep_summary: RunSummary | None = None,
) -> str:
    """Render a review packet enriched with fast run context."""
    from qa_z.reporters import review_packet as review_packet_module

    return review_packet_module._render_run_review_packet_impl(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )


def run_review_packet_json(
    *,
    summary: RunSummary,
    run_source: RunSource,
    contract: ContractContext,
    root: Path,
    deep_summary: RunSummary | None = None,
) -> str:
    """Render run-aware review context as JSON."""
    from qa_z.reporters import review_packet as review_packet_module

    return review_packet_module._run_review_packet_json_impl(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )


def write_review_artifacts(
    markdown: str, json_text: str | None, output_dir: Path
) -> tuple[Path, Path | None]:
    """Write review Markdown and optional JSON artifacts."""
    from qa_z.reporters import review_packet as review_packet_module

    return review_packet_module._write_review_artifacts_impl(
        markdown,
        json_text,
        output_dir,
    )
