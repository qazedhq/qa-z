"""Shared helpers for fast-check selection planners."""

from __future__ import annotations

from pathlib import Path

from qa_z.runners.models import CheckPlan, CheckSpec


def full_check_plan(
    spec: CheckSpec, selection_reason: str, high_risk_reasons: list[str]
) -> CheckPlan:
    """Create a full execution plan."""
    return CheckPlan(
        id=spec.id,
        kind=spec.kind,
        tool=spec.tool,
        enabled=spec.enabled,
        execution_mode="full",
        base_command=list(spec.command),
        resolved_command=list(spec.command),
        target_paths=[],
        selection_reason=selection_reason,
        high_risk_reasons=list(high_risk_reasons),
    )


def targeted_check_plan(
    spec: CheckSpec,
    resolved_command: list[str],
    target_paths: list[str],
    selection_reason: str,
    high_risk_reasons: list[str],
) -> CheckPlan:
    """Create a targeted execution plan."""
    return CheckPlan(
        id=spec.id,
        kind=spec.kind,
        tool=Path(resolved_command[0]).name if resolved_command else spec.tool,
        enabled=spec.enabled,
        execution_mode="targeted",
        base_command=list(spec.command),
        resolved_command=resolved_command,
        target_paths=target_paths,
        selection_reason=selection_reason,
        high_risk_reasons=list(high_risk_reasons),
    )


def skipped_check_plan(spec: CheckSpec, selection_reason: str) -> CheckPlan:
    """Create a skipped execution plan."""
    return CheckPlan(
        id=spec.id,
        kind=spec.kind,
        tool=spec.tool,
        enabled=spec.enabled,
        execution_mode="skipped",
        base_command=list(spec.command),
        resolved_command=list(spec.command),
        target_paths=[],
        selection_reason=selection_reason,
        high_risk_reasons=[],
    )


def command_with_targets(
    spec: CheckSpec,
    targets: list[str],
    *,
    replace_roots: set[str] | None = None,
) -> list[str]:
    """Return the configured command with selected target paths injected."""
    roots = replace_roots or set()
    command = [part for part in spec.command if part not in roots]
    return [*command, *unique_preserve_order(targets)]


def unique_preserve_order(items: list[str]) -> list[str]:
    """Return unique strings in first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
