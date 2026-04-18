"""Structured executor result contracts and ingest helpers for QA-Z."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound, format_path

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
            "summary": self.summary,
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
            "command": list(self.command),
            "status": self.status,
            "exit_code": self.exit_code,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutorValidationResult":
        """Load one validation command result."""
        status = required_string(data, "status")
        if status not in EXECUTOR_VALIDATION_STATUSES:
            raise ArtifactLoadError(f"Unsupported validation result status: {status}")
        return cls(
            command=string_list(data.get("command"), field_name="command"),
            status=status,
            exit_code=optional_int(data.get("exit_code")),
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
            "commands": [list(command) for command in self.commands],
            "results": [result.to_dict() for result in self.results],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutorValidation":
        """Load validation summary data."""
        status = required_string(data, "status")
        if status not in EXECUTOR_VALIDATION_STATUSES:
            raise ArtifactLoadError(f"Unsupported validation status: {status}")
        commands = list_of_string_lists(data.get("commands"), field_name="commands")
        raw_results = data.get("results")
        if raw_results is None:
            raw_results = []
        if not isinstance(raw_results, list):
            raise ArtifactLoadError("Executor validation results must be a list.")
        return cls(
            status=status,
            commands=commands,
            results=[
                ExecutorValidationResult.from_dict(item)
                for item in raw_results
                if isinstance(item, dict)
            ],
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
            "summary": self.summary,
            "verification_hint": self.verification_hint,
            "candidate_run_dir": self.candidate_run_dir,
            "changed_files": [item.to_dict() for item in self.changed_files],
            "validation": self.validation.to_dict(),
            "notes": list(self.notes),
        }

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
        raw_changed_files = data.get("changed_files")
        if raw_changed_files is None:
            raw_changed_files = []
        if not isinstance(raw_changed_files, list):
            raise ArtifactLoadError("Executor result changed_files must be a list.")
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
                ExecutorChangedFile.from_dict(item)
                for item in raw_changed_files
                if isinstance(item, dict)
            ],
            validation=ExecutorValidation.from_dict(validation_data),
            notes=string_list(data.get("notes"), field_name="notes"),
        )


def executor_result_template(
    *,
    bridge_id: str,
    created_at: str,
    source_session_id: str,
    source_loop_id: str | None,
    validation_commands: list[list[str]],
    verification_hint: str = "rerun",
) -> dict[str, Any]:
    """Return a bridge-local template for the expected executor result."""
    return {
        "kind": EXECUTOR_RESULT_KIND,
        "schema_version": EXECUTOR_RESULT_SCHEMA_VERSION,
        "bridge_id": bridge_id,
        "source_session_id": source_session_id,
        "source_loop_id": source_loop_id,
        "created_at": created_at,
        "status": "partial",
        "summary": PLACEHOLDER_SUMMARY,
        "verification_hint": verification_hint,
        "candidate_run_dir": None,
        "changed_files": [],
        "validation": {
            "status": "not_run",
            "commands": [list(command) for command in validation_commands],
            "results": [],
        },
        "notes": [],
    }


def load_executor_result(path: Path) -> ExecutorResult:
    """Load an executor result artifact from disk."""
    data = read_json_object(path)
    return ExecutorResult.from_dict(data)


def resolve_bridge_manifest_path(root: Path, bridge_id: str) -> Path:
    """Resolve a bridge id to its bridge manifest path."""
    path = (root / ".qa-z" / "executor" / bridge_id / "bridge.json").resolve()
    if not path.is_file():
        raise ArtifactSourceNotFound(f"Executor bridge not found: {path}")
    return path


def load_bridge_manifest(root: Path, bridge_id: str) -> dict[str, Any]:
    """Load and validate a bridge manifest."""
    path = resolve_bridge_manifest_path(root, bridge_id)
    data = read_json_object(path)
    if data.get("kind") != "qa_z.executor_bridge":
        raise ArtifactLoadError(f"Unsupported executor bridge artifact: {path}")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def store_executor_result(
    root: Path, session_dir: Path, result: ExecutorResult
) -> Path:
    """Persist an ingested executor result under its owning session."""
    path = session_dir / "executor_result.json"
    write_json(path, result.to_dict())
    return path


def ingest_summary_dict(
    *,
    result_id: str,
    bridge_id: str,
    session_id: str,
    source_loop_id: str | None,
    result_status: str,
    ingest_status: str,
    stored_result_path: Path | None,
    root: Path,
    session_state: str | None,
    verification_hint: str,
    verification_triggered: bool,
    verification_verdict: str | None,
    verify_summary_path: Path | None,
    warnings: list[str],
    freshness_check: dict[str, Any],
    provenance_check: dict[str, Any],
    verify_resume_status: str,
    backlog_implications: list[dict[str, Any]],
    next_recommendation: str,
    ingest_artifact_path: Path,
    ingest_report_path: Path,
) -> dict[str, Any]:
    """Build CLI JSON output for executor result ingestion."""
    return {
        "kind": EXECUTOR_RESULT_INGEST_KIND,
        "schema_version": EXECUTOR_RESULT_SCHEMA_VERSION,
        "result_id": result_id,
        "bridge_id": bridge_id,
        "session_id": session_id,
        "source_loop_id": source_loop_id,
        "result_status": result_status,
        "ingest_status": ingest_status,
        "stored_result_path": (
            format_path(stored_result_path, root) if stored_result_path else None
        ),
        "session_state": session_state,
        "verification_hint": verification_hint,
        "verification_triggered": verification_triggered,
        "verification_verdict": verification_verdict,
        "verify_summary_path": (
            format_path(verify_summary_path, root) if verify_summary_path else None
        ),
        "warnings": list(warnings),
        "freshness_check": dict(freshness_check),
        "provenance_check": dict(provenance_check),
        "verify_resume_status": verify_resume_status,
        "backlog_implications": list(backlog_implications),
        "next_recommendation": next_recommendation,
        "ingest_artifact_path": format_path(ingest_artifact_path, root),
        "ingest_report_path": format_path(ingest_report_path, root),
    }


def next_recommendation_for_result(status: str) -> str:
    """Return a deterministic recommendation when verification is skipped."""
    if status == "completed":
        return "run repair-session verify"
    if status == "no_op":
        return "inspect no-op result"
    if status == "not_applicable":
        return "confirm task applicability"
    if status == "failed":
        return "triage executor failure"
    return "continue repair"


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a required JSON object artifact."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactSourceNotFound(f"Could not read artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(f"Artifact is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ArtifactLoadError(f"Artifact must contain an object: {path}")
    return data


def required_string(data: dict[str, Any], field_name: str) -> str:
    """Return a required non-empty string field."""
    value = optional_string(data.get(field_name))
    if value is None:
        raise ArtifactLoadError(
            f"Executor result is missing required field: {field_name}"
        )
    return value


def optional_string(value: object) -> str | None:
    """Return a stripped string value or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def optional_int(value: object) -> int | None:
    """Return an integer when present and valid."""
    if value is None or value == "":
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise ArtifactLoadError(
            "Executor result exit_code must be an integer."
        ) from exc


def string_list(value: object, *, field_name: str) -> list[str]:
    """Return a normalized list of strings."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise ArtifactLoadError(f"Executor result field {field_name} must be a list.")
    return [str(item).strip() for item in value if str(item).strip()]


def list_of_string_lists(value: object, *, field_name: str) -> list[list[str]]:
    """Return a normalized list of argv arrays."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise ArtifactLoadError(f"Executor result field {field_name} must be a list.")
    commands: list[list[str]] = []
    for item in value:
        commands.append(string_list(item, field_name=field_name))
    return commands
