from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import qa_z.benchmark_executor_session_setup as session_setup_module


def test_seed_executor_session_creates_repair_session_and_rewrites_timestamps(
    monkeypatch, tmp_path: Path
) -> None:
    calls: dict[str, Any] = {}
    manifest_path = tmp_path / ".qa-z" / "sessions" / "session-one" / "session.json"
    manifest_path.parent.mkdir(parents=True)

    monkeypatch.setattr(
        session_setup_module,
        "create_repair_session",
        lambda **kwargs: calls.setdefault("create_repair_session", kwargs),
    )
    monkeypatch.setattr(
        session_setup_module,
        "read_json_object",
        lambda path: {
            "session_id": "session-one",
            "created_at": "older",
            "updated_at": "older",
        },
    )
    monkeypatch.setattr(
        session_setup_module,
        "write_json",
        lambda path, payload: calls.setdefault("write_json", (path, payload)),
    )

    fixed_now = session_setup_module.seed_executor_session(
        workspace=tmp_path,
        config={"checks": []},
        baseline_run=".qa-z/runs/baseline",
        session_id="session-one",
    )

    assert fixed_now == "2026-04-16T00:00:00Z"
    assert calls["create_repair_session"] == {
        "root": tmp_path,
        "config": {"checks": []},
        "baseline_run": ".qa-z/runs/baseline",
        "session_id": "session-one",
    }
    written_path, payload = cast(tuple[Path, dict[str, object]], calls["write_json"])
    assert written_path == manifest_path
    assert payload["created_at"] == fixed_now
    assert payload["updated_at"] == fixed_now
