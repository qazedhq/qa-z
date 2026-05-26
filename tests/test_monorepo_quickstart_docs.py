from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_quickstart_documents_monorepo_init_and_gate_path() -> None:
    quickstart = read("docs/quickstart.md")

    for text in (
        "Mixed Python/TypeScript Monorepo",
        "qa-z init --profile monorepo --with-agent-templates --with-github-workflow",
        "qa-z doctor --json",
        'qa-z plan --title "Review mixed Python/TypeScript change"',
        "qa-z fast",
        "qa-z deep --from-run latest",
        "qa-z review --from-run latest",
        "qa-z repair-prompt --from-run latest --adapter codex",
    ):
        assert text in quickstart


def test_quickstart_explains_monorepo_profile_semantics() -> None:
    quickstart = read("docs/quickstart.md")

    for text in (
        'project.languages: ["python", "typescript"]',
        "Python and TypeScript fast-check surfaces",
        "smart fast selection as the default mode",
    ):
        assert text in quickstart


def test_quickstart_monorepo_keeps_local_deterministic_boundary() -> None:
    quickstart = read("docs/quickstart.md")

    for text in (
        "deterministic local gate",
        "does not call live model APIs",
        "run live agents",
        "publish packages",
        "deploy",
        "create branches",
        "commit",
        "push",
        "post bot comments",
        "Root `.qa-z/**` evidence is local by default",
    ):
        assert text in quickstart


def test_monorepo_docs_match_init_profile_behavior() -> None:
    bootstrap = read("src/qa_z/commands/bootstrap_init.py")
    quickstart = read("docs/quickstart.md")

    assert '"auto"' in bootstrap
    assert '"nextjs"' in bootstrap
    assert '"mixed"' in bootstrap
    assert '"unknown"' in bootstrap
    assert 'project["languages"] = ["python", "typescript"]' in bootstrap
    assert 'selection["default_mode"] = "smart"' in bootstrap
    assert "qa-z init --profile monorepo" in quickstart
