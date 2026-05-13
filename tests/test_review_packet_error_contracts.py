"""JSON failure-contract tests for review packet CLI surfaces."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.cli import main
from tests.repair_prompt_test_support import write_config, write_contract


def test_review_json_reports_missing_run_as_machine_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)

    exit_code = main(
        [
            "review",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/missing",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 4
    assert output == {
        "kind": "qa_z.review_error",
        "error": "source_not_found",
        "exit_code": 4,
        "message": output["message"],
    }
    assert "qa-z review: source not found:" in output["message"]


def test_review_json_reports_missing_contract_as_machine_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)

    exit_code = main(["review", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 4
    assert output == {
        "kind": "qa_z.review_error",
        "error": "source_not_found",
        "exit_code": 4,
        "message": output["message"],
    }
    assert "qa-z review: source not found:" in output["message"]


def test_review_json_reports_broken_config_as_machine_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "qa-z.yaml").write_text("review: [\n", encoding="utf-8")

    exit_code = main(["review", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "kind": "qa_z.review_error",
        "error": "configuration_error",
        "exit_code": 2,
        "message": output["message"],
    }
    assert "qa-z review: configuration error:" in output["message"]


def test_review_json_reports_artifact_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    output_dir = tmp_path / ".qa-z" / "review"
    original_write_text = Path.write_text

    def fail_review_markdown(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path == output_dir / "review.md":
            raise OSError("disk full")
        return original_write_text(
            path, data, encoding=encoding, errors=errors, newline=newline
        )

    monkeypatch.setattr(Path, "write_text", fail_review_markdown)

    exit_code = main(
        [
            "review",
            "--path",
            str(tmp_path),
            "--json",
            "--output-dir",
            str(output_dir),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "kind": "qa_z.review_error",
        "error": "artifact_write_error",
        "exit_code": 2,
        "message": output["message"],
    }
    assert "qa-z review: artifact error:" in output["message"]
    assert "could not write review artifacts" in output["message"]
    assert "could not write review markdown artifact" in output["message"]
    assert str(output_dir / "review.md") in output["message"]
    assert "disk full" in output["message"]


def test_review_json_reports_json_artifact_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    output_dir = tmp_path / ".qa-z" / "review"
    original_write_text = Path.write_text

    def fail_review_json(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path == output_dir / "review.json":
            raise OSError("disk full")
        return original_write_text(
            path, data, encoding=encoding, errors=errors, newline=newline
        )

    monkeypatch.setattr(Path, "write_text", fail_review_json)

    exit_code = main(
        [
            "review",
            "--path",
            str(tmp_path),
            "--json",
            "--output-dir",
            str(output_dir),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "kind": "qa_z.review_error",
        "error": "artifact_write_error",
        "exit_code": 2,
        "message": output["message"],
    }
    assert "qa-z review: artifact error:" in output["message"]
    assert "could not write review artifacts" in output["message"]
    assert "could not write review json artifact" in output["message"]
    assert str(output_dir / "review.json") in output["message"]
    assert "disk full" in output["message"]
