"""CLI tests for the one-command QA-Z guard workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from qa_z.cli import main
from qa_z.guard.risk_classifier import classify_change_risk


def python_command(source: str) -> list[str]:
    return [sys.executable, "-c", source]


def write_config(
    root: Path,
    *,
    fast_checks: list[dict] | None = None,
    deep_checks: list[dict] | None = None,
) -> None:
    config = {
        "project": {"name": "guard-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "fail_on_missing_tool": True,
            "checks": fast_checks
            if fast_checks is not None
            else [{"id": "py_test", "kind": "test", "run": python_command("")}],
        },
        "deep": {
            "fail_on_missing_tool": True,
            "checks": deep_checks if deep_checks is not None else [],
        },
    }
    (root / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_contract(root: Path) -> None:
    contract_dir = root / "qa" / "contracts"
    contract_dir.mkdir(parents=True, exist_ok=True)
    (contract_dir / "contract.md").write_text(
        dedent(
            """
            # QA Contract: Guard test

            ## Acceptance Checks

            - Run deterministic fast checks.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_guard_happy_path_writes_merge_ok_verdict(tmp_path: Path, capsys) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)

    exit_code = main(["guard", "--path", str(tmp_path), "--deep", "never", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "merge_ok"
    assert output["fast"]["status"] == "passed"
    assert output["deep"]["ran"] is False
    assert output["artifacts"]["verdict_json"] == ".qa-z/runs/latest/guard/verdict.json"
    assert (tmp_path / ".qa-z" / "runs" / "latest" / "guard" / "verdict.json").exists()
    assert (tmp_path / ".qa-z" / "runs" / "latest" / "guard" / "verdict.md").exists()


def test_guard_marks_stale_current_truth_context_as_needs_review(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-22T00:00:00Z",
            "items": [
                {
                    "id": "fresh-work",
                    "title": "Fresh backlog work",
                    "category": "workflow_gap",
                    "status": "open",
                    "priority_score": 50,
                }
            ],
        },
    )
    write_json(
        tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json",
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": "inspect-old",
            "generated_at": "2026-04-21T00:00:00Z",
            "live_repository": {"modified_count": 0, "untracked_count": 0},
        },
    )

    exit_code = main(["guard", "--path", str(tmp_path), "--deep", "never", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "needs_review"
    assert output["current_truth"]["status"] == "stale"
    assert output["current_truth"]["source_self_inspection"] == (
        ".qa-z/loops/latest/self_inspect.json"
    )
    assert output["current_truth"]["source_self_inspection_stale_for_backlog"] is True
    assert (
        "Current-truth self-inspection is stale for the improvement backlog."
        in output["reasons"]
    )


def test_guard_marks_missing_self_inspection_as_stale_current_truth(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-22T00:00:00Z",
            "items": [
                {
                    "id": "fresh-work",
                    "title": "Fresh backlog work",
                    "category": "workflow_gap",
                    "status": "open",
                    "priority_score": 50,
                }
            ],
        },
    )

    exit_code = main(["guard", "--path", str(tmp_path), "--deep", "never", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "needs_review"
    assert output["current_truth"]["status"] == "stale"
    assert output["current_truth"]["source_self_inspection"] == (
        ".qa-z/loops/latest/self_inspect.json"
    )
    assert output["current_truth"]["source_self_inspection_stale_for_backlog"] is True
    assert output["current_truth"]["source_self_inspection_refresh_commands"] == [
        "python -m qa_z select-next --refresh --count 3 --json"
    ]
    verdict_md = (
        tmp_path / ".qa-z" / "runs" / "latest" / "guard" / "verdict.md"
    ).read_text(encoding="utf-8")
    assert "- Current truth: `stale`" in verdict_md
    assert (
        "- Current truth source: `.qa-z/loops/latest/self_inspect.json`" in verdict_md
    )
    assert (
        "- Current truth refresh: `python -m qa_z select-next --refresh --count 3 --json`"
        in verdict_md
    )


def test_guard_failed_fast_check_returns_do_not_merge(tmp_path: Path, capsys) -> None:
    write_config(
        tmp_path,
        fast_checks=[
            {
                "id": "py_test",
                "kind": "test",
                "run": python_command("import sys; sys.exit(1)"),
            }
        ],
    )
    write_contract(tmp_path)

    exit_code = main(["guard", "--path", str(tmp_path), "--deep", "never", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "do_not_merge"
    assert output["repair"]["written"] is True
    assert (tmp_path / ".qa-z" / "runs" / "latest" / "repair" / "repair.json").exists()


def test_guard_repair_json_reports_adapter_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_config(
        tmp_path,
        fast_checks=[
            {
                "id": "py_test",
                "kind": "test",
                "run": python_command("import sys; sys.exit(1)"),
            }
        ],
    )
    write_contract(tmp_path)
    codex_path = tmp_path / ".qa-z" / "runs" / "latest" / "repair" / "codex.md"
    original_write_text = Path.write_text

    def fail_codex_handoff(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path == codex_path:
            raise OSError("disk full")
        return original_write_text(
            path, data, encoding=encoding, errors=errors, newline=newline
        )

    monkeypatch.setattr(Path, "write_text", fail_codex_handoff)

    exit_code = main(["guard", "--path", str(tmp_path), "--deep", "never", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "kind": "qa_z.guard_error",
        "error": "artifact_write_error",
        "exit_code": 2,
        "message": output["message"],
    }
    assert "qa-z guard: artifact error:" in output["message"]
    assert "could not write guard repair codex artifact" in output["message"]
    assert str(codex_path) in output["message"]
    assert "disk full" in output["message"]


def test_guard_from_run_replays_existing_fast_summary(tmp_path: Path, capsys) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)

    assert main(["guard", "--path", str(tmp_path), "--deep", "never", "--json"]) == 0
    capsys.readouterr()

    write_config(
        tmp_path,
        fast_checks=[
            {
                "id": "py_test",
                "kind": "test",
                "run": python_command("import sys; sys.exit(1)"),
            }
        ],
    )
    exit_code = main(
        [
            "guard",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/latest",
            "--deep",
            "never",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "merge_ok"
    assert output["fast"]["status"] == "passed"
    assert output["artifacts"]["run_dir"] == ".qa-z/runs/latest"


def test_guard_fail_on_risk_exits_nonzero_for_blocking_verdict(
    tmp_path: Path, capsys
) -> None:
    write_config(
        tmp_path,
        fast_checks=[
            {
                "id": "py_test",
                "kind": "test",
                "run": python_command("import sys; sys.exit(1)"),
            }
        ],
    )
    write_contract(tmp_path)

    exit_code = main(
        [
            "guard",
            "--path",
            str(tmp_path),
            "--deep",
            "never",
            "--fail-on-risk",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["status"] == "do_not_merge"


def test_guard_deep_failure_blocks_merge(tmp_path: Path, capsys) -> None:
    write_config(
        tmp_path,
        deep_checks=[
            {
                "id": "custom_deep",
                "kind": "static-analysis",
                "run": python_command("import sys; sys.exit(1)"),
            }
        ],
    )
    write_contract(tmp_path)

    exit_code = main(["guard", "--path", str(tmp_path), "--deep", "always", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "do_not_merge"
    assert output["deep"]["ran"] is True
    assert output["deep"]["status"] == "failed"


def test_guard_no_checks_configured_needs_review(tmp_path: Path, capsys) -> None:
    write_config(tmp_path, fast_checks=[])
    write_contract(tmp_path)

    exit_code = main(["guard", "--path", str(tmp_path), "--deep", "never", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "needs_review"
    assert "No supported fast checks" in output["reasons"][0]


def test_guard_json_config_error_reports_machine_payload(
    tmp_path: Path, capsys
) -> None:
    (tmp_path / "qa-z.yaml").write_text("project: [unterminated\n", encoding="utf-8")

    exit_code = main(["guard", "--path", str(tmp_path), "--deep", "never", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["kind"] == "qa_z.guard_error"
    assert output["error"] == "configuration_error"
    assert output["exit_code"] == 2
    assert "qa-z guard: configuration error:" in output["message"]


def test_guard_json_reports_verdict_artifact_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    output_dir = tmp_path / ".qa-z" / "runs" / "latest" / "guard"
    original_write_text = Path.write_text

    def fail_verdict_json(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path == output_dir / "verdict.json":
            raise OSError("disk full")
        return original_write_text(
            path, data, encoding=encoding, errors=errors, newline=newline
        )

    monkeypatch.setattr(Path, "write_text", fail_verdict_json)

    exit_code = main(["guard", "--path", str(tmp_path), "--deep", "never", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "kind": "qa_z.guard_error",
        "error": "artifact_write_error",
        "exit_code": 2,
        "message": output["message"],
    }
    assert "qa-z guard: artifact error:" in output["message"]
    assert "could not write guard verdict artifacts" in output["message"]
    assert "disk full" in output["message"]


def test_guard_github_summary_option_writes_summary(tmp_path: Path, capsys) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)

    exit_code = main(
        [
            "guard",
            "--path",
            str(tmp_path),
            "--deep",
            "never",
            "--github-summary",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "QA-Z Guard" in output
    assert (
        tmp_path / ".qa-z" / "runs" / "latest" / "guard" / "github-summary.md"
    ).exists()


def test_guard_github_summary_json_reports_artifact_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    summary_path = (
        tmp_path / ".qa-z" / "runs" / "latest" / "guard" / ("github-summary.md")
    )
    original_write_text = Path.write_text

    def fail_github_summary(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path == summary_path:
            raise OSError("disk full")
        return original_write_text(
            path, data, encoding=encoding, errors=errors, newline=newline
        )

    monkeypatch.setattr(Path, "write_text", fail_github_summary)

    exit_code = main(
        [
            "guard",
            "--path",
            str(tmp_path),
            "--deep",
            "never",
            "--github-summary",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "kind": "qa_z.guard_error",
        "error": "artifact_write_error",
        "exit_code": 2,
        "message": output["message"],
    }
    assert "qa-z guard: artifact error:" in output["message"]
    assert "could not write guard GitHub summary artifact" in output["message"]
    assert str(summary_path) in output["message"]
    assert "disk full" in output["message"]


def test_guard_risk_classifier_detects_auth_api_and_public_surface() -> None:
    risk = classify_change_risk(
        [
            "src/auth/session.py",
            "src/api/users.py",
            "README.md",
        ]
    )

    assert risk.changed_files == [
        "src/auth/session.py",
        "src/api/users.py",
        "README.md",
    ]
    assert risk.categories == ["auth", "API behavior", "public surface"]
