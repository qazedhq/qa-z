"""Public beta stabilization checks for the v0.20-v0.30 roadmap."""

from __future__ import annotations

from pathlib import Path

from qa_z.cli import build_parser


ROOT = Path(__file__).resolve().parents[1]


def test_public_beta_cli_surface_includes_v020_to_v030_commands() -> None:
    parser = build_parser()
    command_action = next(
        action for action in parser._actions if action.dest == "command"
    )
    choices = set(command_action.choices or ())

    for command in (
        "doctor",
        "init",
        "summary",
        "repair-session",
        "github-summary",
        "repair-prompt",
        "scorecard",
        "policy",
        "baseline",
        "waiver",
        "governance",
    ):
        assert command in choices


def test_public_beta_stabilization_report_maps_roadmap_to_evidence() -> None:
    report = (
        ROOT / "docs" / "reports" / "v0.30-public-beta-stabilization.md"
    ).read_text(encoding="utf-8")

    for milestone in (
        "v0.20",
        "v0.21",
        "v0.22",
        "v0.23",
        "v0.24",
        "v0.25",
        "v0.26",
        "v0.27",
        "v0.28",
        "v0.29",
        "v0.30",
    ):
        assert milestone in report

    for command in (
        "qa-z summary --from-run latest",
        "qa-z repair-session",
        "qa-z github-summary",
        "qa-z repair-prompt --adapter human",
        "qa-z scorecard",
        "qa-z policy validate",
        "qa-z baseline create",
        "qa-z waiver add",
        "qa-z governance report",
    ):
        assert command in report

    for boundary in (
        "Production PyPI remains blocked",
        "No PyPI upload",
        "No deploy",
        "No GitHub Release",
    ):
        assert boundary in report
