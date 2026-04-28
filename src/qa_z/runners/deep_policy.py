"""Thin public wrappers for deep-runner policy seams."""

from __future__ import annotations

from typing import Any

from qa_z.runners.models import CheckSpec


def resolve_deep_checks(config: dict[str, Any]) -> list[CheckSpec]:
    """Resolve configured deep checks into executable subprocess specs."""
    from qa_z.runners import deep as deep_module

    return deep_module._resolve_deep_checks_impl(config)


def configured_deep_checks(config: dict[str, Any]) -> list[Any]:
    """Return explicit deep check configuration."""
    from qa_z.runners import deep as deep_module

    return deep_module._configured_deep_checks_impl(config)


def fail_on_missing_tool(config: dict[str, Any]) -> bool:
    """Return whether missing deep tools should fail the run."""
    from qa_z.runners import deep as deep_module

    return deep_module._fail_on_missing_tool_impl(config)


def full_run_threshold(config: dict[str, Any]) -> int:
    """Return the smart-selection full-run threshold for deep checks."""
    from qa_z.runners import deep as deep_module

    return deep_module._full_run_threshold_impl(config)


def high_risk_paths(config: dict[str, Any]) -> list[str]:
    """Return configured paths that should force full deep execution."""
    from qa_z.runners import deep as deep_module

    return deep_module._high_risk_paths_impl(config)


def deep_exclude_paths(config: dict[str, Any]) -> list[str]:
    """Return configured deep selection exclude path patterns."""
    from qa_z.runners import deep as deep_module

    return deep_module._deep_exclude_paths_impl(config)
