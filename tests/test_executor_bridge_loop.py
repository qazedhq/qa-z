"""Behavior tests for executor-bridge loop helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.artifacts import ArtifactSourceNotFound
from qa_z.executor_bridge import ExecutorBridgeError
from qa_z.executor_bridge_loop import load_loop_outcome, repair_session_action


def test_load_loop_outcome_reads_loop_artifact_from_loop_id(tmp_path: Path) -> None:
    outcome_dir = tmp_path / ".qa-z" / "loops" / "loop-001"
    outcome_dir.mkdir(parents=True, exist_ok=True)
    (outcome_dir / "outcome.json").write_text(
        json.dumps(
            {
                "kind": "qa_z.autonomy_outcome",
                "loop_id": "loop-001",
                "actions_prepared": [{"type": "repair_session", "session": "one"}],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    loaded = load_loop_outcome(tmp_path, "loop-001")

    assert loaded["loop_id"] == "loop-001"


def test_repair_session_action_requires_matching_action() -> None:
    with pytest.raises(ExecutorBridgeError, match="repair_session action"):
        repair_session_action({"actions_prepared": [{"type": "noop"}]})


def test_load_loop_outcome_requires_existing_outcome(tmp_path: Path) -> None:
    with pytest.raises(ArtifactSourceNotFound, match="Autonomy outcome not found"):
        load_loop_outcome(tmp_path, "missing-loop")
