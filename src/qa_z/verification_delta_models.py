"""Delta and finding verification models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

VerificationCategory = Literal[
    "resolved",
    "still_failing",
    "regressed",
    "newly_introduced",
    "skipped_or_not_comparable",
]


@dataclass(frozen=True)
class FastCheckDelta:
    """Comparison result for one fast check id."""

    id: str
    classification: VerificationCategory
    baseline_status: str | None
    candidate_status: str | None
    baseline_exit_code: int | None
    candidate_exit_code: int | None
    kind: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Render this fast-check delta as JSON-safe data."""
        data: dict[str, Any] = {
            "id": self.id,
            "classification": self.classification,
            "baseline_status": self.baseline_status,
            "candidate_status": self.candidate_status,
            "baseline_exit_code": self.baseline_exit_code,
            "candidate_exit_code": self.candidate_exit_code,
        }
        if self.kind:
            data["kind"] = self.kind
        if self.message:
            data["message"] = self.message
        return data


@dataclass(frozen=True)
class VerificationFinding:
    """Normalized deep finding identity used for deterministic comparison."""

    source: str
    rule_id: str
    severity: str
    path: str
    line: int | None
    message: str
    blocking: bool
    grouped: bool = False
    occurrences: int | None = None

    @property
    def id(self) -> str:
        """Return the stable human and JSON id for this finding."""
        location = self.path or "unknown"
        if self.line is not None:
            location = f"{location}:{self.line}"
        return f"{self.source}:{self.rule_id}:{location}"

    @property
    def strict_key(self) -> tuple[str, str, str, int | None, str, bool]:
        """Return the strict identity including the normalized message."""
        return (
            self.source,
            self.rule_id,
            self.path,
            self.line,
            _normalize_message(self.message),
            self.grouped,
        )

    @property
    def relaxed_key(self) -> tuple[str, str, str, int | None, bool]:
        """Return the conservative relaxed identity excluding message text."""
        line = None if self.grouped else self.line
        return (self.source, self.rule_id, self.path, line, self.grouped)

    def to_dict(self) -> dict[str, Any]:
        """Render this finding as JSON-safe data."""
        data: dict[str, Any] = {
            "id": self.id,
            "source": self.source,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "path": self.path,
            "line": self.line,
            "message": self.message,
            "blocking": self.blocking,
            "grouped": self.grouped,
        }
        if self.occurrences is not None:
            data["occurrences"] = self.occurrences
        return data


@dataclass(frozen=True)
class VerificationFindingDelta:
    """Comparison result for one deep finding identity."""

    id: str
    classification: VerificationCategory
    source: str
    rule_id: str
    path: str
    line: int | None
    baseline_severity: str | None = None
    candidate_severity: str | None = None
    baseline_blocking: bool | None = None
    candidate_blocking: bool | None = None
    message: str = ""
    match: Literal["strict", "relaxed", "none"] = "none"

    def to_dict(self) -> dict[str, Any]:
        """Render this finding delta as JSON-safe data."""
        return {
            "id": self.id,
            "classification": self.classification,
            "source": self.source,
            "rule_id": self.rule_id,
            "path": self.path,
            "line": self.line,
            "baseline_severity": self.baseline_severity,
            "candidate_severity": self.candidate_severity,
            "baseline_blocking": self.baseline_blocking,
            "candidate_blocking": self.candidate_blocking,
            "message": self.message,
            "match": self.match,
        }


def _normalize_message(message: str) -> str:
    return " ".join(message.split()).strip().lower()


__all__ = [
    "FastCheckDelta",
    "VerificationCategory",
    "VerificationFinding",
    "VerificationFindingDelta",
]
