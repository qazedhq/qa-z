"""Agent adapter registration and deterministic repair handoff renderers."""

from qa_z.adapters.repair_handoff import (
    SUPPORTED_REPAIR_ADAPTERS,
    render_all_repair_handoffs,
    render_repair_handoff_for_adapter,
)

__all__ = [
    "SUPPORTED_REPAIR_ADAPTERS",
    "render_all_repair_handoffs",
    "render_repair_handoff_for_adapter",
]
