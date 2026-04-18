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
from qa_z.executor_result import PLACEHOLDER_SUMMARY, executor_result_template
from qa_z.repair_session import (
    RepairSession,
    ensure_session_safety_artifacts,
    load_repair_session,
    resolve_session_dir,
)

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
    result_template_path: Path


def create_executor_bridge(
    *,
    root: Path,
    from_loop: str | None = None,
    from_session: str | None = None,
    bridge_id: str | None = None,
    output_dir: Path | None = None,
    now: str | None = None,
) -> ExecutorBridgePaths:
    """Create an executor-ready package from an autonomy loop or session."""
    root = root.resolve()
    if bool(from_loop) == bool(from_session):
        raise ExecutorBridgeError("Provide exactly one of from_loop or from_session.")

    generated_at = now or utc_now()
    loop_outcome: dict[str, Any] | None = None
    action: dict[str, Any] | None = None
    if from_loop:
        loop_outcome = load_loop_outcome(root, from_loop)
        action = repair_session_action(loop_outcome)
        session_ref = str(action.get("session_dir") or action.get("session_id") or "")
        if not session_ref:
            raise ExecutorBridgeError(
                "Loop outcome repair_session action is missing a session reference."
            )
    else:
        session_ref = str(from_session)

    ensure_session_exists(root, session_ref)
    session = load_repair_session(root, session_ref)
    session = ensure_session_safety_artifacts(session, root)
    source_loop_id = str(loop_outcome.get("loop_id")) if loop_outcome else None
    resolved_bridge_id = normalize_bridge_id(
        bridge_id or default_bridge_id(generated_at, source_loop_id, session.session_id)
    )
    bridge_dir = resolve_bridge_dir(
        root=root, output_dir=output_dir, bridge_id=resolved_bridge_id
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
        loop_outcome=loop_outcome,
        action=action,
        session=session,
    )
    safety_policy = read_json_object(
        resolve_path(root, session.safety_artifacts["policy_json"])
    )
    handoff = read_json_object(
        resolve_path(root, session.handoff_artifacts["handoff_json"])
    )
    validation_commands = bridge_validation_commands(session)
    manifest = bridge_manifest(
        root=root,
        bridge_dir=bridge_dir,
        bridge_id=resolved_bridge_id,
        generated_at=generated_at,
        loop_outcome=loop_outcome,
        action=action,
        session=session,
        handoff=handoff,
        safety_policy=safety_policy,
        copied_inputs=copied_inputs,
        validation_commands=validation_commands,
    )

    manifest_path = bridge_dir / "bridge.json"
    executor_guide_path = bridge_dir / "executor_guide.md"
    codex_path = bridge_dir / "codex.md"
    claude_path = bridge_dir / "claude.md"
    result_template_path = bridge_dir / "result_template.json"
    write_json(manifest_path, manifest)
    write_json(
        result_template_path,
        executor_result_template(
            bridge_id=resolved_bridge_id,
            created_at=generated_at,
            source_session_id=session.session_id,
            source_loop_id=source_loop_id,
            validation_commands=validation_commands,
            verification_hint="rerun",
        ),
    )
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
        result_template_path=result_template_path,
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
    loop_outcome: dict[str, Any] | None,
    action: dict[str, Any] | None,
    session: RepairSession,
    handoff: dict[str, Any],
    safety_policy: dict[str, Any],
    copied_inputs: dict[str, Any],
    validation_commands: list[list[str]],
) -> dict[str, Any]:
    """Build the machine-readable bridge manifest."""
    selected_task_ids = (
        [str(item) for item in loop_outcome.get("selected_task_ids", [])]
        if loop_outcome
        else []
    )
    handoff_json = session.handoff_artifacts.get("handoff_json")
    codex_markdown = session.handoff_artifacts.get("codex_markdown")
    claude_markdown = session.handoff_artifacts.get("claude_markdown")
    return {
        "kind": EXECUTOR_BRIDGE_KIND,
        "schema_version": EXECUTOR_BRIDGE_SCHEMA_VERSION,
        "bridge_id": bridge_id,
        "created_at": generated_at,
        "status": "ready_for_external_executor",
        "source_loop_id": str(loop_outcome.get("loop_id")) if loop_outcome else None,
        "source_session_id": session.session_id,
        "selected_task_ids": selected_task_ids,
        "prepared_action_type": str(action.get("type")) if action else "repair_session",
        "baseline_run_dir": session.baseline_run_dir,
        "session_dir": session.session_dir,
        "handoff_path": handoff_json,
        "handoff_paths": {
            "handoff_json": handoff_json,
            "codex_markdown": codex_markdown,
            "claude_markdown": claude_markdown,
            "executor_guide": session.executor_guide_path,
        },
        "bridge_dir": format_path(bridge_dir, root),
        "inputs": copied_inputs,
        "validation_commands": validation_commands,
        "safety_package": bridge_safety_package_summary(
            copied_inputs=copied_inputs,
            safety_policy=safety_policy,
        ),
        "non_goals": list(DEFAULT_NON_GOALS),
        "safety_constraints": list(DEFAULT_SAFETY_CONSTRAINTS),
        "return_contract": {
            "expected_next_step": "run repair-session verify after edits",
            "candidate_worktree": "repository working tree edited by external executor",
            "repair_notes": "optional external executor notes may be stored outside QA-Z",
            "verify_command": validation_commands[0] if validation_commands else None,
            "expected_result_artifact": format_path(bridge_dir / "result.json", root),
            "result_template_path": format_path(
                bridge_dir / "result_template.json", root
            ),
            "verification_hint_default": "rerun",
            "expected_verify_artifacts": {
                "summary_json": f"{session.session_dir}/verify/summary.json",
                "compare_json": f"{session.session_dir}/verify/compare.json",
                "report_markdown": f"{session.session_dir}/verify/report.md",
            },
            "partial_completion": (
                "If repair is incomplete, preserve the session and record what failed "
                "before requesting another QA-Z loop."
            ),
        },
        "evidence_summary": bridge_evidence_summary(loop_outcome, session, handoff),
    }


def copy_bridge_inputs(
    *,
    root: Path,
    inputs_dir: Path,
    loop_outcome: dict[str, Any] | None,
    action: dict[str, Any] | None,
    session: RepairSession,
) -> dict[str, Any]:
    """Copy bridge source inputs into the package and return manifest paths."""
    copied: dict[str, Any] = {
        "autonomy_outcome": None,
        "session": None,
        "handoff": None,
        "executor_safety_json": None,
        "executor_safety_markdown": None,
        "action_context": [],
        "action_context_missing": [],
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
    handoff_path = resolve_path(root, session.handoff_artifacts["handoff_json"])
    safety_json_path = resolve_path(root, session.safety_artifacts["policy_json"])
    safety_markdown_path = resolve_path(
        root, session.safety_artifacts["policy_markdown"]
    )
    copy_input(root=root, source=session_path, target=inputs_dir / "session.json")
    copy_input(root=root, source=handoff_path, target=inputs_dir / "handoff.json")
    copy_input(
        root=root,
        source=safety_json_path,
        target=inputs_dir / "executor_safety.json",
    )
    copy_input(
        root=root,
        source=safety_markdown_path,
        target=inputs_dir / "executor_safety.md",
    )
    copied["session"] = format_path(inputs_dir / "session.json", root)
    copied["handoff"] = format_path(inputs_dir / "handoff.json", root)
    copied["executor_safety_json"] = format_path(
        inputs_dir / "executor_safety.json", root
    )
    copied["executor_safety_markdown"] = format_path(
        inputs_dir / "executor_safety.md", root
    )
    action_context, action_context_missing = copy_action_context_inputs(
        root=root, inputs_dir=inputs_dir, action=action
    )
    copied["action_context"] = action_context
    copied["action_context_missing"] = action_context_missing
    return copied


def copy_action_context_inputs(
    *, root: Path, inputs_dir: Path, action: dict[str, Any] | None
) -> tuple[list[dict[str, str]], list[str]]:
    """Copy optional prepared-action context inputs into the bridge package."""
    context_paths = action_context_paths(action)
    copied: list[dict[str, str]] = []
    missing: list[str] = []
    for index, source_text in enumerate(context_paths, start=1):
        source_path = resolve_path(root, source_text)
        source_label = context_source_label(root, source_text, source_path)
        if not path_is_within(root, source_path) or not source_path.is_file():
            missing.append(source_label)
            continue
        target = (
            inputs_dir
            / "context"
            / f"{index:03d}-{safe_context_input_name(source_path.name)}"
        )
        copy_input(root=root, source=source_path, target=target)
        copied.append(
            {
                "source_path": source_label,
                "copied_path": format_path(target, root),
            }
        )
    return copied, missing


def action_context_paths(action: dict[str, Any] | None) -> list[str]:
    """Return ordered non-empty context paths from a prepared action."""
    if not isinstance(action, dict):
        return []
    values = action.get("context_paths")
    if not isinstance(values, list):
        return []
    paths: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        path = value.strip()
        if not path or path in seen:
            continue
        seen.add(path)
        paths.append(path)
    return paths


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
            "--rerun",
        ]
    ]


def bridge_evidence_summary(
    loop_outcome: dict[str, Any] | None,
    session: RepairSession,
    handoff: dict[str, Any],
) -> dict[str, Any]:
    """Return compact bridge evidence context."""
    repair = handoff.get("repair") if isinstance(handoff, dict) else {}
    targets = repair.get("targets") if isinstance(repair, dict) else []
    return {
        "why_selected": (
            loop_outcome.get("next_recommendations", []) if loop_outcome else []
        ),
        "session_state": session.state,
        "baseline_status": session.provenance.get("baseline_status"),
        "repair_needed": session.provenance.get("repair_needed"),
        "target_count": len(targets) if isinstance(targets, list) else 0,
    }


def bridge_safety_package_summary(
    *, copied_inputs: dict[str, Any], safety_policy: dict[str, Any]
) -> dict[str, Any]:
    """Return the compact bridge-local view of the copied safety package."""
    rules = safety_policy.get("rules")
    rule_ids: list[str] = []
    if isinstance(rules, list):
        rule_ids = [
            str(rule.get("id"))
            for rule in rules
            if isinstance(rule, dict) and str(rule.get("id") or "").strip()
        ]
    return {
        "package_id": safety_policy.get("package_id"),
        "status": safety_policy.get("status"),
        "policy_json": copied_inputs.get("executor_safety_json"),
        "policy_markdown": copied_inputs.get("executor_safety_markdown"),
        "rule_ids": rule_ids,
        "rule_count": len(rule_ids),
    }


def bridge_safety_rule_count(manifest: dict[str, Any]) -> int | str:
    """Return the displayable safety rule count for bridge guides."""
    safety_package = manifest.get("safety_package")
    if not isinstance(safety_package, dict):
        return "unknown"
    rule_count = safety_package.get("rule_count")
    if isinstance(rule_count, int):
        return rule_count
    rule_ids = safety_package.get("rule_ids")
    if isinstance(rule_ids, list):
        return len(rule_ids)
    return "unknown"


def bridge_placeholder_summary_guidance() -> str:
    """Return stable guidance for completing result templates."""
    return f"Replace the placeholder summary before ingest: `{PLACEHOLDER_SUMMARY}`"


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
        "This package gives an external human, Codex, or Claude executor the local QA-Z evidence needed for repair.",
        "QA-Z does not call live model APIs, edit code, schedule work, commit, push, or post GitHub comments.",
        "",
        "## Bridge",
        "",
        f"- Bridge id: `{manifest['bridge_id']}`",
        f"- Status: `{manifest['status']}`",
        f"- Source loop: `{manifest.get('source_loop_id') or 'none'}`",
        f"- Source session: `{manifest['source_session_id']}`",
        f"- Baseline run: `{manifest['baseline_run_dir']}`",
        "",
        "## Why This Work Was Selected",
        "",
    ]
    selected = manifest.get("selected_task_ids") or []
    if selected:
        lines.extend(f"- Selected task: `{item}`" for item in selected)
    else:
        lines.append("- Bridge was created directly from a repair session.")
    recommendations = manifest.get("evidence_summary", {}).get("why_selected", [])
    for recommendation in recommendations:
        lines.append(f"- Recommendation: {recommendation}")
    lines.extend(["", "## What To Fix", ""])
    if isinstance(objectives, list) and objectives:
        lines.extend(f"- {objective}" for objective in objectives)
    elif isinstance(targets, list) and targets:
        lines.extend(
            f"- {target.get('objective')}"
            for target in targets
            if isinstance(target, dict)
        )
    else:
        lines.append(
            "- Use the packaged handoff artifacts to identify the repair target."
        )
    lines.extend(["", "## Where To Look", ""])
    lines.append(f"- Session manifest: `{manifest['inputs']['session']}`")
    lines.append(f"- Handoff JSON: `{manifest['inputs']['handoff']}`")
    lines.append(
        f"- Safety package: `{manifest['inputs']['executor_safety_markdown']}`"
    )
    if manifest["inputs"].get("autonomy_outcome"):
        lines.append(f"- Autonomy outcome: `{manifest['inputs']['autonomy_outcome']}`")
    action_context = bridge_action_context_inputs(manifest)
    if action_context:
        lines.append("- Action context:")
        lines.extend(
            f"  - `{item['copied_path']}` from `{item['source_path']}`"
            for item in action_context
        )
    missing_action_context = bridge_missing_action_context_inputs(manifest)
    if missing_action_context:
        lines.append("- Action context missing:")
        lines.extend(f"  - `{path}`" for path in missing_action_context)
    lines.append(
        "- Result template: "
        f"`{manifest['return_contract']['result_template_path']}` "
        f"-> create `{manifest['return_contract']['expected_result_artifact']}`"
    )
    lines.extend(["", "## Do Not Change", ""])
    lines.extend(f"- {item}" for item in manifest["non_goals"])
    lines.extend(["", "## Safety Package", ""])
    lines.append(f"- Policy JSON: `{manifest['safety_package']['policy_json']}`")
    lines.append(
        f"- Policy Markdown: `{manifest['safety_package']['policy_markdown']}`"
    )
    lines.append(f"- Safety rule count: `{bridge_safety_rule_count(manifest)}`")
    lines.extend(["", "## Validation", ""])
    for command in manifest["validation_commands"]:
        lines.append(f"- `{format_command(command)}`")
    lines.extend(
        [
            "",
            "## Return Contract",
            "",
            f"- Expected next step: {manifest['return_contract']['expected_next_step']}",
            "- Write an executor result JSON before re-entering QA-Z verification.",
            (
                "- Result template: "
                f"`{manifest['return_contract']['result_template_path']}`"
            ),
            (
                "- Expected result artifact: "
                f"`{manifest['return_contract']['expected_result_artifact']}`"
            ),
            f"- {bridge_placeholder_summary_guidance()}",
            "- Return control to QA-Z by running the validation command after edits.",
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
        f"- Baseline run: `{manifest['baseline_run_dir']}`",
        f"- Handoff JSON: `{manifest['inputs']['handoff']}`",
        f"- Safety package: `{manifest['safety_package']['policy_markdown']}`",
        f"- Safety rule count: `{bridge_safety_rule_count(manifest)}`",
        "",
        "Use the packaged handoff and session evidence to make the smallest safe repair.",
        "Do not call Codex or Claude APIs from QA-Z.",
        "",
    ]
    action_context = bridge_action_context_inputs(manifest)
    if action_context:
        lines.extend(["## Action Context", ""])
        lines.extend(
            f"- `{item['copied_path']}` from `{item['source_path']}`"
            for item in action_context
        )
        lines.append("")
    missing_action_context = bridge_missing_action_context_inputs(manifest)
    if missing_action_context:
        lines.extend(["## Action context missing", ""])
        lines.extend(f"- `{path}`" for path in missing_action_context)
        lines.append("")
    lines.extend(["## Safety", ""])
    lines.extend(f"- {item}" for item in manifest["non_goals"])
    lines.extend(["", "## Validation", ""])
    for command in manifest["validation_commands"]:
        lines.append(f"- `{format_command(command)}`")
    lines.extend(["", "## Return Contract", ""])
    lines.append(f"- {manifest['return_contract']['expected_next_step']}")
    lines.append(f"- {bridge_placeholder_summary_guidance()}")
    lines.append("- Preserve partial completion evidence if the command fails.")
    return "\n".join(lines).strip() + "\n"


def render_bridge_stdout(manifest: dict[str, Any]) -> str:
    """Render human CLI output for bridge creation."""
    return_contract = manifest.get("return_contract")
    if not isinstance(return_contract, dict):
        return_contract = {}
    verify_command = return_contract.get("verify_command")
    lines = [
        "qa-z executor-bridge: ready_for_external_executor",
        f"Bridge: {manifest['bridge_dir']}",
        f"Source session: {manifest['source_session_id']}",
        f"Handoff: {manifest['handoff_path']}",
        f"Executor guide: {manifest['bridge_dir']}/executor_guide.md",
        f"Result template: {return_contract.get('result_template_path')}",
        f"Expected result: {return_contract.get('expected_result_artifact')}",
        "Template summary: replace placeholder before ingest",
        f"Safety package: {manifest['safety_package']['policy_markdown']}",
        f"Safety rule count: {bridge_safety_rule_count(manifest)}",
    ]
    action_context = bridge_action_context_inputs(manifest)
    if action_context:
        lines.append(f"Action context inputs: {len(action_context)}")
    missing_action_context = bridge_missing_action_context_inputs(manifest)
    if missing_action_context:
        lines.append(
            "Missing action context: "
            f"{len(missing_action_context)} ({'; '.join(missing_action_context)})"
        )
    if isinstance(verify_command, list):
        lines.append(
            f"Verify command: {format_command([str(item) for item in verify_command])}"
        )
    return "\n".join(lines)


def resolve_bridge_dir(*, root: Path, output_dir: Path | None, bridge_id: str) -> Path:
    """Resolve the bridge output directory."""
    if output_dir is not None:
        path = output_dir.expanduser()
        if not path.is_absolute():
            path = root / path
        return path.resolve()
    return (root / ".qa-z" / "executor" / bridge_id).resolve()


def ensure_session_exists(root: Path, session_ref: str) -> None:
    """Raise source-not-found when a repair-session manifest is absent."""
    manifest_path = resolve_session_dir(root, session_ref) / "session.json"
    if not manifest_path.is_file():
        raise ArtifactSourceNotFound(f"Repair session not found: {manifest_path}")


def resolve_path(root: Path, value: str) -> Path:
    """Resolve a path relative to the repository root."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def path_is_within(root: Path, path: Path) -> bool:
    """Return whether path is inside the repository root."""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def context_source_label(root: Path, source_text: str, source_path: Path) -> str:
    """Return a stable manifest label for a context source path."""
    if path_is_within(root, source_path):
        return format_path(source_path, root)
    return source_text


def safe_context_input_name(name: str) -> str:
    """Return a filename-safe context input basename."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip()).strip("-")
    if not safe or safe in {".", ".."}:
        return "context"
    return safe


def bridge_action_context_inputs(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Return copied action-context input records from a bridge manifest."""
    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict):
        return []
    context = inputs.get("action_context")
    if not isinstance(context, list):
        return []
    records: list[dict[str, str]] = []
    for item in context:
        if not isinstance(item, dict):
            continue
        source_path = item.get("source_path")
        copied_path = item.get("copied_path")
        if isinstance(source_path, str) and isinstance(copied_path, str):
            records.append({"source_path": source_path, "copied_path": copied_path})
    return records


def bridge_missing_action_context_inputs(manifest: dict[str, Any]) -> list[str]:
    """Return missing action-context input paths from a bridge manifest."""
    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict):
        return []
    missing = inputs.get("action_context_missing")
    if not isinstance(missing, list):
        return []
    return [str(item) for item in missing if str(item).strip()]


def copy_input(*, root: Path, source: Path, target: Path) -> None:
    """Copy one required bridge input."""
    if not source.is_file():
        raise ArtifactSourceNotFound(f"Required bridge input not found: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a required JSON object artifact."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactSourceNotFound(f"Could not read bridge input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(f"Bridge input is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ArtifactLoadError(f"Bridge input must contain an object: {path}")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def normalize_bridge_id(bridge_id: str) -> str:
    """Validate a bridge id so it cannot escape the executor directory."""
    normalized = bridge_id.strip()
    if not normalized or normalized in {".", ".."}:
        raise ExecutorBridgeError("Bridge id must not be empty.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", normalized):
        raise ExecutorBridgeError(
            "Bridge id may contain only letters, numbers, dot, underscore, and dash."
        )
    return normalized


def default_bridge_id(generated_at: str, loop_id: str | None, session_id: str) -> str:
    """Return a compact deterministic bridge id."""
    digits = re.sub(r"\D", "", generated_at)
    if len(digits) < 14:
        digits = re.sub(r"\D", "", utc_now()).ljust(14, "0")
    source = loop_id or session_id
    return f"bridge-{digits[:8]}-{digits[8:14]}-{slugify(source)}"


def slugify(value: str) -> str:
    """Create a stable id fragment."""
    slug = re.sub(r"[^A-Za-z0-9_]+", "-", value.strip().lower()).strip("-")
    return slug or "unknown"


def format_command(command: list[str]) -> str:
    """Render an argv command for Markdown."""
    return " ".join(command)


def utc_now() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
