from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(*parts: str) -> str:
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


def test_release_continuity_docs_cover_loop_local_prepared_action_context() -> None:
    current_state = " ".join(
        read_text("docs", "reports", "current-state-analysis.md").split()
    ).lower()
    roadmap = " ".join(
        read_text("docs", "reports", "next-improvement-roadmap.md").split()
    ).lower()

    assert "cleanup and workflow packets now also carry loop-local self-inspection" in (
        read_text("docs", "current-truth-maintenance-anchors.md")
    )
    assert (
        "cleanup and workflow prepared actions also carry loop-local self-inspection"
        in read_text("docs", "artifact-schema-v1.md")
    )
    assert (
        "loop-local self-inspection now also stays attached to cleanup and workflow prepared actions through `context_paths`"
        in current_state
    )
    assert (
        "loop-local self-inspection continuity across cleanup and workflow prepared actions"
        in roadmap
    )
