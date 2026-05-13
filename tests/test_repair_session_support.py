"""Behavior tests for repair-session support helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from qa_z.repair_session import RepairSession
from qa_z.repair_session_support import (
    ensure_session_safety_artifacts,
    write_session_manifest,
)


def _session(tmp_path: Path) -> RepairSession:
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    session_dir.mkdir(parents=True, exist_ok=True)
    session = RepairSession(
        session_id="session-one",
        session_dir=".qa-z/sessions/session-one",
        baseline_run_dir=".qa-z/runs/baseline",
        handoff_dir=".qa-z/sessions/session-one/handoff",
        executor_guide_path=".qa-z/sessions/session-one/executor-guide.md",
        state="waiting_for_external_repair",
        created_at="2026-04-22T00:00:00Z",
        updated_at="2026-04-22T00:00:00Z",
        baseline_fast_summary_path=".qa-z/runs/baseline/fast/summary.json",
    )
    (session_dir / "session.json").write_text(
        json.dumps(session.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return session


def test_ensure_session_safety_artifacts_backfills_missing_policy_files(
    tmp_path: Path,
) -> None:
    updated = ensure_session_safety_artifacts(_session(tmp_path), tmp_path)

    assert updated.safety_artifacts["policy_json"].endswith("executor_safety.json")
    assert updated.safety_artifacts["policy_markdown"].endswith("executor_safety.md")
    assert (tmp_path / updated.safety_artifacts["policy_json"]).is_file()
    assert (tmp_path / updated.safety_artifacts["policy_markdown"]).is_file()
    assert updated.updated_at.endswith("Z")


def test_write_session_manifest_reports_manifest_path_on_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _session(tmp_path)
    manifest_path = tmp_path / ".qa-z" / "sessions" / "session-one" / "session.json"
    original_write_text = Path.write_text

    def fail_manifest_write(
        self: Path,
        data: str,
        *args: Any,
        **kwargs: Any,
    ) -> int:
        if self.resolve() == manifest_path.resolve():
            raise OSError("disk full")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_manifest_write)

    with pytest.raises(
        OSError,
        match=r"could not write repair-session manifest .*session\.json.*disk full",
    ):
        write_session_manifest(session, tmp_path)
