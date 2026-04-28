"""Human-readable render helpers for verification reports."""

from __future__ import annotations

from qa_z.verification_models import FastCheckDelta, VerificationFindingDelta


def render_fast_category(title: str, deltas: list[FastCheckDelta]) -> list[str]:
    """Render one fast-check category."""
    lines = [f"### {title}", ""]
    if not deltas:
        return [*lines, "- none", ""]
    for delta in deltas:
        lines.append(
            f"- `{delta.id}`: {delta.baseline_status or 'missing'} -> "
            f"{delta.candidate_status or 'missing'}"
        )
    lines.append("")
    return lines


def render_finding_category(
    title: str, deltas: list[VerificationFindingDelta]
) -> list[str]:
    """Render one deep-finding category."""
    lines = [f"### {title}", ""]
    if not deltas:
        return [*lines, "- none", ""]
    for delta in deltas:
        location = f"{delta.path}:{delta.line}" if delta.line else delta.path
        lines.append(
            f"- `{delta.rule_id}` in `{location or 'unknown'}` "
            f"({delta.baseline_severity or 'missing'} -> "
            f"{delta.candidate_severity or 'missing'}, match: {delta.match})"
        )
    lines.append("")
    return lines
