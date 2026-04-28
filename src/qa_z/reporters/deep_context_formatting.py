"""Thin public wrappers for deep-context formatting seams."""

from __future__ import annotations

from typing import Any


def format_severity_summary(severity_summary: dict[str, int]) -> str:
    """Render severity counts in a compact deterministic order."""
    from qa_z.reporters import deep_context as deep_context_module

    return deep_context_module._format_severity_summary_impl(severity_summary)


def format_finding_location(finding: dict[str, Any]) -> str:
    """Render ``path`` or ``path:line`` for a finding."""
    from qa_z.reporters import deep_context as deep_context_module

    return deep_context_module._format_finding_location_impl(finding)
