"""Executor-bridge packaging helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z import executor_bridge as executor_bridge_module
from qa_z.artifacts import format_path
from qa_z.executor_bridge_context import (
    copy_action_context_inputs,
    copy_input,
    resolve_path,
)
from qa_z.executor_bridge_guides import render_executor_specific_guide
from qa_z.executor_bridge_loop import (
    load_loop_outcome,
    read_json_object,
    repair_session_action,
)
from qa_z.executor_bridge_render import render_executor_bridge_guide
from qa_z.executor_bridge_summary import (
    bridge_evidence_summary,
    bridge_safety_package_summary,
)
from qa_z.executor_bridge_support import (
    default_bridge_id,
    ensure_session_exists,
    normalize_bridge_id,
    resolve_bridge_dir,
    utc_now,
    write_json,
)
from qa_z.executor_result import executor_result_template
from qa_z.repair_session import RepairSession, load_repair_session
from qa_z.repair_session_support import ensure_session_safety_artifacts


def create_executor_bridge(
    *,
    root: Path,
    from_loop: str | None = None,
    from_session: str | None = None,
    bridge_id: str | None = None,
    output_dir: Path | None = None,
    now: str | None = None,
):
    """Create an executor-ready package from an autonomy loop or session."""
    root = root.resolve()
    if bool(from_loop) == bool(from_session):
        raise executor_bridge_module.ExecutorBridgeError(
            "Provide exactly one of from_loop or from_session."
        )

    generated_at = now or utc_now()
    loop_outcome: dict[str, Any] | None = None
    action: dict[str, Any] | None = None
    if from_loop:
        loop_outcome = load_loop_outcome(root, from_loop)
        action = repair_session_action(loop_outcome)
        session_ref = str(action.get("session_dir") or action.get("session_id") or "")
        if not session_ref:
            raise executor_bridge_module.ExecutorBridgeError(
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
        raise executor_bridge_module.ExecutorBridgeError(
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
    return executor_bridge_module.ExecutorBridgePaths(
        bridge_dir=bridge_dir,
        manifest_path=manifest_path,
        executor_guide_path=executor_guide_path,
        codex_path=codex_path,
        claude_path=claude_path,
        result_template_path=result_template_path,
    )


def bridge_manifest(
    *,
    root: Path,
    bridge_dir: Path,
    bridge_id: str,
    generated_at: str,
    loop_outcome: dict[str, Any] | None,
    action: dict[str, Any] | None,
    session,
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
    manifest = {
        "kind": executor_bridge_module.EXECUTOR_BRIDGE_KIND,
        "schema_version": executor_bridge_module.EXECUTOR_BRIDGE_SCHEMA_VERSION,
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
        "non_goals": list(executor_bridge_module.DEFAULT_NON_GOALS),
        "safety_constraints": list(executor_bridge_module.DEFAULT_SAFETY_CONSTRAINTS),
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
    manifest.update(bridge_live_repository_context(loop_outcome))
    return manifest


def bridge_live_repository_context(
    loop_outcome: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return live repository context from the source autonomy outcome."""
    if not loop_outcome:
        return {}
    context: dict[str, Any] = {}
    live_repository = loop_outcome.get("live_repository")
    if isinstance(live_repository, dict) and live_repository:
        context["live_repository"] = dict(live_repository)
    for key in (
        "source_self_inspection",
        "source_self_inspection_loop_id",
        "source_self_inspection_generated_at",
    ):
        value = str(loop_outcome.get(key) or "").strip()
        if value:
            context[key] = value
    return context


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
