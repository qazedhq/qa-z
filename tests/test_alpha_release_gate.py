"""Tests for the alpha release local gate runner."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_gate.py"


def load_gate_module():
    spec = importlib.util.spec_from_file_location("alpha_release_gate", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordingRunner:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.commands = []

    def __call__(self, command, cwd):
        self.commands.append(tuple(command))
        return self.responses.get(tuple(command), (0, "ok\n", ""))


def labels_from_result(result):
    return [check["label"] for check in result.payload["checks"]]


def test_alpha_release_gate_runs_release_checks_in_publish_order(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 0
    assert result.summary == "alpha release gate passed"
    assert labels_from_result(result) == [
        "python scripts/alpha_release_preflight.py --skip-remote --json",
        "python -m ruff format --check .",
        "python -m ruff check .",
        "python -m mypy src tests",
        "python -m pytest",
        "python -m qa_z --help",
        "python -m qa_z init --help",
        "python -m qa_z plan --help",
        "python -m qa_z fast --help",
        "python -m qa_z deep --help",
        "python -m qa_z review --help",
        "python -m qa_z repair-prompt --help",
        "python -m qa_z repair-session --help",
        "python -m qa_z github-summary --help",
        "python -m qa_z verify --help",
        "python -m qa_z benchmark --help",
        "python -m qa_z self-inspect --help",
        "python -m qa_z select-next --help",
        "python -m qa_z backlog --help",
        "python -m qa_z autonomy --help",
        "python -m qa_z executor-bridge --help",
        "python -m qa_z executor-result --help",
        "python -m qa_z fast --selection smart --json",
        "python -m qa_z deep --selection smart --json",
        "python -m qa_z benchmark --json",
        "python -m build --sdist --wheel",
        "python scripts/alpha_release_artifact_smoke.py --json",
        "python scripts/alpha_release_bundle_manifest.py --json",
    ]
    assert [tuple(command) for command in result.commands] == runner.commands


def test_alpha_release_gate_records_failures_but_continues_running(tmp_path):
    module = load_gate_module()
    failing_command = module.default_gate_commands()[4].command
    runner = RecordingRunner(
        {tuple(failing_command): (1, "", "pytest failed with one regression\n")}
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert result.summary == "alpha release gate failed"
    assert result.payload["check_count"] == len(module.default_gate_commands())
    assert result.payload["passed_count"] == len(module.default_gate_commands()) - 1
    assert result.payload["failed_count"] == 1
    assert result.payload["failed_checks"] == ["pytest"]
    assert len(runner.commands) == len(module.default_gate_commands())
    failed_checks = [
        check for check in result.payload["checks"] if check["status"] == "failed"
    ]
    assert failed_checks == [
        {
            "name": "pytest",
            "label": "python -m pytest",
            "status": "failed",
            "exit_code": 1,
            "stdout_tail": "",
            "stderr_tail": "pytest failed with one regression",
        }
    ]


def test_alpha_release_gate_can_include_dependency_smoke(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(tmp_path, with_deps=True, runner=runner)

    assert result.exit_code == 0
    labels = labels_from_result(result)
    assert "python scripts/alpha_release_artifact_smoke.py --with-deps --json" in labels
    assert labels.index("python scripts/alpha_release_artifact_smoke.py --json") < (
        labels.index(
            "python scripts/alpha_release_artifact_smoke.py --with-deps --json"
        )
    )


def test_alpha_release_gate_can_allow_dirty_worktree_for_development(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(tmp_path, allow_dirty=True, runner=runner)

    assert result.exit_code == 0
    assert labels_from_result(result)[0] == (
        "python scripts/alpha_release_preflight.py --skip-remote --allow-dirty --json"
    )
    assert "--allow-dirty" in runner.commands[0]


def test_alpha_release_gate_can_include_remote_preflight(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(
        tmp_path,
        include_remote=True,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/qazedhq/qa-z.git",
        allow_existing_refs=True,
        runner=runner,
    )

    assert result.exit_code == 0
    assert labels_from_result(result)[0] == (
        "python scripts/alpha_release_preflight.py "
        "--repository-url https://github.com/qazedhq/qa-z.git "
        "--expected-origin-url https://github.com/qazedhq/qa-z.git "
        "--allow-existing-refs --json"
    )
    assert "--skip-remote" not in runner.commands[0]
    assert "--allow-existing-refs" in runner.commands[0]
    assert "--expected-origin-url" in runner.commands[0]


def test_alpha_release_gate_include_remote_defaults_origin_to_repository_url(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(
        tmp_path,
        include_remote=True,
        repository_url="https://github.com/qazedhq/qa-z.git",
        runner=runner,
    )

    assert result.exit_code == 0
    assert labels_from_result(result)[0] == (
        "python scripts/alpha_release_preflight.py "
        "--repository-url https://github.com/qazedhq/qa-z.git "
        "--expected-origin-url https://github.com/qazedhq/qa-z.git --json"
    )
    assert "--expected-origin-url" in runner.commands[0]


def test_alpha_release_gate_remote_options_imply_remote_preflight(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(
        tmp_path,
        expected_origin_url="https://github.com/qazedhq/qa-z.git",
        runner=runner,
    )

    assert result.exit_code == 0
    assert result.payload["include_remote"] is True
    assert labels_from_result(result)[0] == (
        "python scripts/alpha_release_preflight.py "
        "--repository-url https://github.com/qazedhq/qa-z.git "
        "--expected-origin-url https://github.com/qazedhq/qa-z.git --json"
    )
    assert "--skip-remote" not in runner.commands[0]


def test_alpha_release_gate_can_request_preflight_output_artifact(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()
    preflight_output = tmp_path / "evidence" / "preflight.json"

    result = module.run_alpha_release_gate(
        tmp_path,
        preflight_output=preflight_output,
        runner=runner,
    )

    assert result.exit_code == 0
    assert result.payload["preflight_output"] == str(preflight_output)
    assert labels_from_result(result)[0] == (
        "python scripts/alpha_release_preflight.py --skip-remote "
        f"--output {preflight_output} --json"
    )
    assert "--output" in runner.commands[0]
    assert str(preflight_output) in runner.commands[0]


def test_alpha_release_gate_cli_can_emit_json_and_write_output(
    monkeypatch, tmp_path, capsys
):
    module = load_gate_module()
    output_path = tmp_path / "evidence.json"

    def fake_run_alpha_release_gate(_repo_root, **kwargs):
        assert kwargs["with_deps"] is True
        assert kwargs["allow_dirty"] is True
        assert kwargs["include_remote"] is True
        assert kwargs["repository_url"] == "https://github.com/qazedhq/qa-z.git"
        assert kwargs["expected_origin_url"] == "https://github.com/qazedhq/qa-z.git"
        assert kwargs["allow_existing_refs"] is True
        assert kwargs["preflight_output"] == output_path.with_suffix(".preflight.json")
        return module.AlphaReleaseGateResult(
            summary="alpha release gate passed",
            exit_code=0,
            commands=[],
            payload={
                "summary": "alpha release gate passed",
                "exit_code": 0,
                "checks": [],
            },
        )

    monkeypatch.setattr(module, "run_alpha_release_gate", fake_run_alpha_release_gate)

    exit_code = module.main(
        [
            "--with-deps",
            "--allow-dirty",
            "--include-remote",
            "--repository-url",
            "https://github.com/qazedhq/qa-z.git",
            "--expected-origin-url",
            "https://github.com/qazedhq/qa-z.git",
            "--allow-existing-refs",
            "--json",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["summary"] == "alpha release gate passed"
    assert json.loads(output_path.read_text()) == payload
