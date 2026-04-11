"""Integration tests for shipped example workflows."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from qa_z.cli import main

ROOT = Path(__file__).resolve().parents[1]


def copy_fastapi_demo(tmp_path: Path) -> Path:
    demo = tmp_path / "fastapi-demo"
    shutil.copytree(
        ROOT / "examples" / "fastapi-demo",
        demo,
        ignore=shutil.ignore_patterns(".qa-z", "qa", "__pycache__"),
    )
    return demo


def test_fastapi_demo_passing_flow_runs_to_green(tmp_path, capsys) -> None:
    demo = copy_fastapi_demo(tmp_path)

    plan_exit = main(
        [
            "plan",
            "--path",
            str(demo),
            "--title",
            "Protect invoice access",
            "--issue",
            str(demo / "issue.md"),
            "--spec",
            str(demo / "spec.md"),
        ]
    )
    capsys.readouterr()
    fast_exit = main(
        [
            "fast",
            "--path",
            str(demo),
            "--output-dir",
            str(demo / ".qa-z" / "runs" / "pass"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert plan_exit == 0
    assert fast_exit == 0
    assert output["status"] == "passed"


def test_fastapi_demo_failing_flow_generates_repair_packet(tmp_path, capsys) -> None:
    demo = copy_fastapi_demo(tmp_path)
    main(
        [
            "plan",
            "--path",
            str(demo),
            "--title",
            "Protect invoice access",
            "--issue",
            str(demo / "issue.md"),
            "--spec",
            str(demo / "spec.md"),
        ]
    )
    capsys.readouterr()

    fast_exit = main(
        [
            "fast",
            "--path",
            str(demo),
            "--config",
            str(demo / "qa-z.failing.yaml"),
            "--output-dir",
            str(demo / ".qa-z" / "runs" / "fail"),
            "--json",
        ]
    )
    fast_output = json.loads(capsys.readouterr().out)
    repair_exit = main(
        [
            "repair-prompt",
            "--path",
            str(demo),
            "--from-run",
            str(demo / ".qa-z" / "runs" / "fail"),
            "--json",
        ]
    )
    repair_packet = json.loads(capsys.readouterr().out)

    assert fast_exit == 1
    assert fast_output["status"] == "failed"
    assert repair_exit == 0
    assert repair_packet["repair_needed"] is True
    assert repair_packet["suggested_fix_order"] == ["py_test_bug_demo"]
