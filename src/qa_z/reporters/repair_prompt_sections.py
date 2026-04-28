"""Section and formatting helpers for repair prompts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from qa_z.reporters.deep_context import DeepContext, format_finding_location
from qa_z.reporters.deep_context import format_severity_summary as format_deep_severity

if TYPE_CHECKING:
    from qa_z.reporters.repair_prompt import FailureContext


def render_optional_list(
    heading: str, items: list[str], *, bullet: str = "-"
) -> list[str]:
    """Render a markdown heading and list when items exist."""
    if not items:
        return []
    return [heading, "", *[f"{bullet} {item}" for item in items], ""]


def render_failure_markdown(failure: "FailureContext") -> list[str]:
    """Render one failed check for the repair prompt."""
    lines = [
        f"### {failure.id}",
        "",
        f"- Tool: {failure.tool}",
        f"- Command: `{format_command(failure.command)}`",
        f"- Exit code: `{failure.exit_code}`",
    ]
    if failure.candidate_files:
        lines.extend(["- Candidate files:"])
        lines.extend(f"  - `{path}`" for path in failure.candidate_files)
    lines.extend(["", "Evidence:", "```text", evidence_tail(failure), "```", ""])
    return lines


def render_security_findings(deep: dict[str, Any] | None) -> list[str]:
    """Render Semgrep findings for repair prompts."""
    if not isinstance(deep, dict):
        return []

    grouped_findings = blocking_grouped_findings(deep)
    if grouped_findings:
        lines = [
            "## Deep QA Findings",
            "",
            "The following Semgrep findings must be addressed:",
            "",
        ]
        for finding in grouped_findings:
            lines.append(format_grouped_finding(finding))
        lines.extend(
            [
                "",
                "### Deep QA Completion Criteria",
                "",
                "- `qa-z deep` exits successfully",
                "- no blocking findings remain",
                "- fast checks remain green",
                "",
            ]
        )
        return lines

    findings = deep.get("top_findings")
    if not isinstance(findings, list) or not findings:
        return []

    lines = [
        "## Security Findings (Semgrep)",
        "",
        f"- Findings: {deep.get('findings_count', 0)}",
        f"- Highest severity: {deep.get('highest_severity') or 'none'}",
        f"- Severity summary: {format_severity_summary_dict(deep.get('severity_summary'))}",
        f"- Affected files: {format_inline_code_list(deep.get('affected_files'))}",
        "",
    ]
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        lines.append(
            "- "
            f"`{format_finding_location(finding)}` "
            f"{finding.get('severity', 'UNKNOWN')} "
            f"{finding.get('rule_id', 'unknown')} - "
            f"{finding.get('message', '')}"
        )
    lines.extend(
        [
            "",
            "Repair these findings without weakening fast checks, tests, or documented behavior.",
            "",
        ]
    )
    return lines


def evidence_tail(failure: "FailureContext") -> str:
    """Combine stdout and stderr tail for markdown evidence."""
    parts = []
    if failure.stdout_tail:
        parts.append(failure.stdout_tail.rstrip())
    if failure.stderr_tail:
        parts.append(failure.stderr_tail.rstrip())
    return "\n".join(parts) if parts else "No stdout or stderr tail captured."


def format_command(command: list[str]) -> str:
    """Render a subprocess command for human-readable markdown."""
    return " ".join(command)


def format_list(value: object) -> str:
    """Render a compact list for human-readable prompts."""
    if not isinstance(value, list) or not value:
        return "none"
    return ", ".join(str(item) for item in value)


def format_inline_code_list(value: object) -> str:
    """Render a list of strings as inline-code Markdown."""
    if not isinstance(value, list) or not value:
        return "none"
    return ", ".join(f"`{item}`" for item in value)


def format_severity_summary_dict(value: object) -> str:
    """Render a serialized severity summary."""
    if not isinstance(value, dict):
        return "none"
    return format_deep_severity({str(key): int(item) for key, item in value.items()})


def suggested_fix_order(
    failures: list["FailureContext"], deep: DeepContext | None
) -> list[str]:
    """Return deterministic repair order including deep findings."""
    order = [failure.id for failure in failures]
    if has_blocking_deep_findings(deep) and "sg_scan" not in order:
        order.append("sg_scan")
    return order


def done_when_items(repair_needed: bool, deep: DeepContext | None) -> list[str]:
    """Return completion criteria with deep context when relevant."""
    from qa_z.reporters import repair_prompt as repair_prompt_module

    if not repair_needed:
        return repair_prompt_module.PASSING_DONE_WHEN
    items = list(repair_prompt_module.DEFAULT_DONE_WHEN)
    if has_blocking_deep_findings(deep):
        items.append("qa-z deep exits with code 0")
        items.append("No blocking deep findings remain")
    return items


def has_blocking_deep_findings(deep: DeepContext | None) -> bool:
    """Return whether deep context contains blocking findings."""
    return bool(deep is not None and deep.blocking_findings_count > 0)


def blocking_grouped_findings(deep: dict[str, Any]) -> list[dict[str, Any]]:
    """Return grouped findings whose severities are configured as blocking."""
    grouped = deep.get("top_grouped_findings")
    if not isinstance(grouped, list):
        return []
    blocking = blocking_severities(deep)
    return [
        finding
        for finding in grouped
        if isinstance(finding, dict)
        and str(finding.get("severity", "")).upper() in blocking
    ]


def blocking_severities(deep: dict[str, Any]) -> set[str]:
    """Return blocking severities from deep policy metadata."""
    policy = deep.get("policy")
    if not isinstance(policy, dict):
        return {"ERROR"}
    severities = policy.get("fail_on_severity")
    if not isinstance(severities, list):
        return {"ERROR"}
    normalized = {str(item).upper() for item in severities if str(item).strip()}
    return normalized or {"ERROR"}


def format_grouped_finding(finding: dict[str, Any]) -> str:
    """Render one grouped finding in repair-prompt style."""
    count = int(finding.get("count") or 1)
    occurrence = "occurrence" if count == 1 else "occurrences"
    path = str(finding.get("path") or "unknown")
    line = finding.get("representative_line")
    location = f"{path}:{line}" if line else path
    return (
        "- "
        f"`{finding.get('rule_id', 'unknown')}` in `{location}` "
        f"({count} {occurrence}) - {finding.get('message', '')}"
    )


def unique_preserve_order(items: list[str]) -> list[str]:
    """Return unique non-empty items in first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        key = normalized.rstrip(".")
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def utc_now() -> str:
    """Return an ISO-like UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
