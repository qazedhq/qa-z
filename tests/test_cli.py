"""CLI tests for the QA-Z bootstrap."""

from __future__ import annotations

import argparse
import json
import os
import sys
from textwrap import dedent

import pytest
import yaml

from qa_z.cli import build_parser, main


def get_subcommands(parser: argparse.ArgumentParser) -> set[str]:
    """Extract registered subcommand names from the parser."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    raise AssertionError("Parser does not define subcommands")


def python_command(source: str) -> list[str]:
    """Build a cross-platform Python subprocess command for fast-runner tests."""
    return [sys.executable, "-c", source]


def write_fast_config(
    tmp_path, checks: list[dict], *, strict_no_tests: bool = False
) -> None:
    """Write a qa-z config with explicit fast checks."""
    config = {
        "project": {"name": "qa-z-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "strict_no_tests": strict_no_tests,
            "fail_on_missing_tool": True,
            "checks": [
                {
                    "id": check["id"],
                    "enabled": check.get("enabled", True),
                    "run": check["run"],
                    "kind": check.get("kind", "test"),
                    "no_tests": check.get("no_tests", "warn"),
                }
                for check in checks
            ],
        },
    }
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_contract(
    tmp_path, name: str = "contract.md", title: str = "Fast runner"
) -> None:
    """Write a minimal contract file under the configured contract directory."""
    contract_dir = tmp_path / "qa" / "contracts"
    contract_dir.mkdir(parents=True, exist_ok=True)
    (contract_dir / name).write_text(
        f"# QA Contract: {title}\n\n## Acceptance Checks\n\n- Run fast checks.\n",
        encoding="utf-8",
    )


def test_parser_registers_core_subcommands() -> None:
    parser = build_parser()
    assert {
        "init",
        "plan",
        "fast",
        "deep",
        "review",
        "repair-prompt",
    } <= get_subcommands(parser)


def test_init_creates_bootstrap_files(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["init", "--path", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert (tmp_path / "qa-z.yaml").exists()
    assert (tmp_path / "qa" / "contracts" / "README.md").exists()
    assert "created: qa-z.yaml" in captured.out


def test_init_is_idempotent(tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    first_exit = main(["init", "--path", str(tmp_path)])
    first_output = capsys.readouterr().out
    second_exit = main(["init", "--path", str(tmp_path)])
    second_output = capsys.readouterr().out

    assert first_exit == 0
    assert "created: qa-z.yaml" in first_output
    assert second_exit == 0
    assert "skipped: qa-z.yaml" in second_output
    assert "Nothing new was written" in second_output


def test_plan_creates_a_contract_draft_from_sources(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "qa-z.yaml").write_text(
        dedent(
            """
            project:
              name: qa-z
              languages:
                - python
            contracts:
              output_dir: qa/contracts
            checks:
              fast:
                - lint
                - unit
              deep:
                - security
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    issue_path = tmp_path / "issue.md"
    issue_path.write_text(
        "# Problem\nUsers can bypass the auth guard on the billing route.\n",
        encoding="utf-8",
    )
    spec_path = tmp_path / "spec.md"
    spec_path.write_text(
        "# Spec\nProtect billing endpoints and add a regression test.\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "plan",
            "--path",
            str(tmp_path),
            "--title",
            "Protect billing auth guard",
            "--issue",
            str(issue_path),
            "--spec",
            str(spec_path),
        ]
    )
    captured = capsys.readouterr()
    contract_path = tmp_path / "qa" / "contracts" / "protect-billing-auth-guard.md"

    assert exit_code == 0
    assert contract_path.exists()
    contract = contract_path.read_text(encoding="utf-8")
    assert "# QA Contract: Protect billing auth guard" in contract
    assert "\n## Contract Summary\n" in contract
    assert "Users can bypass the auth guard" in contract
    assert "Protect billing endpoints" in contract
    assert "## Suggested Checks" in contract
    assert "\n- Languages: python\n" in contract
    assert "- lint" in contract
    assert "- unit" in contract
    assert (
        "created contract: qa/contracts/protect-billing-auth-guard.md" in captured.out
    )


def test_plan_uses_custom_contract_output_directory(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "qa-z.yaml").write_text(
        dedent(
            """
            project:
              name: qa-z
              languages:
                - typescript
            contracts:
              output_dir: quality/contracts
            checks:
              fast:
                - typecheck
              deep:
                - e2e_smoke
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "plan",
            "--path",
            str(tmp_path),
            "--title",
            "Add checkout smoke coverage",
        ]
    )
    captured = capsys.readouterr()
    contract_path = (
        tmp_path / "quality" / "contracts" / "add-checkout-smoke-coverage.md"
    )

    assert exit_code == 0
    assert contract_path.exists()
    assert (
        "created contract: quality/contracts/add-checkout-smoke-coverage.md"
        in captured.out
    )


def test_plan_reads_top_level_fast_check_ids(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "qa-z.yaml").write_text(
        dedent(
            """
            project:
              name: qa-z
              languages:
                - python
            contracts:
              output_dir: qa/contracts
            fast:
              checks:
                - id: py_lint
                  enabled: true
                  run: ["ruff", "check", "."]
                  kind: lint
                - id: py_test
                  enabled: true
                  run: ["pytest", "-q"]
                  kind: test
            checks:
              deep:
                - security
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = main(["plan", "--path", str(tmp_path), "--title", "Honor fast config"])
    capsys.readouterr()
    contract = (tmp_path / "qa" / "contracts" / "honor-fast-config.md").read_text(
        encoding="utf-8"
    )

    assert exit_code == 0
    assert "- py_lint" in contract
    assert "- py_test" in contract


def test_review_renders_a_packet_from_the_latest_contract(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "qa-z.yaml").write_text(
        dedent(
            """
            project:
              name: qa-z
              languages:
                - python
            contracts:
              output_dir: qa/contracts
            checks:
              fast:
                - lint
                - unit
              deep:
                - security
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    issue_path = tmp_path / "issue.md"
    issue_path.write_text(
        "# Problem\nUsers can bypass the auth guard on the billing route.\n",
        encoding="utf-8",
    )

    plan_exit = main(
        [
            "plan",
            "--path",
            str(tmp_path),
            "--title",
            "Protect billing auth guard",
            "--issue",
            str(issue_path),
        ]
    )
    plan_output = capsys.readouterr().out
    review_exit = main(["review", "--path", str(tmp_path)])
    review_output = capsys.readouterr().out

    assert plan_exit == 0
    assert "created contract: qa/contracts/protect-billing-auth-guard.md" in plan_output
    assert review_exit == 0
    assert "# QA-Z Review Packet" in review_output
    assert "qa/contracts/protect-billing-auth-guard.md" in review_output
    assert (
        "Authentication and authorization paths need regression coverage."
        in review_output
    )
    assert "- lint" in review_output


def test_fast_runs_configured_checks_and_writes_json_artifacts(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checks = [
        {"id": "py_lint", "kind": "lint", "run": python_command("")},
        {"id": "py_format", "kind": "format", "run": python_command("")},
        {"id": "py_type", "kind": "typecheck", "run": python_command("")},
        {"id": "py_test", "kind": "test", "run": python_command("")},
    ]
    write_fast_config(tmp_path, checks)
    write_contract(tmp_path)
    output_dir = tmp_path / "runs" / "local"

    exit_code = main(
        [
            "fast",
            "--path",
            str(tmp_path),
            "--contract",
            str(tmp_path / "qa" / "contracts" / "contract.md"),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    summary_path = output_dir / "fast" / "summary.json"

    assert exit_code == 0
    assert output["mode"] == "fast"
    assert output["status"] == "passed"
    assert output["totals"] == {"passed": 4, "failed": 0, "skipped": 0, "warning": 0}
    assert output["contract_path"] == "qa/contracts/contract.md"
    assert summary_path.exists()
    assert (output_dir / "fast" / "summary.md").exists()
    assert (output_dir / "fast" / "checks" / "py_lint.json").exists()
    assert json.loads(summary_path.read_text(encoding="utf-8"))["status"] == "passed"


def test_fast_defaults_to_latest_contract_and_prints_human_summary(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_fast_config(
        tmp_path, [{"id": "py_test", "kind": "test", "run": python_command("")}]
    )
    write_contract(tmp_path, "older.md", title="Older")
    write_contract(tmp_path, "newer.md", title="Newer")
    os.utime(tmp_path / "qa" / "contracts" / "older.md", (1, 1))
    os.utime(tmp_path / "qa" / "contracts" / "newer.md", (2, 2))

    exit_code = main(
        ["fast", "--path", str(tmp_path), "--output-dir", str(tmp_path / "runs")]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "qa-z fast: passed" in output
    assert "Contract: qa/contracts/newer.md" in output
    assert "Summary:" in output


def test_fast_returns_failure_when_a_check_fails(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checks = [
        {"id": "py_lint", "kind": "lint", "run": python_command("")},
        {
            "id": "py_test",
            "kind": "test",
            "run": python_command("import sys; sys.exit(1)"),
        },
    ]
    write_fast_config(tmp_path, checks)
    write_contract(tmp_path)

    exit_code = main(
        [
            "fast",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "runs"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["status"] == "failed"
    assert output["totals"]["failed"] == 1
    assert [
        check["id"] for check in output["checks"] if check["status"] == "failed"
    ] == ["py_test"]


def test_fast_can_warn_or_fail_when_pytest_finds_no_tests(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checks = [
        {
            "id": "py_test",
            "kind": "test",
            "run": python_command("import sys; sys.exit(5)"),
            "no_tests": "warn",
        }
    ]
    write_fast_config(tmp_path, checks)
    write_contract(tmp_path)

    warning_exit = main(
        [
            "fast",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "warn"),
            "--json",
        ]
    )
    warning_output = json.loads(capsys.readouterr().out)
    strict_exit = main(
        [
            "fast",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "strict"),
            "--strict-no-tests",
            "--json",
        ]
    )
    strict_output = json.loads(capsys.readouterr().out)

    assert warning_exit == 0
    assert warning_output["status"] == "passed"
    assert warning_output["checks"][0]["status"] == "warning"
    assert strict_exit == 1
    assert strict_output["status"] == "failed"
    assert strict_output["checks"][0]["status"] == "failed"


def test_fast_config_can_make_no_tests_strict(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checks = [
        {
            "id": "py_test",
            "kind": "test",
            "run": python_command("import sys; sys.exit(5)"),
            "no_tests": "warn",
        }
    ]
    write_fast_config(tmp_path, checks, strict_no_tests=True)
    write_contract(tmp_path)

    exit_code = main(
        [
            "fast",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "runs"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["status"] == "failed"
    assert output["checks"][0]["status"] == "failed"


def test_fast_returns_missing_tool_exit_code(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_fast_config(
        tmp_path,
        [{"id": "py_lint", "kind": "lint", "run": ["definitely-missing-qa-z-tool"]}],
    )
    write_contract(tmp_path)

    exit_code = main(
        [
            "fast",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "runs"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 3
    assert output["status"] == "error"
    assert output["checks"][0]["status"] == "error"


def test_fast_returns_unsupported_when_no_checks_are_configured(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_fast_config(tmp_path, [])
    write_contract(tmp_path)

    exit_code = main(
        [
            "fast",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "runs"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 4
    assert output["status"] == "unsupported"
    assert output["checks"] == []


def test_fast_returns_config_error_for_broken_yaml(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "qa-z.yaml").write_text("fast: [\n", encoding="utf-8")

    exit_code = main(["fast", "--path", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 2
    assert "qa-z fast: configuration error:" in output


@pytest.mark.parametrize("command", ["deep"])
def test_placeholder_commands_emit_guidance(
    command: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([command])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"qa-z {command}" in captured.out
    assert "scaffolded" in captured.out
