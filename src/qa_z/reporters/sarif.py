"""SARIF reporting for normalized QA-Z deep findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.runners.models import CheckResult, RunSummary

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_VERSION = "2.1.0"


def build_sarif_log(summary: RunSummary) -> dict[str, Any]:
    """Convert a QA-Z deep summary into a compact SARIF 2.1.0 log."""
    rules: list[dict[str, Any]] = []
    rule_indexes: dict[str, int] = {}
    results: list[dict[str, Any]] = []

    for check in summary.checks:
        for finding in sarif_findings_for_check(check):
            rule_id = finding["rule_id"]
            if rule_id not in rule_indexes:
                rule_indexes[rule_id] = len(rules)
                rules.append(build_rule(finding, check))
            results.append(
                build_result(
                    finding=finding,
                    check=check,
                    rule_index=rule_indexes[rule_id],
                )
            )

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "QA-Z",
                        "rules": rules,
                    }
                },
                "results": results,
                "properties": run_properties(summary),
            }
        ],
    }


def sarif_json(summary: RunSummary) -> str:
    """Render a QA-Z deep summary as deterministic SARIF JSON text."""
    return json.dumps(build_sarif_log(summary), indent=2, sort_keys=True) + "\n"


def write_sarif_artifact(summary: RunSummary, output_path: Path) -> Path:
    """Write a SARIF artifact and return its path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sarif_json(summary), encoding="utf-8")
    return output_path


def sarif_level_for_severity(severity: object) -> str:
    """Map QA-Z/Semgrep severity text to a SARIF result level."""
    normalized = str(severity or "").strip().upper()
    if normalized in {"ERROR", "HIGH", "CRITICAL"}:
        return "error"
    if normalized in {"WARNING", "WARN", "MEDIUM", "MODERATE"}:
        return "warning"
    if normalized in {"INFO", "INFORMATIONAL", "LOW", "NOTE"}:
        return "note"
    if normalized in {"NONE", "OFF"}:
        return "none"
    return "warning"


def sarif_findings_for_check(check: CheckResult) -> list[dict[str, Any]]:
    """Return SARIF-ready finding records from one normalized check result."""
    active = [
        finding
        for raw in check.findings
        if isinstance(raw, dict)
        for finding in [normalize_active_finding(raw, check)]
        if finding is not None
    ]
    if active:
        return active

    return [
        finding
        for raw in check.grouped_findings
        if isinstance(raw, dict)
        for finding in [normalize_grouped_finding(raw, check)]
        if finding is not None
    ]


def normalize_active_finding(
    raw: dict[str, Any], check: CheckResult
) -> dict[str, Any] | None:
    """Normalize an active QA-Z finding for SARIF output."""
    rule_id = first_nonempty(raw.get("rule_id"), check.id, "unknown")
    severity = first_nonempty(raw.get("severity"), "UNKNOWN")
    message = first_nonempty(raw.get("message"), rule_id)
    path = normalize_sarif_path(first_nonempty(raw.get("path"), ""))
    return {
        "rule_id": rule_id,
        "severity": severity,
        "path": path,
        "line": coerce_positive_int(raw.get("line")),
        "message": message,
        "grouped_count": None,
    }


def normalize_grouped_finding(
    raw: dict[str, Any], check: CheckResult
) -> dict[str, Any] | None:
    """Normalize a grouped QA-Z finding for SARIF output."""
    rule_id = first_nonempty(raw.get("rule_id"), check.id, "unknown")
    severity = first_nonempty(raw.get("severity"), "UNKNOWN")
    path = normalize_sarif_path(first_nonempty(raw.get("path"), ""))
    count = coerce_positive_int(raw.get("count")) or 1
    message = first_nonempty(raw.get("message"), rule_id)
    if count > 1:
        message = f"{message} ({count} occurrences)"
    return {
        "rule_id": rule_id,
        "severity": severity,
        "path": path,
        "line": coerce_positive_int(raw.get("representative_line")),
        "message": message,
        "grouped_count": count,
    }


def build_rule(finding: dict[str, Any], check: CheckResult) -> dict[str, Any]:
    """Build one SARIF rule descriptor."""
    severity = str(finding["severity"])
    return {
        "id": finding["rule_id"],
        "name": finding["rule_id"],
        "shortDescription": {"text": compact_text(str(finding["message"]))},
        "properties": {
            "qa_z_check_id": check.id,
            "severity": severity,
        },
    }


def build_result(
    *,
    finding: dict[str, Any],
    check: CheckResult,
    rule_index: int,
) -> dict[str, Any]:
    """Build one SARIF result from a normalized finding."""
    result: dict[str, Any] = {
        "ruleId": finding["rule_id"],
        "ruleIndex": rule_index,
        "level": sarif_level_for_severity(finding["severity"]),
        "message": {"text": finding["message"]},
        "properties": result_properties(finding, check),
    }
    location = build_location(finding)
    if location is not None:
        result["locations"] = [location]
    return result


def build_location(finding: dict[str, Any]) -> dict[str, Any] | None:
    """Build a SARIF physical location when QA-Z has a path."""
    path = str(finding.get("path") or "")
    if not path:
        return None

    physical_location: dict[str, Any] = {
        "artifactLocation": {"uri": path},
    }
    line = coerce_positive_int(finding.get("line"))
    if line is not None:
        physical_location["region"] = {"startLine": line}
    return {"physicalLocation": physical_location}


def result_properties(finding: dict[str, Any], check: CheckResult) -> dict[str, Any]:
    """Return stable SARIF properties derived from QA-Z finding evidence."""
    properties: dict[str, Any] = {
        "qa_z_check_id": check.id,
        "qa_z_check_status": check.status,
        "severity": str(finding["severity"]),
    }
    grouped_count = coerce_positive_int(finding.get("grouped_count"))
    if grouped_count is not None:
        properties["qa_z_grouped_count"] = grouped_count
    return properties


def run_properties(summary: RunSummary) -> dict[str, Any]:
    """Return compact SARIF run metadata derived from the QA-Z summary."""
    properties: dict[str, Any] = {
        "qa_z_mode": summary.mode,
        "qa_z_status": summary.status,
        "qa_z_schema_version": summary.schema_version,
    }
    if summary.artifact_dir:
        properties["qa_z_artifact_dir"] = summary.artifact_dir
    if summary.contract_path:
        properties["qa_z_contract_path"] = summary.contract_path
    return properties


def first_nonempty(*values: object) -> str:
    """Return the first non-empty value as text."""
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def normalize_sarif_path(path: str) -> str:
    """Normalize paths to slash-separated SARIF artifact URIs."""
    return path.replace("\\", "/").strip()


def compact_text(text: str, *, limit: int = 160) -> str:
    """Return a single-line compact text field for SARIF rule metadata."""
    compacted = " ".join(text.split())
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3].rstrip() + "..."


def coerce_positive_int(value: object) -> int | None:
    """Return a positive integer, otherwise ``None``."""
    try:
        number = int(str(value))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
