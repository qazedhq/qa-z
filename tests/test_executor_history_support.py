"""Behavior tests for executor-history support helpers."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.executor_history_support import (
    allocate_attempt_id,
    legacy_attempt_base,
    resolve_path,
    write_json,
)


def test_allocate_attempt_id_adds_numeric_suffix_for_collisions() -> None:
    attempt_id = allocate_attempt_id(
        base="repair-attempt",
        used_ids={"repair-attempt", "repair-attempt-2"},
    )

    assert attempt_id == "repair-attempt-3"


def test_legacy_attempt_base_normalizes_bridge_and_timestamp() -> None:
    attempt_base = legacy_attempt_base(
        {
            "bridge_id": "Bridge Session/One",
            "created_at": "2026-04-22T01:02:03Z",
        }
    )

    assert attempt_base == "bridge-session-one-20260422t010203z"


def test_resolve_path_expands_relative_paths_against_root(tmp_path: Path) -> None:
    resolved = resolve_path(tmp_path, ".qa-z/sessions/demo/session.json")

    assert (
        resolved
        == (tmp_path / ".qa-z" / "sessions" / "demo" / "session.json").resolve()
    )


def test_write_json_writes_sorted_payload_with_trailing_newline(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "artifact.json"
    write_json(path, {"b": 2, "a": 1})

    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1, "b": 2}
    assert path.read_text(encoding="utf-8").endswith("\n")
