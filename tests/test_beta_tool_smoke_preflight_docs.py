from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_PATH = "docs/reports/v0.10.0-beta-tool-smoke-preflight.md"
PREFLIGHT = ROOT / PREFLIGHT_PATH
NO_RELEASE_PATH = "docs/reports/v0.10.0-beta-no-release-decision.md"
CHECKLIST_PATH = "docs/reports/v0.10.0-beta-release-execution-checklist.md"
DECISION_PATH = "docs/reports/v0.10.0-beta-release-decision.md"


def read(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_tool_smoke_preflight_packet_exists_and_records_decision() -> None:
    assert PREFLIGHT.exists()
    packet = read(PREFLIGHT)

    for section in (
        "## Purpose",
        "## Current No-release State",
        "## Worktree Preflight",
        "## Tool Availability",
        "## Credential Boundary",
        "## Smoke Execution Decision",
        "## Smoke Results, if run",
        "## What This Does Not Prove",
        "## Explicit Non-actions",
        "## Remaining Blockers",
    ):
        assert section in packet

    assert "Decision: `BLOCKED_TOOL_MISSING`." in packet
    assert "`v0.10.0-beta` is not released." in packet
    assert "Release execution remains `NO-GO`." in packet
    assert "Smoke results: `NOT RUN`." in packet
    assert "`registry_upload_executed=false`" in packet
    assert "`bc1cef8b2a38a1099f92bad52a6db11bf34640f2`" in packet


def test_tool_smoke_preflight_documents_required_status_vocabulary() -> None:
    packet = read(PREFLIGHT)

    for status in (
        "READY_FOR_NO_UPLOAD_SMOKE",
        "BLOCKED_TOOL_MISSING",
        "BLOCKED_CREDENTIAL_PRESENT",
        "BLOCKED_DIRTY_WORKTREE",
        "NOT RUN",
        "PASS",
        "FAIL",
    ):
        assert f"`{status}`" in packet


def test_missing_tools_are_recorded_as_blocked_not_passed() -> None:
    packet = read(PREFLIGHT)

    for tool in ("twine", "pipx", "uvx"):
        tool_lines = [line for line in packet.splitlines() if f"| `{tool}` |" in line]
        assert len(tool_lines) == 1
        assert "`BLOCKED_TOOL_MISSING`" in tool_lines[0]
        assert "`PASS`" not in tool_lines[0]

    assert "No tool install was performed." in packet
    assert "claim missing tools are `PASS`" in packet


def test_credential_boundary_records_absence_without_values() -> None:
    packet = read(PREFLIGHT)

    assert (
        "| Package-publish environment variables | `PASS` | "
        "`NO_PACKAGE_PUBLISH_CREDENTIAL_ENV_FOUND` |"
    ) in packet
    assert "| User `.pypirc` | `PASS` | `PYPIRC_ABSENT` |" in packet
    assert "No credential values were printed." in packet
    assert "Credentials are not approval." in packet

    for secret_assignment in (
        r"TWINE_PASSWORD\s*=",
        r"TWINE_API_TOKEN\s*=",
        r"PYPI_TOKEN\s*=",
        r"UV_PUBLISH_TOKEN\s*=",
    ):
        assert re.search(secret_assignment, packet, re.IGNORECASE) is None


def test_preflight_keeps_release_actions_blocked_and_unexecuted() -> None:
    packet = read(PREFLIGHT)
    text = normalized(packet)

    for non_action in (
        "release `v0.10.0-beta`",
        "change `pyproject.toml`",
        "bump version metadata",
        "install `twine`, `pipx`, `uvx`, or other release tools",
        "load registry credentials",
        "create a tag",
        "create a GitHub Release",
        "publish a package",
        "run `twine upload`",
        "deploy",
    ):
        assert non_action in packet

    for executed_boundary in (
        "No `twine upload` command was run.",
        "No tag command was run.",
        "No GitHub Release was created.",
        "No package publish occurred.",
        "No deploy occurred.",
        "No version bump occurred.",
    ):
        assert executed_boundary in text


def test_preflight_links_from_release_truth_docs_and_keeps_no_go() -> None:
    for report_path in (NO_RELEASE_PATH, CHECKLIST_PATH, DECISION_PATH):
        report = read(report_path)
        text = normalized(report)

        assert PREFLIGHT_PATH in report
        assert "tool-smoke preflight" in text.lower()
        assert (
            "release execution `NO-GO`" in text
            or "release execution remains `NO-GO`" in text
            or "release execution is currently `NO-GO`" in text
        )


def test_preflight_does_not_reclassify_smoke_as_run() -> None:
    packet = read(PREFLIGHT)

    for field in (
        "| `twine_check` | `NOT RUN` |",
        "| `pipx_wheel_help` | `NOT RUN` |",
        "| `uvx_wheel_help` | `NOT RUN` |",
        "| `registry_upload_executed` | `false` |",
    ):
        assert field in packet

    for false_claim in (
        "twine_check=PASS",
        "pipx_wheel_help=PASS",
        "uvx_wheel_help=PASS",
        "registry_upload_executed=true",
        "release execution is `GO`",
    ):
        assert false_claim not in packet
