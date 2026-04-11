"""Shared models for deterministic QA-Z runners."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckSpec:
    """A configured subprocess check."""

    id: str
    command: list[str]
    kind: str
    enabled: bool = True
    no_tests: str = "warn"
    timeout_seconds: int | None = None

    @property
    def tool(self) -> str:
        """Return the command executable name for reporting."""
        if not self.command:
            return ""
        return Path(self.command[0]).name

    def to_dict(self) -> dict[str, Any]:
        """Render this check spec as JSON-safe data."""
        return {
            "id": self.id,
            "tool": self.tool,
            "command": self.command,
            "kind": self.kind,
            "enabled": self.enabled,
            "no_tests": self.no_tests,
            "timeout_seconds": self.timeout_seconds,
        }


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
    stdout_tail: str = ""
    stderr_tail: str = ""
    message: str = ""
    error_type: str | None = None

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
        }
        if self.message:
            data["message"] = self.message
        if self.error_type:
            data["error_type"] = self.error_type
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
            stdout_tail=str(data.get("stdout_tail", "")),
            stderr_tail=str(data.get("stderr_tail", "")),
            message=str(data.get("message", "")),
            error_type=(
                str(data["error_type"]) if data.get("error_type") is not None else None
            ),
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
        )
