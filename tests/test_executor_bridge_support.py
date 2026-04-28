"""Behavior tests for executor-bridge support helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_z.artifacts import ArtifactSourceNotFound
from qa_z.executor_bridge_support import ensure_session_exists, resolve_bridge_dir


def test_resolve_bridge_dir_uses_default_executor_root(tmp_path: Path) -> None:
    resolved = resolve_bridge_dir(
        root=tmp_path, output_dir=None, bridge_id="bridge-one"
    )

    assert resolved == (tmp_path / ".qa-z" / "executor" / "bridge-one").resolve()


def test_ensure_session_exists_requires_manifest(tmp_path: Path) -> None:
    with pytest.raises(ArtifactSourceNotFound, match="Repair session not found"):
        ensure_session_exists(tmp_path, "missing-session")
