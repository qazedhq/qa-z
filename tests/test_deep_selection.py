"""Tests for deep-runner smart selection."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
import yaml

from qa_z.cli import main
from qa_z.diffing.models import ChangedFile, ChangeSet
from qa_z.runners.models import CheckSpec
from qa_z.runners.selection_deep import build_deep_selection


def sg_scan_spec() -> CheckSpec:
    """Return the built-in Semgrep check shape used by deep selection."""
    return CheckSpec(
        id="sg_scan",
        command=["semgrep", "--config", "auto", "--json"],
        kind="static-analysis",
    )


def changed(
    path: str,
    *,
    status: str = "modified",
    language: str = "python",
    kind: str = "source",
) -> ChangedFile:
    """Build a changed-file record for planner tests."""
    return ChangedFile(
        path=path,
        old_path=path if status != "added" else None,
        status=status,  # type: ignore[arg-type]
        additions=1,
        deletions=1,
        language=language,  # type: ignore[arg-type]
        kind=kind,  # type: ignore[arg-type]
    )


def write_deep_config(root: Path) -> None:
    """Write a minimal qa-z config with smart deep selection enabled."""
    config: dict[str, Any] = {
        "project": {"name": "qa-z-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {"output_dir": ".qa-z/runs"},
        "deep": {
            "fail_on_missing_tool": True,
            "selection": {
                "default_mode": "smart",
                "full_run_threshold": 15,
                "high_risk_paths": ["qa-z.yaml"],
            },
            "checks": [
                {
                    "id": "sg_scan",
                    "enabled": True,
                    "run": ["semgrep", "--config", "auto", "--json"],
                    "kind": "static-analysis",
                }
            ],
        },
    }
    (root / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_diff(root: Path, name: str, path: str, body: str = "+new\n") -> Path:
    """Write a one-file unified diff for CLI selection tests."""
    diff_path = root / name
    diff_path.write_text(
        dedent(
            f"""\
            diff --git a/{path} b/{path}
            index 1111111..2222222 100644
            --- a/{path}
            +++ b/{path}
            @@ -1 +1,2 @@
             old
            {body.rstrip()}
            """
        ),
        encoding="utf-8",
    )
    return diff_path


def test_docs_only_deep_run_is_skipped(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(tmp_path)
    diff_path = write_diff(tmp_path, "docs.diff", "docs/readme.md")

    def fail_if_called(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise AssertionError("docs-only deep selection should not run Semgrep")

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fail_if_called)

    exit_code = main(
        [
            "deep",
            "--path",
            str(tmp_path),
            "--selection",
            "smart",
            "--diff",
            str(diff_path),
            "--output-dir",
            str(tmp_path / "runs" / "docs"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "passed"
    assert output["selection"]["mode"] == "smart"
    assert output["selection"]["skipped_checks"] == ["sg_scan"]
    assert output["checks"][0]["status"] == "skipped"
    assert output["checks"][0]["execution_mode"] == "skipped"
    assert output["checks"][0]["selection_reason"] == "docs-only change"


def test_source_change_deep_run_is_targeted(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(tmp_path)
    diff_path = write_diff(tmp_path, "source.diff", "src/app.py")
    commands: list[list[str]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        command = list(args[0])
        commands.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout='{"results": []}',
            stderr="",
        )

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fake_run)

    exit_code = main(
        [
            "deep",
            "--path",
            str(tmp_path),
            "--selection",
            "smart",
            "--diff",
            str(diff_path),
            "--output-dir",
            str(tmp_path / "runs" / "source"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert commands == [["semgrep", "--config", "auto", "--json", "src/app.py"]]
    assert output["checks"][0]["execution_mode"] == "targeted"
    assert output["checks"][0]["target_paths"] == ["src/app.py"]
    assert output["selection"]["targeted_checks"] == ["sg_scan"]


def test_config_change_deep_run_escalates_to_full(tmp_path: Path) -> None:
    plans, selection = build_deep_selection(
        check_specs=[sg_scan_spec()],
        change_set=ChangeSet(
            source="cli_diff",
            files=[changed("qa-z.yaml", language="yaml", kind="config")],
        ),
        selection_mode="smart",
        full_run_threshold=15,
        high_risk_paths=["qa-z.yaml"],
    )

    assert plans[0].execution_mode == "full"
    assert plans[0].resolved_command == ["semgrep", "--config", "auto", "--json"]
    assert "high-risk path changed: qa-z.yaml" in selection.high_risk_reasons
    assert "config files changed" in selection.high_risk_reasons
    assert selection.full_checks == ["sg_scan"]


def test_deleted_file_change_deep_run_escalates_to_full(tmp_path: Path) -> None:
    plans, selection = build_deep_selection(
        check_specs=[sg_scan_spec()],
        change_set=ChangeSet(
            source="cli_diff",
            files=[changed("src/old.py", status="deleted")],
        ),
        selection_mode="smart",
        full_run_threshold=15,
        high_risk_paths=[],
    )

    assert plans[0].execution_mode == "full"
    assert (
        plans[0].selection_reason == "full run required because high-risk files changed"
    )
    assert selection.high_risk_reasons == ["deleted files changed"]
    assert selection.full_checks == ["sg_scan"]


def test_deep_summary_includes_selection_metadata(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_deep_config(tmp_path)
    diff_path = write_diff(tmp_path, "summary.diff", "src/app.py")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout='{"results": []}',
            stderr="",
        )

    monkeypatch.setattr("qa_z.runners.subprocess.subprocess.run", fake_run)

    exit_code = main(
        [
            "deep",
            "--path",
            str(tmp_path),
            "--diff",
            str(diff_path),
            "--output-dir",
            str(tmp_path / "runs" / "summary"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    summary_path = tmp_path / output["artifact_dir"] / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert summary["selection"]["mode"] == "smart"
    assert summary["selection"]["input_source"] == "cli_diff"
    assert summary["selection"]["changed_files"][0]["path"] == "src/app.py"
    assert summary["checks"][0]["selection_reason"] == "source files changed"


def test_semgrep_targeted_selection_replaces_configured_scan_roots(
    tmp_path: Path,
) -> None:
    plans, _selection = build_deep_selection(
        check_specs=[
            CheckSpec(
                id="sg_scan",
                command=["semgrep", "--config", "auto", "--json", "src", "tests"],
                kind="static-analysis",
            )
        ],
        change_set=ChangeSet(source="cli_diff", files=[changed("src/app.py")]),
        selection_mode="smart",
        full_run_threshold=15,
        high_risk_paths=[],
    )

    assert plans[0].resolved_command == [
        "semgrep",
        "--config",
        "auto",
        "--json",
        "src/app.py",
    ]


def test_semgrep_targeted_selection_preserves_option_values(
    tmp_path: Path,
) -> None:
    plans, _selection = build_deep_selection(
        check_specs=[
            CheckSpec(
                id="sg_scan",
                command=[
                    "semgrep",
                    "--config",
                    "auto",
                    "--json",
                    "--exclude",
                    "src/generated",
                    "src",
                ],
                kind="static-analysis",
            )
        ],
        change_set=ChangeSet(source="cli_diff", files=[changed("src/app.py")]),
        selection_mode="smart",
        full_run_threshold=15,
        high_risk_paths=[],
    )

    assert plans[0].resolved_command == [
        "semgrep",
        "--config",
        "auto",
        "--json",
        "--exclude",
        "src/generated",
        "src/app.py",
    ]


def test_semgrep_targeted_selection_preserves_wrapper_command(
    tmp_path: Path,
) -> None:
    plans, _selection = build_deep_selection(
        check_specs=[
            CheckSpec(
                id="sg_scan",
                command=["uv", "run", "semgrep", "--json", "src"],
                kind="static-analysis",
            )
        ],
        change_set=ChangeSet(source="cli_diff", files=[changed("src/app.py")]),
        selection_mode="smart",
        full_run_threshold=15,
        high_risk_paths=[],
    )

    assert plans[0].resolved_command == [
        "uv",
        "run",
        "semgrep",
        "--json",
        "src/app.py",
    ]
