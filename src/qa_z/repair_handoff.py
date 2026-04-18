"""Normalized repair handoff packets for executor-facing adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qa_z.artifacts import RunSource, format_path
from qa_z.reporters.deep_context import format_finding_location
from qa_z.reporters.repair_prompt import (
    DEFAULT_CONSTRAINTS,
    RepairPacket,
    blocking_severities,
    evidence_tail,
    unique_preserve_order,
)
from qa_z.runners.models import RunSummary


HANDOFF_KIND = "qa_z.repair_handoff"
HANDOFF_SCHEMA_VERSION = 1

DEFAULT_NON_GOALS = [
    "Do not call Codex, Claude, or any external LLM/API from QA-Z.",
    "Do not build a scheduler, queue, or remote execution controller.",
    "Do not make unrelated refactors or broad architecture changes.",
]

DEFAULT_WORKFLOW_STEPS = [
    "Fix blocking repair targets before non-blocking cleanup.",
    "Keep edits focused to affected files unless the evidence clearly points elsewhere.",
    "Run the validation commands after repair.",
    "Regenerate QA-Z review or repair artifacts if validation still fails.",
]


@dataclass(frozen=True)
class RepairTarget:
    """One executor-actionable repair target."""

    id: str
    source: str
    severity: str
    title: str
    rationale: str
    objective: str
    affected_files: list[str] = field(default_factory=list)
    command: list[str] = field(default_factory=list)
    evidence: str = ""
    location: str | None = None
    occurrences: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Render this target as JSON-safe data."""
        data: dict[str, Any] = {
            "id": self.id,
            "source": self.source,
            "severity": self.severity,
            "title": self.title,
            "rationale": self.rationale,
            "objective": self.objective,
            "affected_files": list(self.affected_files),
        }
        if self.command:
            data["command"] = list(self.command)
        if self.evidence:
            data["evidence"] = self.evidence
        if self.location:
            data["location"] = self.location
        if self.occurrences is not None:
            data["occurrences"] = self.occurrences
        return data


@dataclass(frozen=True)
class ValidationCommand:
    """A deterministic post-repair command and expected result."""

    id: str
    command: list[str]
    success_criteria: str

    def to_dict(self) -> dict[str, Any]:
        """Render this validation command as JSON-safe data."""
        return {
            "id": self.id,
            "command": list(self.command),
            "success_criteria": self.success_criteria,
        }


@dataclass(frozen=True)
class RepairHandoffPacket:
    """Stable handoff contract consumed by executor adapters."""

    generated_at: str
    project: dict[str, Any]
    provenance: dict[str, Any]
    repair_needed: bool
    targets: list[RepairTarget]
    affected_files: list[str]
    repair_objectives: list[str]
    constraints: list[str]
    non_goals: list[str]
    validation_commands: list[ValidationCommand]
    success_criteria: list[str]
    workflow_steps: list[str]
    schema_version: int = HANDOFF_SCHEMA_VERSION
    kind: str = HANDOFF_KIND

    def to_dict(self) -> dict[str, Any]:
        """Render this handoff packet as JSON-safe data."""
        return {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project": dict(self.project),
            "provenance": dict(self.provenance),
            "repair": {
                "repair_needed": self.repair_needed,
                "targets": [target.to_dict() for target in self.targets],
                "affected_files": list(self.affected_files),
                "objectives": list(self.repair_objectives),
            },
            "constraints": {
                "must_follow": list(self.constraints),
                "non_goals": list(self.non_goals),
            },
            "validation": {
                "commands": [command.to_dict() for command in self.validation_commands],
                "success_criteria": list(self.success_criteria),
            },
            "workflow": {"suggested_steps": list(self.workflow_steps)},
        }


def build_repair_handoff(
    *,
    repair_packet: RepairPacket,
    summary: RunSummary,
    run_source: RunSource,
    root: Path,
    deep_summary: RunSummary | None = None,
) -> RepairHandoffPacket:
    """Build a normalized executor-facing repair handoff packet."""
    targets = [
        *fast_failure_targets(repair_packet),
        *blocking_deep_targets(repair_packet.deep),
    ]
    affected_files = collect_affected_files(targets)
    has_deep_requirements = any(target.source == "deep_finding" for target in targets)

    return RepairHandoffPacket(
        generated_at=repair_packet.generated_at,
        project=project_context(summary, root),
        provenance=provenance_context(
            repair_packet=repair_packet,
            summary=summary,
            run_source=run_source,
            root=root,
            deep_summary=deep_summary,
        ),
        repair_needed=repair_packet.repair_needed,
        targets=targets,
        affected_files=affected_files,
        repair_objectives=repair_objectives(repair_packet.repair_needed, targets),
        constraints=unique_preserve_order(
            [
                *repair_packet.contract.get("constraints", []),
                *DEFAULT_CONSTRAINTS,
            ]
        ),
        non_goals=list(DEFAULT_NON_GOALS),
        validation_commands=validation_commands(targets, has_deep_requirements),
        success_criteria=unique_preserve_order(
            [*repair_packet.done_when, "No unrelated changes were introduced."]
        ),
        workflow_steps=list(DEFAULT_WORKFLOW_STEPS),
    )


def fast_failure_targets(repair_packet: RepairPacket) -> list[RepairTarget]:
    """Convert failed fast checks into repair targets."""
    targets: list[RepairTarget] = []
    for failure in repair_packet.failures:
        targets.append(
            RepairTarget(
                id=f"check:{failure.id}",
                source="fast_check",
                severity="blocking",
                title=f"Failed {failure.kind} check: {failure.id}",
                rationale=failure.summary,
                objective=(
                    "Make this deterministic check pass without weakening the "
                    "configured gate."
                ),
                affected_files=list(failure.candidate_files),
                command=list(failure.command),
                evidence=evidence_tail(failure),
            )
        )
    return targets


def blocking_deep_targets(deep: dict[str, Any] | None) -> list[RepairTarget]:
    """Convert blocking deep findings into repair targets."""
    if not isinstance(deep, dict) or int(deep.get("blocking_findings_count") or 0) <= 0:
        return []

    blocking = blocking_severities(deep)
    grouped = [
        finding
        for finding in safe_mapping_list(deep.get("top_grouped_findings"))
        if str(finding.get("severity", "")).upper() in blocking
    ]
    if grouped:
        return [deep_group_target(finding) for finding in grouped]

    findings = [
        finding
        for finding in safe_mapping_list(deep.get("top_findings"))
        if str(finding.get("severity", "")).upper() in blocking
    ]
    if not findings:
        findings = safe_mapping_list(deep.get("top_findings"))
    return [deep_finding_target(finding) for finding in findings]


def deep_group_target(finding: dict[str, Any]) -> RepairTarget:
    """Build a repair target from one grouped deep finding."""
    path = str(finding.get("path") or "")
    rule_id = str(finding.get("rule_id") or "unknown")
    message = str(finding.get("message") or "")
    location = format_finding_location(finding)
    occurrences = int(finding.get("count") or 1)
    return RepairTarget(
        id=f"deep:{rule_id}:{path or 'unknown'}",
        source="deep_finding",
        severity=str(finding.get("severity") or "UNKNOWN"),
        title=f"Blocking deep finding: {rule_id}",
        rationale=message or "Blocking deep finding reported by QA-Z.",
        objective=(
            "Remove or mitigate the blocking finding without suppressing the "
            "rule unless the contract explicitly permits it."
        ),
        affected_files=[path] if path else [],
        location=location,
        occurrences=occurrences,
    )


def deep_finding_target(finding: dict[str, Any]) -> RepairTarget:
    """Build a repair target from one ungrouped deep finding."""
    path = str(finding.get("path") or "")
    rule_id = str(finding.get("rule_id") or "unknown")
    message = str(finding.get("message") or "")
    location = format_finding_location(finding)
    return RepairTarget(
        id=f"deep:{rule_id}:{location}",
        source="deep_finding",
        severity=str(finding.get("severity") or "UNKNOWN"),
        title=f"Blocking deep finding: {rule_id}",
        rationale=message or "Blocking deep finding reported by QA-Z.",
        objective=(
            "Remove or mitigate the blocking finding without suppressing the "
            "rule unless the contract explicitly permits it."
        ),
        affected_files=[path] if path else [],
        location=location,
        occurrences=1,
    )


def validation_commands(
    targets: list[RepairTarget], has_deep_requirements: bool
) -> list[ValidationCommand]:
    """Return exact validation commands for the post-repair loop."""
    commands: list[ValidationCommand] = []
    seen_commands: set[tuple[str, ...]] = set()
    for target in targets:
        command_key = tuple(target.command)
        if target.command and command_key not in seen_commands:
            seen_commands.add(command_key)
            commands.append(
                ValidationCommand(
                    id=target.id,
                    command=list(target.command),
                    success_criteria="Command exits with code 0.",
                )
            )

    commands.append(
        ValidationCommand(
            id="qa-z-fast",
            command=["python", "-m", "qa_z", "fast"],
            success_criteria="qa-z fast exits with code 0.",
        )
    )
    if has_deep_requirements:
        commands.append(
            ValidationCommand(
                id="qa-z-deep",
                command=["python", "-m", "qa_z", "deep", "--from-run", "latest"],
                success_criteria=(
                    "qa-z deep exits with code 0 and no blocking findings remain."
                ),
            )
        )
    return commands


def project_context(summary: RunSummary, root: Path) -> dict[str, Any]:
    """Return repository context QA-Z actually knows."""
    return {
        "root": format_path(root, root),
        "summary_project_root": summary.project_root,
        "mode": summary.mode,
    }


def provenance_context(
    *,
    repair_packet: RepairPacket,
    summary: RunSummary,
    run_source: RunSource,
    root: Path,
    deep_summary: RunSummary | None,
) -> dict[str, Any]:
    """Return source artifact pointers for this handoff."""
    return {
        "source_run_dir": format_path(run_source.run_dir, root),
        "fast_summary_path": format_path(run_source.summary_path, root),
        "deep_summary_path": (
            format_path(run_source.run_dir / "deep" / "summary.json", root)
            if deep_summary is not None
            else None
        ),
        "contract_path": repair_packet.contract.get("path"),
        "source_status": summary.status,
        "started_at": summary.started_at,
        "finished_at": summary.finished_at,
    }


def repair_objectives(repair_needed: bool, targets: list[RepairTarget]) -> list[str]:
    """Return concise repair objectives."""
    if not repair_needed:
        return ["No repair required for the source run."]
    if not targets:
        return ["Investigate QA-Z repair-needed state and regenerate artifacts."]
    return [target.objective for target in targets]


def collect_affected_files(targets: list[RepairTarget]) -> list[str]:
    """Collect affected files from targets in deterministic first-seen order."""
    return unique_preserve_order(
        [path for target in targets for path in target.affected_files]
    )


def safe_mapping_list(value: object) -> list[dict[str, Any]]:
    """Return a list containing only mapping values."""
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def repair_handoff_json(handoff: RepairHandoffPacket) -> str:
    """Render a handoff packet as deterministic JSON."""
    return json.dumps(handoff.to_dict(), indent=2, sort_keys=True) + "\n"


def write_repair_handoff_artifact(
    handoff: RepairHandoffPacket, output_dir: Path
) -> Path:
    """Write the normalized handoff JSON artifact."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "handoff.json"
    path.write_text(repair_handoff_json(handoff), encoding="utf-8")
    return path
