from __future__ import annotations

from pathlib import Path

from qa_z.adapters import SUPPORTED_REPAIR_ADAPTERS


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_agent_adapter_docs_cover_supported_repair_prompt_adapters() -> None:
    docs = read("docs/agent-adapters.md")

    for adapter in SUPPORTED_REPAIR_ADAPTERS:
        assert f"`{adapter}`" in docs
        assert f"repair/{adapter}.md" in docs

    for section in (
        "objective",
        "relevant evidence paths",
        "files and risks",
        "forbidden actions",
        "required validation",
        "final report format",
        "merge-safety boundaries",
        "not to claim success without validation",
    ):
        assert section in docs


def test_agent_adapter_docs_preserve_local_handoff_boundary() -> None:
    docs = read("docs/agent-adapters.md")

    for text in (
        "deterministic local files",
        "They do not call agent APIs",
        "Changing `--adapter` changes presentation only",
        "QA-Z remains the judge of merge evidence",
    ):
        assert text in docs

    for forbidden in (
        "QA-Z calls Codex",
        "live model calls",
        "automatic Cursor execution",
        "uploads packages",
    ):
        assert forbidden not in docs
