"""CLI tests for SARIF artifact emission."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from qa_z.cli import main


def write_deep_config(root: Path) -> None:
    """Write a minimal config that enables Semgrep deep checks."""
    config: dict[str, Any] = {
        "project": {"name": "qa-z-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {"output_dir": ".qa-z/runs"},
        "deep": {
            "checks": [
                {
                    "id": "sg_scan",
                    "enabled": True,
                    "run": ["semgrep", "--config", "auto", "--json"],
                    "kind": "static-analysis",
                    "semgrep": {"config": "auto"},
                }
            ],
        },
    }
    (root / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def test_deep_writes_sarif_artifact_and_optional_copy(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(tmp_path)
    payload = {
        "results": [
            {
                "check_id": "python.lang.security.audit.eval",
                "path": "src/app.py",
                "start": {"line": 42},
                "extra": {"severity": "ERROR", "message": "Avoid use of eval"},
            }
        ]
    }

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=1,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fake_run)
    sarif_copy = tmp_path / "qa-z.sarif"

    exit_code = main(
        [
            "deep",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / ".qa-z" / "runs" / "local"),
            "--sarif-output",
            str(sarif_copy),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    sarif_path = tmp_path / output["artifact_dir"] / "results.sarif"
    sarif = json.loads(sarif_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert sarif_path.exists()
    assert sarif_copy.exists()
    assert json.loads(sarif_copy.read_text(encoding="utf-8")) == sarif
    assert sarif["runs"][0]["results"][0]["ruleId"] == (
        "python.lang.security.audit.eval"
    )
    assert sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"] == {
        "artifactLocation": {"uri": "src/app.py"},
        "region": {"startLine": 42},
    }


def test_deep_writes_empty_sarif_when_no_deep_checks_are_configured(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(
            {
                "project": {"name": "qa-z-test", "languages": ["python"]},
                "contracts": {"output_dir": "qa/contracts"},
                "fast": {"output_dir": ".qa-z/runs"},
                "deep": {"checks": []},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "deep",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / ".qa-z" / "runs" / "local"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    sarif_path = tmp_path / output["artifact_dir"] / "results.sarif"
    sarif = json.loads(sarif_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert sarif["runs"][0]["results"] == []
