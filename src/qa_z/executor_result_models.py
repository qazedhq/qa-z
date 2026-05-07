"""Structured executor-result model contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from qa_z.artifacts import ArtifactLoadError
from qa_z.executor_result_parsing import (
    list_of_dicts,
    list_of_string_lists,
    optional_int,
    optional_string,
    required_string,
    string_list,
)
from qa_z.runners.models import redact_sensitive_text, redact_sensitive_value

EXECUTOR_RESULT_KIND = "qa_z.executor_result"
EXECUTOR_RESULT_INGEST_KIND = "qa_z.executor_result_ingest"
EXECUTOR_RESULT_SCHEMA_VERSION = 1

ExecutorResultStatus = Literal[
    "completed", "partial", "failed", "no_op", "not_applicable"
]
ExecutorValidationStatus = Literal["passed", "failed", "not_run"]
ExecutorVerificationHint = Literal["rerun", "candidate_run", "skip"]

CHANGED_FILE_STATUSES = {"added", "modified", "deleted", "renamed", "unknown"}
EXECUTOR_RESULT_STATUSES = {
    "completed",
    "partial",
    "failed",
    "no_op",
    "not_applicable",
}
EXECUTOR_VALIDATION_STATUSES = {"passed", "failed", "not_run"}
EXECUTOR_VERIFICATION_HINTS = {"rerun", "candidate_run", "skip"}

PLACEHOLDER_SUMMARY = "Replace with executor outcome summary before ingest."


@dataclass(frozen=True)
class ExecutorChangedFile:
    """One file the external executor changed or inspected."""

    path: str
    status: str
    old_path: str | None = None
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Render a JSON-safe changed-file entry."""
        return {
            "path": self.path,
            "status": self.status,
            "old_path": self.old_path,
            "summary": redact_sensitive_text(self.summary),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutorChangedFile":
        """Load one changed-file entry from JSON-safe data."""
        path = required_string(data, "path")
        status = required_string(data, "status")
        if status not in CHANGED_FILE_STATUSES:
            raise ArtifactLoadError(f"Unsupported changed file status: {status}")
        return cls(
            path=path,
            status=status,
            old_path=optional_string(data.get("old_path")),
            summary=optional_string(data.get("summary")) or "",
        )


@dataclass(frozen=True)
class ExecutorValidationResult:
    """One validation command result reported by the external executor."""

    command: list[str]
    status: str
    exit_code: int | None
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Render a JSON-safe validation command result."""
        return {
            "command": redact_sensitive_value(list(self.command)),
            "status": self.status,
            "exit_code": self.exit_code,
            "summary": redact_sensitive_text(self.summary),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutorValidationResult":
        """Load one validation command result."""
        status = required_string(data, "status")
        if status not in EXECUTOR_VALIDATION_STATUSES:
            raise ArtifactLoadError(f"Unsupported validation result status: {status}")
        command = string_list(
            data.get("command"), field_name="validation result command"
        )
        if not command:
            raise ArtifactLoadError(
                "Executor result field validation result command must contain "
                "at least one argument."
            )
        return cls(
            command=command,
            status=status,
            exit_code=optional_int(data.get("exit_code"), field_name="exit_code"),
            summary=optional_string(data.get("summary")) or "",
        )


@dataclass(frozen=True)
class ExecutorValidation:
    """Validation summary carried in an executor result."""

    status: str
    commands: list[list[str]] = field(default_factory=list)
    results: list[ExecutorValidationResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Render a JSON-safe validation section."""
        return {
            "status": self.status,
            "commands": [
                redact_sensitive_value(list(command)) for command in self.commands
            ],
            "results": [result.to_dict() for result in self.results],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutorValidation":
        """Load validation summary data."""
        status = required_string(data, "status")
        if status not in EXECUTOR_VALIDATION_STATUSES:
            raise ArtifactLoadError(f"Unsupported validation status: {status}")
        commands = list_of_string_lists(data.get("commands"), field_name="commands")
        raw_results = list_of_dicts(
            data.get("results"), field_name="validation results"
        )
        return cls(
            status=status,
            commands=commands,
            results=[ExecutorValidationResult.from_dict(item) for item in raw_results],
        )


@dataclass(frozen=True)
class ExecutorResult:
    """Structured return artifact from an external executor."""

    bridge_id: str
    source_session_id: str
    source_loop_id: str | None
    created_at: str
    status: str
    summary: str
    verification_hint: str
    candidate_run_dir: str | None = None
    changed_files: list[ExecutorChangedFile] = field(default_factory=list)
    validation: ExecutorValidation = field(
        default_factory=lambda: ExecutorValidation(status="not_run")
    )
    notes: list[str] = field(default_factory=list)
    schema_version: int = EXECUTOR_RESULT_SCHEMA_VERSION
    kind: str = EXECUTOR_RESULT_KIND

    def to_dict(self) -> dict[str, Any]:
        """Render this result as deterministic JSON-safe data."""
        return {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "source_session_id": self.source_session_id,
            "source_loop_id": self.source_loop_id,
            "created_at": self.created_at,
            "status": self.status,
            "summary": redact_sensitive_text(self.summary),
            "verification_hint": self.verification_hint,
            "candidate_run_dir": self.serialized_candidate_run_dir(),
            "changed_files": [item.to_dict() for item in self.changed_files],
            "validation": self.validation.to_dict(),
            "notes": redact_sensitive_value(list(self.notes)),
        }

    def serialized_candidate_run_dir(self) -> str | None:
        """Return a candidate run path only when verification will use it."""
        if self.verification_hint != "candidate_run":
            return None
        return self.candidate_run_dir

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutorResult":
        """Load and validate an executor result payload."""
        if data.get("kind") != EXECUTOR_RESULT_KIND:
            raise ArtifactLoadError("Executor result has an unsupported kind.")
        if int(data.get("schema_version", 0)) != EXECUTOR_RESULT_SCHEMA_VERSION:
            raise ArtifactLoadError(
                "Executor result has an unsupported schema version."
            )
        bridge_id = required_string(data, "bridge_id")
        source_session_id = required_string(data, "source_session_id")
        created_at = required_string(data, "created_at")
        status = required_string(data, "status")
        if status not in EXECUTOR_RESULT_STATUSES:
            raise ArtifactLoadError(f"Unsupported executor result status: {status}")
        summary = required_string(data, "summary")
        if summary == PLACEHOLDER_SUMMARY:
            raise ArtifactLoadError(
                "Executor result still uses the bridge placeholder summary."
            )
        verification_hint = required_string(data, "verification_hint")
        if verification_hint not in EXECUTOR_VERIFICATION_HINTS:
            raise ArtifactLoadError(
                f"Unsupported executor verification hint: {verification_hint}"
            )
        candidate_run_dir = optional_string(data.get("candidate_run_dir"))
        if verification_hint == "candidate_run" and not candidate_run_dir:
            raise ArtifactLoadError(
                "Executor result requires candidate_run_dir when "
                "verification_hint is candidate_run."
            )
        raw_changed_files = list_of_dicts(
            data.get("changed_files"), field_name="changed_files"
        )
        validation_data = data.get("validation")
        if not isinstance(validation_data, dict):
            raise ArtifactLoadError("Executor result validation must be an object.")
        return cls(
            bridge_id=bridge_id,
            source_session_id=source_session_id,
            source_loop_id=optional_string(data.get("source_loop_id")),
            created_at=created_at,
            status=status,
            summary=summary,
            verification_hint=verification_hint,
            candidate_run_dir=candidate_run_dir,
            changed_files=[
                ExecutorChangedFile.from_dict(item) for item in raw_changed_files
            ],
            validation=ExecutorValidation.from_dict(validation_data),
            notes=string_list(data.get("notes"), field_name="notes"),
        )
