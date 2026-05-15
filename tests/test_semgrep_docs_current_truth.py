from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def squash_whitespace(text: str) -> str:
    return " ".join(text.split())


def test_semgrep_docs_cover_custom_rule_acceptance() -> None:
    docs = read("docs/use-with-semgrep.md")
    normalized_docs = squash_whitespace(docs)

    for expected_text in (
        "This example satisfies the custom-rule workflow",
        "examples/fastapi-agent-bug/semgrep-rules/auth-bypass.yml",
        "semgrep-rules/auth-bypass.yml",
        "sg_scan",
        "fail_on_severity",
        ".qa-z/runs/baseline/deep/results.sarif",
        "github/codeql-action/upload-sarif@v4",
        "Raw Semgrep answers",
        "QA-Z deep keeps that result tied to the fast run",
        ".qa-z/runs/baseline/deep/summary.json",
        "review and repair packets",
        "Do not commit generated `.qa-z` runtime evidence",
        "do not call live services",
        "live model APIs",
        "package registries",
    ):
        assert expected_text in normalized_docs


def test_fastapi_example_uses_documented_custom_semgrep_rule() -> None:
    config = yaml.safe_load(read("examples/fastapi-agent-bug/qa-z.yaml"))
    deep_checks = config["deep"]["checks"]

    assert [check["id"] for check in deep_checks] == ["sg_scan"]

    sg_scan = deep_checks[0]
    assert sg_scan["run"] == [
        "semgrep",
        "--config",
        "semgrep-rules/auth-bypass.yml",
        "--json",
        "app",
    ]
    assert sg_scan["semgrep"]["config"] == "semgrep-rules/auth-bypass.yml"
    assert sg_scan["semgrep"]["fail_on_severity"] == ["ERROR"]
