"""JSON failure-contract tests for verify CLI artifact writing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.cli import main
from tests.repair_prompt_test_support import write_config, write_contract, write_summary


def test_verify_json_reports_artifact_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "baseline")
    write_summary(
        tmp_path,
        "candidate",
        status="passed",
        checks=[
            {
                "id": "py_type",
                "tool": "mypy",
                "command": ["mypy", "src", "tests"],
                "kind": "typecheck",
                "status": "passed",
                "exit_code": 0,
                "duration_ms": 100,
                "stdout_tail": "",
                "stderr_tail": "",
            }
        ],
    )
    output_dir = tmp_path / ".qa-z" / "runs" / "candidate" / "verify"
    original_write_text = Path.write_text

    def fail_verify_summary(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path == output_dir / "summary.json":
            raise OSError("disk full")
        return original_write_text(
            path, data, encoding=encoding, errors=errors, newline=newline
        )

    monkeypatch.setattr(Path, "write_text", fail_verify_summary)

    exit_code = main(
        [
            "verify",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--candidate-run",
            ".qa-z/runs/candidate",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "kind": "qa_z.verify_error",
        "error": "artifact_write_error",
        "exit_code": 2,
        "message": output["message"],
    }
    assert "qa-z verify: artifact error:" in output["message"]
    assert "could not write verification artifacts" in output["message"]
    assert "disk full" in output["message"]
