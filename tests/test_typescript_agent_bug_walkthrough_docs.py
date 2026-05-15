from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_typescript_agent_walkthrough_documents_baseline_candidate_and_verify() -> None:
    docs = read("docs/walkthroughs/typescript-agent-bug.md")

    for text in (
        'qa-z plan --title "TypeScript agent bug caught by QA-Z"',
        "qa-z fast --output-dir .qa-z/runs/baseline",
        "qa-z deep --from-run .qa-z/runs/baseline",
        "qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex",
        "cp src/invoice.fixed.ts src/invoice.ts",
        "Copy-Item src\\invoice.fixed.ts src\\invoice.ts -Force",
        "qa-z fast --output-dir .qa-z/runs/candidate",
        "qa-z deep --from-run .qa-z/runs/candidate",
        "qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate",
    ):
        assert text in docs


def test_typescript_agent_walkthrough_names_artifacts_to_inspect() -> None:
    combined = read("docs/walkthroughs/typescript-agent-bug.md") + read(
        "examples/typescript-agent-bug/README.md"
    )

    for path in (
        ".qa-z/runs/baseline/fast/summary.json",
        ".qa-z/runs/baseline/deep/summary.json",
        ".qa-z/runs/baseline/deep/checks/sg_scan.json",
        ".qa-z/runs/baseline/deep/results.sarif",
        ".qa-z/runs/baseline/repair/codex.md",
        ".qa-z/runs/candidate/fast/summary.json",
        ".qa-z/runs/candidate/deep/summary.json",
        ".qa-z/runs/candidate/verify/summary.json",
        ".qa-z/runs/candidate/verify/compare.json",
        ".qa-z/runs/candidate/verify/report.md",
    ):
        assert path in combined


def test_typescript_agent_example_config_and_source_match_walkthrough() -> None:
    config = yaml.safe_load(read("examples/typescript-agent-bug/qa-z.yaml"))
    unsafe = read("examples/typescript-agent-bug/src/invoice.ts")
    fixed = read("examples/typescript-agent-bug/src/invoice.fixed.ts")
    rule = read("examples/typescript-agent-bug/semgrep-rules/auth-bypass.yml")

    assert [check["id"] for check in config["fast"]["checks"]] == [
        "ts_lint",
        "ts_type",
        "ts_test",
    ]
    assert [check["id"] for check in config["deep"]["checks"]] == ["sg_scan"]
    assert "return actorId !== null;" in unsafe
    assert "return actorId === invoice.ownerId;" in fixed
    assert "qa-z.typescript-auth-bypass-any-signed-in-user" in rule


def test_typescript_agent_walkthrough_preserves_local_only_boundary() -> None:
    docs = read("docs/walkthroughs/typescript-agent-bug.md")
    readme = read("examples/typescript-agent-bug/README.md")

    for text in (docs, readme):
        assert "Do not commit" in text
        assert ".qa-z" in text
        assert "live agents" in text

    for forbidden_claim in (
        "calls live agents",
        "requires hosted services",
        "publishes packages",
    ):
        assert forbidden_claim not in docs.lower()


def test_docs_index_links_typescript_agent_walkthrough() -> None:
    docs_index = read("docs/README.md")

    assert "walkthroughs/typescript-agent-bug.md" in docs_index
    assert "TypeScript agent bug" in docs_index
