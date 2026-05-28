"""Behavior tests for local governance artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from qa_z.cli import main


def read_json_stdout(capsys) -> dict[str, Any]:
    return json.loads(capsys.readouterr().out)


def write_config(root: Path) -> None:
    (root / "qa-z.yaml").write_text(
        yaml.safe_dump({"project": {"name": "governance-test"}}, sort_keys=False),
        encoding="utf-8",
    )


def test_baseline_create_writes_local_governance_baseline(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)

    exit_code = main(["baseline", "create", "--path", str(tmp_path), "--json"])
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["kind"] == "qa_z.governance_baseline"
    assert payload["status"] == "created"
    assert payload["summary"]["config_exists"] is True
    baseline_path = tmp_path / ".qa-z" / "governance" / "baseline.json"
    assert baseline_path.is_file()
    assert json.loads(baseline_path.read_text(encoding="utf-8")) == payload


def test_waiver_add_records_owner_reason_and_expiration(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "waiver",
            "add",
            "--path",
            str(tmp_path),
            "--finding-id",
            "AUTH-001",
            "--owner",
            "security",
            "--reason",
            "False positive after manual review.",
            "--expires",
            "2026-12-31",
            "--json",
        ]
    )
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["kind"] == "qa_z.governance_waiver"
    assert payload["status"] == "active"
    assert payload["finding_id"] == "AUTH-001"
    assert payload["owner"] == "security"
    assert payload["expires"] == "2026-12-31"
    waivers = json.loads(
        (tmp_path / ".qa-z" / "governance" / "waivers.json").read_text(encoding="utf-8")
    )
    assert waivers["waivers"] == [payload]


def test_governance_report_reads_baseline_and_waivers(tmp_path: Path, capsys) -> None:
    write_config(tmp_path)
    assert main(["baseline", "create", "--path", str(tmp_path), "--json"]) == 0
    capsys.readouterr()
    assert (
        main(
            [
                "waiver",
                "add",
                "--path",
                str(tmp_path),
                "--finding-id",
                "AUTH-001",
                "--owner",
                "security",
                "--reason",
                "False positive after manual review.",
                "--expires",
                "2026-12-31",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()

    exit_code = main(["governance", "report", "--path", str(tmp_path), "--json"])
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["kind"] == "qa_z.governance_report"
    assert payload["status"] == "warning"
    assert payload["baseline"]["status"] == "created"
    assert payload["waiver_summary"] == {
        "active": 1,
        "expired": 0,
        "total": 1,
    }
    assert payload["audit_trail"] == [
        ".qa-z/governance/baseline.json",
        ".qa-z/governance/waivers.json",
    ]
