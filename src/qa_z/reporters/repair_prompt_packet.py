"""Thin public wrappers for repair-prompt packet seams."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from qa_z.artifacts import ContractContext, RunSource
from qa_z.runners.models import RunSummary

if TYPE_CHECKING:
    from qa_z.reporters.repair_prompt import RepairPacket


def build_repair_packet(
    *,
    summary: RunSummary,
    run_source: RunSource,
    contract: ContractContext,
    root: Path,
    deep_summary: RunSummary | None = None,
) -> RepairPacket:
    """Build a repair packet from a run summary and contract."""
    from qa_z.reporters import repair_prompt as repair_prompt_module

    return repair_prompt_module._build_repair_packet_impl(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
