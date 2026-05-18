from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NO_RELEASE_PATH = "docs/reports/v0.10.0-beta-no-release-decision.md"
NO_RELEASE = ROOT / NO_RELEASE_PATH


def read(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_no_release_decision_packet_exists_and_freezes_current_decision() -> None:
    assert NO_RELEASE.exists()
    packet = read(NO_RELEASE)
    text = normalized(packet)

    assert "Current decision: `No release yet`." in packet
    assert "`v0.10.0-beta` is not released." in packet
    assert "Release execution remains `NO-GO`." in packet
    assert "blockers are deferred, not resolved" in text
    assert "Current package metadata remains `0.9.8a0`." in packet
    assert "PR #70 merged as `62224680e7433604f6a150f0c157833ad9ea3173`" in packet

    for false_claim in (
        "release execution is `GO`",
        "registry_upload_executed=true",
        "PyPI publish completed",
        "TestPyPI publish completed",
        "rollback/yank proof is complete",
    ):
        assert false_claim not in packet


def test_no_release_decision_preserves_all_remaining_blockers() -> None:
    packet = read(NO_RELEASE)

    for blocker in (
        "Release-owner selected registry/release path",
        "Official policy verification at execution time",
        "Actual rollback/yank proof",
        "Tool-equipped twine/pipx/uvx smoke",
        "Registry credentials",
        "Version execution decision",
        "Advisory option/proof",
        "Final release-execution-time SHA proof",
    ):
        assert blocker in packet

    for status_line in (
        "| Release-owner selected registry/release path | `BLOCKED` |",
        "| Tool-equipped twine/pipx/uvx smoke | `PASS` |",
        "| Registry credentials | `BLOCKED` |",
        "| Final release-execution-time SHA proof | `BLOCKED` |",
    ):
        assert status_line in packet


def test_no_release_decision_blocks_release_adjacent_actions() -> None:
    packet = read(NO_RELEASE)

    assert "These examples are blocked commands, not safe commands." in packet
    for blocked in (
        "python -m twine upload --repository testpypi dist/*",
        "python -m twine upload dist/*",
        "git tag ...",
        "gh release create ...",
        "npm publish",
        "deploy commands",
    ):
        assert blocked in packet

    for non_action in (
        "release `v0.10.0-beta`",
        "change `pyproject.toml`",
        "create a tag",
        "create a GitHub Release",
        "publish a package",
        "deploy",
        "resolve release blockers",
    ):
        assert non_action in packet


def test_no_release_decision_is_linked_from_release_truth_surfaces() -> None:
    for report_path in (
        "docs/reports/v0.10.0-beta-release-execution-checklist.md",
        "docs/reports/v0.10.0-beta-release-decision.md",
    ):
        report = read(report_path)
        text = normalized(report)

        assert NO_RELEASE_PATH in report
        assert "no-release decision" in text
        assert (
            "release execution `NO-GO`" in text
            or "release execution remains `NO-GO`" in text
        )
