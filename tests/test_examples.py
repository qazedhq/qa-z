"""Integration tests for shipped example workflows."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

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


def test_fastapi_demo_readme_states_dependency_light_deterministic_boundary() -> None:
    demo = ROOT / "examples" / "fastapi-demo"
    readme = (demo / "README.md").read_text(encoding="utf-8")
    config = yaml.safe_load((demo / "qa-z.yaml").read_text(encoding="utf-8"))
    failing_config = yaml.safe_load(
        (demo / "qa-z.failing.yaml").read_text(encoding="utf-8")
    )

    assert [check["id"] for check in config["fast"]["checks"]] == [
        "py_lint",
        "py_format",
        "py_test",
    ]
    assert [check["id"] for check in failing_config["fast"]["checks"]] == [
        "py_lint",
        "py_format",
        "py_test_bug_demo",
    ]
    assert config["checks"]["deep"] == []
    assert failing_config["checks"]["deep"] == []
    assert "dependency-light" in readme
    assert "works without installing a web server" in readme
    assert "deterministic fast and repair-prompt demo" in readme
    assert "does not configure deep checks" in readme
    assert "does not call live agents" in readme
    assert (
        "does not run `repair-session`, `executor-bridge`, or `executor-result`"
        in readme
    )


def test_nextjs_demo_readme_is_honest_placeholder() -> None:
    demo = ROOT / "examples" / "nextjs-demo"
    readme = (demo / "README.md").read_text(encoding="utf-8")

    assert sorted(path.name for path in demo.iterdir()) == ["README.md"]
    assert "placeholder-only" in readme
    assert "not a runnable Next.js project" in readme
    assert "does not include `package.json`" in readme
    assert "does not include `qa-z.yaml`" in readme
    assert "does not call live agents" in readme
    assert "does not run `executor-bridge` or `executor-result`" in readme
    assert "not wired" in readme.lower()
    assert "examples/typescript-demo" in readme
    assert "Stryker" not in readme
    assert "Playwright smoke coverage" not in readme


def test_typescript_demo_readme_states_fast_only_live_free_boundary() -> None:
    demo = ROOT / "examples" / "typescript-demo"
    readme = (demo / "README.md").read_text(encoding="utf-8")
    config = yaml.safe_load((demo / "qa-z.yaml").read_text(encoding="utf-8"))

    assert [check["id"] for check in config["fast"]["checks"]] == [
        "ts_lint",
        "ts_type",
        "ts_test",
    ]
    assert config["checks"]["deep"] == []
    assert "TypeScript fast gate" in readme
    assert "fast-only demo" in readme
    assert "not a Next.js demo" in readme
    assert "does not configure TypeScript-specific deep automation" in readme
    assert "does not call live agents" in readme
    assert "does not run `executor-bridge` or `executor-result`" in readme
