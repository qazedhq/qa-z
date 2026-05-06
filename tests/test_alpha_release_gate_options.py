"""Tests for alpha release gate option and output-artifact surfaces."""

from __future__ import annotations

import json

from tests.alpha_release_gate_test_support import (
    RecordingRunner,
    labels_from_result,
    load_gate_module,
)


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
        "--allow-existing-refs --skip-release-tag-check --json"
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
        "--expected-origin-url https://github.com/qazedhq/qa-z.git "
        "--skip-release-tag-check --json"
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
        "--expected-origin-url https://github.com/qazedhq/qa-z.git "
        "--skip-release-tag-check --json"
    )
    assert "--skip-remote" not in runner.commands[0]


def test_alpha_release_gate_quality_mode_skips_historical_tag_preflight(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(
        tmp_path, mode="quality", allow_dirty=True, runner=runner
    )

    assert result.exit_code == 0
    assert result.payload["mode"] == "quality"
    assert result.payload["target_tag"] is None
    assert labels_from_result(result)[0] == (
        "python scripts/alpha_release_preflight.py --skip-remote --allow-dirty "
        "--skip-release-tag-check --json"
    )
    assert "--skip-release-tag-check" in runner.commands[0]
    assert "--expected-tag" not in runner.commands[0]


def test_alpha_release_gate_release_mode_checks_target_tag(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(
        tmp_path, mode="release", target_tag="v0.10.0", runner=runner
    )

    assert result.exit_code == 0
    assert result.payload["mode"] == "release"
    assert result.payload["target_tag"] == "v0.10.0"
    assert labels_from_result(result)[0] == (
        "python scripts/alpha_release_preflight.py --skip-remote "
        "--expected-tag v0.10.0 --json"
    )
    assert "--expected-tag" in runner.commands[0]
    assert "v0.10.0" in runner.commands[0]


def test_alpha_release_gate_release_mode_includes_bundle_manifest(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(
        tmp_path, mode="release", target_tag="v0.10.0", runner=runner
    )

    labels = labels_from_result(result)
    assert result.exit_code == 0
    assert labels[0] == (
        "python scripts/alpha_release_preflight.py --skip-remote "
        "--expected-tag v0.10.0 --json"
    )
    assert labels[-1] == "python scripts/alpha_release_bundle_manifest.py --json"


def test_alpha_release_gate_release_mode_fails_when_target_tag_exists(tmp_path):
    module = load_gate_module()
    local_preflight = module.default_gate_commands(
        mode="release", target_tag="v0.10.0"
    )[0].command
    preflight_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
        "failed_checks": ["release_tag_absent"],
        "checks": [
            {
                "name": "release_tag_absent",
                "status": "failed",
                "detail": "v0.10.0",
            }
        ],
    }
    runner = RecordingRunner(
        {tuple(local_preflight): (1, json.dumps(preflight_payload), "")}
    )

    result = module.run_alpha_release_gate(
        tmp_path, mode="release", target_tag="v0.10.0", runner=runner
    )

    assert result.exit_code == 1
    assert result.payload["mode"] == "release"
    assert result.payload["target_tag"] == "v0.10.0"
    assert result.payload["failed_checks"] == ["local_preflight"]
    assert result.payload["preflight_failed_checks"] == ["release_tag_absent"]
    assert result.payload["evidence"]["gate_failures"]["local_preflight"] == {
        "kind": "local_release_tag_exists",
        "summary": "local release tag already exists: v0.10.0",
        "tag": "v0.10.0",
    }


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
        f"--skip-release-tag-check --output {preflight_output} --json"
    )
    assert "--output" in runner.commands[0]
    assert str(preflight_output) in runner.commands[0]


def test_alpha_release_gate_can_request_worktree_plan_output_artifact(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()
    worktree_plan_output = tmp_path / "evidence" / "worktree-plan.json"

    result = module.run_alpha_release_gate(
        tmp_path,
        worktree_plan_output=worktree_plan_output,
        runner=runner,
    )

    assert result.exit_code == 0
    assert result.payload["worktree_plan_output"] == str(worktree_plan_output)
    assert labels_from_result(result)[1] == (
        "python scripts/worktree_commit_plan.py --include-ignored "
        f"--output {worktree_plan_output} --json"
    )
    assert "--output" in runner.commands[1]
    assert str(worktree_plan_output) in runner.commands[1]


def test_alpha_release_gate_reads_worktree_plan_fields_from_output_file(tmp_path):
    module = load_gate_module()
    worktree_plan_output = tmp_path / "evidence" / "worktree-plan.json"
    worktree_payload = {
        "kind": "qa_z.worktree_commit_plan",
        "status": "attention_required",
        "attention_reasons": ["generated_artifacts_present"],
        "summary": {
            "changed_batch_count": 4,
            "generated_artifact_count": 9,
            "cross_cutting_count": 2,
            "unassigned_source_path_count": 1,
            "multi_batch_path_count": 0,
        },
        "next_actions": ["Review generated_artifact_paths before staging."],
    }

    class FileWritingRunner(RecordingRunner):
        def __call__(self, command, cwd):
            self.commands.append(tuple(command))
            if any(
                str(argument).endswith("worktree_commit_plan.py")
                for argument in command
            ):
                worktree_plan_output.parent.mkdir(parents=True, exist_ok=True)
                worktree_plan_output.write_text(
                    json.dumps(worktree_payload), encoding="utf-8"
                )
                return 1, "worktree commit plan needs attention\n", ""
            return 0, "ok\n", ""

    result = module.run_alpha_release_gate(
        tmp_path,
        worktree_plan_output=worktree_plan_output,
        runner=FileWritingRunner(),
    )

    assert result.exit_code == 1
    evidence = result.payload["evidence"]["worktree_commit_plan"]
    assert evidence["status"] == "attention_required"
    assert evidence["generated_artifact_count"] == 9
    assert evidence["attention_reasons"] == ["generated_artifacts_present"]
    assert result.payload["next_actions"] == [
        "Review generated_artifact_paths before staging."
    ]


def test_alpha_release_gate_quick_mode_runs_source_gate_without_slow_release_checks(
    tmp_path,
):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(tmp_path, quick=True, runner=runner)

    labels = labels_from_result(result)
    assert result.exit_code == 0
    assert result.payload["quick"] is True
    assert "python -m pytest" in labels
    assert "python -m qa_z executor-result --help" in labels
    assert "python -m qa_z fast --selection smart --json" not in labels
    assert "python -m qa_z deep --selection smart --json" not in labels
    assert "python -m qa_z benchmark --json" not in labels
    assert "python -m build --sdist --wheel" not in labels
    assert "python scripts/alpha_release_artifact_smoke.py --json" not in labels
    assert "python scripts/alpha_release_bundle_manifest.py --json" not in labels


def test_alpha_release_gate_quick_mode_reports_with_deps_as_not_run(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(
        tmp_path, quick=True, with_deps=True, runner=runner
    )

    labels = labels_from_result(result)
    assert result.payload["with_deps"] is False
    assert result.payload["with_deps_requested"] is True
    assert (
        "python scripts/alpha_release_artifact_smoke.py --with-deps --json"
        not in labels
    )
