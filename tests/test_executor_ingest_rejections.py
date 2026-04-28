"""Behavior tests for executor-ingest rejection helpers."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from qa_z.executor_ingest import ExecutorResultIngestRejected
from qa_z.executor_ingest_rejections import raise_rejected_ingest


def test_raise_rejected_ingest_writes_outcome_and_raises(tmp_path: Path) -> None:
    result = SimpleNamespace(
        bridge_id="bridge-one",
        status="completed",
        verification_hint="rerun",
    )

    with pytest.raises(ExecutorResultIngestRejected) as exc_info:
        raise_rejected_ingest(
            root=tmp_path,
            session=None,
            result=result,
            result_id="bridge-one-20260422t030405z",
            session_id="session-one",
            source_loop_id="loop-001",
            ingest_status="rejected_invalid",
            warnings=["warning-a"],
            freshness_check={"status": "warning", "details": ["not evaluated"]},
            provenance_check={"status": "failed", "details": ["bridge missing"]},
            verify_resume_status="verify_blocked",
            freshness_reason=None,
            provenance_reason="bridge_missing",
            next_recommendation="fix executor bridge reference",
            message="bridge missing",
            exit_code=4,
            source_context={
                "source_self_inspection": ".qa-z/loops/loop-001/self_inspect.json",
                "source_self_inspection_loop_id": "loop-001",
            },
        )

    ingest_path = (
        tmp_path
        / ".qa-z"
        / "executor-results"
        / "bridge-one-20260422t030405z"
        / "ingest.json"
    )
    payload = json.loads(ingest_path.read_text(encoding="utf-8"))

    assert exc_info.value.exit_code == 4
    assert payload["ingest_status"] == "rejected_invalid"
    assert payload["next_recommendation"] == "fix executor bridge reference"
    assert payload["source_self_inspection_loop_id"] == "loop-001"
