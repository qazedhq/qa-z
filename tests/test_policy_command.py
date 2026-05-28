"""Behavior tests for local merge policy packs."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml

from qa_z.cli import main


def read_json_stdout(capsys) -> dict[str, Any]:
    return json.loads(capsys.readouterr().out)


def python_command(source: str) -> list[str]:
    return [sys.executable, "-c", source]


def write_guard_config(root: Path) -> None:
    config = {
        "project": {"name": "policy-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "checks": [{"id": "py_test", "kind": "test", "run": python_command("")}],
        },
        "deep": {"checks": []},
    }
    (root / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    contract_dir = root / "qa" / "contracts"
    contract_dir.mkdir(parents=True, exist_ok=True)
    (contract_dir / "contract.md").write_text(
        dedent(
            """
            # QA Contract: Policy test

            ## Acceptance Checks

            - Run the configured deterministic check.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def test_policy_validate_accepts_builtin_strict_pack(tmp_path: Path, capsys) -> None:
    exit_code = main(
        ["policy", "validate", "--path", str(tmp_path), "--policy", "strict", "--json"]
    )
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["kind"] == "qa_z.policy_validation"
    assert payload["status"] == "valid"
    assert payload["policy"]["name"] == "strict"
    assert payload["policy"]["block_on"] == [
        "auth_regression",
        "owner_check_removed",
        "secret_leak",
    ]
    assert payload["policy"]["require_review"] == [
        "generated_code_change",
        "dependency_change",
    ]


def test_policy_validate_rejects_empty_configured_block_on(
    tmp_path: Path, capsys
) -> None:
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(
            {
                "project": {"name": "policy-test"},
                "merge_policy": {
                    "name": "team",
                    "block_on": [],
                    "require_review": ["dependency_change"],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    exit_code = main(["policy", "validate", "--path", str(tmp_path), "--json"])
    payload = read_json_stdout(capsys)

    assert exit_code == 1
    assert payload["status"] == "invalid"
    assert payload["errors"] == [
        "merge_policy.block_on must contain at least one rule id."
    ]


def test_guard_accepts_strict_policy_and_records_it(tmp_path: Path, capsys) -> None:
    write_guard_config(tmp_path)

    exit_code = main(
        [
            "guard",
            "--path",
            str(tmp_path),
            "--deep",
            "never",
            "--policy",
            "strict",
            "--json",
        ]
    )
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "merge_ok"
    assert payload["policy"]["name"] == "strict"
    assert payload["policy"]["source"] == "builtin"
