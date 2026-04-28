"""Semgrep check configuration and output normalization."""

from __future__ import annotations

import json
from collections import Counter, OrderedDict
from fnmatch import fnmatch
from typing import Any

from qa_z.runners.models import (
    CheckResult,
    CheckSpec,
    GroupedFinding,
    SemgrepCheckPolicy,
    SemgrepFinding,
)

SEMGREP_CHECK_ID = "sg_scan"

SEMGREP_DEFAULT = CheckSpec(
    id=SEMGREP_CHECK_ID,
    command=["semgrep", "--config", "auto", "--json"],
    kind="static-analysis",
    timeout_seconds=600,
)

SEMGREP_ALIASES = {
    "sg_scan": SEMGREP_CHECK_ID,
    "semgrep": SEMGREP_CHECK_ID,
    "security": SEMGREP_CHECK_ID,
}

SEMGREP_OPTION_VALUE_FLAGS = {
    "--baseline-commit",
    "--config",
    "--exclude",
    "--include",
    "--jobs",
    "--max-memory",
    "--metrics",
    "--project-root",
    "--severity",
    "--timeout",
    "--timeout-threshold",
    "-c",
}


def default_semgrep_spec_for_name(name: str) -> CheckSpec | None:
    """Return a copy of the built-in Semgrep check by id or alias."""
    if SEMGREP_ALIASES.get(name) != SEMGREP_CHECK_ID:
        return None
    return CheckSpec(
        id=SEMGREP_DEFAULT.id,
        command=list(SEMGREP_DEFAULT.command),
        kind=SEMGREP_DEFAULT.kind,
        enabled=SEMGREP_DEFAULT.enabled,
        no_tests=SEMGREP_DEFAULT.no_tests,
        timeout_seconds=SEMGREP_DEFAULT.timeout_seconds,
        semgrep_policy=SemgrepCheckPolicy(),
    )


def normalize_semgrep_result(
    result: CheckResult,
    policy: SemgrepCheckPolicy | None = None,
) -> CheckResult:
    """Normalize Semgrep JSON stdout into QA-Z finding metadata."""
    policy = normalized_semgrep_policy(policy)
    result.policy = policy.to_dict()

    if result.error_type:
        return result

    try:
        payload = json.loads(result.stdout or result.stdout_tail or "{}")
    except json.JSONDecodeError:
        return invalid_semgrep_json_result(result, policy)

    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        return invalid_semgrep_json_result(result, policy)

    findings = [
        finding
        for item in payload["results"]
        if isinstance(item, dict)
        for finding in [normalize_semgrep_finding(item)]
        if finding is not None
    ]
    active_findings, filter_reasons = filter_semgrep_findings(findings, policy)
    grouped_findings = group_semgrep_findings(active_findings)
    scan_warnings = normalize_semgrep_scan_warnings(payload)
    severity_summary = Counter(
        str(finding["severity"])
        for finding in active_findings
        if finding.get("severity")
    )
    result.findings_count = len(findings)
    result.blocking_findings_count = count_blocking_findings(active_findings, policy)
    result.filtered_findings_count = sum(filter_reasons.values())
    result.filter_reasons = dict(sorted(filter_reasons.items()))
    result.severity_summary = dict(sorted(severity_summary.items()))
    result.grouped_findings = grouped_findings
    result.findings = active_findings
    result.scan_warning_count = len(scan_warnings)
    result.scan_warnings = scan_warnings
    result.message = semgrep_findings_message(
        findings_count=len(findings),
        blocking_count=result.blocking_findings_count or 0,
        filtered_count=result.filtered_findings_count or 0,
        scan_warning_count=result.scan_warning_count or 0,
    )
    if is_semgrep_payload_error(payload, result):
        result.status = "error"
        if is_semgrep_config_error(result, policy):
            result.error_type = "semgrep_config_error"
            result.message = f"Semgrep config failed: {policy.config}"
        else:
            result.error_type = "semgrep_error"
            result.message = semgrep_error_message(policy)
    elif result.blocking_findings_count:
        result.status = "failed"
    else:
        result.status = "passed"
    return result


def normalize_semgrep_finding(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the QA-Z Semgrep finding fields from one raw result."""
    extra = raw.get("extra")
    if not isinstance(extra, dict):
        extra = {}
    start = raw.get("start")
    if not isinstance(start, dict):
        start = {}

    rule_id = first_string(raw.get("check_id"), raw.get("rule_id"))
    path = first_string(raw.get("path"))
    line = coerce_positive_int(start.get("line"))
    message = first_string(extra.get("message"))
    severity = normalize_severity(first_string(extra.get("severity")))

    if not rule_id and not path and not message:
        return None

    finding = SemgrepFinding(
        rule_id=rule_id or "unknown",
        severity=severity,
        path=normalize_path(path or ""),
        line=line,
        message=message or "",
    )
    return finding.to_dict()


def invalid_semgrep_json_result(
    result: CheckResult,
    policy: SemgrepCheckPolicy | None = None,
) -> CheckResult:
    """Mark invalid successful Semgrep JSON as an error; preserve failures."""
    policy = normalized_semgrep_policy(policy)
    result.policy = policy.to_dict()
    result.findings_count = 0
    result.blocking_findings_count = 0
    result.filtered_findings_count = 0
    result.filter_reasons = {}
    result.severity_summary = {}
    result.grouped_findings = []
    result.findings = []
    result.scan_warning_count = 0
    result.scan_warnings = []
    if result.exit_code == 0:
        result.status = "error"
        result.error_type = "invalid_semgrep_json"
        result.message = "Semgrep output was not valid JSON."
    elif is_semgrep_config_error(result, policy):
        result.status = "error"
        result.error_type = "semgrep_config_error"
        result.message = f"Semgrep config failed: {policy.config}"
    else:
        result.message = "Semgrep failed before producing valid JSON."
    return result


def semgrep_findings_message(
    *,
    findings_count: int,
    blocking_count: int,
    filtered_count: int = 0,
    scan_warning_count: int = 0,
) -> str:
    """Return a compact normalized Semgrep result message."""
    noun = "finding" if findings_count == 1 else "findings"
    message = f"Semgrep reported {findings_count} {noun}; {blocking_count} blocking."
    if filtered_count:
        message += f" {filtered_count} filtered."
    if scan_warning_count:
        warning_noun = "warning" if scan_warning_count == 1 else "warnings"
        message += f" {scan_warning_count} scan {warning_noun}."
    return message


def normalize_semgrep_scan_warnings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract non-fatal Semgrep scan-quality warnings from JSON payloads."""
    errors = list_payload_items(payload.get("errors"))
    time_payload = payload.get("time")
    if isinstance(time_payload, dict):
        errors.extend(list_payload_items(time_payload.get("fixpoint_timeouts")))
    warnings: list[dict[str, Any]] = []
    for error in errors:
        if not isinstance(error, dict):
            continue
        severity = normalize_severity(first_string(error.get("severity")))
        if severity not in {"WARN", "WARNING"}:
            continue
        warning: dict[str, Any] = {
            "error_type": first_string(error.get("error_type")) or "semgrep_warning",
            "severity": "WARN",
            "message": first_string(error.get("message")) or "",
        }
        location = error.get("location")
        if isinstance(location, dict):
            path = first_string(location.get("path"))
            if path:
                warning["path"] = normalize_path(path)
            start = location.get("start")
            if isinstance(start, dict):
                line = coerce_positive_int(start.get("line"))
                if line is not None:
                    warning["line"] = line
        warnings.append(warning)
    return warnings


def list_payload_items(value: Any) -> list[Any]:
    """Return a list payload or an empty list for malformed fields."""
    return value if isinstance(value, list) else []


def semgrep_policy_from_config(
    item: dict[str, Any], *, global_exclude_paths: list[str] | None = None
) -> SemgrepCheckPolicy:
    """Build a Semgrep policy from a deep check config item."""
    semgrep_config = item.get("semgrep")
    if not isinstance(semgrep_config, dict):
        semgrep_config = {}

    command = item.get("run")
    command_config = semgrep_config_from_command(
        command if isinstance(command, list) else []
    )
    policy = SemgrepCheckPolicy(
        config=first_string(semgrep_config.get("config"), command_config) or "auto",
        fail_on_severity=string_list(
            semgrep_config.get("fail_on_severity"), default=["ERROR"]
        ),
        ignore_rules=string_list(semgrep_config.get("ignore_rules")),
        exclude_paths=unique_strings(
            [
                *(global_exclude_paths or []),
                *string_list(semgrep_config.get("exclude_paths")),
            ]
        ),
    )
    return normalized_semgrep_policy(policy)


def semgrep_command_with_config(command: list[str], config: str) -> list[str]:
    """Return a Semgrep command with exactly one configured ``--config`` value."""
    if not is_semgrep_executable(command):
        return list(command)

    cleaned: list[str] = []
    skip_next = False
    for part in command:
        if skip_next:
            skip_next = False
            continue
        if part == "--config":
            skip_next = True
            continue
        if part.startswith("--config="):
            continue
        cleaned.append(part)

    insert_at = 1 if cleaned else 0
    configured = [*cleaned[:insert_at], "--config", config, *cleaned[insert_at:]]
    if "--json" not in configured:
        configured.append("--json")
    return configured


def semgrep_targeted_command(command: list[str], targets: list[str]) -> list[str]:
    """Replace configured positional Semgrep scan roots with selected targets."""
    semgrep_index = semgrep_executable_index(command)
    if semgrep_index is None:
        return unique_strings([*command, *targets])

    prefix = list(command[:semgrep_index])
    semgrep_parts = command[semgrep_index:]
    cleaned: list[str] = []
    index = 0
    while index < len(semgrep_parts):
        part = semgrep_parts[index]
        cleaned.append(part)
        if part in SEMGREP_OPTION_VALUE_FLAGS and index + 1 < len(semgrep_parts):
            cleaned.append(semgrep_parts[index + 1])
            index += 2
            continue
        if part.startswith("-"):
            index += 1
            continue
        if index == 0:
            index += 1
            continue
        cleaned.pop()
        index += 1

    return unique_strings([*prefix, *cleaned, *targets])


def is_semgrep_executable(command: list[str]) -> bool:
    """Return whether the configured command invokes a Semgrep executable."""
    if not command:
        return False
    executable = command[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    return executable in {"semgrep", "semgrep.exe", "semgrep.cmd", "semgrep.bat"}


def semgrep_executable_index(command: list[str]) -> int | None:
    """Return the position of a Semgrep executable token in a command."""
    for index, part in enumerate(command):
        executable = part.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if executable in {"semgrep", "semgrep.exe", "semgrep.cmd", "semgrep.bat"}:
            return index
    return None


def semgrep_config_from_command(command: list[Any]) -> str | None:
    """Extract a ``--config`` value from a Semgrep command."""
    for index, part in enumerate(command):
        if not isinstance(part, str):
            continue
        if part == "--config" and index + 1 < len(command):
            next_part = command[index + 1]
            return next_part if isinstance(next_part, str) else None
        if part.startswith("--config="):
            return part.split("=", 1)[1]
    return None


def filter_semgrep_findings(
    findings: list[dict[str, Any]], policy: SemgrepCheckPolicy
) -> tuple[list[dict[str, Any]], Counter[str]]:
    """Apply exclude path and ignore rule policy to normalized findings."""
    active: list[dict[str, Any]] = []
    reasons: Counter[str] = Counter()
    for finding in findings:
        if is_excluded_path(str(finding.get("path") or ""), policy.exclude_paths):
            reasons["excluded_path"] += 1
            continue
        if str(finding.get("rule_id") or "") in set(policy.ignore_rules):
            reasons["ignored_rule"] += 1
            continue
        active.append(finding)
    return active, reasons


def group_semgrep_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group findings by rule id, path, and severity for concise reporting."""
    buckets: OrderedDict[tuple[str, str, str], GroupedFinding] = OrderedDict()
    for finding in findings:
        rule_id = str(finding.get("rule_id") or "unknown")
        path = str(finding.get("path") or "")
        severity = str(finding.get("severity") or "UNKNOWN")
        line = coerce_positive_int(finding.get("line"))
        key = (rule_id, path, severity)
        current = buckets.get(key)
        if current is None:
            buckets[key] = GroupedFinding(
                rule_id=rule_id,
                severity=severity,
                path=path,
                count=1,
                representative_line=line,
                message=str(finding.get("message") or ""),
            )
            continue

        representative_line = current.representative_line
        if line is not None and (
            representative_line is None or line < representative_line
        ):
            representative_line = line
        buckets[key] = GroupedFinding(
            rule_id=current.rule_id,
            severity=current.severity,
            path=current.path,
            count=current.count + 1,
            representative_line=representative_line,
            message=current.message,
        )
    return [group.to_dict() for group in buckets.values()]


def count_blocking_findings(
    findings: list[dict[str, Any]], policy: SemgrepCheckPolicy
) -> int:
    """Count findings whose severity is configured as blocking."""
    blocking = {normalize_severity(severity) for severity in policy.fail_on_severity}
    return sum(
        1
        for finding in findings
        if normalize_severity(str(finding.get("severity") or "")) in blocking
    )


def is_excluded_path(path: str, patterns: list[str]) -> bool:
    """Return whether a normalized path matches any configured exclude pattern."""
    normalized = normalize_path(path)
    return any(fnmatch(normalized, normalize_path(pattern)) for pattern in patterns)


def is_semgrep_payload_error(payload: dict[str, Any], result: CheckResult) -> bool:
    """Return whether Semgrep emitted a fatal error payload instead of findings."""
    if result.exit_code in (0, 1):
        return False
    errors = payload.get("errors")
    return isinstance(errors, list) and bool(errors)


def is_semgrep_config_error(result: CheckResult, policy: SemgrepCheckPolicy) -> bool:
    """Detect Semgrep failures caused by invalid configured rulesets."""
    if policy.config == "auto":
        return False
    evidence = " ".join(
        part.lower()
        for part in (
            result.stdout,
            result.stderr,
            result.stdout_tail,
            result.stderr_tail,
            result.message,
        )
        if part
    )
    return any(
        token in evidence
        for token in ("config", "rule", "not found", "no such file", "invalid")
    )


def semgrep_error_message(policy: SemgrepCheckPolicy) -> str:
    """Return a stable Semgrep fatal-error message."""
    return f"Semgrep failed while using config: {policy.config}"


def normalized_semgrep_policy(
    policy: SemgrepCheckPolicy | None,
) -> SemgrepCheckPolicy:
    """Normalize policy casing and empty values."""
    if policy is None:
        policy = SemgrepCheckPolicy()
    return SemgrepCheckPolicy(
        config=policy.config.strip() if policy.config.strip() else "auto",
        fail_on_severity=[
            normalize_severity(item)
            for item in policy.fail_on_severity
            if str(item).strip()
        ]
        or ["ERROR"],
        ignore_rules=unique_strings(policy.ignore_rules),
        exclude_paths=unique_strings(policy.exclude_paths),
    )


def normalize_severity(value: str | None) -> str:
    """Return Semgrep severity using stable uppercase spelling."""
    if not value:
        return "UNKNOWN"
    return value.strip().upper() or "UNKNOWN"


def normalize_path(value: str) -> str:
    """Normalize paths to slash-separated relative-looking strings."""
    return value.replace("\\", "/").strip()


def string_list(value: Any, *, default: list[str] | None = None) -> list[str]:
    """Return a list of non-empty strings from config input."""
    if not isinstance(value, list):
        return list(default or [])
    return [str(item).strip() for item in value if str(item).strip()]


def unique_strings(values: list[str]) -> list[str]:
    """Return unique non-empty strings in first-seen order."""
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        item = str(value).strip()
        if item and item not in seen:
            seen.add(item)
            items.append(item)
    return items


def first_string(*values: Any) -> str | None:
    """Return the first non-empty string among values."""
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def coerce_positive_int(value: Any) -> int | None:
    """Return a positive integer, otherwise ``None``."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
