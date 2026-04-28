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
