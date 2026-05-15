from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_comparison_mentions_major_agent_tools_and_positions_qa_z() -> None:
    comparison = read("docs/comparison.md")
    normalized = comparison.lower()

    for tool_name in ("aider", "OpenHands", "Goose"):
        assert tool_name in comparison

    assert "model-agnostic merge evidence layer" in normalized
    assert "qa-z is not a coding agent" in normalized
    assert "does not replace coding agents" in normalized


def test_comparison_preserves_non_goals_and_no_superiority_claims() -> None:
    comparison = read("docs/comparison.md")
    normalized = comparison.lower()

    for boundary in (
        "no live model api execution",
        "no autonomous editing",
        "no branch mutation, commits, pushes, tags, releases, deploys, or bot comments",
        "no package publishing claim",
        "no replacement for tests, semgrep, or human review",
    ):
        assert boundary in normalized

    for unsupported_claim in (
        "qa-z is better than",
        "qa-z beats",
        "qa-z outperforms",
        "qa-z replaces codex",
        "qa-z replaces aider",
        "qa-z replaces openhands",
        "qa-z replaces goose",
    ):
        assert unsupported_claim not in normalized


def test_readme_links_comparison_without_embedding_table() -> None:
    readme = read("README.md")
    why_qa_z = readme.split("## Why QA-Z?", 1)[1].split("## Before / After", 1)[0]

    assert "[Comparison](docs/comparison.md)" in readme
    assert "| Tool |" not in why_qa_z
    assert "| Primary role |" not in why_qa_z
    assert "aider |" not in why_qa_z.lower()
