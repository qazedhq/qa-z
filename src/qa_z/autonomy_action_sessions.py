"""Session and verification-evidence helpers for autonomy prepared actions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactLoadError
from qa_z.autonomy_action_packets import prepared_action
from qa_z.repair_session import create_repair_session
from qa_z.self_improvement import slugify

__all__ = [
    "baseline_run_from_verify_evidence",
    "existing_session_id",
    "executor_dry_run_command",
    "repair_session_action",
]


def repair_session_action(
    *,
    root: Path,
    config: dict[str, Any],
    loop_id: str,
    task_id: str,
    baseline_run: str,
    context_paths: list[str] | None = None,
    deps: Any | None = None,
) -> dict[str, object]:
    """Prepare a repair session for a task when baseline evidence is available."""
    session_id = f"{loop_id}-{slugify(task_id)}"
    create_repair_session_fn = (
        getattr(deps, "create_repair_session")
        if deps is not None and hasattr(deps, "create_repair_session")
        else create_repair_session
    )
    try:
        result = create_repair_session_fn(
            root=root,
            config=config,
            baseline_run=baseline_run,
            session_id=session_id,
        )
    except (ArtifactLoadError, FileNotFoundError, ValueError) as exc:
        action = prepared_action(
            task_id=task_id,
            action_type="verification_stabilization_plan",
            title="Repair session could not be created from current evidence.",
            next_recommendation="repair baseline evidence before starting a session",
            commands=[
                f"python -m qa_z repair-session start --baseline-run {baseline_run}"
            ],
            context_paths=context_paths,
        )
        action["baseline_run"] = baseline_run
        action["error"] = str(exc)
        return action

    session = result.session
    session_action: dict[str, object] = {
        "type": "repair_session",
        "task_id": task_id,
        "title": "Prepared a local repair session from verification evidence.",
        "baseline_run": baseline_run,
        "session_id": session.session_id,
        "session_dir": session.session_dir,
        "executor_guide": session.executor_guide_path,
        "handoff_dir": session.handoff_dir,
        "next_recommendation": "run external repair, then repair-session verify",
        "commands": [
            f"python -m qa_z repair-session status --session {session.session_dir}",
            f"python -m qa_z repair-session verify --session {session.session_dir} --rerun",
        ],
    }
    if context_paths:
        session_action["context_paths"] = list(context_paths)
    return session_action


def baseline_run_from_verify_evidence(root: Path, task: dict[str, Any]) -> str | None:
    """Find a baseline run path from verify compare artifacts referenced by a task."""
    for entry in task.get("evidence", []):
        if not isinstance(entry, dict) or not entry.get("path"):
            continue
        evidence_path = resolve_evidence_path(root, str(entry["path"]))
        compare_path = (
            evidence_path
            if evidence_path.name == "compare.json"
            else evidence_path.parent / "compare.json"
        )
        compare = read_json_object(compare_path)
        if compare.get("kind") != "qa_z.verify_compare":
            continue
        baseline = compare.get("baseline")
        if isinstance(baseline, dict) and baseline.get("run_dir"):
            return str(baseline["run_dir"])
        baseline_run_id = compare.get("baseline_run_id")
        if baseline_run_id:
            return f".qa-z/runs/{baseline_run_id}"
    return None


def executor_dry_run_command(session_id: str | None) -> str:
    """Return the best local dry-run command for a selected task."""
    if session_id:
        return f"python -m qa_z executor-result dry-run --session {session_id}"
    return "python -m qa_z executor-result dry-run --session <session>"


def existing_session_id(task: dict[str, Any]) -> str | None:
    """Extract an existing repair session id from task evidence paths."""
    for entry in task.get("evidence", []):
        if not isinstance(entry, dict) or not entry.get("path"):
            continue
        parts = Path(str(entry["path"]).replace("\\", "/")).parts
        for index, part in enumerate(parts):
            if part == "sessions" and index + 1 < len(parts):
                return parts[index + 1]
    return None


def resolve_evidence_path(root: Path, value: str) -> Path:
    """Resolve one evidence path relative to the repository root."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object, returning an empty mapping for optional artifacts."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}
