from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_executor_bridge_custom_output_warning_is_documented() -> None:
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")
    repair_sessions = (ROOT / "docs" / "repair-sessions.md").read_text(encoding="utf-8")

    for text in (schema, repair_sessions):
        assert "custom_output_dir_outside_repository" in text
        assert "custom_output_dir_outside_qa_z" in text
        assert "outside the repository root" in text
        assert "outside `.qa-z`" in text
        assert "non-blocking warning" in text
        assert "output_policy" in text
    assert "`codex.md`, and `claude.md` repeat the warning" in schema
