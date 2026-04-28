"""Behavior tests for executor-ingest support helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_z.artifacts import ArtifactLoadError
from qa_z.executor_ingest_support import (
    format_relative_path,
    normalize_repo_path,
    optional_text,
    parse_timestamp,
    read_json_object,
    resolve_relative_path,
)


def test_resolve_and_format_relative_paths_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "artifact.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")

    resolved = resolve_relative_path(tmp_path, Path("nested/artifact.json"))

    assert resolved == target.resolve()
    assert format_relative_path(resolved, tmp_path) == "nested/artifact.json"


def test_normalize_repo_path_cleans_windows_separators() -> None:
    assert normalize_repo_path("\\src\\qa_z\\executor_ingest.py\\") == (
        "src/qa_z/executor_ingest.py"
    )


def test_read_json_object_rejects_non_object_payload(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    path.write_text('["not", "an", "object"]', encoding="utf-8")

    with pytest.raises(ArtifactLoadError):
        read_json_object(path)


def test_optional_text_and_parse_timestamp_normalize_inputs() -> None:
    assert optional_text("  hello  ") == "hello"
    assert optional_text("   ") is None
    assert parse_timestamp("2026-04-22T03:04:05Z") is not None
    assert parse_timestamp("not-a-timestamp") is None
