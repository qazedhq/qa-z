"""Codex-facing rendering for normalized repair handoff packets."""

from __future__ import annotations

from qa_z.adapters.repair_handoff import render_repair_handoff_for_adapter
from qa_z.repair_handoff import RepairHandoffPacket


def render_codex_handoff(handoff: RepairHandoffPacket) -> str:
    """Render a concise Codex execution prompt from a handoff packet."""
    return render_repair_handoff_for_adapter("codex", handoff)
