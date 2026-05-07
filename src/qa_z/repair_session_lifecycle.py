"""Repair-session lifecycle helpers."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from qa_z.adapters.claude import render_claude_handoff
from qa_z.adapters.codex import render_codex_handoff
from qa_z.artifacts import (
    ArtifactLoadError,
    format_path,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    resolve_path,
    resolve_run_source,
)
from qa_z.executor_safety import write_executor_safety_artifacts
from qa_z.repair_handoff import build_repair_handoff, write_repair_handoff_artifact
from qa_z.repair_session_guides import write_executor_guide
from qa_z.repair_session_outcome import render_outcome_markdown, session_summary_dict
from qa_z.repair_session_support import (
    create_session_id,
    handoff_artifact_paths,
    normalize_session_id,
    resolve_session_dir,
    sessions_dir,
    utc_now,
    write_session_manifest,
)
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.reporters.repair_prompt import build_repair_packet, write_repair_artifacts


def create_repair_session(
    *,
    root: Path,
    config: dict[str, Any],
    baseline_run: str,
    session_id: str | None = None,
):
    """Create a repair session from an existing baseline run."""
    from qa_z.repair_session import RepairSession, RepairSessionStartResult

    baseline_source = resolve_run_source(root, config, baseline_run)
    summary = load_run_summary(baseline_source.summary_path)
    deep_summary = load_sibling_deep_summary(baseline_source)
    contract_path = resolve_contract_source(root, config, summary=summary)
    contract = load_contract_context(contract_path, root)
    repair_packet = build_repair_packet(
        summary=summary,
        run_source=baseline_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    handoff = build_repair_handoff(
        repair_packet=repair_packet,
        summary=summary,
        run_source=baseline_source,
        root=root,
        deep_summary=deep_summary,
    )

    resolved_session_id = normalize_session_id(session_id or create_session_id())
    session_dir = sessions_dir(root) / resolved_session_id
    manifest_path = session_dir / "session.json"
    if manifest_path.exists():
        raise ValueError(
            f"Repair session already exists: {format_path(session_dir, root)}"
        )

    handoff_dir = session_dir / "handoff"
    write_repair_artifacts(repair_packet, handoff_dir)
    write_repair_handoff_artifact(handoff, handoff_dir)
    (handoff_dir / "codex.md").write_text(
        render_codex_handoff(handoff), encoding="utf-8"
    )
    (handoff_dir / "claude.md").write_text(
        render_claude_handoff(handoff), encoding="utf-8"
    )
    safety_artifacts = write_executor_safety_artifacts(
        root=root, output_dir=session_dir
    )

    now = utc_now()
    session = RepairSession(
        session_id=resolved_session_id,
        session_dir=format_path(session_dir, root),
        baseline_run_dir=format_path(baseline_source.run_dir, root),
        baseline_fast_summary_path=format_path(baseline_source.summary_path, root),
        baseline_deep_summary_path=(
            format_path(baseline_source.run_dir / "deep" / "summary.json", root)
            if deep_summary is not None
            else None
        ),
        handoff_dir=format_path(handoff_dir, root),
        handoff_artifacts=handoff_artifact_paths(handoff_dir, root),
        executor_guide_path=format_path(session_dir / "executor_guide.md", root),
        state="waiting_for_external_repair",
        created_at=now,
        updated_at=now,
        provenance={
            "baseline_status": summary.status,
            "contract_path": summary.contract_path,
            "repair_needed": repair_packet.repair_needed,
        },
        safety_artifacts=safety_artifacts,
    )
    write_executor_guide(session, handoff, root)
    write_session_manifest(session, root)
    return RepairSessionStartResult(session=session, handoff=handoff)


def complete_session_verification(
    *,
    session,
    root: Path,
    candidate_run_dir: Path,
    verify_paths,
    comparison,
):
    """Persist the results of session verification into session artifacts."""
    from qa_z.repair_session import load_session_dry_run_summary

    session_dir = resolve_path(root, session.session_dir)
    summary_path = session_dir / "summary.json"
    outcome_path = session_dir / "outcome.md"
    updated = replace(
        session,
        state="completed",
        updated_at=utc_now(),
        candidate_run_dir=format_path(candidate_run_dir, root),
        verify_dir=format_path(verify_paths.summary_path.parent, root),
        verify_artifacts={
            "summary_json": format_path(verify_paths.summary_path, root),
            "compare_json": format_path(verify_paths.compare_path, root),
            "report_markdown": format_path(verify_paths.report_path, root),
        },
        outcome_path=format_path(outcome_path, root),
        summary_path=format_path(summary_path, root),
    )
    dry_run_summary = load_session_dry_run_summary(updated, root)
    summary = session_summary_dict(updated, comparison, dry_run_summary=dry_run_summary)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    outcome_path.write_text(
        render_outcome_markdown(updated, comparison, summary), encoding="utf-8"
    )
    write_session_manifest(updated, root)
    return updated, summary


def load_repair_session(root: Path, session: str):
    """Load a repair-session manifest by id, directory, or session.json path."""
    from qa_z.repair_session import RepairSession

    session_dir = resolve_session_dir(root, session)
    manifest_path = session_dir / "session.json"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactLoadError(
            f"Could not read repair session: {manifest_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(
            f"Repair session manifest is not valid JSON: {manifest_path}"
        ) from exc
    if not isinstance(data, dict):
        raise ArtifactLoadError("Repair session manifest must contain an object.")
    loaded = RepairSession.from_dict(data)
    loaded_session_dir = resolve_path(root, loaded.session_dir)
    if loaded_session_dir != session_dir:
        raise ArtifactLoadError(
            "Repair session manifest session_dir does not match loaded manifest path: "
            f"expected {format_path(session_dir, root)}, "
            f"got {format_path(loaded_session_dir, root)}"
        )
    if loaded.session_id != session_dir.name:
        raise ArtifactLoadError(
            "Repair session manifest session_id does not match loaded manifest path: "
            f"expected {session_dir.name}, got {loaded.session_id}"
        )
    _validate_session_local_path(
        root=root,
        session_dir=session_dir,
        field="handoff_dir",
        value=loaded.handoff_dir,
    )
    _validate_session_local_path(
        root=root,
        session_dir=session_dir,
        field="executor_guide_path",
        value=loaded.executor_guide_path,
    )
    for key, value in loaded.handoff_artifacts.items():
        _validate_session_local_path(
            root=root,
            session_dir=session_dir,
            field=f"handoff_artifacts.{key}",
            value=value,
        )
    for key, value in loaded.safety_artifacts.items():
        _validate_session_local_path(
            root=root,
            session_dir=session_dir,
            field=f"safety_artifacts.{key}",
            value=value,
        )
    return loaded


def _validate_session_local_path(
    *, root: Path, session_dir: Path, field: str, value: str | None
) -> None:
    """Reject session-local artifact paths that escape the loaded session."""
    text = str(value or "").strip()
    if not text:
        return
    resolved = resolve_path(root, text)
    try:
        resolved.relative_to(session_dir)
    except ValueError as exc:
        raise ArtifactLoadError(
            f"Repair session manifest {field} must stay under session_dir: "
            f"{format_path(resolved, root)}"
        ) from exc
