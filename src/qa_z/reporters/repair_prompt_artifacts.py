"""Thin public wrappers for repair-prompt artifact seams."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_z.reporters.repair_prompt import RepairPacket


def write_repair_artifacts(packet: RepairPacket, output_dir: Path) -> tuple[Path, Path]:
    """Write packet.json and prompt.md artifacts."""
    from qa_z.reporters import repair_prompt as repair_prompt_module

    return repair_prompt_module._write_repair_artifacts_impl(packet, output_dir)


def repair_packet_json(packet: RepairPacket) -> str:
    """Render a repair packet as JSON for stdout."""
    from qa_z.reporters import repair_prompt as repair_prompt_module

    return repair_prompt_module._repair_packet_json_impl(packet)
