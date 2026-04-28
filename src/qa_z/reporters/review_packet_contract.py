"""Thin public wrappers for review-packet contract seams."""

from __future__ import annotations

from pathlib import Path

from qa_z.artifacts import ContractContext


def contract_output_dir(root: Path, config: dict) -> Path:
    """Resolve the configured contract directory."""
    from qa_z.reporters import review_packet as review_packet_module

    return review_packet_module._contract_output_dir_impl(root, config)


def find_latest_contract(root: Path, config: dict) -> Path:
    """Find the newest contract in the configured output directory."""
    from qa_z.reporters import review_packet as review_packet_module

    return review_packet_module._find_latest_contract_impl(root, config)


def load_contract_review_context(contract_path: Path, root: Path) -> ContractContext:
    """Load contract context for callers that need a shared parser."""
    from qa_z.reporters import review_packet as review_packet_module

    return review_packet_module._load_contract_review_context_impl(contract_path, root)
