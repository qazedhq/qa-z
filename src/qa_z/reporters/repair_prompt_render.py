"""Thin public wrappers for repair-prompt render seams."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_z.reporters.repair_prompt import RepairPacket


def render_repair_prompt(packet: RepairPacket) -> str:
    """Render a Markdown prompt that can be pasted into a coding agent."""
    from qa_z.reporters import repair_prompt as repair_prompt_module

    return repair_prompt_module._render_repair_prompt_impl(packet)
