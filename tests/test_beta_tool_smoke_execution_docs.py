from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXECUTION_PATH = "docs/reports/v0.10.0-beta-tool-smoke-execution.md"
EXECUTION = ROOT / EXECUTION_PATH


def read(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_tool_smoke_execution_packet_records_no_upload_pass() -> None:
    assert EXECUTION.exists()
    packet = read(EXECUTION)

    assert "Decision: `NO_UPLOAD_SMOKE_PASS`." in packet
    assert "`v0.10.0-beta` is not released." in packet
    assert "Release execution remains `NO-GO`." in packet
    assert "`b63d1f43f6a194e2c9302238a7557760e5cc492b`" in packet
    assert "`registry_upload_executed=false`" in packet

    for check in (
        '"summary": "package smoke rehearsal passed"',
        '"exit_code": 0',
        '"id": "twine_check"',
        '"id": "pipx_wheel_help"',
        '"id": "uvx_wheel_help"',
        '"status": "PASS"',
    ):
        assert check in packet


def test_tool_smoke_execution_keeps_release_actions_blocked() -> None:
    packet = read(EXECUTION)

    for non_action in (
        "release `v0.10.0-beta`",
        "change `pyproject.toml`",
        "bump version metadata",
        "create a tag",
        "create a GitHub Release",
        "publish a package",
        "run `twine upload`",
        "run `uv publish`",
        "run `npm publish`",
        "deploy",
        "load or print registry credentials",
    ):
        assert non_action in packet

    for false_claim in (
        "registry_upload_executed=true",
        "PyPI publish completed",
        "TestPyPI publish completed",
        "release execution is `GO`",
    ):
        assert false_claim not in packet


def test_tool_smoke_execution_is_linked_from_current_release_truth_docs() -> None:
    for report_path in (
        "docs/package-publish-plan.md",
        "docs/reports/v0.10.0-beta-no-release-decision.md",
        "docs/reports/v0.10.0-beta-release-decision.md",
        "docs/reports/v0.10.0-beta-release-execution-checklist.md",
        "docs/reports/v0.10.0-beta-readiness.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
        "docs/reports/v0.10.0-beta-exact-sha-proof.md",
        "docs/reports/v0.10.0-beta-final-sha-proof-protocol.md",
        "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md",
        "docs/reports/v0.10.0-beta-rollback-yank-policy.md",
    ):
        report = read(report_path)
        text = normalized(report)

        assert EXECUTION_PATH in report
        assert (
            "release execution remains `NO-GO`" in text
            or "release execution `NO-GO`" in text
            or "Release execution remains `NO-GO`" in report
        )


def test_tool_smoke_execution_updates_current_blocker_matrix() -> None:
    checklist = read("docs/reports/v0.10.0-beta-release-execution-checklist.md")
    decision = read("docs/reports/v0.10.0-beta-release-decision.md")
    no_release = read("docs/reports/v0.10.0-beta-no-release-decision.md")

    assert "| tool-equipped twine/pipx/uvx smoke | `PASS` |" in checklist
    assert "| Local package smoke |" in decision
    assert "| Tool-equipped package smoke rehearsal | `PASS` |" in decision
    assert "| Tool-equipped twine/pipx/uvx smoke | `PASS` |" in no_release
    assert "registry_upload_executed=false" in checklist
    assert "registry_upload_executed=false" in decision
    assert "registry_upload_executed=false" in no_release
