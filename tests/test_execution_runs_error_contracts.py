"""JSON failure-contract tests for fast/deep run artifact writing."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

from qa_z.cli import main


def python_command(source: str) -> list[str]:
    return [sys.executable, "-c", source]


def write_fast_config(root: Path) -> None:
    config = {
        "project": {"name": "run-error-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "fail_on_missing_tool": True,
            "checks": [
                {
                    "id": "py_test",
                    "kind": "test",
                    "run": python_command(""),
                }
            ],
        },
    }
    (root / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_deep_config(root: Path) -> None:
    config = {
        "project": {"name": "run-error-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {"output_dir": ".qa-z/runs"},
        "deep": {"checks": []},
    }
    (root / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_contract(root: Path) -> None:
    contract_dir = root / "qa" / "contracts"
    contract_dir.mkdir(parents=True, exist_ok=True)
    (contract_dir / "contract.md").write_text(
        "# QA Contract: Run error test\n\n## Acceptance Checks\n\n- Run checks.\n",
        encoding="utf-8",
    )


def test_fast_json_reports_run_summary_artifact_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_fast_config(tmp_path)
    write_contract(tmp_path)
    output_dir = tmp_path / ".qa-z" / "runs" / "local"
    original_write_text = Path.write_text

    def fail_summary_json(path: Path, *args, **kwargs) -> int:
        if path == output_dir / "fast" / "summary.json":
            raise OSError("disk full")
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_summary_json)

    exit_code = main(
        [
            "fast",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["kind"] == "qa_z.fast_error"
    assert output["error"] == "artifact_write_error"
    assert "qa-z fast: artifact write error:" in output["message"]
    assert "could not write run summary artifacts" in output["message"]
    assert "disk full" in output["message"]


def test_deep_json_reports_run_summary_artifact_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(tmp_path)
    output_dir = tmp_path / ".qa-z" / "runs" / "local"
    original_write_text = Path.write_text

    def fail_summary_json(path: Path, *args, **kwargs) -> int:
        if path == output_dir / "deep" / "summary.json":
            raise OSError("disk full")
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_summary_json)

    exit_code = main(
        [
            "deep",
            "--path",
            str(tmp_path),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["kind"] == "qa_z.deep_error"
    assert output["error"] == "artifact_write_error"
    assert "qa-z deep: artifact write error:" in output["message"]
    assert "could not write run summary artifacts" in output["message"]
    assert "disk full" in output["message"]
