"""Focused parsing tests for executor-result helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.artifacts import ArtifactLoadError
from qa_z.executor_result import load_executor_result


def test_load_executor_result_reports_field_aware_invalid_integer(
    tmp_path: Path,
) -> None:
    path = tmp_path / "executor-result.json"
    path.write_text(
        json.dumps(
            {
                "kind": "qa_z.executor_result",
                "schema_version": 1,
                "bridge_id": "bridge-1",
                "source_session_id": "session-1",
                "source_loop_id": None,
                "created_at": "2026-04-16T00:00:00Z",
                "status": "completed",
                "summary": "done",
                "verification_hint": "rerun",
                "candidate_run_dir": None,
                "changed_files": [],
                "validation": {
                    "status": "passed",
                    "commands": [],
                    "results": [
                        {
                            "command": ["python", "-m", "pytest"],
                            "status": "passed",
                            "exit_code": "NaN",
                            "summary": "bad int",
                        }
                    ],
                },
                "notes": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ArtifactLoadError, match="field exit_code must be an integer"):
        load_executor_result(path)
