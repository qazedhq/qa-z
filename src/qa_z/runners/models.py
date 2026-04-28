"""Shared models for deterministic QA-Z runners."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from qa_z.diffing.models import ChangedFile

ExecutionMode = Literal["full", "targeted", "skipped"]

__all__ = [
    "CheckPlan",
    "CheckResult",
    "CheckSpec",
    "ExecutionMode",
    "GroupedFinding",
    "RunSummary",
    "SelectionSummary",
    "SemgrepCheckPolicy",
    "SemgrepFinding",
    "coerce_execution_mode",
    "coerce_int_mapping",
    "string_list",
]


@dataclass(slots=True)
class SemgrepFinding:
    """Normalized finding extracted from Semgrep JSON output."""

    rule_id: str
    severity: str
    path: str
    line: int | None
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Render this finding as JSON-safe data."""
        data: dict[str, Any] = {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "path": self.path,
            "line": self.line,
            "message": self.message,
        }
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data


@dataclass(slots=True)
class GroupedFinding:
    """Dedupe bucket for findings with the same rule, path, and severity."""

    rule_id: str
    severity: str
    path: str
    count: int
    representative_line: int | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Render this grouped finding as JSON-safe data."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "path": self.path,
            "count": self.count,
            "representative_line": self.representative_line,
            "message": self.message,
        }


@dataclass(slots=True)
class SemgrepCheckPolicy:
    """Policy controls for the built-in Semgrep deep check."""

    config: str = "auto"
    fail_on_severity: list[str] = field(default_factory=lambda: ["ERROR"])
    ignore_rules: list[str] = field(default_factory=list)
    exclude_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Render this policy as JSON-safe data."""
        return {
            "config": self.config,
            "fail_on_severity": list(self.fail_on_severity),
            "ignore_rules": list(self.ignore_rules),
            "exclude_paths": list(self.exclude_paths),
        }


@dataclass
class CheckSpec:
    """A configured subprocess check."""

    id: str
    command: list[str]
    kind: str
    enabled: bool = True
    no_tests: str = "warn"
    timeout_seconds: int | None = None
    semgrep_policy: SemgrepCheckPolicy | None = None

    @property
    def tool(self) -> str:
        """Return the command executable name for reporting."""
        if not self.command:
            return ""
        return Path(self.command[0]).name

    def to_dict(self) -> dict[str, Any]:
        """Render this check spec as JSON-safe data."""
        data: dict[str, Any] = {
            "id": self.id,
            "tool": self.tool,
            "command": self.command,
            "kind": self.kind,
            "enabled": self.enabled,
            "no_tests": self.no_tests,
            "timeout_seconds": self.timeout_seconds,
        }
        if self.semgrep_policy is not None:
            data["semgrep_policy"] = self.semgrep_policy.to_dict()
        return data


@dataclass(slots=True)
class CheckPlan:
    """A selected execution plan for one fast check."""

    id: str
    kind: str
    tool: str
    enabled: bool
    execution_mode: ExecutionMode
    base_command: list[str]
    resolved_command: list[str]
    target_paths: list[str]
    selection_reason: str
    high_risk_reasons: list[str] = field(default_factory=list)


@dataclass
class CheckResult:
    """A normalized subprocess check result."""

    id: str
    tool: str
    command: list[str]
    kind: str
    status: str
    exit_code: int | None
    duration_ms: int
    stdout: str = ""
    stderr: str = ""
    stdout_tail: str = ""
    stderr_tail: str = ""
    message: str = ""
    error_type: str | None = None
    execution_mode: ExecutionMode | None = None
    target_paths: list[str] = field(default_factory=list)
    selection_reason: str | None = None
    high_risk_reasons: list[str] = field(default_factory=list)
    findings_count: int | None = None
    blocking_findings_count: int | None = None
    filtered_findings_count: int | None = None
    filter_reasons: dict[str, int] = field(default_factory=dict)
    severity_summary: dict[str, int] = field(default_factory=dict)
    grouped_findings: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    scan_warning_count: int | None = None
    scan_warnings: list[dict[str, Any]] = field(default_factory=list)
    policy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Render this result as JSON-safe data."""
        data: dict[str, Any] = {
            "id": self.id,
            "tool": self.tool,
            "command": self.command,
            "kind": self.kind,
            "status": self.status,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
            "execution_mode": self.execution_mode,
            "target_paths": self.target_paths,
            "selection_reason": self.selection_reason,
            "high_risk_reasons": self.high_risk_reasons,
        }
        if self.message:
            data["message"] = self.message
        if self.error_type:
            data["error_type"] = self.error_type
        if self.findings_count is not None:
            data["findings_count"] = self.findings_count
            data["blocking_findings_count"] = self.blocking_findings_count
            data["filtered_findings_count"] = self.filtered_findings_count
            data["filter_reasons"] = dict(self.filter_reasons)
            data["severity_summary"] = dict(self.severity_summary)
            data["grouped_findings"] = list(self.grouped_findings)
            data["findings"] = list(self.findings)
        if self.scan_warning_count is not None:
            data["scan_warning_count"] = self.scan_warning_count
            data["scan_warnings"] = list(self.scan_warnings)
        if self.policy:
            data["policy"] = dict(self.policy)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckResult":
        """Load a check result from a summary artifact mapping."""
        required = (
            "id",
            "tool",
            "command",
            "kind",
            "status",
            "duration_ms",
        )
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Check result is missing required fields: {missing}")
        command = data["command"]
        if not isinstance(command, list):
            raise ValueError("Check result command must be a list.")
        return cls(
            id=str(data["id"]),
            tool=str(data["tool"]),
            command=[str(item) for item in command],
            kind=str(data["kind"]),
            status=str(data["status"]),
            exit_code=data.get("exit_code"),
            duration_ms=int(data["duration_ms"]),
            stdout="",
            stderr="",
            stdout_tail=str(data.get("stdout_tail", "")),
            stderr_tail=str(data.get("stderr_tail", "")),
            message=str(data.get("message", "")),
            error_type=(
                str(data["error_type"]) if data.get("error_type") is not None else None
            ),
            execution_mode=coerce_execution_mode(data.get("execution_mode")),
            target_paths=[
                str(item) for item in data.get("target_paths", []) if item is not None
            ],
            selection_reason=(
                str(data["selection_reason"])
                if data.get("selection_reason") is not None
                else None
            ),
            high_risk_reasons=[
                str(item)
                for item in data.get("high_risk_reasons", [])
                if item is not None
            ],
            findings_count=(
                int(data["findings_count"])
                if data.get("findings_count") is not None
                else None
            ),
            blocking_findings_count=(
                int(data["blocking_findings_count"])
                if data.get("blocking_findings_count") is not None
                else None
            ),
            filtered_findings_count=(
                int(data["filtered_findings_count"])
                if data.get("filtered_findings_count") is not None
                else None
            ),
            filter_reasons=coerce_int_mapping(data.get("filter_reasons", {})),
            severity_summary=coerce_int_mapping(data.get("severity_summary", {})),
            grouped_findings=[
                dict(item)
                for item in data.get("grouped_findings", [])
                if isinstance(item, dict)
            ],
            findings=[
                dict(item)
                for item in data.get("findings", [])
                if isinstance(item, dict)
            ],
            scan_warning_count=(
                int(data["scan_warning_count"])
                if data.get("scan_warning_count") is not None
                else None
            ),
            scan_warnings=[
                dict(item)
                for item in data.get("scan_warnings", [])
                if isinstance(item, dict)
            ],
            policy=dict(data["policy"]) if isinstance(data.get("policy"), dict) else {},
        )


@dataclass(slots=True)
class SelectionSummary:
    """Summary of how fast checks were selected."""

    mode: str
    input_source: str
    changed_files: list[ChangedFile] = field(default_factory=list)
    high_risk_reasons: list[str] = field(default_factory=list)
    selected_checks: list[str] = field(default_factory=list)
    full_checks: list[str] = field(default_factory=list)
    targeted_checks: list[str] = field(default_factory=list)
    skipped_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Render this selection summary as JSON-safe data."""
        return {
            "mode": self.mode,
            "input_source": self.input_source,
            "changed_files": [changed.to_dict() for changed in self.changed_files],
            "high_risk_reasons": self.high_risk_reasons,
            "selected_checks": self.selected_checks,
            "full_checks": self.full_checks,
            "targeted_checks": self.targeted_checks,
            "skipped_checks": self.skipped_checks,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SelectionSummary":
        """Load selection metadata from a summary artifact."""
        changed_files = data.get("changed_files", [])
        if not isinstance(changed_files, list):
            changed_files = []
        return cls(
            mode=str(data.get("mode", "")),
            input_source=str(data.get("input_source", "none")),
            changed_files=[
                ChangedFile.from_dict(item)
                for item in changed_files
                if isinstance(item, dict)
            ],
            high_risk_reasons=string_list(data.get("high_risk_reasons", [])),
            selected_checks=string_list(data.get("selected_checks", [])),
            full_checks=string_list(data.get("full_checks", [])),
            targeted_checks=string_list(data.get("targeted_checks", [])),
            skipped_checks=string_list(data.get("skipped_checks", [])),
        )


@dataclass
class RunSummary:
    """Summary for one QA-Z runner invocation."""

    mode: str
    contract_path: str | None
    project_root: str
    status: str
    started_at: str
    finished_at: str
    checks: list[CheckResult] = field(default_factory=list)
    artifact_dir: str | None = None
    contract_title: str | None = None
    message: str = ""
    schema_version: int = 1
    selection: SelectionSummary | None = None
    policy: dict[str, Any] = field(default_factory=dict)
    run_resolution: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    @property
    def totals(self) -> dict[str, int]:
        """Count check results by status."""
        return {
            "passed": sum(1 for check in self.checks if check.status == "passed"),
            "failed": sum(1 for check in self.checks if check.status == "failed"),
            "skipped": sum(1 for check in self.checks if check.status == "skipped"),
            "warning": sum(1 for check in self.checks if check.status == "warning"),
        }

    def to_dict(self) -> dict[str, Any]:
        """Render this summary as JSON-safe data."""
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "contract_path": self.contract_path,
            "project_root": self.project_root,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "checks": [check.to_dict() for check in self.checks],
            "totals": self.totals,
        }
        if self.artifact_dir:
            data["artifact_dir"] = self.artifact_dir
        if self.contract_title:
            data["contract_title"] = self.contract_title
        if self.message:
            data["message"] = self.message
        if self.selection is not None or self.schema_version >= 2:
            data["selection"] = (
                self.selection.to_dict() if self.selection is not None else None
            )
        if self.policy:
            data["policy"] = dict(self.policy)
        if self.run_resolution:
            data["run_resolution"] = dict(self.run_resolution)
        if self.diagnostics:
            data["diagnostics"] = dict(self.diagnostics)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunSummary":
        """Load a run summary from a JSON artifact mapping."""
        required = (
            "mode",
            "contract_path",
            "project_root",
            "status",
            "started_at",
            "finished_at",
            "checks",
        )
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Run summary is missing required fields: {missing}")
        checks = data["checks"]
        if not isinstance(checks, list):
            raise ValueError("Run summary checks must be a list.")
        return cls(
            mode=str(data["mode"]),
            contract_path=(
                str(data["contract_path"])
                if data.get("contract_path") is not None
                else None
            ),
            project_root=str(data["project_root"]),
            status=str(data["status"]),
            started_at=str(data["started_at"]),
            finished_at=str(data["finished_at"]),
            checks=[
                CheckResult.from_dict(check)
                for check in checks
                if isinstance(check, dict)
            ],
            artifact_dir=(
                str(data["artifact_dir"]) if data.get("artifact_dir") else None
            ),
            contract_title=(
                str(data["contract_title"]) if data.get("contract_title") else None
            ),
            message=str(data.get("message", "")),
            schema_version=int(data.get("schema_version", 1)),
            selection=(
                SelectionSummary.from_dict(data["selection"])
                if isinstance(data.get("selection"), dict)
                else None
            ),
            policy=dict(data["policy"]) if isinstance(data.get("policy"), dict) else {},
            run_resolution=(
                dict(data["run_resolution"])
                if isinstance(data.get("run_resolution"), dict)
                else {}
            ),
            diagnostics=(
                dict(data["diagnostics"])
                if isinstance(data.get("diagnostics"), dict)
                else {}
            ),
        )


def string_list(value: Any) -> list[str]:
    """Return a normalized list of strings."""
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def coerce_execution_mode(value: Any) -> ExecutionMode | None:
    """Return a valid execution mode or ``None`` for legacy artifacts."""
    if value in {"full", "targeted", "skipped"}:
        return value
    return None


def coerce_int_mapping(value: Any) -> dict[str, int]:
    """Return a JSON-safe string-to-int mapping."""
    if not isinstance(value, dict):
        return {}
    mapping: dict[str, int] = {}
    for key, item in value.items():
        try:
            mapping[str(key)] = int(item)
        except (TypeError, ValueError):
            continue
    return mapping
