"""End-to-end product tests for the repair -> verify workflow."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from qa_z.cli import main
from qa_z.commands.session_verify import render_verify_stdout
from qa_z.verification import VerificationArtifactPaths, compare_verification_runs
from tests.repair_prompt_test_support import write_contract, write_summary
from tests.verification_test_support import check_result, verification_run


def write_repair_verify_config(tmp_path: Path) -> None:
    """Write a dependency-light config for verify --from-run rerun tests."""
    payload = {
        "project": {"name": "repair-verify-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "checks": [
                {
                    "id": "py_test",
                    "enabled": True,
                    "kind": "test",
                    "run": [sys.executable, "-c", ""],
                }
            ],
        },
        "deep": {"checks": []},
    }
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )


def write_passed_deep_summary(tmp_path: Path, run_id: str) -> None:
    payload = {
        "schema_version": 2,
        "mode": "deep",
        "contract_path": "qa/contracts/auth.md",
        "project_root": str(tmp_path),
        "status": "passed",
        "started_at": "2026-05-27T00:00:00Z",
        "finished_at": "2026-05-27T00:00:01Z",
        "artifact_dir": f".qa-z/runs/{run_id}/deep",
        "checks": [],
        "totals": {"passed": 0, "failed": 0, "skipped": 0, "warning": 0},
    }
    summary_path = tmp_path / ".qa-z" / "runs" / run_id / "deep" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload), encoding="utf-8")


def test_verify_from_run_latest_reruns_candidate_and_reports_improved(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_repair_verify_config(tmp_path)
    write_contract(tmp_path)
    write_summary(
        tmp_path,
        "baseline",
        checks=[
            {
                "id": "py_test",
                "tool": "python",
                "command": [sys.executable, "-c", ""],
                "kind": "test",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 100,
                "stdout_tail": "assertion failed\n",
                "stderr_tail": "",
            }
        ],
    )
    write_passed_deep_summary(tmp_path, "baseline")

    exit_code = main(
        ["verify", "--path", str(tmp_path), "--from-run", "latest", "--json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["kind"] == "qa_z.verify_compare"
    assert payload["verdict"] == "improved"
    assert payload["artifacts"] == {
        "summary": ".qa-z/runs/candidate/verify/summary.json",
        "compare": ".qa-z/runs/candidate/verify/compare.json",
        "report": ".qa-z/runs/candidate/verify/report.md",
    }
    assert any(
        "qa-z summary --from-run .qa-z/runs/candidate" in action
        for action in payload["next_actions"]
    )
    assert (tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "report.md").exists()


def test_verify_stdout_labels_regression_as_worse_and_lists_next_actions(
    tmp_path: Path,
) -> None:
    baseline = verification_run(
        "baseline",
        fast_checks=[check_result("py_test", "passed", kind="test", exit_code=0)],
    )
    candidate = verification_run(
        "candidate",
        fast_checks=[check_result("py_test", "failed", kind="test", exit_code=1)],
    )
    comparison = compare_verification_runs(baseline, candidate)
    paths = VerificationArtifactPaths(
        summary_path=(
            tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json"
        ),
        compare_path=(
            tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "compare.json"
        ),
        report_path=(
            tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "report.md"
        ),
    )

    output = render_verify_stdout("regressed", paths, tmp_path, comparison=comparison)

    assert "QA-Z Verify: worse (regressed)" in output
    assert "qa-z verify: regressed" in output
    assert "Delta: 0 blocking before -> 1 after; resolved 0; new/regressed 1" in output
    assert "Next actions:" in output
    assert (
        "Repair new or regressed issues, then rerun "
        "`qa-z verify --from-run .qa-z/runs/baseline`."
    ) in output


def test_repair_prompt_codex_output_names_source_evidence_and_verify_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_repair_verify_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "baseline")

    exit_code = main(
        [
            "repair-prompt",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/baseline",
            "--adapter",
            "codex",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Fast summary: `.qa-z/runs/baseline/fast/summary.json`" in output
    assert "Evidence:" in output
    assert "## Forbidden Shortcuts" in output
    assert "Do not weaken, delete, or skip tests" in output
    assert "## Validation Commands" in output
    assert "`qa-z verify --from-run .qa-z/runs/baseline`" in output


def test_auth_bug_demo_has_deterministic_fix_and_verify_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert main(["demo", "auth-bug", "--path", str(tmp_path)]) == 0
    demo_root = tmp_path / ".qa-z" / "demo" / "auth-bug"
    capsys.readouterr()

    shutil.copyfile(demo_root / "app" / "auth.fixed.py", demo_root / "app" / "auth.py")
    monkeypatch.chdir(demo_root)

    exit_code = main(["verify", "--from-run", "latest", "--config", "qa-z.demo.yaml"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "QA-Z Verify: improved" in output
    assert "Resolved: 1" in output
    assert "Report: .qa-z/runs/candidate/verify/report.md" in output
    summary = json.loads(
        (
            demo_root / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json"
        ).read_text(encoding="utf-8")
    )
    assert summary["verdict"] == "improved"
