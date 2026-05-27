"""Claude-facing rendering for normalized repair handoff packets."""

from __future__ import annotations

from qa_z.adapters.repair_handoff import render_repair_handoff_for_adapter
from qa_z.repair_handoff import RepairHandoffPacket


def render_claude_handoff(handoff: RepairHandoffPacket) -> str:
    """Render an explanatory Claude repair prompt from a handoff packet."""
    return render_repair_handoff_for_adapter("claude", handoff)
