"""Light repair-session orchestration artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from qa_z.artifacts import ArtifactLoadError
from qa_z.repair_handoff import RepairHandoffPacket

REPAIR_SESSION_KIND = "qa_z.repair_session"
REPAIR_SESSION_SUMMARY_KIND = "qa_z.repair_session_summary"
REPAIR_SESSION_SCHEMA_VERSION = 1

RepairSessionState = Literal[
    "created",
    "handoff_ready",
    "waiting_for_external_repair",
    "candidate_generated",
    "verification_complete",
    "completed",
    "failed",
]
REPAIR_SESSION_STATES = (
    "created",
    "handoff_ready",
    "waiting_for_external_repair",
    "candidate_generated",
    "verification_complete",
    "completed",
    "failed",
)


@dataclass(frozen=True)
class RepairSession:
    """Persisted state for one local repair workflow."""

    session_id: str
    session_dir: str
    baseline_run_dir: str
    handoff_dir: str
    executor_guide_path: str
    state: RepairSessionState
    created_at: str
    updated_at: str
    baseline_fast_summary_path: str
    handoff_artifacts: dict[str, str] = field(default_factory=dict)
    candidate_run_dir: str | None = None
    verify_dir: str | None = None
    verify_artifacts: dict[str, str] = field(default_factory=dict)
    outcome_path: str | None = None
    summary_path: str | None = None
    baseline_deep_summary_path: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    safety_artifacts: dict[str, str] = field(default_factory=dict)
    executor_result_path: str | None = None
    executor_result_status: str | None = None
    executor_result_validation_status: str | None = None
    executor_result_bridge_id: str | None = None
    schema_version: int = REPAIR_SESSION_SCHEMA_VERSION
    kind: str = REPAIR_SESSION_KIND

    def to_dict(self) -> dict[str, Any]:
        """Render the session manifest as deterministic JSON-safe data."""
        return {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "baseline_run_dir": self.baseline_run_dir,
            "baseline_fast_summary_path": self.baseline_fast_summary_path,
            "baseline_deep_summary_path": self.baseline_deep_summary_path,
            "handoff_dir": self.handoff_dir,
            "handoff_artifacts": dict(self.handoff_artifacts),
            "executor_guide_path": self.executor_guide_path,
            "candidate_run_dir": self.candidate_run_dir,
            "verify_dir": self.verify_dir,
            "verify_artifacts": dict(self.verify_artifacts),
            "outcome_path": self.outcome_path,
            "summary_path": self.summary_path,
            "provenance": dict(self.provenance),
            "safety_artifacts": dict(self.safety_artifacts),
            "executor_result_path": self.executor_result_path,
            "executor_result_status": self.executor_result_status,
            "executor_result_validation_status": self.executor_result_validation_status,
            "executor_result_bridge_id": self.executor_result_bridge_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepairSession":
        """Load and validate a repair-session manifest."""
        if data.get("kind") != REPAIR_SESSION_KIND:
            raise ArtifactLoadError("Repair session manifest has an unsupported kind.")
        if int(data.get("schema_version", 0)) != REPAIR_SESSION_SCHEMA_VERSION:
            raise ArtifactLoadError(
                "Repair session manifest has an unsupported schema version."
            )
        required = (
            "session_id",
            "session_dir",
            "baseline_run_dir",
            "handoff_dir",
            "executor_guide_path",
            "state",
            "created_at",
            "updated_at",
            "baseline_fast_summary_path",
        )
        missing = [key for key in required if not data.get(key)]
        if missing:
            raise ArtifactLoadError(
                f"Repair session manifest is missing required fields: {missing}"
            )
        state = str(data["state"])
        if state not in REPAIR_SESSION_STATES:
            raise ArtifactLoadError(f"Unsupported repair session state: {state}")
        return cls(
            session_id=str(data["session_id"]),
            session_dir=str(data["session_dir"]),
            baseline_run_dir=str(data["baseline_run_dir"]),
            handoff_dir=str(data["handoff_dir"]),
            executor_guide_path=str(data["executor_guide_path"]),
            state=state,  # type: ignore[arg-type]
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            baseline_fast_summary_path=str(data["baseline_fast_summary_path"]),
            handoff_artifacts=string_mapping(data.get("handoff_artifacts", {})),
            candidate_run_dir=optional_string(data.get("candidate_run_dir")),
            verify_dir=optional_string(data.get("verify_dir")),
            verify_artifacts=string_mapping(data.get("verify_artifacts", {})),
            outcome_path=optional_string(data.get("outcome_path")),
            summary_path=optional_string(data.get("summary_path")),
            baseline_deep_summary_path=optional_string(
                data.get("baseline_deep_summary_path")
            ),
            provenance=dict(data["provenance"])
            if isinstance(data.get("provenance"), dict)
            else {},
            safety_artifacts=string_mapping(data.get("safety_artifacts", {})),
            executor_result_path=optional_string(data.get("executor_result_path")),
            executor_result_status=optional_string(data.get("executor_result_status")),
            executor_result_validation_status=optional_string(
                data.get("executor_result_validation_status")
            ),
            executor_result_bridge_id=optional_string(
                data.get("executor_result_bridge_id")
            ),
        )


@dataclass(frozen=True)
class RepairSessionStartResult:
    """Artifacts created by repair-session start."""

    session: RepairSession
    handoff: RepairHandoffPacket


from qa_z.repair_session_dry_run import (  # noqa: E402
    dry_run_action_summary_text,
    enrich_dry_run_operator_fields,
    load_session_dry_run_summary,
    normalized_dry_run_actions,
    safety_package_id_for_session,
    synthesize_session_dry_run_summary,
)
from qa_z.repair_session_lifecycle import (  # noqa: E402
    complete_session_verification,
    create_repair_session,
    load_repair_session,
)
from qa_z.repair_session_outcome import (  # noqa: E402
    recommendation_for_verdict,
    render_outcome_markdown,
    session_status_dict,
    session_summary_dict,
    session_summary_json,
)
from qa_z.repair_session_render import (  # noqa: E402
    render_session_start_stdout,
    render_session_status,
    render_session_status_with_dry_run,
    render_session_verify_stdout,
)
from qa_z.repair_session_support import (  # noqa: E402
    create_session_id,
    ensure_session_safety_artifacts,
    handoff_artifact_paths,
    normalize_session_id,
    optional_string,
    resolve_session_dir,
    sessions_dir,
    string_mapping,
    utc_now,
    write_session_manifest,
)

__all__ = [
    "REPAIR_SESSION_KIND",
    "REPAIR_SESSION_SUMMARY_KIND",
    "REPAIR_SESSION_SCHEMA_VERSION",
    "RepairSessionState",
    "REPAIR_SESSION_STATES",
    "RepairSession",
    "RepairSessionStartResult",
    "create_repair_session",
    "complete_session_verification",
    "load_repair_session",
    "render_session_status",
    "render_session_status_with_dry_run",
    "render_session_start_stdout",
    "render_session_verify_stdout",
    "write_session_manifest",
    "ensure_session_safety_artifacts",
    "handoff_artifact_paths",
    "resolve_session_dir",
    "sessions_dir",
    "create_session_id",
    "normalize_session_id",
    "utc_now",
    "optional_string",
    "string_mapping",
    "session_status_dict",
    "session_summary_json",
    "session_summary_dict",
    "render_outcome_markdown",
    "recommendation_for_verdict",
    "load_session_dry_run_summary",
    "synthesize_session_dry_run_summary",
    "safety_package_id_for_session",
    "enrich_dry_run_operator_fields",
    "normalized_dry_run_actions",
    "dry_run_action_summary_text",
]
