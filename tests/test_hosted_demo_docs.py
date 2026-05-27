from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_hosted_demo_docs_pin_local_replay_commands() -> None:
    docs = read("docs/hosted-demo.md")

    for text in (
        "examples/agent-auth-bug",
        "docs/demo-script.md",
        'qa-z plan --title "AI auth bug caught by QA-Z"',
        "qa-z fast --output-dir .qa-z/runs/baseline",
        "qa-z review --from-run .qa-z/runs/baseline",
        "qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex",
        "qa-z deep --from-run .qa-z/runs/baseline",
        "cp app/auth.fixed.py app/auth.py",
        "qa-z verify --from-run .qa-z/runs/baseline",
    ):
        assert text in docs


def test_hosted_demo_docs_name_replay_artifacts() -> None:
    docs = read("docs/hosted-demo.md")

    for artifact in (
        ".qa-z/runs/baseline/fast/summary.json",
        ".qa-z/runs/baseline/review/",
        ".qa-z/runs/baseline/repair/",
        ".qa-z/runs/baseline/deep/results.sarif",
        ".qa-z/runs/candidate/fast/summary.json",
        ".qa-z/runs/candidate/verify/summary.json",
        ".qa-z/runs/candidate/verify/compare.json",
        ".qa-z/runs/candidate/verify/report.md",
        "verdict `improved`",
    ):
        assert artifact in docs


def test_hosted_demo_docs_do_not_imply_cloud_or_live_execution() -> None:
    docs = read("docs/hosted-demo.md") + "\n" + read("docs/docs-site.md")

    for text in (
        "static docs page",
        "not QA-Z Cloud",
        "must not imply QA-Z Cloud",
        "hidden backend state",
        "live-agent execution",
        "uploaded source-code analysis",
        "local replay commands",
    ):
        assert text in docs

    for forbidden in (
        "upload your repository",
        "hosted repair execution",
        "remote QA-Z run",
        "QA-Z Cloud backend",
    ):
        assert forbidden not in docs


def test_docs_site_links_hosted_demo_static_sources() -> None:
    docs_site = read("docs/docs-site.md")

    for text in (
        "Hosted Demo Page",
        "docs/hosted-demo.md",
        "docs/demo-script.md",
        "docs/assets/qa-z-agent-auth-bug.cast",
        "docs/assets/qa-z-demo.cast",
        "docs/assets/qa-z-demo.svg",
        "Markdown under `docs/` is the canonical source",
    ):
        assert text in docs_site
