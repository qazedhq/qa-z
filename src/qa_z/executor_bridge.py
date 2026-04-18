"""External executor bridge packages for QA-Z repair sessions."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound, format_path
from qa_z.repair_session import RepairSession, load_repair_session

EXECUTOR_BRIDGE_KIND = "qa_z.executor_bridge"
EXECUTOR_BRIDGE_SCHEMA_VERSION = 1

DEFAULT_NON_GOALS = [
    "do not broaden scope",
    "do not perform unrelated refactors",
    "do not weaken deterministic checks",
    "do not call Codex or Claude APIs from QA-Z",
    "do not commit, push, create branches, or post GitHub comments",
]

DEFAULT_SAFETY_CONSTRAINTS = [
    "Use only the packaged QA-Z evidence and linked handoff artifacts.",
    "Keep edits focused on the selected repair-session objective.",
    "Record partial completion honestly if validation cannot pass.",
    "Return control to QA-Z through repair-session verification.",
]


class ExecutorBridgeError(ValueError):
    """Raised when a bridge package cannot be created from available evidence."""


@dataclass(frozen=True)
class ExecutorBridgePaths:
    """Paths written for one executor bridge package."""

    bridge_dir: Path
    manifest_path: Path
    executor_guide_path: Path
    codex_path: Path
    claude_path: Path


def create_executor_bridge(
    *,
    root: Path,
    from_loop: str | None = None,
    from_session: str | None = None,
    bridge_id: str | None = None,
    output_dir: Path | None = None,
    now: str | None = None,
) -> ExecutorBridgePaths:
    """Create an executor-ready package from a loop outcome or session."""
    root = root.resolve()
    if bool(from_loop) == bool(from_session):
        raise ExecutorBridgeError("Provide exactly one of from_loop or from_session.")

    loop_outcome: dict[str, Any] | None = None
    action: dict[str, Any] | None = None
    if from_loop:
        loop_outcome = load_loop_outcome(root, from_loop)
        action = repair_session_action(loop_outcome)
        session_ref = str(action.get("session_dir") or action.get("session_id") or "")
        if not session_ref:
            raise ExecutorBridgeError(
                "Loop repair_session action is missing a session reference."
            )
    else:
        session_ref = str(from_session)

    session = load_repair_session(root, session_ref)
    generated_at = now or utc_now()
    source_loop_id = (
        optional_string(loop_outcome.get("loop_id")) if loop_outcome else None
    )
    resolved_bridge_id = normalize_bridge_id(
        bridge_id or default_bridge_id(generated_at, source_loop_id, session.session_id)
    )
    bridge_dir = resolve_bridge_dir(
        root=root,
        bridge_id=resolved_bridge_id,
        output_dir=output_dir,
    )
    if bridge_dir.exists():
        raise ExecutorBridgeError(
            f"Executor bridge already exists: {format_path(bridge_dir, root)}"
        )

    bridge_dir.mkdir(parents=True, exist_ok=False)
    inputs_dir = bridge_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    copied_inputs = copy_bridge_inputs(
        root=root,
        inputs_dir=inputs_dir,
        session=session,
        loop_outcome=loop_outcome,
    )
    handoff = read_json_object(resolve_path(root, session.handoff_dir) / "handoff.json")
    validation_commands = bridge_validation_commands(session)
    manifest = bridge_manifest(
        root=root,
        bridge_dir=bridge_dir,
        bridge_id=resolved_bridge_id,
        generated_at=generated_at,
        source_loop_id=source_loop_id,
        selected_task_ids=selected_task_ids(loop_outcome),
        session=session,
        handoff=handoff,
        copied_inputs=copied_inputs,
        validation_commands=validation_commands,
    )

    manifest_path = bridge_dir / "bridge.json"
    executor_guide_path = bridge_dir / "executor_guide.md"
    codex_path = bridge_dir / "codex.md"
    claude_path = bridge_dir / "claude.md"
    write_json(manifest_path, manifest)
    executor_guide_path.write_text(
        render_executor_bridge_guide(manifest, handoff), encoding="utf-8"
    )
    codex_path.write_text(
        render_executor_specific_guide(manifest, "Codex"), encoding="utf-8"
    )
    claude_path.write_text(
        render_executor_specific_guide(manifest, "Claude"), encoding="utf-8"
    )
    return ExecutorBridgePaths(
        bridge_dir=bridge_dir,
        manifest_path=manifest_path,
        executor_guide_path=executor_guide_path,
        codex_path=codex_path,
        claude_path=claude_path,
    )


def load_loop_outcome(root: Path, from_loop: str) -> dict[str, Any]:
    """Load an autonomy outcome by loop id, loop directory, or outcome path."""
    path = resolve_loop_outcome_path(root, from_loop)
    data = read_json_object(path)
    if data.get("kind") != "qa_z.autonomy_outcome":
        raise ArtifactLoadError(f"Unsupported autonomy outcome artifact: {path}")
    return data


def resolve_loop_outcome_path(root: Path, from_loop: str) -> Path:
    """Resolve loop id, loop directory, or outcome artifact to outcome.json."""
    path = Path(from_loop).expanduser()
    if path.name == "outcome.json":
        candidate = path
    elif not path.is_absolute() and len(path.parts) == 1:
        candidate = root / ".qa-z" / "loops" / path / "outcome.json"
    else:
        candidate = path / "outcome.json"
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise ArtifactSourceNotFound(f"Autonomy outcome not found: {candidate}")
    return candidate


def repair_session_action(loop_outcome: dict[str, Any]) -> dict[str, Any]:
    """Return the first repair_session action from an autonomy outcome."""
    actions = loop_outcome.get("actions_prepared")
    if not isinstance(actions, list):
        actions = []
    for action in actions:
        if isinstance(action, dict) and action.get("type") == "repair_session":
            return action
    raise ExecutorBridgeError("Loop outcome does not contain a repair_session action.")


def bridge_manifest(
    *,
    root: Path,
    bridge_dir: Path,
    bridge_id: str,
    generated_at: str,
    source_loop_id: str | None,
    selected_task_ids: list[str],
    session: RepairSession,
    handoff: dict[str, Any],
    copied_inputs: dict[str, Any],
    validation_commands: list[list[str]],
) -> dict[str, Any]:
    """Build the machine-readable bridge manifest."""
    handoff_dir = resolve_path(root, session.handoff_dir)
    return {
        "kind": EXECUTOR_BRIDGE_KIND,
        "schema_version": EXECUTOR_BRIDGE_SCHEMA_VERSION,
        "bridge_id": bridge_id,
        "created_at": generated_at,
        "status": "ready_for_external_executor",
        "source_loop_id": source_loop_id,
        "source_session_id": session.session_id,
        "selected_task_ids": selected_task_ids,
        "baseline_run": session.baseline_run,
        "session_dir": session.session_dir,
        "handoff_dir": session.handoff_dir,
        "bridge_dir": format_path(bridge_dir, root),
        "inputs": copied_inputs,
        "handoff_paths": {
            "handoff_json": format_path(handoff_dir / "handoff.json", root),
            "codex_markdown": format_path(handoff_dir / "codex.md", root),
            "claude_markdown": format_path(handoff_dir / "claude.md", root),
            "executor_guide": session.executor_guide_path,
        },
        "validation_commands": validation_commands,
        "safety_constraints": list(DEFAULT_SAFETY_CONSTRAINTS),
        "non_goals": list(DEFAULT_NON_GOALS),
        "return_contract": {
            "expected_next_step": "run repair-session verify after external repair",
            "candidate_run": "<candidate-run>",
            "verify_command": validation_commands[0] if validation_commands else None,
            "expected_verify_artifacts": {
                "summary_json": f"{session.session_dir}/verify/summary.json",
                "compare_json": f"{session.session_dir}/verify/compare.json",
                "report_markdown": f"{session.session_dir}/verify/report.md",
            },
        },
        "evidence_summary": bridge_evidence_summary(
            session=session,
            handoff=handoff,
        ),
    }


def copy_bridge_inputs(
    *,
    root: Path,
    inputs_dir: Path,
    session: RepairSession,
    loop_outcome: dict[str, Any] | None,
) -> dict[str, Any]:
    """Copy bridge source inputs into the package and return manifest paths."""
    copied: dict[str, Any] = {
        "autonomy_outcome": None,
        "session": None,
        "handoff": None,
    }
    if loop_outcome:
        outcome_path_text = str(loop_outcome.get("artifacts", {}).get("outcome", ""))
        if outcome_path_text:
            copy_input(
                root=root,
                source=resolve_path(root, outcome_path_text),
                target=inputs_dir / "autonomy_outcome.json",
            )
            copied["autonomy_outcome"] = format_path(
                inputs_dir / "autonomy_outcome.json", root
            )

    session_path = resolve_path(root, session.session_dir) / "session.json"
    handoff_path = resolve_path(root, session.handoff_dir) / "handoff.json"
    copy_input(root=root, source=session_path, target=inputs_dir / "session.json")
    copy_input(root=root, source=handoff_path, target=inputs_dir / "handoff.json")
    copied["session"] = format_path(inputs_dir / "session.json", root)
    copied["handoff"] = format_path(inputs_dir / "handoff.json", root)
    return copied


def bridge_validation_commands(session: RepairSession) -> list[list[str]]:
    """Return the deterministic post-edit validation command for this bridge."""
    return [
        [
            "python",
            "-m",
            "qa_z",
            "repair-session",
            "verify",
            "--session",
            session.session_dir,
            "--candidate-run",
            "<candidate-run>",
        ]
    ]


def bridge_evidence_summary(
    *,
    session: RepairSession,
    handoff: dict[str, Any],
) -> dict[str, Any]:
    """Return compact bridge evidence context."""
    repair = handoff.get("repair") if isinstance(handoff, dict) else {}
    targets = repair.get("targets") if isinstance(repair, dict) else []
    return {
        "session_state": session.state,
        "target_count": len(targets) if isinstance(targets, list) else 0,
    }


def render_executor_bridge_guide(
    manifest: dict[str, Any], handoff: dict[str, Any]
) -> str:
    """Render the human-readable bridge guide."""
    repair = handoff.get("repair") if isinstance(handoff, dict) else {}
    targets = repair.get("targets") if isinstance(repair, dict) else []
    objectives = repair.get("objectives") if isinstance(repair, dict) else []
    lines = [
        "# QA-Z External Executor Bridge",
        "",
        "This package gives an external human, Codex, or Claude executor local QA-Z repair evidence.",
        "QA-Z does not call live model APIs, edit code, schedule work, commit, push, or post GitHub comments.",
        "",
        "## Bridge",
        "",
        f"- Bridge id: `{manifest['bridge_id']}`",
        f"- Status: `{manifest['status']}`",
        f"- Source loop: `{manifest.get('source_loop_id') or 'none'}`",
        f"- Source session: `{manifest['source_session_id']}`",
        f"- Baseline run: `{manifest['baseline_run']}`",
        "",
        "## What To Fix",
        "",
    ]
    if isinstance(objectives, list) and objectives:
        lines.extend(f"- {objective}" for objective in objectives)
    elif isinstance(targets, list) and targets:
        lines.extend(
            f"- {target.get('objective')}"
            for target in targets
            if isinstance(target, dict)
        )
    else:
        lines.append("- Use the packaged handoff artifacts to identify the target.")
    lines.extend(
        [
            "",
            "## Where To Look",
            "",
            f"- Session manifest: `{manifest['inputs']['session']}`",
            f"- Handoff JSON: `{manifest['inputs']['handoff']}`",
        ]
    )
    if manifest["inputs"].get("autonomy_outcome"):
        lines.append(f"- Autonomy outcome: `{manifest['inputs']['autonomy_outcome']}`")
    lines.extend(["", "## Do Not Change", ""])
    lines.extend(f"- {item}" for item in manifest["non_goals"])
    lines.extend(["", "## Validation", ""])
    for command in manifest["validation_commands"]:
        lines.append(f"- `{format_command(command)}`")
    lines.extend(
        [
            "",
            "## Return Contract",
            "",
            f"- Return: {manifest['return_contract']['expected_next_step']}",
            "- Replace `<candidate-run>` with the candidate run directory after external repair.",
            "- If validation fails, preserve partial evidence and record what remains.",
            f"- Verify summary: `{manifest['return_contract']['expected_verify_artifacts']['summary_json']}`",
            f"- Verify compare: `{manifest['return_contract']['expected_verify_artifacts']['compare_json']}`",
            f"- Verify report: `{manifest['return_contract']['expected_verify_artifacts']['report_markdown']}`",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_executor_specific_guide(manifest: dict[str, Any], executor: str) -> str:
    """Render a bridge-specific Codex or Claude guide."""
    lines = [
        f"# QA-Z Executor Bridge for {executor}",
        "",
        f"- Bridge id: `{manifest['bridge_id']}`",
        f"- Source session: `{manifest['source_session_id']}`",
        f"- Session manifest: `{manifest['inputs']['session']}`",
        f"- Handoff JSON: `{manifest['inputs']['handoff']}`",
        "",
        "## Constraints",
        "",
    ]
    lines.extend(f"- {item}" for item in manifest["non_goals"])
    lines.extend(["", "## Return", ""])
    lines.append(f"- `{format_command(manifest['validation_commands'][0])}`")
    return "\n".join(lines).strip() + "\n"


def render_bridge_stdout(manifest: dict[str, Any]) -> str:
    """Render compact human output for the executor-bridge CLI."""
    verify_command = manifest.get("return_contract", {}).get("verify_command") or []
    return "\n".join(
        [
            f"qa-z executor-bridge: {manifest.get('status')}",
            f"Bridge: {manifest.get('bridge_dir')}",
            f"Session: {manifest.get('source_session_id')}",
            f"Inputs: {manifest.get('inputs', {}).get('session')}, {manifest.get('inputs', {}).get('handoff')}",
            f"Verify: {format_command(verify_command)}",
            f"Return: {manifest.get('return_contract', {}).get('expected_next_step')}",
        ]
    )


def selected_task_ids(loop_outcome: dict[str, Any] | None) -> list[str]:
    """Return selected task ids from an optional loop outcome."""
    if not loop_outcome:
        return []
    values = loop_outcome.get("selected_task_ids")
    if not isinstance(values, list):
        return []
    return [str(value) for value in values]


def resolve_bridge_dir(
    *,
    root: Path,
    bridge_id: str,
    output_dir: Path | None,
) -> Path:
    """Resolve the bridge package directory."""
    if output_dir is None:
        return (root / ".qa-z" / "executor" / bridge_id).resolve()
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    return output_dir.resolve()


def copy_input(*, root: Path, source: Path, target: Path) -> None:
    """Copy one bridge input, raising a normalized source error."""
    if not source.is_file():
        raise ArtifactSourceNotFound(
            f"Bridge input not found: {format_path(source, root)}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object artifact."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactSourceNotFound(f"Could not read bridge source: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(f"Bridge source is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ArtifactLoadError("Bridge source JSON must contain an object.")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write stable JSON with a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def resolve_path(root: Path, value: str) -> Path:
    """Resolve a path relative to the repository root."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def default_bridge_id(
    generated_at: str,
    source_loop_id: str | None,
    session_id: str,
) -> str:
    """Return a deterministic default bridge id."""
    source = source_loop_id or session_id
    digits = re.sub(r"\D", "", generated_at)[:14] or "local"
    return f"bridge-{normalize_bridge_id(source)}-{digits}"


def normalize_bridge_id(value: str) -> str:
    """Normalize an id fragment for filesystem use."""
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-")
    return normalized or "bridge"


def format_command(command: list[Any]) -> str:
    """Render a command list for human output."""
    return " ".join(str(part) for part in command)


def optional_string(value: object) -> str | None:
    """Return a non-empty string or None."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def utc_now() -> str:
    """Return a UTC timestamp."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
