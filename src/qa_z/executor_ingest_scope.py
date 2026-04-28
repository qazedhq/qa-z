"""Scope validation helpers for executor-ingest flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    ArtifactLoadError,
    extract_candidate_files,
    extract_contract_candidate_files,
    load_contract_context,
)
from qa_z.executor_ingest_support import (
    normalize_repo_path,
    read_json_object,
    resolve_relative_path,
)
from qa_z.repair_session import RepairSession


def validate_result_scope(
    *,
    root: Path,
    bridge: dict[str, Any],
    result: Any,
    session: RepairSession | None = None,
) -> None:
    """Reject executor results that report unrelated changed files."""
    allowed_files = bridge_allowed_files(root=root, bridge=bridge, session=session)
    if not allowed_files and not result.changed_files:
        return
    if not allowed_files:
        raise ArtifactLoadError(
            "Executor bridge affected_files are missing, so changed_files cannot be validated."
        )
    unexpected = unexpected_changed_files(
        changed_files=result.changed_files,
        allowed_files=allowed_files,
    )
    if unexpected:
        raise ArtifactLoadError(
            "Executor result changed_files are outside the bridge affected_files: "
            + ", ".join(unexpected)
        )


def bridge_allowed_files(
    *, root: Path, bridge: dict[str, Any], session: RepairSession | None = None
) -> set[str]:
    """Return the allowed changed files declared by the bridge handoff."""
    handoff_path_text = str(bridge.get("handoff_path") or "").strip()
    if not handoff_path_text:
        inputs = bridge.get("inputs")
        if isinstance(inputs, dict):
            handoff_path_text = str(inputs.get("handoff") or "").strip()
    if not handoff_path_text:
        raise ArtifactLoadError(
            "Executor bridge is missing handoff_path required for scope validation."
        )
    handoff = read_json_object(resolve_relative_path(root, handoff_path_text))
    repair = handoff.get("repair")
    if not isinstance(repair, dict):
        raise ArtifactLoadError("Executor bridge handoff is missing repair scope.")
    allowed = {
        normalize_repo_path(str(path))
        for path in repair.get("affected_files", [])
        if str(path).strip()
    }
    targets = repair.get("targets")
    if isinstance(targets, list):
        for target in targets:
            if not isinstance(target, dict):
                continue
            for path in target.get("affected_files", []):
                text = str(path).strip()
                if text:
                    allowed.add(normalize_repo_path(text))
    if not allowed and session is not None:
        contract_path_text = str(session.provenance.get("contract_path") or "").strip()
        if contract_path_text:
            contract = load_contract_context(
                resolve_relative_path(root, contract_path_text), root
            )
            allowed.update(
                normalize_repo_path(path)
                for path in extract_contract_candidate_files(contract)
            )
            if not allowed:
                allowed.update(
                    normalize_repo_path(path)
                    for path in extract_candidate_files(contract.raw_markdown)
                )
    return allowed


def unexpected_changed_files(
    *, changed_files: list[Any], allowed_files: set[str]
) -> list[str]:
    """Return changed file paths that fall outside the allowed bridge scope."""
    unexpected: list[str] = []
    for changed in changed_files:
        path = normalize_repo_path(str(getattr(changed, "path", "") or ""))
        old_path = normalize_repo_path(str(getattr(changed, "old_path", "") or ""))
        if path and path in allowed_files:
            continue
        if old_path and old_path in allowed_files:
            continue
        if path:
            unexpected.append(path)
    return unexpected
