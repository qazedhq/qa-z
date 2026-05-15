from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_use_with_codex_contains_copy_this_prompt_snippet() -> None:
    docs = read("docs/use-with-codex.md")

    for text in (
        "Copy This Prompt To Codex",
        ".qa-z/runs/latest/repair/codex.md",
        ".qa-z/runs/latest/fast/summary.json",
        ".qa-z/runs/latest/deep/summary.json",
        "QA-Z artifacts as the source of truth",
        "Do not replace failing checks with LLM-only judgment",
        "run the validation commands listed in the QA-Z repair prompt",
    ):
        assert text in docs


def test_codex_docs_keep_qa_z_as_evidence_source_not_live_executor() -> None:
    docs = read("docs/use-with-codex.md")

    for text in (
        "QA-Z does not call Codex APIs",
        "human-operated Codex workflow",
        "Codex is the executor, not the judge",
    ):
        assert text in docs

    forbidden_claims = (
        "QA-Z calls Codex",
        "QA-Z invokes Codex",
        "automatic Codex execution",
        "live Codex API",
    )

    for claim in forbidden_claims:
        assert claim not in docs


def test_readme_links_to_codex_handoff_guide_without_expanding_flow() -> None:
    readme = read("README.md")

    assert "[Use with Codex](docs/use-with-codex.md)" in readme
    assert readme.count("docs/use-with-codex.md") == 1
