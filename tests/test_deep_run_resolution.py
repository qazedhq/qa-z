"""Tests for deep runner run resolution and skeleton artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from qa_z.cli import main
from qa_z.runners.deep import configured_deep_checks, resolve_deep_checks
from qa_z.runners.deep import resolve_deep_run_dir


def write_config(root: Path) -> dict[str, Any]:
    """Write a minimal qa-z config with the default run root."""
    config: dict[str, Any] = {
        "project": {"name": "qa-z-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {"output_dir": ".qa-z/runs"},
    }
    (root / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    return config


def write_fast_summary(root: Path, run_id: str, *, status: str = "passed") -> Path:
    """Write a minimal fast summary and point latest-run.json at it."""
    run_dir = root / ".qa-z" / "runs" / run_id
    summary_path = run_dir / "fast" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "mode": "fast",
        "contract_path": "qa/contracts/example.md",
        "project_root": str(root),
        "status": status,
        "started_at": "2026-04-12T00:00:00Z",
        "finished_at": "2026-04-12T00:00:01Z",
        "artifact_dir": f".qa-z/runs/{run_id}/fast",
        "selection": None,
        "checks": [],
    }
    summary_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    (root / ".qa-z" / "runs" / "latest-run.json").write_text(
        json.dumps({"run_dir": f".qa-z/runs/{run_id}"}) + "\n", encoding="utf-8"
    )
    return run_dir


def test_deep_attaches_to_latest_valid_fast_run(tmp_path: Path) -> None:
    config = write_config(tmp_path)
    fast_run_dir = write_fast_summary(tmp_path, "ci")

    resolution = resolve_deep_run_dir(
        root=tmp_path,
        config=config,
        output_dir=None,
        from_run=None,
    )

    assert resolution.run_dir == fast_run_dir
    assert resolution.deep_dir == fast_run_dir / "deep"
    assert resolution.attached_to_fast_run is True
    assert resolution.source == "latest"


def test_deep_creates_new_run_when_no_valid_fast_run_exists(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)

    exit_code = main(["deep", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)
    artifact_dir = tmp_path / output["artifact_dir"]

    assert exit_code == 0
    assert output["mode"] == "deep"
    assert output["status"] == "passed"
    assert output["checks"] == []
    assert output["run_resolution"]["source"] == "new_run"
    assert output["run_resolution"]["attached_to_fast_run"] is False
    assert artifact_dir.name == "deep"
    assert (artifact_dir / "summary.json").exists()
    assert (artifact_dir / "summary.md").exists()
    assert "# QA-Z Deep Summary" in (artifact_dir / "summary.md").read_text(
        encoding="utf-8"
    )
    assert "- Source: new_run" in (artifact_dir / "summary.md").read_text(
        encoding="utf-8"
    )


def test_deep_output_dir_overrides_attach_behavior(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_fast_summary(tmp_path, "ci")
    output_dir = tmp_path / "custom-run"

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

    assert exit_code == 0
    assert output["artifact_dir"] == "custom-run/deep"
    assert output["run_resolution"] == {
        "attached_to_fast_run": False,
        "deep_dir": "custom-run/deep",
        "fast_summary_path": None,
        "run_dir": "custom-run",
        "source": "output_dir",
    }
    assert (output_dir / "deep" / "summary.json").exists()
    assert not (tmp_path / ".qa-z" / "runs" / "ci" / "deep").exists()


def test_deep_from_run_records_explicit_resolution(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_fast_summary(tmp_path, "ci")

    exit_code = main(
        [
            "deep",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/ci",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["run_resolution"] == {
        "attached_to_fast_run": True,
        "deep_dir": ".qa-z/runs/ci/deep",
        "fast_summary_path": ".qa-z/runs/ci/fast/summary.json",
        "run_dir": ".qa-z/runs/ci",
        "source": "from_run",
    }


def test_deep_rejects_from_run_with_output_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_fast_summary(tmp_path, "ci")
    output_dir = tmp_path / "custom-run"

    exit_code = main(
        [
            "deep",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/ci",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "qa-z deep: argument error:" in captured.out
    assert "--from-run and --output-dir cannot be combined" in captured.out
    assert not output_dir.exists()
    assert not (tmp_path / ".qa-z" / "runs" / "ci" / "deep").exists()


def test_deep_runner_uses_legacy_checks_deep_when_modern_deep_absent() -> None:
    config = {"checks": {"deep": ["security"]}}

    specs = resolve_deep_checks(config)

    assert configured_deep_checks(config) == ["security"]
    assert [spec.id for spec in specs] == ["sg_scan"]


def test_deep_runner_prefers_modern_deep_checks_over_legacy() -> None:
    config = {
        "deep": {"checks": []},
        "checks": {"deep": ["security"]},
    }

    assert configured_deep_checks(config) == []
    assert resolve_deep_checks(config) == []
